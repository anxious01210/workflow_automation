# accounts/context_processors.py
from django.conf import settings


def ui_flags(request):
    allowed_sso = getattr(settings, "ALLOWED_SSO_DOMAINS", [])
    if isinstance(allowed_sso, (set, tuple)):
        allowed_sso = list(allowed_sso)

    social_allow = getattr(settings, "SOCIAL_SSO_ALLOW_SIGNUP", False)
    if isinstance(social_allow, dict):
        social_allow = dict(social_allow)

    return {
        "LOCAL_ACCOUNT_ALLOW_SIGNUP": bool(getattr(settings, "LOCAL_ACCOUNT_ALLOW_SIGNUP", False)),
        "LOCAL_ACCOUNT_ALLOW_LOGIN": bool(getattr(settings, "LOCAL_ACCOUNT_ALLOW_LOGIN", False)),  # 👈 NEW
        "SOCIAL_SSO_ALLOW_SIGNUP": social_allow,
        "ALLOWED_SSO_DOMAINS": allowed_sso,
    }
