# accounts/views.py
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch
from django.views import View
from django.views.generic import TemplateView

from .models import ROLE_STUDENT, ROLE_FACULTY, ROLE_STAFF, ROLE_PARENT, ROLE_EXTERNAL

# (Important!) Default mapping (override with settings.ACCOUNTS_ROLE_REDIRECTS if you want)
DEFAULT_ROLE_REDIRECTS = {
    ROLE_STUDENT: "student:home",
    ROLE_FACULTY: "faculty:home",
    ROLE_STAFF: "staff:home",
    ROLE_PARENT: "guardian:home",
    ROLE_EXTERNAL: "external:home",
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
    Admins -> /admin/.
    If no role match, show a neutral landing page (no redirect loop).
    """
    PRIORITY = [ROLE_STUDENT, ROLE_FACULTY, ROLE_STAFF, ROLE_PARENT, ROLE_EXTERNAL]

    def get(self, request, *args, **kwargs):
        u = request.user

        # Admins straight to admin
        if u.is_superuser or u.is_staff:
            return redirect("/admin/")

        # Choose mapping (settings can override the defaults)
        routes = getattr(settings, "ACCOUNTS_ROLE_REDIRECTS", DEFAULT_ROLE_REDIRECTS)

        # Make one DB call, then check membership in Python
        user_groups = set(u.groups.values_list("name", flat=True))

        for role in self.PRIORITY:
            if role in user_groups:
                urlname = routes.get(role)
                if urlname:
                    url = _reverse_or_none(urlname)
                    if url:
                        return redirect(url)

        # No role match: go to the neutral landing page (no further redirects)
        landing = _reverse_or_none("accounts:post_login_landing")
        if landing:
            return redirect(landing)

        # Final fallback: render the landing template directly
        from django.shortcuts import render
        return render(request, "accounts/post_login.html", {"user": u})


class PostLoginView(LoginRequiredMixin, TemplateView):
    """Neutral landing page if no specific dashboard exists yet."""
    template_name = "accounts/post_login.html"


class PortalEntryView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_staff or user.is_superuser:
            return redirect("/admin/")
        if user.has_perm("portals.portal_access"):
            return redirect("portals:home")
        # Fallback if logged-in user lacks portal access:
        return redirect("account_logout")  # or a safe info page
