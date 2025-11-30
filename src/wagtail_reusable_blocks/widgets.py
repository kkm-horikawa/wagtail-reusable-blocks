"""Custom widgets for wagtail-reusable-blocks."""

from django import forms
from django.utils.functional import cached_property
from wagtail.blocks.struct_block import StructBlockAdapter


class ReusableLayoutBlockAdapter(StructBlockAdapter):  # type: ignore[misc]
    """Custom adapter for ReusableLayoutBlock.

    Adds JavaScript for dynamic slot selection.
    """

    js_constructor = "wagtail_reusable_blocks.blocks.ReusableLayoutBlock"

    @cached_property
    def media(self):  # type: ignore[no-untyped-def]
        """Include slot chooser JavaScript."""
        structblock_media = super().media
        return forms.Media(
            js=structblock_media._js + ["wagtail_reusable_blocks/js/slot-chooser.js"],
            css=structblock_media._css,
        )
