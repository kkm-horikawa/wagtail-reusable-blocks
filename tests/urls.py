"""
URL configuration for tests.

Minimal URL configuration for running tests.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("wagtail.admin.urls")),
    path("", include("wagtail.urls")),
]
