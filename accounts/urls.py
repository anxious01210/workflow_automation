# accounts/urls.py
from django.urls import path, include
from .views import PostLoginRouter, PostLoginView

app_name = "accounts"

urlpatterns = [
    # Keep this: allauth routes under /accounts/ (login, logout, microsoft, etc.)
    path("", include("allauth.urls")),

    # Role-based router (LOGIN_REDIRECT_URL should point here)
    path("post-login/", PostLoginRouter.as_view(), name="post_login"),
    # # where LOGIN_REDIRECT_URL points
    # path("post-login/", PostLoginView.as_view(), name="post_login"),

    # Neutral fallback landing page if no specific dashboard exists
    path("post-login/landing/", PostLoginView.as_view(), name="post_login_landing"),
]
