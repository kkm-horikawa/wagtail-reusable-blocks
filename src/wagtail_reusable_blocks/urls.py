"""URL configuration for wagtail-reusable-blocks."""

from django.urls import path

from .views import block_slots_view

app_name = "wagtail_reusable_blocks"

urlpatterns = [
    path(
        "blocks/<int:block_id>/slots/",
        block_slots_view,
        name="block_slots",
    ),
]
