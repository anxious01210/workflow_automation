from typing import Dict, Any, List
from django.contrib.auth.models import AnonymousUser
from .registry import get_all_features


def portal_menu(request) -> Dict[str, Any]:
    user = getattr(request, "user", None)
    visible: List[dict] = []

    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return {"PORTAL_MENU": visible}

    if not user.has_perm("portals.portal_access"):
        return {"PORTAL_MENU": visible}

    for item in get_all_features():
        perms = item.get("required_perms") or []
        if not perms or user.has_perms(perms):
            visible.append(item)

    return {"PORTAL_MENU": visible}
