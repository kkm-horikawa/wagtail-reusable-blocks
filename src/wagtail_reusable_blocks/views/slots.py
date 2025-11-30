"""Views for slot-related API endpoints."""

from typing import TYPE_CHECKING

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from wagtail.admin.auth import permission_required

from ..models import ReusableBlock
from ..utils import detect_slots_from_html

if TYPE_CHECKING:
    from django.http import HttpRequest


@require_http_methods(["GET"])
@permission_required("wagtailadmin.access_admin")  # type: ignore[untyped-decorator]
def block_slots_view(request: "HttpRequest", block_id: int) -> JsonResponse:
    """API endpoint to get slots from a ReusableBlock.

    Returns JSON with detected slots from the block's content.

    Args:
        request: HTTP request
        block_id: Primary key of the ReusableBlock

    Returns:
        JsonResponse with slots list:
        {
            "slots": [
                {"id": "main", "label": "Main Content", "has_default": false},
                {"id": "sidebar", "label": "Sidebar", "has_default": true},
                ...
            ]
        }

    Example:
        GET /admin/reusable-blocks/blocks/123/slots/

        Response:
        {
            "slots": [
                {"id": "header", "label": "Header Area", "has_default": true},
                {"id": "main", "label": "main", "has_default": false}
            ]
        }

    Usage:
        This endpoint is used by the JavaScript widget (Issue #50) to populate
        slot_id dropdowns when a user selects a layout in ReusableLayoutBlock.
    """
    block = get_object_or_404(ReusableBlock, pk=block_id)

    # Render the block's content to HTML
    html = block.content.render_as_block()

    # Detect slots
    slots = detect_slots_from_html(html)

    return JsonResponse({"slots": slots})
