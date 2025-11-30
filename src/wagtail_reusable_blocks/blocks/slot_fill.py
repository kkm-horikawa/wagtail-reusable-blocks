"""SlotFillBlock for filling slots in layout templates."""

from typing import TYPE_CHECKING

from wagtail.blocks import (
    CharBlock,
    RawHTMLBlock,
    RichTextBlock,
    StreamBlock,
    StructBlock,
)

if TYPE_CHECKING:
    from wagtail.blocks import StructBlock as StructBlockType
else:
    StructBlockType = StructBlock  # type: ignore[misc,assignment]


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

    slot_id = CharBlock(
        max_length=50,
        help_text="The slot identifier to fill (e.g., 'main', 'sidebar')",
        label="Slot ID",
    )

    content = StreamBlock(
        [
            ("rich_text", RichTextBlock()),
            ("raw_html", RawHTMLBlock()),
        ],
        help_text="Content to inject into this slot",
        label="Slot Content",
    )

    class Meta:
        icon = "placeholder"
        label = "Slot Fill"
        help_text = "Fill a specific slot with content"


# Note: This will be extended with additional block types in a follow-up
# to support ReusableBlockChooserBlock and ReusableLayoutBlock (recursive nesting)
# after those blocks are implemented.
