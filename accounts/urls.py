# accounts/urls.py
from django.urls import path, include
from .views import PostLoginView

app_name = "accounts"

urlpatterns = [
    # allauth: /accounts/login, /accounts/logout, /accounts/microsoft/login, ...
    path("", include("allauth.urls")),
    # where LOGIN_REDIRECT_URL points
    path("post-login/", PostLoginView.as_view(), name="post_login"),
]
