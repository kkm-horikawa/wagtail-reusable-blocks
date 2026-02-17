"""
URL configuration for tests.

Minimal URL configuration for running tests.
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from wagtail.api.v2.router import WagtailAPIRouter

from wagtail_reusable_blocks.api import (
    ReusableBlockAPIViewSet,
    ReusableBlockModelViewSet,
)

# Wagtail API v2 router (read-only)
wagtail_api_router = WagtailAPIRouter("wagtailapi")
wagtail_api_router.register_endpoint("reusable-blocks", ReusableBlockAPIViewSet)

# DRF router (CRUD)
drf_router = DefaultRouter()
drf_router.register("reusable-blocks", ReusableBlockModelViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v2/", wagtail_api_router.urls),
    path("api/", include(drf_router.urls)),
    path("", include("wagtail.admin.urls")),
    path("", include("wagtail.urls")),
]
