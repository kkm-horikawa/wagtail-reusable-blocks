"""Slot detection utilities for parsing HTML and finding slots."""

from typing import TYPE_CHECKING, TypedDict

from bs4 import BeautifulSoup

from ..conf import get_setting

if TYPE_CHECKING:
    pass


class SlotInfo(TypedDict):
    """Information about a detected slot.

    Attributes:
        id: The slot identifier (from data-slot attribute)
        label: Human-readable label (from data-slot-label or defaults to id)
        has_default: Whether the slot has default content (child elements)
    """

    id: str
    label: str
    has_default: bool


def detect_slots_from_html(html: str) -> list[SlotInfo]:
    """Detect slots from HTML content using BeautifulSoup.

    Parses HTML to find elements with slot attributes (e.g., data-slot="main")
    and extracts metadata about each slot.

    Args:
        html: HTML string to parse for slot elements

    Returns:
        List of SlotInfo dicts containing slot metadata:
        - id: The slot identifier
        - label: Display label for the slot
        - has_default: Whether the slot has default content

    Example:
        >>> html = '''
        ... <div data-slot="header" data-slot-label="Header Area">
        ...     <h1>Default Header</h1>
        ... </div>
        ... <div data-slot="main"></div>
        ... '''
        >>> slots = detect_slots_from_html(html)
        >>> slots[0]
        {'id': 'header', 'label': 'Header Area', 'has_default': True}
        >>> slots[1]
        {'id': 'main', 'label': 'main', 'has_default': False}

    Configuration:
        Uses SLOT_ATTRIBUTE and SLOT_LABEL_ATTRIBUTE from settings:

        >>> # settings.py
        >>> WAGTAIL_REUSABLE_BLOCKS = {
        ...     'SLOT_ATTRIBUTE': 'data-slot',  # default
        ...     'SLOT_LABEL_ATTRIBUTE': 'data-slot-label',  # default
        ... }
    """
    slot_attr = get_setting("SLOT_ATTRIBUTE")
    label_attr = get_setting("SLOT_LABEL_ATTRIBUTE")

    soup = BeautifulSoup(html, "html.parser")
    slots: list[SlotInfo] = []

    # Find all elements with the slot attribute
    for element in soup.find_all(attrs={slot_attr: True}):
        slot_id = str(element[slot_attr])

        # Get label from data-slot-label attribute, or use slot_id as fallback
        label = str(element.get(label_attr, slot_id))

        # Check if slot has default content (child elements)
        # element.contents includes text nodes and child tags
        # We check for any non-empty content
        has_default = bool(
            [
                content
                for content in element.contents
                if str(content).strip()  # Filter out whitespace-only text nodes
            ]
        )

        slots.append(
            SlotInfo(
                id=slot_id,
                label=label,
                has_default=has_default,
            )
        )

    return slots
