"""Wagtail admin UI customizations for ReusableBlock."""

from typing import TYPE_CHECKING

from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.ui.tables import UpdatedAtColumn
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

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
        - Display name, slug, and last updated timestamp
        - Default ordering by most recently updated
    """

    model = ReusableBlock
    icon = "snippet"
    menu_label = "Reusable Blocks"
    menu_order = 200
    add_to_admin_menu = True

    # Search configuration
    search_fields = ["name", "slug"]

    # List display configuration
    list_display = [
        "name",
        "slug",
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


# Register the custom viewset only if default registration is enabled
# This prevents double registration
if get_setting("REGISTER_DEFAULT_SNIPPET"):
    register_snippet(ReusableBlockViewSet)
