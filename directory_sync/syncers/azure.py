import os, time, requests
from msal import ConfidentialClientApplication
from accounts.models import User

GRAPH_SCOPE = ["https://graph.microsoft.com/.default"]
GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class AzureSyncer:
    def __init__(self, directory):
        self.d = directory
        c = directory.credentials or {}
        self.tenant_id = c.get("tenant_id")
        self.client_id = c.get("client_id")
        self.client_secret = c.get("client_secret")

    def _token(self):
        app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
        )
        result = app.acquire_token_for_client(scopes=GRAPH_SCOPE)
        if "access_token" not in result:
            raise RuntimeError(f"Azure token error: {result}")
        return result["access_token"]

    def _get(self, url, token, params=None, retry=1):
        r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params or {})
        if r.status_code == 429 and retry <= 3:
            time.sleep(int(r.headers.get("Retry-After", "2")))
            return self._get(url, token, params, retry + 1)
        r.raise_for_status()
        return r.json()

    def test_connection(self):
        token = self._token()
        # simple call
        _ = self._get(f"{GRAPH_BASE}/organization", token)
        return True

    def sync(self):
        token = self._token()

        # Start from saved delta_link if present, else do an initial delta crawl
        base_select = "id,mail,userPrincipalName,givenName,surname,displayName,jobTitle,department,accountEnabled"
        if self.d.delta_link:
            url = self.d.delta_link
            params = None  # deltaLink already encodes params
        else:
            url = f"{GRAPH_BASE}/users/delta"
            params = {"$select": base_select, "$top": 999}

        created = updated = deactivated = 0
        notes = []
        include_groups = self.d.include_groups
        include_licenses = self.d.include_licenses

        def apply_user_fields(obj, u):
            # identity + status
            obj.identity_source = "AZURE"
            obj.is_active = bool(u.get("accountEnabled", True))
            obj.azure_oid = u.get("id")
            obj.tenant_id = self.d.credentials.get("tenant_id")

            # org fields
            obj.job_title = (u.get("jobTitle") or "").strip() or None
            obj.department = (u.get("department") or "").strip() or None

            # names
            fn = (u.get("givenName") or "").strip()
            ln = (u.get("surname") or "").strip()
            if not fn and not ln and u.get("displayName"):
                parts = u["displayName"].strip().split()
                if parts:
                    fn = parts[0]
                    ln = " ".join(parts[1:])
            # never None; AbstractUser uses null=False for these fields
            obj.first_name = fn[:150]  # default max_length is 150
            obj.last_name = ln[:150]

        # collect errors across the whole run (all pages)
        errors_total = 0
        sample_errors = []

        while True:
            data = self._get(url, token, params=params)

            for u in data.get("value", []):
                try:
                    # 1) delta removals
                    if "@removed" in u:
                        if self.d.deprovision_missing:
                            q = User.objects.filter(identity_source="AZURE", azure_oid=u.get("id"))
                            deactivated += q.update(is_active=False)
                        continue

                    # 2) basic identity
                    email = (u.get("mail") or u.get("userPrincipalName") or "").strip().lower()
                    if not email:
                        # skip users with no usable email
                        continue

                    obj, is_created = User.objects.get_or_create(
                        email=email,
                        defaults={"identity_source": "AZURE", "is_active": bool(u.get("accountEnabled", True))},
                    )

                    # 3) map fields (names included; never None for names)
                    apply_user_fields(obj, u)

                    # 4) optional extras (only for changed users)
                    # manager
                    manager_email = None
                    try:
                        mgr = self._get(f"{GRAPH_BASE}/users/{u['id']}/manager", token)
                        manager_email = (mgr.get("mail") or mgr.get("userPrincipalName") or "").strip().lower() or None
                    except requests.HTTPError as e:
                        if e.response.status_code != 404:
                            raise
                    obj.manager_email = manager_email

                    # licenses
                    if include_licenses:
                        try:
                            lic = self._get(f"{GRAPH_BASE}/users/{u['id']}/licenseDetails", token)
                            obj.licenses = [x.get("skuPartNumber") for x in lic.get("value", []) if
                                            x.get("skuPartNumber")]
                        except requests.HTTPError:
                            # ignore per-user license errors
                            pass

                    # groups
                    if include_groups:
                        try:
                            r = requests.post(
                                f"{GRAPH_BASE}/users/{u['id']}/getMemberGroups",
                                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                                json={"securityEnabledOnly": False},
                            )
                            if r.status_code == 200:
                                obj.groups_cache = r.json().get("value", [])
                        except requests.HTTPError:
                            # ignore per-user group errors
                            pass

                    # 5) save and count
                    obj.save()
                    created += int(is_created)
                    updated += int(not is_created)

                except Exception as e:
                    # log and continue with the next user
                    errors_total += 1
                    if len(sample_errors) < 5:
                        ident = (u.get("mail") or u.get("userPrincipalName") or u.get("id") or "<unknown>")
                        sample_errors.append(f"{ident}: {e.__class__.__name__}: {e}")
                    continue  # keep processing the rest

            # paging / delta handling
            next_url = data.get("@odata.nextLink")
            delta_url = data.get("@odata.deltaLink")
            if next_url:
                url, params = next_url, None
                continue
            if delta_url:
                self.d.delta_link = delta_url
                self.d.save(update_fields=["delta_link"])
            break

        # attach error summary to notes (shown in admin)
        if errors_total:
            notes.append(f"errors={errors_total}; samples: " + "; ".join(sample_errors))

        return dict(created=created, updated=updated, deactivated=deactivated, notes="\n".join(notes))
