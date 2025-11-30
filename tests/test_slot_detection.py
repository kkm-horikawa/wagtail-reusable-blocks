"""Tests for slot detection utilities (Issue #48)."""

import pytest

from wagtail_reusable_blocks.utils import SlotInfo, detect_slots_from_html


class TestDetectSlotsFromHTML:
    """Tests for detect_slots_from_html function."""

    def test_detect_single_slot_no_default(self):
        """Detects a single slot without default content."""
        html = '<div data-slot="main"></div>'
        slots = detect_slots_from_html(html)

        assert len(slots) == 1
        assert slots[0]["id"] == "main"
        assert slots[0]["label"] == "main"  # Falls back to ID
        assert slots[0]["has_default"] is False

    def test_detect_single_slot_with_default(self):
        """Detects a single slot with default content."""
        html = '<div data-slot="main"><p>Default content</p></div>'
        slots = detect_slots_from_html(html)

        assert len(slots) == 1
        assert slots[0]["id"] == "main"
        assert slots[0]["has_default"] is True

    def test_detect_slot_with_label(self):
        """Detects slot with custom label."""
        html = '<div data-slot="header" data-slot-label="Header Area"></div>'
        slots = detect_slots_from_html(html)

        assert len(slots) == 1
        assert slots[0]["id"] == "header"
        assert slots[0]["label"] == "Header Area"

    def test_detect_multiple_slots(self):
        """Detects multiple slots in HTML."""
        html = """
        <div data-slot="header" data-slot-label="Header">
            <h1>Default Header</h1>
        </div>
        <div data-slot="main"></div>
        <div data-slot="footer" data-slot-label="Footer Area">
            <p>Default footer</p>
        </div>
        """
        slots = detect_slots_from_html(html)

        assert len(slots) == 3

        # Header slot
        assert slots[0]["id"] == "header"
        assert slots[0]["label"] == "Header"
        assert slots[0]["has_default"] is True

        # Main slot
        assert slots[1]["id"] == "main"
        assert slots[1]["label"] == "main"
        assert slots[1]["has_default"] is False

        # Footer slot
        assert slots[2]["id"] == "footer"
        assert slots[2]["label"] == "Footer Area"
        assert slots[2]["has_default"] is True

    def test_detect_nested_slots(self):
        """Detects slots in nested HTML structure."""
        html = """
        <div class="layout">
            <aside>
                <div data-slot="sidebar-top"></div>
                <nav>Fixed navigation</nav>
                <div data-slot="sidebar-bottom"></div>
            </aside>
            <main>
                <div data-slot="main-content"></div>
            </main>
        </div>
        """
        slots = detect_slots_from_html(html)

        assert len(slots) == 3
        slot_ids = [s["id"] for s in slots]
        assert "sidebar-top" in slot_ids
        assert "sidebar-bottom" in slot_ids
        assert "main-content" in slot_ids

    def test_empty_html(self):
        """Returns empty list for HTML without slots."""
        html = "<div><p>No slots here</p></div>"
        slots = detect_slots_from_html(html)

        assert len(slots) == 0
        assert slots == []

    def test_whitespace_only_not_considered_default(self):
        """Whitespace-only content is not considered default content."""
        html = "<div data-slot='main'>   \n\t   </div>"
        slots = detect_slots_from_html(html)

        assert len(slots) == 1
        assert slots[0]["has_default"] is False

    def test_text_content_is_default(self):
        """Text content is considered default content."""
        html = '<div data-slot="main">Some text</div>'
        slots = detect_slots_from_html(html)

        assert len(slots) == 1
        assert slots[0]["has_default"] is True

    def test_mixed_text_and_tags_is_default(self):
        """Mixed text and tags is considered default content."""
        html = '<div data-slot="main">Text <strong>bold</strong> more text</div>'
        slots = detect_slots_from_html(html)

        assert len(slots) == 1
        assert slots[0]["has_default"] is True

    def test_slot_id_with_special_characters(self):
        """Handles slot IDs with hyphens, underscores, numbers."""
        html = """
        <div data-slot="sidebar-top"></div>
        <div data-slot="content_1"></div>
        <div data-slot="footer2"></div>
        """
        slots = detect_slots_from_html(html)

        assert len(slots) == 3
        slot_ids = [s["id"] for s in slots]
        assert "sidebar-top" in slot_ids
        assert "content_1" in slot_ids
        assert "footer2" in slot_ids

    def test_complex_real_world_layout(self):
        """Detects slots in a complex real-world layout."""
        html = """
        <div class="two-column-layout">
            <header data-slot="header" data-slot-label="Page Header">
                <h1>Default Site Title</h1>
            </header>
            <div class="content-wrapper">
                <aside class="sidebar" data-slot="sidebar" data-slot-label="Sidebar">
                    <div class="widget">Default widget</div>
                </aside>
                <main data-slot="main" data-slot-label="Main Content"></main>
            </div>
            <footer data-slot="footer">
                <p>&copy; 2024 Default</p>
            </footer>
        </div>
        """
        slots = detect_slots_from_html(html)

        assert len(slots) == 4

        # Verify all slots detected
        slot_map = {s["id"]: s for s in slots}

        assert "header" in slot_map
        assert slot_map["header"]["label"] == "Page Header"
        assert slot_map["header"]["has_default"] is True

        assert "sidebar" in slot_map
        assert slot_map["sidebar"]["label"] == "Sidebar"
        assert slot_map["sidebar"]["has_default"] is True

        assert "main" in slot_map
        assert slot_map["main"]["label"] == "Main Content"
        assert slot_map["main"]["has_default"] is False

        assert "footer" in slot_map
        assert slot_map["footer"]["has_default"] is True


