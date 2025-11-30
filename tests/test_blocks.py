"""Tests for ReusableBlockChooserBlock."""

import pytest

from wagtail_reusable_blocks.blocks import ReusableBlockChooserBlock
from wagtail_reusable_blocks.models import ReusableBlock


class TestReusableBlockChooserBlock:
    """Tests for ReusableBlockChooserBlock functionality."""

    @pytest.fixture
    def block(self):
        """Create a ReusableBlockChooserBlock instance."""
        return ReusableBlockChooserBlock()

    @pytest.fixture
    def reusable_block(self, db):
        """Create a test ReusableBlock."""
        return ReusableBlock.objects.create(
            name="Test Block",
            content=[
                ("rich_text", "<p>Hello World</p>"),
            ],
        )

    def test_initialization(self, block):
        """ReusableBlockChooserBlock initializes with correct target model."""
        assert block.target_model == ReusableBlock

    def test_render_basic_with_valid_block(self, block, reusable_block):
        """render_basic() renders the ReusableBlock's content."""
        html = block.render_basic(reusable_block)

        assert "<p>Hello World</p>" in html

    def test_render_basic_with_none(self, block):
        """render_basic() returns empty string for None value."""
        html = block.render_basic(None)

        assert html == ""

    def test_render_basic_with_empty_content(self, block, db):
        """render_basic() handles empty content gracefully."""
        empty_block = ReusableBlock.objects.create(
            name="Empty Block",
            content=[],
        )

        html = block.render_basic(empty_block)

        assert html.strip() == ""

    def test_render_basic_with_context(self, block, reusable_block):
        """render_basic() passes context to ReusableBlock.render()."""
        context = {"page_title": "My Page"}
        html = block.render_basic(reusable_block, context=context)

        # Verify content is rendered (context passing tested in test_templates.py)
        assert "<p>Hello World</p>" in html

    def test_render_basic_handles_deleted_block(self, block, reusable_block, db):
        """render_basic() returns empty string for deleted block."""
        # Delete the block
        block_id = reusable_block.id
        reusable_block.delete()

        # Try to render with a stale reference (simulating deleted block)
        # We'll create a mock object with deleted block's id
        class DeletedBlock:
            id = block_id

            def render(self, context=None):
                raise ReusableBlock.DoesNotExist("Block has been deleted")

        deleted = DeletedBlock()
        html = block.render_basic(deleted)

        assert html == ""

    def test_render_basic_handles_rendering_error(self, block, reusable_block):
        """render_basic() handles rendering errors gracefully."""

        # Mock a block that raises an error during rendering
        class ErrorBlock:
            def render(self, context=None):
                raise Exception("Template rendering error")

        error_block = ErrorBlock()
        html = block.render_basic(error_block)

        assert html == ""

    def test_import_from_package(self):
        """ReusableBlockChooserBlock can be imported from package root."""
        from wagtail_reusable_blocks import ReusableBlockChooserBlock

        assert ReusableBlockChooserBlock is not None

    def test_meta_icon(self, block):
        """Block has correct default icon."""
        assert block.meta.icon == "snippet"


class TestReusableBlockChooserBlockIntegration:
    """Integration tests with Wagtail's chooser interface."""

    @pytest.fixture
    def block(self):
        """Create a ReusableBlockChooserBlock instance."""
        return ReusableBlockChooserBlock()

    def test_widget_is_snippet_chooser(self, block):
        """Block uses AdminSnippetChooser widget."""
        from wagtail.snippets.widgets import AdminSnippetChooser

        assert isinstance(block.widget, AdminSnippetChooser)

    def test_widget_targets_reusable_block(self, block):
        """Widget is configured for ReusableBlock model."""
        assert block.widget.model == ReusableBlock

    def test_field_queryset(self, block):
        """Field queryset returns all ReusableBlocks."""
        queryset = block.field.queryset
        assert queryset.model == ReusableBlock

    def test_multiple_blocks_available(self, block, db):
        """Chooser shows all available ReusableBlocks."""
        # Create multiple blocks
        ReusableBlock.objects.create(name="Block 1", content=[])
        ReusableBlock.objects.create(name="Block 2", content=[])
        ReusableBlock.objects.create(name="Block 3", content=[])

        queryset = block.field.queryset
        assert queryset.count() == 3


class TestReusableBlockChooserBlockEdgeCases:
    """Edge case tests for ReusableBlockChooserBlock."""

    @pytest.fixture
    def block(self):
        """Create a ReusableBlockChooserBlock instance."""
        return ReusableBlockChooserBlock()

    def test_render_with_multiple_content_blocks(self, block, db):
        """render_basic() handles multiple content blocks."""
        multi_block = ReusableBlock.objects.create(
            name="Multi Block",
            content=[
                ("rich_text", "<p>First paragraph</p>"),
                ("rich_text", "<p>Second paragraph</p>"),
            ],
        )

        html = block.render_basic(multi_block)

        assert "<p>First paragraph</p>" in html
        assert "<p>Second paragraph</p>" in html

    def test_render_with_raw_html_content(self, block, db):
        """render_basic() handles raw HTML content."""
        html_block = ReusableBlock.objects.create(
            name="HTML Block",
            content=[
                ("raw_html", "<div class='custom'>Custom HTML</div>"),
            ],
        )

        html = block.render_basic(html_block)

        assert "<div class='custom'>Custom HTML</div>" in html

    def test_block_with_special_characters_in_name(self, block, db):
        """Block handles special characters in name."""
        special_block = ReusableBlock.objects.create(
            name="Block with Unicode & Special <chars>",
            content=[("rich_text", "<p>Content</p>")],
        )

        html = block.render_basic(special_block)

        assert "<p>Content</p>" in html
