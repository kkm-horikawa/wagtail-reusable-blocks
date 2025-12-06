"""Tests for SlotFillBlock (Issue #47)."""

from wagtail.blocks import RichTextBlock

from wagtail_reusable_blocks.blocks import SlotFillBlock


class TestSlotFillBlock:
    """Tests for SlotFillBlock structure and behavior."""

    def test_block_creation(self):
        """SlotFillBlock can be instantiated."""
        block = SlotFillBlock()
        assert block is not None

    def test_block_has_slot_id_field(self):
        """SlotFillBlock has slot_id CharBlock field."""
        block = SlotFillBlock()
        assert "slot_id" in block.child_blocks
        # CharBlock exists and is the correct type
        from wagtail.blocks import CharBlock

        assert isinstance(block.child_blocks["slot_id"], CharBlock)

    def test_block_has_content_field(self):
        """SlotFillBlock has content StreamBlock field."""
        block = SlotFillBlock()
        assert "content" in block.child_blocks
        # StreamBlock should have child blocks
        content_block = block.child_blocks["content"]
        assert "rich_text" in content_block.child_blocks
        assert "raw_html" in content_block.child_blocks

    def test_block_value_structure(self):
        """SlotFillBlock value has correct structure."""
        block = SlotFillBlock()

        # Create a value
        value = block.to_python(
            {
                "slot_id": "main",
                "content": [{"type": "rich_text", "value": "<p>Test content</p>"}],
            }
        )

        # Verify structure
        assert value["slot_id"] == "main"
        assert len(value["content"]) == 1
        assert value["content"][0].block_type == "rich_text"

    def test_slot_id_validation(self):
        """slot_id field validates correctly."""
        block = SlotFillBlock()
        slot_id_block = block.child_blocks["slot_id"]

        # Valid IDs
        assert slot_id_block.clean("main") == "main"
        assert slot_id_block.clean("sidebar-top") == "sidebar-top"
        assert slot_id_block.clean("content_1") == "content_1"

        # Empty should be allowed (Wagtail's default behavior)
        # The block itself might be optional in StreamField

    def test_content_field_accepts_rich_text(self):
        """content field accepts RichTextBlock."""
        block = SlotFillBlock()
        value = block.to_python(
            {
                "slot_id": "test",
                "content": [{"type": "rich_text", "value": "<p>Rich text content</p>"}],
            }
        )

        assert value["content"][0].block_type == "rich_text"
        assert isinstance(value["content"][0].block, RichTextBlock)

    def test_content_field_accepts_raw_html(self):
        """content field accepts RawHTMLBlock."""
        block = SlotFillBlock()
        value = block.to_python(
            {
                "slot_id": "test",
                "content": [{"type": "raw_html", "value": "<div>Custom HTML</div>"}],
            }
        )

        assert value["content"][0].block_type == "raw_html"

    def test_content_field_accepts_multiple_blocks(self):
        """content field can contain multiple blocks."""
        block = SlotFillBlock()
        value = block.to_python(
            {
                "slot_id": "test",
                "content": [
                    {"type": "rich_text", "value": "<p>First</p>"},
                    {"type": "raw_html", "value": "<hr>"},
                    {"type": "rich_text", "value": "<p>Second</p>"},
                ],
            }
        )

        assert len(value["content"]) == 3

    def test_empty_content_allowed(self):
        """content field can be empty (useful for clearing default content)."""
        block = SlotFillBlock()
        value = block.to_python({"slot_id": "test", "content": []})

        assert value["slot_id"] == "test"
        assert len(value["content"]) == 0

    def test_meta_properties(self):
        """SlotFillBlock has correct Meta properties."""
        block = SlotFillBlock()
        assert block.meta.icon == "placeholder"
        assert block.meta.label == "Slot Fill"


class TestSlotFillBlockRendering:
    """Tests for SlotFillBlock rendering behavior."""

    def test_rendering_is_not_used_directly(self):
        """SlotFillBlock is not rendered directly (used by ReusableLayoutBlock)."""
        # SlotFillBlock is a data structure block
        # Its rendering is handled by ReusableLayoutBlock's render() method
        # So we don't test render() here - it uses default StructBlock rendering

        block = SlotFillBlock()
        value = block.to_python(
            {
                "slot_id": "test",
                "content": [{"type": "rich_text", "value": "<p>Content</p>"}],
            }
        )

        # The block can be rendered (uses default StructBlock rendering)
        # but this is not the intended use case
        rendered = block.render(value)
        assert rendered is not None  # Just verify it doesn't error


class TestSlotContentStreamBlock:
    """Tests for SlotContentStreamBlock."""

    def test_slot_content_stream_block_has_correct_types(self):
        """SlotContentStreamBlock includes all expected block types."""
        from wagtail_reusable_blocks.blocks.slot_fill import SlotContentStreamBlock

        block = SlotContentStreamBlock()

        # Should have basic types
        assert "rich_text" in block.child_blocks
        assert "raw_html" in block.child_blocks
        assert "image" in block.child_blocks
        assert "reusable_block" in block.child_blocks

        # reusable_layout should be available for nested layouts
        assert "reusable_layout" in block.child_blocks

    def test_slot_content_stream_block_includes_reusable_layout(self):
        """SlotContentStreamBlock includes ReusableLayoutBlock for nested layouts."""
        from wagtail_reusable_blocks.blocks.slot_fill import SlotContentStreamBlock

        block = SlotContentStreamBlock()

        # Should have reusable_layout for nested layouts (Issue #62)
        assert "reusable_layout" in block.child_blocks

        # Verify it's the correct type
        from wagtail_reusable_blocks.blocks import ReusableLayoutBlock

        assert isinstance(block.child_blocks["reusable_layout"], ReusableLayoutBlock)


class TestSlotFillBlockCustomization:
    """Tests for SlotFillBlock customization options."""

    def test_slot_fill_with_custom_local_blocks(self):
        """SlotFillBlock can be initialized with custom local_blocks."""
        from wagtail_reusable_blocks.blocks.slot_fill import SlotContentStreamBlock

        # Create custom content block
        custom_content = SlotContentStreamBlock()

        # Pass local_blocks with custom content
        block = SlotFillBlock(
            local_blocks=[
                ("content", custom_content),
            ]
        )

        # Should use the provided content block
        assert "content" in block.child_blocks
        assert "slot_id" in block.child_blocks

    def test_slot_fill_with_empty_local_blocks(self):
        """SlotFillBlock handles empty local_blocks list."""
        block = SlotFillBlock(local_blocks=[])

        # Should still have slot_id and content
        assert "slot_id" in block.child_blocks
        assert "content" in block.child_blocks


class TestSlotFillBlockIntegration:
    """Integration tests for SlotFillBlock."""

    def test_import_from_package(self):
        """SlotFillBlock can be imported from package."""
        from wagtail_reusable_blocks.blocks import SlotFillBlock as ImportedBlock

        assert ImportedBlock is not None

    def test_block_in_all_exports(self):
        """SlotFillBlock is in __all__ exports."""
        from wagtail_reusable_blocks import blocks

        assert "SlotFillBlock" in blocks.__all__
