# accounts/utils.py
from django.contrib.auth.models import Group
from accounts.models import ROLE_FACULTY, ROLE_STUDENT, ROLE_STAFF, ROLE_PARENT, ROLE_EXTERNAL


def set_groups_for_user(user, *, is_student=False, is_faculty=False, is_staff=False, is_parent=False, is_external=False):
    wanted = set()
    if is_student:  wanted.add(ROLE_STUDENT)
    if is_faculty:  wanted.add(ROLE_FACULTY)
    if is_staff:    wanted.add(ROLE_STAFF)
    if is_parent:   wanted.add(ROLE_PARENT)
    if is_external: wanted.add(ROLE_EXTERNAL)

    # Remove old role groups, add new
    role_groups = Group.objects.filter(name__in=[ROLE_STUDENT, ROLE_FACULTY, ROLE_STAFF, ROLE_PARENT, ROLE_EXTERNAL])
    user.groups.remove(*role_groups)
    for gname in wanted:
        Group.objects.get(name=gname).user_set.add(user)
