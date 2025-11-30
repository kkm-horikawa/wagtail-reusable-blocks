"""Tests for slot rendering logic."""

from unittest.mock import Mock

import pytest

from wagtail_reusable_blocks.blocks import ReusableLayoutBlock
from wagtail_reusable_blocks.models import ReusableBlock
from wagtail_reusable_blocks.utils.rendering import (
    render_layout_with_slots,
    render_streamfield_content,
)


class TestRenderStreamfieldContent:
    """Tests for render_streamfield_content function."""

    def test_render_single_block(self):
        """Renders a single block."""
        block = Mock()
        block.render.return_value = "<p>Content</p>"

        result = render_streamfield_content([block])

        assert result == "<p>Content</p>"
        block.render.assert_called_once_with(None)

    def test_render_multiple_blocks(self):
        """Renders and concatenates multiple blocks."""
        block1 = Mock()
        block1.render.return_value = "<p>First</p>"

        block2 = Mock()
        block2.render.return_value = "<p>Second</p>"

        block3 = Mock()
        block3.render.return_value = "<p>Third</p>"

        result = render_streamfield_content([block1, block2, block3])

        assert result == "<p>First</p><p>Second</p><p>Third</p>"

    def test_render_with_context(self):
        """Passes context to block renders."""
        block = Mock()
        block.render.return_value = "<p>Content</p>"

        context = {"page": {"title": "Test"}}
        render_streamfield_content([block], context)

        block.render.assert_called_once_with(context)

    def test_render_empty_list(self):
        """Handles empty block list."""
        result = render_streamfield_content([])

        assert result == ""


class TestRenderLayoutWithSlots:
    """Tests for render_layout_with_slots function."""

    def test_empty_slot_fills(self):
        """Renders layout unchanged when no slot fills."""
        html = '<div data-slot="main"><p>Default</p></div>'
        result = render_layout_with_slots(html, [])

        assert "Default" in result
        assert 'data-slot="main"' in result

    def test_single_slot_fill(self):
        """Fills a single slot."""
        html = '<div data-slot="main"><p>Default</p></div>'

        # Mock BoundBlock
        content_block = Mock()
        content_block.render.return_value = "<p>New content</p>"

        slot_fills = [{"slot_id": "main", "content": [content_block]}]

        result = render_layout_with_slots(html, slot_fills)

        assert "New content" in result
        assert "Default" not in result

    def test_multiple_slot_fills(self):
        """Fills multiple slots."""
        html = """
        <div data-slot="header"><h1>Default Header</h1></div>
        <div data-slot="main"><p>Default Content</p></div>
        <div data-slot="footer"><p>Default Footer</p></div>
        """

        header_block = Mock()
        header_block.render.return_value = "<h1>Custom Header</h1>"

        main_block = Mock()
        main_block.render.return_value = "<p>Custom Content</p>"

        slot_fills = [
            {"slot_id": "header", "content": [header_block]},
            {"slot_id": "main", "content": [main_block]},
            # footer not filled - should keep default
        ]

        result = render_layout_with_slots(html, slot_fills)

        assert "Custom Header" in result
        assert "Custom Content" in result
        assert "Default Footer" in result  # Unfilled slot keeps default
        assert "Default Header" not in result
        assert "Default Content" not in result

    def test_slot_not_in_html(self):
        """Ignores slot_fill if slot doesn't exist in HTML."""
        html = '<div data-slot="main"></div>'

        content_block = Mock()
        content_block.render.return_value = "<p>Content</p>"

        slot_fills = [{"slot_id": "nonexistent", "content": [content_block]}]

        result = render_layout_with_slots(html, slot_fills)

        # Should not error, just ignore the fill
        assert 'data-slot="main"' in result

    def test_multiple_blocks_in_slot_content(self):
        """Concatenates multiple blocks in slot content."""
        html = '<div data-slot="main"></div>'

        block1 = Mock()
        block1.render.return_value = "<p>First</p>"

        block2 = Mock()
        block2.render.return_value = "<p>Second</p>"

        block3 = Mock()
        block3.render.return_value = "<p>Third</p>"

        slot_fills = [{"slot_id": "main", "content": [block1, block2, block3]}]

        result = render_layout_with_slots(html, slot_fills)

        assert "<p>First</p><p>Second</p><p>Third</p>" in result

    def test_nested_html_structure(self):
        """Handles complex nested HTML."""
        html = """
        <div class="layout">
            <aside class="sidebar">
                <div data-slot="sidebar-top"></div>
                <nav>Fixed nav</nav>
                <div data-slot="sidebar-bottom"><p>Default ads</p></div>
            </aside>
            <main>
                <div data-slot="main"></div>
            </main>
        </div>
        """

        sidebar_top = Mock()
        sidebar_top.render.return_value = "<h2>User Menu</h2>"

        main_content = Mock()
        main_content.render.return_value = "<article>Article content</article>"

        slot_fills = [
            {"slot_id": "sidebar-top", "content": [sidebar_top]},
            {"slot_id": "main", "content": [main_content]},
        ]

        result = render_layout_with_slots(html, slot_fills)

        assert "User Menu" in result
        assert "Article content" in result
        assert "Fixed nav" in result
        assert "Default ads" in result  # sidebar-bottom not filled

    def test_context_propagation(self):
        """Context is passed to block.render() calls."""
        html = '<div data-slot="main"></div>'

        content_block = Mock()
        content_block.render.return_value = "<p>Content</p>"

        slot_fills = [{"slot_id": "main", "content": [content_block]}]

        context = {"page": {"title": "Test Page"}}
        render_layout_with_slots(html, slot_fills, context)

        # Verify context was passed to render
        content_block.render.assert_called_once_with(context)


