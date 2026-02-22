"""API views for wagtail-reusable-blocks."""

from typing import Any

from django.utils.module_loading import import_string
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from wagtail.actions.unpublish import UnpublishAction
from wagtail.api.v2.filters import FieldsFilter, OrderingFilter, SearchFilter
from wagtail.api.v2.views import BaseAPIViewSet

from wagtail_reusable_blocks.api.serializers import ReusableBlockSerializer
from wagtail_reusable_blocks.conf import get_setting
from wagtail_reusable_blocks.models import ReusableBlock


def _resolve_classes(setting_key: str) -> list[type[Any]] | None:
    """Resolve class paths from settings to actual classes.

    Args:
        setting_key: The setting key containing class paths.

    Returns:
        List of resolved classes, or None if the setting is None.
    """
    classes = get_setting(setting_key)
    if classes is None:
        return None

    resolved: list[type[Any]] = []
    for cls in classes:
        if isinstance(cls, str):
            resolved.append(import_string(cls))
        else:
            resolved.append(cls)
    return resolved


class ReusableBlockAPIViewSet(BaseAPIViewSet):  # type: ignore[misc]
    """Read-only API endpoint for ReusableBlock (Wagtail API v2 compatible).

    Provides:
    - GET /api/v2/reusable-blocks/ (list)
    - GET /api/v2/reusable-blocks/<id>/ (detail)

    Only returns published (live) blocks.

    Usage::

        from wagtail.api.v2.router import WagtailAPIRouter
        from wagtail_reusable_blocks.api import ReusableBlockAPIViewSet

        api_router = WagtailAPIRouter("wagtailapi")
        api_router.register_endpoint("reusable-blocks", ReusableBlockAPIViewSet)
    """

    model = ReusableBlock
    body_fields = BaseAPIViewSet.body_fields + [
        "name",
        "slug",
        "content",
        "live",
        "created_at",
        "updated_at",
    ]
    listing_default_fields = BaseAPIViewSet.listing_default_fields + [
        "name",
        "slug",
        "live",
        "updated_at",
    ]
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    name = "reusable_blocks"

    def get_queryset(self) -> Any:
        """Return only live (published) blocks."""
        return ReusableBlock.objects.filter(live=True)


class ReusableBlockModelViewSet(viewsets.ModelViewSet):  # type: ignore[misc]
    """Full CRUD API endpoint for ReusableBlock (DRF-based).

    Provides:
    - GET    /reusable-blocks/      (list)
    - POST   /reusable-blocks/      (create)
    - GET    /reusable-blocks/<id>/ (retrieve)
    - PUT    /reusable-blocks/<id>/ (update)
    - PATCH  /reusable-blocks/<id>/ (partial update)
    - DELETE /reusable-blocks/<id>/ (destroy)

    Usage::

        from rest_framework.routers import DefaultRouter
        from wagtail_reusable_blocks.api import ReusableBlockModelViewSet

        router = DefaultRouter()
        router.register("reusable-blocks", ReusableBlockModelViewSet)
    """

    queryset = ReusableBlock.objects.all()
    serializer_class = ReusableBlockSerializer
    lookup_field = "pk"

    def get_permissions(self) -> list[permissions.BasePermission]:
        """Get permission classes from settings."""
        classes = _resolve_classes("API_PERMISSION_CLASSES")
        if classes is None:
            return []
        return [cls() for cls in classes]

    def get_authenticators(self) -> list[Any]:
        """Get authentication classes from settings, or use DRF defaults."""
        classes = _resolve_classes("API_AUTHENTICATION_CLASSES")
        if classes is None:
            return super().get_authenticators()  # type: ignore[no-any-return]
        return [cls() for cls in classes]

    def get_queryset(self) -> Any:
        """Return all blocks, with optional filtering."""
        qs = ReusableBlock.objects.all()

        slug = self.request.query_params.get("slug")
        if slug:
            qs = qs.filter(slug=slug)

        live = self.request.query_params.get("live")
        if live is not None:
            qs = qs.filter(live=live.lower() in ("true", "1", "yes"))

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)

        return qs

    @action(  # type: ignore[untyped-decorator]
        detail=True,
        methods=["post"],
        url_path="publish",
        url_name="publish",
    )
    def publish(self, request: Any, **kwargs: Any) -> Response:
        """Publish a reusable block via DraftStateMixin.publish().

        Creates a revision, sets live=True, and updates publishing timestamps.
        Idempotent: succeeds even if the block is already published.
        """
        instance = self.get_object()
        revision = instance.save_revision(user=request.user)
        instance.publish(revision, user=request.user, skip_permission_checks=True)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(  # type: ignore[untyped-decorator]
        detail=True,
        methods=["post"],
        url_path="unpublish",
        url_name="unpublish",
    )
    def unpublish(self, request: Any, **kwargs: Any) -> Response:
        """Unpublish a reusable block via DraftStateMixin.unpublish().

        Sets live=False. Idempotent: succeeds even if already unpublished.
        """
        instance = self.get_object()
        UnpublishAction(instance, user=request.user).execute(
            skip_permission_checks=True
        )
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(  # type: ignore[untyped-decorator]
        detail=True,
        methods=["get"],
        url_path="render",
        url_name="render",
    )
    def render(self, request: Any, **kwargs: Any) -> Response:
        """Render a reusable block to HTML."""
        instance = self.get_object()
        try:
            html = instance.render()
        except Exception as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response({"html": html}, status=status.HTTP_200_OK)
