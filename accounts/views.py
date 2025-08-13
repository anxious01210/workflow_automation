# accounts/views.py
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch
from django.views import View
from django.views.generic import TemplateView

from .models import ROLE_STUDENT, ROLE_FACULTY, ROLE_STAFF, ROLE_PARENT, ROLE_EXTERNAL

# Default mapping (override with settings.ACCOUNTS_ROLE_REDIRECTS if you want)
DEFAULT_ROLE_REDIRECTS = {
    ROLE_STUDENT: "student:dashboard",
    ROLE_FACULTY: "faculty:dashboard",
    ROLE_STAFF: "staff:dashboard",
    ROLE_PARENT: "guardian:dashboard",
    ROLE_EXTERNAL: "external:dashboard",
}


def _reverse_or_none(name: str) -> str | None:
    try:
        return reverse(name)
    except NoReverseMatch:
        return None


def _reverse_any(*names: str) -> str:
    """Try several URL names until one reverses; raise if none do."""
    for n in names:
        try:
            return reverse(n)
        except NoReverseMatch:
            continue
    raise NoReverseMatch(f"Could not reverse any of: {', '.join(names)}")


class PostLoginRouter(LoginRequiredMixin, View):
    """
    Decide where to send the user right after login based on their role group.
    Priority: student > faculty > staff > guardian > external.
    Falls back to Admin for staff/superusers, else to a neutral landing page.
    """
    PRIORITY = [ROLE_STUDENT, ROLE_FACULTY, ROLE_STAFF, ROLE_PARENT, ROLE_EXTERNAL]

    # def get(self, request, *args, **kwargs):
    #     user = request.user
    #     role_map = getattr(settings, "ACCOUNTS_ROLE_REDIRECTS", DEFAULT_ROLE_REDIRECTS)
    #
    #     # Prefer admin if no role matches for staff/superuser
    #     admin_url = _reverse_or_none("admin:index")
    #
    #     # Role checks in priority order
    #     for role in self.PRIORITY:
    #         if user.groups.filter(name=role).exists():
    #             target_name = role_map.get(role)
    #             if target_name:
    #                 url = _reverse_or_none(target_name)
    #                 if url:
    #                     return redirect(url)
    #
    #     # No explicit role:
    #     if (user.is_staff or user.is_superuser) and admin_url:
    #         return redirect(admin_url)
    #
    #     # Final fallback: neutral landing page
    #     landing = _reverse_or_none("accounts:post_login_landing")
    #     return redirect(landing or "/")
    # accounts/views.py (only this helper call order changes)
    def get(self, request, *args, **kwargs):
        post_login = _reverse_any("accounts:post_login", "post_login")
        if not request.user.is_authenticated:
            login_url = _reverse_any("account_login", "accounts:account_login")  # plain first
            return redirect(f"{login_url}?{urlencode({'next': post_login})}")
        return redirect(post_login)


class PostLoginView(LoginRequiredMixin, TemplateView):
    """Neutral landing page if no specific dashboard exists yet."""
    template_name = "accounts/post_login.html"


class PortalEntryView(View):
    """
    /portal/ entry:
    - Anonymous -> allauth login with next=role router
    - Authenticated -> role router directly
    """

    def get(self, request, *args, **kwargs):
        post_login = _reverse_any("accounts:post_login", "post_login")
        if not request.user.is_authenticated:
            login_url = _reverse_any("accounts:account_login", "account_login")
            return redirect(f"{login_url}?{urlencode({'next': post_login})}")
        return redirect(post_login)