class TestSlotInfoTypeDict:
    """Tests for SlotInfo TypedDict."""

    def test_slot_info_structure(self):
        """SlotInfo has correct structure."""
        slot: SlotInfo = {"id": "test", "label": "Test Slot", "has_default": True}

        assert slot["id"] == "test"
        assert slot["label"] == "Test Slot"
        assert slot["has_default"] is True

    def test_slot_info_from_detection(self):
        """SlotInfo from detect_slots_from_html matches type."""
        html = '<div data-slot="test" data-slot-label="Test"></div>'
        slots = detect_slots_from_html(html)

        slot: SlotInfo = slots[0]
        assert isinstance(slot["id"], str)
        assert isinstance(slot["label"], str)
        assert isinstance(slot["has_default"], bool)


class TestSlotDetectionIntegration:
    """Integration tests for slot detection."""

    def test_import_from_utils(self):
        """Can import from utils package."""
        from wagtail_reusable_blocks.utils import (
            SlotInfo,
            detect_slots_from_html,
        )

        assert detect_slots_from_html is not None
        assert SlotInfo is not None

    def test_utils_exports(self):
        """Utils package exports correct symbols."""
        from wagtail_reusable_blocks import utils

        assert "detect_slots_from_html" in utils.__all__
        assert "SlotInfo" in utils.__all__

    @pytest.mark.django_db
    def test_with_reusable_block(self):
        """Detects slots from ReusableBlock content."""
        from wagtail_reusable_blocks.models import ReusableBlock

        # Create a ReusableBlock with slots
        block = ReusableBlock.objects.create(
            name="Test Layout",
            content=[
                {
                    "type": "raw_html",
                    "value": """
                    <div data-slot="header"></div>
                    <div data-slot="main"></div>
                    """,
                }
            ],
        )

        # Render the block's content to HTML
        html = block.content.render_as_block()

        # Detect slots
        slots = detect_slots_from_html(html)

        assert len(slots) == 2
        slot_ids = [s["id"] for s in slots]
        assert "header" in slot_ids
        assert "main" in slot_ids
