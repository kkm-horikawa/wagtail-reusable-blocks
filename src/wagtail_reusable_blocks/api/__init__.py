"""REST API support for wagtail-reusable-blocks.

Provides two types of API endpoints:

1. Wagtail API v2 (read-only):
   Uses Wagtail's built-in API framework for public content delivery.

2. DRF ModelViewSet (full CRUD):
   Uses Django REST Framework for complete CRUD operations.

Setup:
    # Option A: Wagtail API v2 (read-only)
    from wagtail.api.v2.router import WagtailAPIRouter
    from wagtail_reusable_blocks.api import ReusableBlockAPIViewSet

    api_router = WagtailAPIRouter("wagtailapi")
    api_router.register_endpoint("reusable-blocks", ReusableBlockAPIViewSet)

    # Option B: DRF CRUD
    from rest_framework.routers import DefaultRouter
    from wagtail_reusable_blocks.api import ReusableBlockModelViewSet

    router = DefaultRouter()
    router.register("reusable-blocks", ReusableBlockModelViewSet)
"""

from wagtail_reusable_blocks.api.views import (
    ReusableBlockAPIViewSet,
    ReusableBlockModelViewSet,
)

__all__ = [
    "ReusableBlockAPIViewSet",
    "ReusableBlockModelViewSet",
]
