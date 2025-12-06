"""Layout block for slot-based composition."""

from typing import TYPE_CHECKING

from django.utils.safestring import mark_safe
from wagtail.admin.telepath import register
from wagtail.blocks import StreamBlock, StructBlock
from wagtail.snippets.blocks import SnippetChooserBlock

from ..widgets import ReusableLayoutBlockAdapter
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

    # Note: We define slot_content in __init__ to ensure SlotFillBlock
    # is instantiated after this class is fully defined, allowing
    # nested ReusableLayoutBlock support.

    layout = SnippetChooserBlock(
        target_model="wagtail_reusable_blocks.ReusableBlock",
        help_text="Select a layout template with slot placeholders",
    )

    def __init__(self, local_blocks=None, **kwargs):  # type: ignore[no-untyped-def]
        if local_blocks is None:
            local_blocks = []

        # Add slot_content block if not already provided
        local_block_names = [name for name, _ in local_blocks]
        if "slot_content" not in local_block_names:
            local_blocks = list(local_blocks) + [
                (
                    "slot_content",
                    StreamBlock(
                        [
                            ("slot_fill", SlotFillBlock()),
                        ],
                        required=False,
                        help_text="Fill the slots in this layout template",
                    ),
                )
            ]

        super().__init__(local_blocks, **kwargs)

    class Meta:
        icon = "doc-empty"
        label = "Reusable Layout"
        help_text = "Layout template with customizable content slots"
        adapter_class = ReusableLayoutBlockAdapter

    def render(self, value, context=None):  # type: ignore[no-untyped-def]
        """Render the layout with slots filled.

        Renders the layout ReusableBlock to HTML, then injects content from
        slot_fills into the corresponding slot elements. Unfilled slots retain
        their default content.

        Args:
            value: Block value dict with 'layout' and 'slot_content'
            context: Template context (propagated to nested blocks)

        Returns:
            Rendered HTML string with slots injected
        """
        from ..utils.rendering import render_layout_with_slots

        layout = value["layout"]
        slot_content = value.get("slot_content", [])

        # Render the layout to HTML
        layout_html = layout.content.render_as_block(context)

        # If no slots to fill, return layout as-is
        if not slot_content:
            return mark_safe(layout_html)

        # Convert slot_content StreamField to list of dicts
        slot_fills = []
        for slot_fill_block in slot_content:
            # slot_fill_block is a BoundBlock wrapping SlotFillBlock
            slot_fill_value = slot_fill_block.value
            slot_fills.append(
                {
                    "slot_id": slot_fill_value["slot_id"],
                    "content": slot_fill_value["content"],  # List of BoundBlocks
                }
            )

        # Render with slots
        return render_layout_with_slots(layout_html, slot_fills, context)

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


# Register the custom adapter with telepath
register(ReusableLayoutBlockAdapter(), ReusableLayoutBlock)
