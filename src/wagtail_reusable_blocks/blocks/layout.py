"""Layout block for slot-based composition."""

from typing import TYPE_CHECKING

from wagtail.blocks import StreamBlock, StructBlock
from wagtail.snippets.blocks import SnippetChooserBlock

from .slot_fill import SlotFillBlock

if TYPE_CHECKING:
    from wagtail.blocks import StructBlock as StructBlockType
else:
    StructBlockType = StructBlock  # type: ignore[misc,assignment]

__all__ = ["ReusableLayoutBlock"]


class ReusableLayoutBlock(StructBlockType):  # type: ignore[misc]
    """Layout template with fillable slots.

    This block allows users to select a ReusableBlock that contains slot
    placeholders (HTML elements with data-slot attributes) and fill those
    slots with custom content.

    Example:
        >>> # In a page model
        >>> body = StreamField([
        ...     ('layout', ReusableLayoutBlock()),
        ... ])

        >>> # In page data
        >>> {
        ...     'type': 'layout',
        ...     'value': {
        ...         'layout': <ReusableBlock instance>,
        ...         'slot_content': [
        ...             {
        ...                 'type': 'slot_fill',
        ...                 'value': {
        ...                     'slot_id': 'main',
        ...                     'content': [...]
        ...                 }
        ...             }
        ...         ]
        ...     }
        ... }

    Attributes:
        layout: The ReusableBlock to use as a template
        slot_content: List of SlotFillBlocks to inject into slots
    """

    layout = SnippetChooserBlock(
        target_model="wagtail_reusable_blocks.ReusableBlock",
        help_text="Select a layout template with slot placeholders",
    )

    slot_content = StreamBlock(
        [
            ("slot_fill", SlotFillBlock()),
        ],
        required=False,
        help_text="Fill the slots in this layout template",
    )

    class Meta:
        icon = "doc-empty"
        label = "Reusable Layout"
        help_text = "Layout template with customizable content slots"

    def render(self, value, context=None):  # type: ignore[no-untyped-def]
        """Render the layout with slots filled.

        For now, this is a placeholder. Full implementation will be
        done in Issue #51 (Rendering Logic).

        Args:
            value: Block value dict with 'layout' and 'slot_content'
            context: Template context

        Returns:
            Rendered HTML string
        """
        # Placeholder: just render the layout without slot injection
        # Full implementation in Issue #51
        layout = value["layout"]
        return layout.render(context)

    def get_form_context(self, value, prefix, errors=None):  # type: ignore[no-untyped-def]
        """Add available slots to form context.

        This will be enhanced with JavaScript in Issue #50.
        For now, just provide basic context.
        """
        context = super().get_form_context(value, prefix, errors)

        # If a layout is selected, we could extract slots here
        # But the dynamic UI (Issue #50) will handle this better
        if value and value.get("layout"):
            from ..utils.slot_detection import detect_slots_from_html

            layout = value["layout"]
            html = layout.content.render_as_block()
            slots = detect_slots_from_html(html)
            context["available_slots"] = slots

        return context