class TestReusableLayoutBlockRendering:
    """Integration tests for ReusableLayoutBlock rendering."""

    @pytest.mark.django_db
    def test_render_layout_without_slots(self):
        """Renders layout without slots correctly."""
        layout = ReusableBlock.objects.create(
            name="Simple Layout",
            content=[{"type": "rich_text", "value": "<p>Static content</p>"}],
        )

        block = ReusableLayoutBlock()
        value = block.to_python({"layout": layout.id, "slot_content": []})

        html = block.render(value)
        assert "Static content" in html

    @pytest.mark.django_db
    def test_render_layout_with_filled_slot(self):
        """Renders layout with slot filled."""
        layout = ReusableBlock.objects.create(
            name="Layout With Slot",
            content=[
                {
                    "type": "raw_html",
                    "value": '<div data-slot="main"><p>Default</p></div>',
                }
            ],
        )

        block = ReusableLayoutBlock()
        value = block.to_python(
            {
                "layout": layout.id,
                "slot_content": [
                    {
                        "type": "slot_fill",
                        "value": {
                            "slot_id": "main",
                            "content": [
                                {"type": "rich_text", "value": "<p>Custom content</p>"}
                            ],
                        },
                    }
                ],
            }
        )

        html = block.render(value)
        assert "Custom content" in html
        assert "Default" not in html

    @pytest.mark.django_db
    def test_render_preserves_unfilled_slots(self):
        """Unfilled slots keep their default content."""
        layout = ReusableBlock.objects.create(
            name="Multi-Slot Layout",
            content=[
                {
                    "type": "raw_html",
                    "value": """
                        <div data-slot="header"><h1>Default Header</h1></div>
                        <div data-slot="main"><p>Default Main</p></div>
                    """,
                }
            ],
        )

        block = ReusableLayoutBlock()
        value = block.to_python(
            {
                "layout": layout.id,
                "slot_content": [
                    {
                        "type": "slot_fill",
                        "value": {
                            "slot_id": "main",
                            "content": [
                                {"type": "rich_text", "value": "<p>Custom main</p>"}
                            ],
                        },
                    }
                    # header not filled
                ],
            }
        )

        html = block.render(value)
        assert "Custom main" in html
        assert "Default Header" in html  # Preserved

    @pytest.mark.django_db
    def test_render_multiple_slot_fills(self):
        """Renders multiple filled slots correctly."""
        layout = ReusableBlock.objects.create(
            name="Three-Slot Layout",
            content=[
                {
                    "type": "raw_html",
                    "value": """
                        <div data-slot="header"></div>
                        <div data-slot="main"></div>
                        <div data-slot="footer"></div>
                    """,
                }
            ],
        )

        block = ReusableLayoutBlock()
        value = block.to_python(
            {
                "layout": layout.id,
                "slot_content": [
                    {
                        "type": "slot_fill",
                        "value": {
                            "slot_id": "header",
                            "content": [
                                {"type": "rich_text", "value": "<h1>Header</h1>"}
                            ],
                        },
                    },
                    {
                        "type": "slot_fill",
                        "value": {
                            "slot_id": "main",
                            "content": [{"type": "rich_text", "value": "<p>Main</p>"}],
                        },
                    },
                    {
                        "type": "slot_fill",
                        "value": {
                            "slot_id": "footer",
                            "content": [
                                {
                                    "type": "rich_text",
                                    "value": "<footer>Footer</footer>",
                                }
                            ],
                        },
                    },
                ],
            }
        )

        html = block.render(value)
        assert "<h1>Header</h1>" in html
        assert "<p>Main</p>" in html
        assert "<footer>Footer</footer>" in html

    @pytest.mark.django_db
    def test_render_slot_with_multiple_content_blocks(self):
        """Renders multiple content blocks in a single slot."""
        layout = ReusableBlock.objects.create(
            name="Layout",
            content=[{"type": "raw_html", "value": '<div data-slot="main"></div>'}],
        )

        block = ReusableLayoutBlock()
        value = block.to_python(
            {
                "layout": layout.id,
                "slot_content": [
                    {
                        "type": "slot_fill",
                        "value": {
                            "slot_id": "main",
                            "content": [
                                {"type": "rich_text", "value": "<p>First</p>"},
                                {"type": "rich_text", "value": "<p>Second</p>"},
                                {"type": "rich_text", "value": "<p>Third</p>"},
                            ],
                        },
                    }
                ],
            }
        )

        html = block.render(value)
        # All three blocks should be concatenated
        assert "<p>First</p>" in html
        assert "<p>Second</p>" in html
        assert "<p>Third</p>" in html
