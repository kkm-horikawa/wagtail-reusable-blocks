"""Wagtail admin UI customizations for ReusableBlock."""

from typing import TYPE_CHECKING

from django.urls import include, path, reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.ui.tables import LiveStatusTagColumn, UpdatedAtColumn
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .cache import ReusableBlockCache
from .conf import get_setting
from .models import ReusableBlock

if TYPE_CHECKING:
    from wagtail.admin.filters import WagtailFilterSet as WagtailFilterSetType
    from wagtail.snippets.views.snippets import SnippetViewSet as SnippetViewSetType
else:
    WagtailFilterSetType = WagtailFilterSet  # type: ignore[misc,assignment]
    SnippetViewSetType = SnippetViewSet  # type: ignore[misc,assignment]


class ReusableBlockFilterSet(WagtailFilterSetType):  # type: ignore[misc]
    """Custom filter set for ReusableBlock admin."""

    class Meta:
        model = ReusableBlock
        fields = {
            "created_at": ["date"],
            "updated_at": ["date"],
        }


class ReusableBlockViewSet(SnippetViewSetType):  # type: ignore[misc]
    """Custom admin interface for ReusableBlock snippets.

    Provides search, filtering, and enhanced list display for managing
    reusable content blocks in the Wagtail admin.

    Features:
        - Search by name and slug
        - Filter by creation and update dates
        - Display name, slug, live status, and last updated timestamp
        - Default ordering by most recently updated
        - Draft/publish workflow support
        - Locking support
        - Revision history
        - Preview functionality
    """

    model = ReusableBlock
    icon = "snippet"
    menu_label = _("Reusable Blocks")
    menu_order = 200
    add_to_admin_menu = True

    # Search configuration
    search_fields = ["name", "slug"]

    # List display configuration (includes live status for DraftStateMixin)
    list_display = [
        "name",
        "slug",
        LiveStatusTagColumn(),
        UpdatedAtColumn(),
    ]
    list_per_page = 50

    # Filtering configuration
    filterset_class = ReusableBlockFilterSet

    # Default ordering (most recently updated first)
    ordering = ["-updated_at"]

    # Enable copy functionality for duplicating blocks
    copy_view_enabled = True

    # Enable inspect view for read-only preview
    inspect_view_enabled = True

    # Enable preview (for PreviewableMixin)
    preview_enabled = True


# Register the custom viewset only if default registration is enabled
# This prevents double registration
if get_setting("REGISTER_DEFAULT_SNIPPET"):
    register_snippet(ReusableBlockViewSet)


@hooks.register("register_admin_urls")  # type: ignore[untyped-decorator]
def register_admin_urls() -> list[object]:
    """Register URL patterns for the Wagtail admin.

    Registers API endpoints for slot detection and other admin functionality.
    URLs are prefixed with 'admin/reusable-blocks/'.
    """
    from . import urls

    return [
        path(
            "reusable-blocks/",
            include(
                (urls, "wagtail_reusable_blocks"), namespace="wagtail_reusable_blocks"
            ),
        ),
    ]


@hooks.register("register_snippet_listing_buttons")  # type: ignore[untyped-decorator]
def register_clear_cache_button(
    snippet: object,
    user: object,
    next_url: str | None = None,
) -> list[object]:
    """Add a 'Clear Cache' button to the snippet listing actions.

    Only shows for ReusableBlock snippets when caching is enabled.
    """
    from wagtail.snippets.widgets import SnippetListingButton

    if not isinstance(snippet, ReusableBlock):
        return []

    if not ReusableBlockCache.is_enabled():
        return []

    return [
        SnippetListingButton(
            _("Clear Cache"),
            reverse(
                "wagtail_reusable_blocks:clear_block_cache",
                args=[snippet.pk],
            ),
            priority=100,
            attrs={"data-controller": "w-action", "data-w-action-method-value": "POST"},
        ),
    ]


@hooks.register("insert_global_admin_js")  # type: ignore[untyped-decorator]
def global_admin_js() -> str:
    """Add JavaScript for cache clear functionality.

    This adds a form submission handler for the clear cache button.
    """
    if not ReusableBlockCache.is_enabled():
        return ""

    return mark_safe(
        """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Handle clear cache button clicks
            document.addEventListener('click', function(e) {
                const btn = e.target.closest('[data-clear-cache-url]');
                if (btn) {
                    e.preventDefault();
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.action = btn.dataset.clearCacheUrl;

                    // Add CSRF token
                    const csrfInput = document.createElement('input');
                    csrfInput.type = 'hidden';
                    csrfInput.name = 'csrfmiddlewaretoken';
                    csrfInput.value = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                                     document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
                    form.appendChild(csrfInput);

                    document.body.appendChild(form);
                    form.submit();
                }
            });
        });
        </script>
        """
    )
