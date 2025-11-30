"""Custom widgets for wagtail-reusable-blocks."""

from typing import Any

from django.forms import Media
from wagtail.blocks.struct_block import StructBlockAdapter


class ReusableLayoutBlockAdapter(StructBlockAdapter):  # type: ignore[misc]
    """Custom adapter for ReusableLayoutBlock.

    Adds JavaScript for dynamic slot selection.
    """

    @property
    def media(self) -> Any:
        """Include slot chooser JavaScript."""
        return super().media + Media(
            js=[
                "wagtail_reusable_blocks/js/slot-chooser.js",
            ]
        )

    def js_initializer(self) -> str:
        """Initialize SlotChooserWidget on the client side."""
        return f"new SlotChooserWidget('{self.id}-layout', '{self.id}-slot_content')"
