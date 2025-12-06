"""URL configuration for wagtail-reusable-blocks."""

from django.urls import path

from .views import block_slots_view, clear_all_cache_view, clear_block_cache_view

app_name = "wagtail_reusable_blocks"

urlpatterns = [
    path(
        "blocks/<int:block_id>/slots/",
        block_slots_view,
        name="block_slots",
    ),
    path(
        "blocks/<int:block_id>/clear-cache/",
        clear_block_cache_view,
        name="clear_block_cache",
    ),
    path(
        "clear-all-cache/",
        clear_all_cache_view,
        name="clear_all_cache",
    ),
]
