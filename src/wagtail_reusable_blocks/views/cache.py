"""Cache management views for wagtail-reusable-blocks."""

from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from wagtail.admin.auth import permission_denied

from ..cache import ReusableBlockCache
from ..models import ReusableBlock


@require_POST
def clear_block_cache_view(request: HttpRequest, block_id: int) -> HttpResponse:
    """Clear cache for a specific ReusableBlock.

    This view is called from the admin interface to manually clear the cache
    for a specific block.

    Args:
        request: The HTTP request
        block_id: The ID of the ReusableBlock to clear cache for

    Returns:
        Redirect to the block edit page with a success message
    """
    # Check permission
    if not request.user.has_perm("wagtail_reusable_blocks.change_reusableblock"):
        response: HttpResponse = permission_denied(request)
        return response

    block = get_object_or_404(ReusableBlock, pk=block_id)

    # Clear the cache
    ReusableBlockCache.invalidate(block.pk)

    messages.success(
        request,
        _("Cache cleared for '%(name)s'.") % {"name": block.name},
    )

    # Redirect back to the edit page
    return HttpResponseRedirect(
        reverse(
            "wagtailsnippets_wagtail_reusable_blocks_reusableblock:edit",
            args=[block_id],
        )
    )


@require_POST
def clear_all_cache_view(request: HttpRequest) -> HttpResponse:
    """Clear all ReusableBlock cache entries.

    This view is called from the admin interface to clear the entire cache.

    Args:
        request: The HTTP request

    Returns:
        Redirect to the block list page with a success message
    """
    # Check permission - require change permission on at least one block
    if not request.user.has_perm("wagtail_reusable_blocks.change_reusableblock"):
        response: HttpResponse = permission_denied(request)
        return response

    # Clear all cache
    ReusableBlockCache.clear_all()

    messages.success(
        request,
        _("All ReusableBlock cache entries have been cleared."),
    )

    # Redirect back to the list page
    return HttpResponseRedirect(
        reverse("wagtailsnippets_wagtail_reusable_blocks_reusableblock:list")
    )
