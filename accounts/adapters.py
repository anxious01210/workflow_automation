# accounts/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.models import Group
from accounts.models import ROLE_EXTERNAL

ALLOWED_SSO_DOMAINS = {"bisk.edu.krd"}  # extend as you like


class AccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        # normal allauth save
        user = super().save_user(request, user, form, commit)
        # If LOCAL signup, default to external role
        social = getattr(user, "socialaccount_set", None)
        if not social or not social.exists():
            Group.objects.get(name=ROLE_EXTERNAL).user_set.add(user)
        return user

    def clean_email(self, email):
        email = super().clean_email(email)
        return email
