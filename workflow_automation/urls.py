"""
URL configuration for workflow_automation project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from accounts.views import PortalEntryView
from django.conf.urls.static import static
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    # allauth: keep un-namespaced so its internal reverses work
    path("accounts/", include("allauth.urls")),
    # path("accounts/", include("accounts.urls", namespace="accounts")),
    # path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("accounts/", include("accounts.urls", namespace="accounts")),

    path('', include('core.urls', namespace='core')),  # Add this
    path("cms/", include(wagtailadmin_urls)),  # editors here
    path("documents/", include(wagtaildocs_urls)),
    # 👇 exact /portal/ goes to entry router
    path("portal/", PortalEntryView.as_view(), name="portal"),
    # 👇 /portal/<something>/ goes to your portals app
    path("portal/", include("portals.urls", namespace="portals")),
    # Public site (Wagtail handles /)
    path("", include(wagtail_urls)),
]

# ✅ Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_title = "BISK Admin Portal"
admin.site.site_header = "Welcome to BISK Admin Area"
admin.site.index_title = "Dashboard Overview"
