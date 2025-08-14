# accounts/urls.py
from django.urls import path, include
from .views import PostLoginRouter, PostLoginView
from django.views.generic import RedirectView

app_name = "accounts"

urlpatterns = [
    # Keep this: allauth routes under /accounts/ (login, logout, microsoft, etc.)
    # path("", include("allauth.urls")),
    # If you want /accounts/ to be friendlier, Then /accounts/ will take you to the role-based router (which in turn sends you
    # to portals:home). if you remove the below line then /accounts/ will take you to the /accounts/email/ while logged in
    path("", RedirectView.as_view(pattern_name="accounts:post_login", permanent=False)),

    # Role-based router (LOGIN_REDIRECT_URL should point here)
    path("post-login/", PostLoginRouter.as_view(), name="post_login"),
    # # where LOGIN_REDIRECT_URL points
    # path("post-login/", PostLoginView.as_view(), name="post_login"),

    # Neutral fallback landing page if no specific dashboard exists
    path("post-login/landing/", PostLoginView.as_view(), name="post_login_landing"),
]
