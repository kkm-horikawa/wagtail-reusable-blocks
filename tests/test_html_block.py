"""Tests for the HTMLBlock conditional import."""

from wagtail.blocks import RawHTMLBlock


class TestHTMLBlockImport:
    """Test HTMLBlock import and fallback behavior."""

    def test_html_block_importable(self):
        """HTMLBlock should be importable from blocks.html."""
        from wagtail_reusable_blocks.blocks.html import HTMLBlock

        assert HTMLBlock is not None

    def test_html_block_is_raw_html_block_without_editor(self):
        """Without wagtail-html-editor, HTMLBlock should be RawHTMLBlock."""
        from wagtail_reusable_blocks.blocks.html import HTMLBlock

        # In test environment, wagtail-html-editor is not installed
        # so HTMLBlock should be RawHTMLBlock
        assert HTMLBlock is RawHTMLBlock

    def test_html_block_in_all(self):
        """HTMLBlock should be in __all__."""
        from wagtail_reusable_blocks.blocks import html

        assert "HTMLBlock" in html.__all__


class TestHTMLBlockUsage:
    """Test HTMLBlock is used correctly in the codebase."""

    def test_slot_fill_uses_html_block(self):
        """SlotContentStreamBlock should use HTMLBlock."""
        from wagtail_reusable_blocks.blocks.slot_fill import SlotContentStreamBlock

        block = SlotContentStreamBlock()
        child_blocks = dict(block.child_blocks)

        assert "raw_html" in child_blocks
        # Should be RawHTMLBlock (fallback) in test environment
        assert isinstance(child_blocks["raw_html"], RawHTMLBlock)

    def test_reusable_block_content_uses_html_block(self):
        """ReusableBlock.content should use HTMLBlock."""
        from wagtail_reusable_blocks.models import ReusableBlock

        content_field = ReusableBlock._meta.get_field("content")
        stream_block = content_field.stream_block

        child_blocks = dict(stream_block.child_blocks)
        assert "raw_html" in child_blocks
        # Should be RawHTMLBlock (fallback) in test environment
        assert isinstance(child_blocks["raw_html"], RawHTMLBlock)
