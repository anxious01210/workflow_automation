# accounts/views.py
from django.shortcuts import redirect
from .models import ROLE_STUDENT, ROLE_FACULTY, ROLE_STAFF, ROLE_PARENT, ROLE_EXTERNAL
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


def post_login_redirect(request):
    u = request.user
    # use constants so we never drift on group names again
    if u.groups.filter(name=ROLE_STUDENT).exists():
        return redirect("student:dashboard")
    if u.groups.filter(name=ROLE_FACULTY).exists():
        return redirect("faculty:dashboard")
    if u.groups.filter(name=ROLE_STAFF).exists():
        return redirect("staff:dashboard")
    if u.groups.filter(name=ROLE_PARENT).exists():
        return redirect("guardian:dashboard")  # you can keep 'parent:dashboard' if that's your URL name
    return redirect("external:dashboard")


class PostLoginView(LoginRequiredMixin, TemplateView):
    template_name = "account/post_login.html"
