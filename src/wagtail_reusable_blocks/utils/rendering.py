"""Rendering utilities for slot-based layouts."""

from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup
from django.utils.safestring import SafeString, mark_safe

from ..conf import get_setting

if TYPE_CHECKING:
    from django.template.context import Context


def render_layout_with_slots(
    layout_html: str,
    slot_fills: list[dict[str, Any]],
    context: "dict[str, Any] | Context | None" = None,
) -> SafeString:
    """Render a layout with slots filled.

    Parses the layout HTML, finds elements with slot attributes, and injects
    rendered content from slot_fills. Preserves default content for unfilled slots.

    Args:
        layout_html: Rendered HTML of the layout ReusableBlock
        slot_fills: List of dicts with 'slot_id' and 'content' (BoundBlocks)
        context: Template context to pass to slot content rendering

    Returns:
        HTML with slots filled

    Example:
        >>> layout_html = '<div data-slot="main"><p>Default</p></div>'
        >>> slot_fills = [{
        ...     'slot_id': 'main',
        ...     'content': [rich_text_block]  # BoundBlock instances
        ... }]
        >>> html = render_layout_with_slots(layout_html, slot_fills)
        >>> # Returns: '<div data-slot="main"><p>Rendered content</p></div>'
    """
    slot_attr = get_setting("SLOT_ATTRIBUTE")

    # Parse HTML
    soup = BeautifulSoup(layout_html, "html.parser")

    # Create slot_id -> rendered content mapping
    slot_map: dict[str, str] = {}
    for fill in slot_fills:
        slot_id = fill["slot_id"]
        content_blocks = fill["content"]

        # Render each block in the content StreamField
        rendered_parts = []
        for block_data in content_blocks:
            # block_data is a BoundBlock from StreamField
            rendered = block_data.render(context)
            rendered_parts.append(str(rendered))

        # Combine all rendered parts
        slot_map[slot_id] = "".join(rendered_parts)

    # Find and replace slot elements
    for element in soup.find_all(attrs={slot_attr: True}):
        slot_id = str(element[slot_attr])

        if slot_id in slot_map:
            # Replace element's children with slot content
            element.clear()
            # Parse slot content and append each child individually
            # to avoid IndexError when appending document fragments
            slot_soup = BeautifulSoup(slot_map[slot_id], "html.parser")
            for child in list(slot_soup.children):
                element.append(child)
        # else: keep default content (element's existing children)

    return mark_safe(str(soup))


def render_streamfield_content(
    content_blocks: list[Any],
    context: "dict[str, Any] | Context | None" = None,
) -> str:
    """Render StreamField content blocks.

    Helper function to render a list of BoundBlock instances from a StreamField.

    Args:
        content_blocks: List of BoundBlock instances from StreamField
        context: Template context

    Returns:
        Concatenated rendered HTML
    """
    rendered_parts = []

    for block in content_blocks:
        rendered = block.render(context)
        rendered_parts.append(str(rendered))

    return "".join(rendered_parts)
