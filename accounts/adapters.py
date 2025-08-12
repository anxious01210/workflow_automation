# accounts/adapters.py
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpResponseForbidden

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse

from accounts.models import ROLE_EXTERNAL


def _allowed_domains_from_settings() -> set[str]:
    """
    Read ALLOWED_SSO_DOMAINS from settings.
    Accepts set/list/tuple OR a comma-separated string.
    Returns a lowercase set. Empty set => no restriction.
    """
    raw = getattr(settings, "ALLOWED_SSO_DOMAINS", None)
    if not raw:
        return set()
    if isinstance(raw, (set, list, tuple)):
        items = raw
    elif isinstance(raw, str):
        items = [x.strip() for x in raw.split(",")]
    else:
        return set()
    return {x.strip().lower() for x in items if isinstance(x, str) and x.strip()}


def _extract_email(sociallogin) -> str:
    data = sociallogin.account.extra_data or {}
    # try common fields for Microsoft/Google
    email = (
            data.get("mail")
            or data.get("userPrincipalName")
            or data.get("email")
            or sociallogin.user.email
            or ""
    )
    return (email or "").strip().lower()


def _extract_oid(sociallogin) -> str | None:
    # Microsoft often provides 'id' or 'oid'; Google may use 'sub'
    data = sociallogin.account.extra_data or {}
    return data.get("id") or data.get("oid") or data.get("sub")


class AccountAdapter(DefaultAccountAdapter):
    """
    Used for LOCAL (email+password) sign-ups only.
    Put such users into the external role group by default.
    """

    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit)
        # If not a social signup, add to external group
        social = getattr(user, "socialaccount_set", None)
        if not social or not social.exists():
            g, _ = Group.objects.get_or_create(name=ROLE_EXTERNAL)
            g.user_set.add(user)
        return user

    def is_open_for_signup(self, request):
        # Gate LOCAL email+password sign-ups via a setting
        return bool(getattr(settings, "LOCAL_ACCOUNT_ALLOW_SIGNUP", False))


class LinkByEmailAdapter(DefaultSocialAccountAdapter):
    """
    Used for SOCIAL logins (Microsoft, Google).
    - Enforces ALLOWED_SSO_DOMAINS from settings (if non-empty).
    - Links to an existing user by Azure OID first, then by email.
    - Blocks creation of new users via SSO unless already provisioned.
    """

    def pre_social_login(self, request, sociallogin):
        # Already linked? nothing to do.
        if sociallogin.is_existing:
            return

        allowed = _allowed_domains_from_settings()
        email = _extract_email(sociallogin)

        # 1) Domain allow-list
        if email and allowed:
            domain = email.split("@")[-1]
            if domain not in allowed:
                raise ImmediateHttpResponse(
                    HttpResponseForbidden("This email domain is not allowed for SSO.")
                )

        User = get_user_model()

        # 2) Strong link by Azure OID (if present)
        oid = _extract_oid(sociallogin)
        if oid:
            try:
                user = User.objects.get(azure_oid=oid)
                sociallogin.connect(request, user)
                return
            except User.DoesNotExist:
                pass

        # 3) Fallback link by email (must already exist from your sync/admin)
        if email:
            try:
                user = User.objects.get(email=email)
                sociallogin.connect(request, user)
                return
            except User.DoesNotExist:
                pass
        # If no match, is_open_for_signup decides whether to allow auto-creation.

    def is_open_for_signup(self, request, sociallogin):
        # Require pre-provisioned accounts (via Azure sync or admin).
        # Change to True (from the settings.py) if you later want to auto-create users from SSO.
        conf = getattr(settings, "SOCIAL_SSO_ALLOW_SIGNUP", False)
        if isinstance(conf, dict):
            # per-provider override, e.g. {"microsoft": False, "google": True}
            return bool(conf.get(sociallogin.account.provider, False))
        return bool(conf)
