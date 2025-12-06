"""Tests for ReusableLayoutBlock."""

import pytest

from wagtail_reusable_blocks.blocks import ReusableLayoutBlock
from wagtail_reusable_blocks.models import ReusableBlock


class TestReusableLayoutBlock:
    """Tests for ReusableLayoutBlock."""

    def test_block_creation(self):
        """ReusableLayoutBlock can be instantiated."""
        block = ReusableLayoutBlock()
        assert block is not None

    def test_block_has_required_fields(self):
        """ReusableLayoutBlock has layout and slot_content fields."""
        block = ReusableLayoutBlock()
        assert "layout" in block.child_blocks
        assert "slot_content" in block.child_blocks

    def test_layout_is_snippet_chooser(self):
        """layout field is a SnippetChooserBlock."""
        from wagtail.snippets.blocks import SnippetChooserBlock

        block = ReusableLayoutBlock()
        assert isinstance(block.child_blocks["layout"], SnippetChooserBlock)

    def test_layout_targets_reusable_block(self):
        """layout field targets ReusableBlock model."""
        block = ReusableLayoutBlock()
        layout_block = block.child_blocks["layout"]
        # target_model returns the model class, not string
        from wagtail_reusable_blocks.models import ReusableBlock

        assert layout_block.target_model == ReusableBlock

    def test_slot_content_is_streamblock(self):
        """slot_content field is a StreamBlock."""
        from wagtail.blocks import StreamBlock

        block = ReusableLayoutBlock()
        assert isinstance(block.child_blocks["slot_content"], StreamBlock)

    def test_slot_content_contains_slot_fill(self):
        """slot_content StreamBlock contains slot_fill."""
        block = ReusableLayoutBlock()
        slot_content = block.child_blocks["slot_content"]
        assert "slot_fill" in slot_content.child_blocks

    def test_block_metadata(self):
        """ReusableLayoutBlock has correct metadata."""
        block = ReusableLayoutBlock()
        assert block.meta.icon == "doc-empty"
        assert block.meta.label == "Reusable Layout"

    @pytest.mark.django_db
    def test_get_form_context_with_layout(self):
        """get_form_context() adds available_slots when layout is selected."""
        layout = ReusableBlock.objects.create(
            name="Layout with Slots",
            content=[
                {
                    "type": "raw_html",
                    "value": """
                        <div data-slot="header" data-slot-label="Header Area"></div>
                        <div data-slot="main"></div>
                    """,
                }
            ],
        )

        block = ReusableLayoutBlock()
        value = block.to_python({"layout": layout.id, "slot_content": []})

        context = block.get_form_context(value, prefix="test")

        assert "available_slots" in context
        assert len(context["available_slots"]) == 2
        assert context["available_slots"][0]["id"] == "header"
        assert context["available_slots"][0]["label"] == "Header Area"
        assert context["available_slots"][1]["id"] == "main"

    def test_get_form_context_without_layout(self):
        """get_form_context() works when no layout is selected."""
        block = ReusableLayoutBlock()
        value = block.to_python({"layout": None, "slot_content": []})

        context = block.get_form_context(value, prefix="test")

        assert "available_slots" not in context

    def test_get_form_context_with_empty_value(self):
        """get_form_context() works with empty dict value."""
        block = ReusableLayoutBlock()

        # Empty dict represents no value selected yet
        context = block.get_form_context({}, prefix="test")

        assert "available_slots" not in context

    @pytest.mark.django_db
    def test_block_value_creation(self):
        """ReusableLayoutBlock can create and store values."""
        layout_block_model = ReusableBlock.objects.create(
            name="Test Layout",
            content=[{"type": "raw_html", "value": '<div data-slot="main"></div>'}],
        )

        block = ReusableLayoutBlock()
        value = block.to_python(
            {
                "layout": layout_block_model.id,  # Use ID for SnippetChooserBlock
                "slot_content": [
                    {
                        "type": "slot_fill",
                        "value": {
                            "slot_id": "main",
                            "content": [
                                {"type": "rich_text", "value": "<p>Content</p>"}
                            ],
                        },
                    }
                ],
            }
        )

        assert value["layout"] == layout_block_model
        assert len(value["slot_content"]) == 1

    @pytest.mark.django_db
    def test_empty_slot_content_allowed(self):
        """slot_content can be empty."""
        layout_block_model = ReusableBlock.objects.create(
            name="Test Layout", content=[]
        )

        block = ReusableLayoutBlock()
        value = block.to_python({"layout": layout_block_model.id, "slot_content": []})

        # Should not raise
        block.clean(value)
        assert len(value["slot_content"]) == 0

    @pytest.mark.django_db
    def test_render_without_slots(self):
        """Rendering works even without slot_content."""
        layout_block_model = ReusableBlock.objects.create(
            name="Simple Layout",
            content=[{"type": "rich_text", "value": "<p>Static content</p>"}],
        )

        block = ReusableLayoutBlock()
        value = block.to_python({"layout": layout_block_model.id, "slot_content": []})

        html = block.render(value)
        assert "Static content" in html

    @pytest.mark.django_db
    def test_multiple_slot_fills(self):
        """Can have multiple slot_fill blocks."""
        layout_block_model = ReusableBlock.objects.create(
            name="Multi-Slot Layout",
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
                "layout": layout_block_model.id,
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

        assert len(value["slot_content"]) == 3


class TestSlotFillNesting:
    """Tests for nesting ReusableBlocks within SlotFill."""

    @pytest.mark.django_db
    def test_slot_fill_can_contain_reusable_block(self):
        """SlotFill content can include ReusableBlockChooserBlock."""
        from wagtail_reusable_blocks.blocks import SlotFillBlock

        nested_block = ReusableBlock.objects.create(
            name="Nested Content",
            content=[{"type": "rich_text", "value": "<p>Nested</p>"}],
        )

        block = SlotFillBlock()
        value = block.to_python(
            {
                "slot_id": "main",
                "content": [{"type": "reusable_block", "value": nested_block.id}],
            }
        )

        assert len(value["content"]) == 1
        assert value["content"][0].block_type == "reusable_block"

    @pytest.mark.django_db
    def test_slot_fill_can_contain_reusable_layout(self):
        """SlotFill content can include ReusableLayoutBlock (recursive)."""
        from wagtail_reusable_blocks.blocks import SlotFillBlock

        nested_layout = ReusableBlock.objects.create(
            name="Nested Layout",
            content=[{"type": "raw_html", "value": '<div data-slot="inner"></div>'}],
        )

        block = SlotFillBlock()

        # First, check if reusable_layout is available
        content_block = block.child_blocks["content"]
        if "reusable_layout" not in content_block.child_blocks:
            pytest.skip("reusable_layout not yet loaded (circular import)")

        value = block.to_python(
            {
                "slot_id": "main",
                "content": [
                    {
                        "type": "reusable_layout",
                        "value": {"layout": nested_layout.id, "slot_content": []},
                    }
                ],
            }
        )

        assert len(value["content"]) == 1
        assert value["content"][0].block_type == "reusable_layout"

    @pytest.mark.django_db
    def test_slot_fill_has_image_support(self):
        """SlotFill content can include ImageChooserBlock."""
        from wagtail_reusable_blocks.blocks import SlotFillBlock

        block = SlotFillBlock()

        # Check that image block type is available
        content_block = block.child_blocks["content"]
        assert "image" in content_block.child_blocks

    def test_slot_fill_content_block_types(self):
        """SlotFill content has all expected block types."""
        from wagtail_reusable_blocks.blocks import SlotFillBlock

        block = SlotFillBlock()
        content_block = block.child_blocks["content"]

        # v0.1.0 types
        assert "rich_text" in content_block.child_blocks
        assert "raw_html" in content_block.child_blocks

        # v0.2.0 types
        assert "image" in content_block.child_blocks
        assert "reusable_block" in content_block.child_blocks

        # reusable_layout should be available for nested layouts (Issue #62)
        assert "reusable_layout" in content_block.child_blocks


class TestReusableLayoutBlockCustomization:
    """Tests for ReusableLayoutBlock customization options."""

    def test_layout_block_with_custom_local_blocks(self):
        """ReusableLayoutBlock can be initialized with custom local_blocks."""
        from wagtail.blocks import StreamBlock

        from wagtail_reusable_blocks.blocks import SlotFillBlock

        # Create custom slot_content block
        custom_slot_content = StreamBlock([("slot_fill", SlotFillBlock())])

        # Pass local_blocks with custom slot_content
        block = ReusableLayoutBlock(
            local_blocks=[
                ("slot_content", custom_slot_content),
            ]
        )

        # Should use the provided slot_content block
        assert "slot_content" in block.child_blocks
        assert "layout" in block.child_blocks

    def test_layout_block_with_empty_local_blocks(self):
        """ReusableLayoutBlock handles empty local_blocks list."""
        block = ReusableLayoutBlock(local_blocks=[])

        # Should still have layout and slot_content
        assert "layout" in block.child_blocks
        assert "slot_content" in block.child_blocks
