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
            return self._get(url, token, params, retry+1)
        r.raise_for_status()
        return r.json()

    def test_connection(self):
        token = self._token()
        # simple call
        _ = self._get(f"{GRAPH_BASE}/organization", token)
        return True

    def sync(self):
        token = self._token()
        url = f"{GRAPH_BASE}/users"
        params = {"$select": "id,mail,userPrincipalName,jobTitle,department,accountEnabled", "$top": 50}

        created = updated = 0
        seen_emails = set()
        notes = []

        include_groups = self.d.include_groups
        include_licenses = self.d.include_licenses

        while True:
            data = self._get(url, token, params=params)
            for u in data.get("value", []):
                email = (u.get("mail") or u.get("userPrincipalName") or "").strip().lower()
                if not email: continue
                seen_emails.add(email)

                obj, is_created = User.objects.get_or_create(
                    email=email,
                    defaults={"identity_source": "AZURE", "is_active": bool(u.get("accountEnabled", True))},
                )

                obj.identity_source = "AZURE"
                obj.is_active = bool(u.get("accountEnabled", True))
                obj.azure_oid = u.get("id")
                obj.tenant_id = self.d.credentials.get("tenant_id")
                obj.job_title = (u.get("jobTitle") or "").strip() or None
                obj.department = (u.get("department") or "").strip() or None

                # Manager
                manager_email = None
                try:
                    mgr = self._get(f"{GRAPH_BASE}/users/{u['id']}/manager", token)
                    manager_email = (mgr.get("mail") or mgr.get("userPrincipalName") or "").strip().lower() or None
                except requests.HTTPError as e:
                    if e.response.status_code != 404: raise
                obj.manager_email = manager_email

                # Licenses
                if include_licenses:
                    try:
                        lic = self._get(f"{GRAPH_BASE}/users/{u['id']}/licenseDetails", token)
                        obj.licenses = [x.get("skuPartNumber") for x in lic.get("value", []) if x.get("skuPartNumber")]
                    except requests.HTTPError:
                        pass

                # Groups (IDs)
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
                        pass

                obj.save()
                created += int(is_created)
                updated += int(not is_created)

            next_url = data.get("@odata.nextLink")
            if not next_url: break
            url, params = next_url, None

        deactivated = 0
        if self.d.deprovision_missing:
            qs = User.objects.filter(identity_source="AZURE").exclude(email__in=seen_emails)
            deactivated = qs.update(is_active=False)

        return dict(created=created, updated=updated, deactivated=deactivated, notes="\n".join(notes))
