from django.shortcuts import render, redirect

# Create your views here.
def post_login_redirect(request):
    u = request.user
    if u.groups.filter(name="role_student").exists():
        return redirect("student:dashboard")
    if u.groups.filter(name="role_faculty").exists():
        return redirect("faculty:dashboard")
    if u.groups.filter(name="role_staff").exists():
        return redirect("staff:dashboard")
    if u.groups.filter(name="role_parent").exists():
        return redirect("parent:dashboard")
    return redirect("external:dashboard")  # default