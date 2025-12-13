"""SlotFillBlock for filling slots in layout templates."""

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _
from wagtail.blocks import (
    CharBlock,
    RichTextBlock,
    StreamBlock,
    StructBlock,
)

from .html import HTMLBlock

if TYPE_CHECKING:
    from wagtail.blocks import StreamBlock as StreamBlockType
    from wagtail.blocks import StructBlock as StructBlockType
else:
    StreamBlockType = StreamBlock  # type: ignore[misc,assignment]
    StructBlockType = StructBlock  # type: ignore[misc,assignment]


class SlotContentStreamBlock(StreamBlockType):  # type: ignore[misc]
    """StreamBlock for slot content with lazy block type loading."""

    # Class-level flag to prevent infinite recursion when creating nested layouts
    _creating_instance = False

    def __init__(self, **kwargs):  # type: ignore[no-untyped-def]
        # Import here to avoid circular dependency
        from .chooser import ReusableBlockChooserBlock
        from .image import ImageBlock

        block_types = [
            ("rich_text", RichTextBlock()),
            ("raw_html", HTMLBlock()),
            ("image", ImageBlock()),
            ("reusable_block", ReusableBlockChooserBlock()),
        ]

        # Try to import ReusableLayoutBlock if available
        # This will work after ReusableLayoutBlock is defined
        # Use _creating_instance flag to prevent infinite recursion
        if not SlotContentStreamBlock._creating_instance:
            try:
                SlotContentStreamBlock._creating_instance = True
                from .layout import ReusableLayoutBlock

                block_types.append(
                    ("reusable_layout", ReusableLayoutBlock())  # type: ignore[no-untyped-call]
                )
            except ImportError:
                # ReusableLayoutBlock not yet defined, skip it
                pass
            finally:
                SlotContentStreamBlock._creating_instance = False

        super().__init__(block_types, **kwargs)


class SlotFillBlock(StructBlockType):  # type: ignore[misc]
    """Content to inject into a specific slot in a layout template.

    This block allows editors to specify which slot to fill and what content
    to inject into that slot. It's used within ReusableLayoutBlock to customize
    layouts on a per-page basis.

    Usage:
        SlotFillBlock is typically used within a ReusableLayoutBlock's slot_content:

        >>> from wagtail_reusable_blocks.blocks import ReusableLayoutBlock
        >>> layout_block = ReusableLayoutBlock()
        >>> # In the admin, editors will:
        >>> # 1. Select a layout with slots
        >>> # 2. Add SlotFillBlock instances to fill specific slots
        >>> # 3. Provide content for each slot

    Example:
        A layout has slots "header", "main", "footer".
        Editor creates SlotFillBlocks:
        - slot_id: "header", content: [RichTextBlock with title]
        - slot_id: "main", content: [RichTextBlock with article]
        - slot_id: "footer" is not filled → uses default content

    Attributes:
        slot_id: The identifier of the slot to fill (e.g., "main", "sidebar")
        content: StreamField containing the content to inject into the slot
    """

    # Note: We don't define `content` as a class attribute because
    # SlotContentStreamBlock needs to be instantiated after ReusableLayoutBlock
    # is defined to include it in the available block types.
    # Instead, we define it in __init__.

    slot_id = CharBlock(
        max_length=50,
        help_text=_("The slot identifier to fill (e.g., 'main', 'sidebar')"),
        label=_("Slot ID"),
    )

    def __init__(self, local_blocks=None, **kwargs):  # type: ignore[no-untyped-def]
        # Create SlotContentStreamBlock at runtime to ensure ReusableLayoutBlock
        # is available for nested layouts
        if local_blocks is None:
            local_blocks = []

        # Add content block if not already provided
        local_block_names = [name for name, _ in local_blocks]
        if "content" not in local_block_names:
            local_blocks = list(local_blocks) + [
                (
                    "content",
                    SlotContentStreamBlock(  # type: ignore[no-untyped-call]
                        help_text=_("Content to inject into this slot"),
                        label=_("Slot Content"),
                    ),
                )
            ]

        super().__init__(local_blocks, **kwargs)

    class Meta:
        icon = "placeholder"
        label = _("Slot Fill")
        help_text = _("Fill a specific slot with content")


# Nesting support (Issue #49):
# - reusable_block: Include ReusableBlock content (v0.1.0 feature)
# - reusable_layout: Include ReusableLayoutBlock (v0.2.0 feature, recursive!)
# - Lazy imports prevent circular dependency between SlotFillBlock and ReusableLayoutBlock
