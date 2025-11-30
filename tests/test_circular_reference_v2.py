"""Tests for v0.2.0 circular reference detection with slots."""

import pytest
from django.core.exceptions import ValidationError
from wagtail.blocks import RawHTMLBlock, RichTextBlock

from wagtail_reusable_blocks.models import ReusableBlock


class TestCircularReferenceWithLayoutBlocks:
    """Tests for circular reference detection with ReusableLayoutBlock."""

    @pytest.fixture(autouse=True)
    def patch_streamfield(self, monkeypatch):
        """Patch ReusableBlock's content field to include ReusableBlockChooserBlock and ReusableLayoutBlock."""
        from wagtail.blocks import StreamBlock

        from wagtail_reusable_blocks.blocks import (
            ReusableBlockChooserBlock,
            ReusableLayoutBlock,
        )

        new_child_blocks = [
            ("rich_text", RichTextBlock()),
            ("raw_html", RawHTMLBlock()),
            ("reusable_block", ReusableBlockChooserBlock()),
            ("reusable_layout", ReusableLayoutBlock()),
        ]

        new_stream_block = StreamBlock(new_child_blocks, required=False)
        monkeypatch.setattr(
            ReusableBlock.content.field, "stream_block", new_stream_block
        )

    @pytest.mark.django_db
    def test_layout_block_in_content_detected(self):
        """Detects ReusableBlock referenced in layout field."""
        # Create a layout template
        layout = ReusableBlock.objects.create(
            name="Layout Template",
            content=[{"type": "raw_html", "value": '<div data-slot="main"></div>'}],
        )

        # Create a block that uses the layout
        block_with_layout = ReusableBlock.objects.create(
            name="Block With Layout",
            content=[
                {
                    "type": "reusable_layout",
                    "value": {
                        "layout": layout.id,
                        "slot_content": [],
                    },
                }
            ],
        )

        # Verify the layout is detected
        refs = block_with_layout._get_referenced_blocks()
        assert len(refs) == 1
        assert refs[0] == layout

    @pytest.mark.django_db
    def test_block_in_slot_content_detected(self):
        """Detects ReusableBlock nested in slot content."""
        # Create a nested block
        nested_block = ReusableBlock.objects.create(
            name="Nested Block",
            content=[{"type": "rich_text", "value": "<p>Nested content</p>"}],
        )

        # Create a layout
        layout = ReusableBlock.objects.create(
            name="Layout",
            content=[{"type": "raw_html", "value": '<div data-slot="main"></div>'}],
        )

        # Create a block that uses the layout and fills slot with nested block
        block_with_nested = ReusableBlock.objects.create(
            name="Block With Nested",
            content=[
                {
                    "type": "reusable_layout",
                    "value": {
                        "layout": layout.id,
                        "slot_content": [
                            {
                                "type": "slot_fill",
                                "value": {
                                    "slot_id": "main",
                                    "content": [
                                        {
                                            "type": "reusable_block",
                                            "value": nested_block.id,
                                        }
                                    ],
                                },
                            }
                        ],
                    },
                }
            ],
        )

        # Verify both layout and nested block are detected
        refs = block_with_nested._get_referenced_blocks()
        assert len(refs) == 2
        assert layout in refs
        assert nested_block in refs

    @pytest.mark.django_db
    def test_circular_reference_via_layout(self):
        """Detects circular reference through layout blocks."""
        # Create block A with placeholder content
        block_a = ReusableBlock.objects.create(
            name="Block A",
            content=[{"type": "raw_html", "value": '<div data-slot="main"></div>'}],
        )

        # Create block B that references A via layout
        block_b = ReusableBlock.objects.create(
            name="Block B",
            content=[
                {
                    "type": "reusable_layout",
                    "value": {
                        "layout": block_a.id,
                        "slot_content": [],
                    },
                }
            ],
        )

        # Try to update A to reference B (creating a cycle)
        block_a.content = [
            {
                "type": "reusable_layout",
                "value": {
                    "layout": block_b.id,
                    "slot_content": [],
                },
            }
        ]

        # Should detect circular reference
        with pytest.raises(ValidationError, match="Circular reference detected"):
            block_a.save()

    @pytest.mark.django_db
    def test_circular_reference_via_slot_content(self):
        """Detects circular reference through slot content."""
        # Create block A
        block_a = ReusableBlock.objects.create(
            name="Block A",
            content=[{"type": "raw_html", "value": '<div data-slot="main"></div>'}],
        )

        # Create layout
        layout = ReusableBlock.objects.create(
            name="Layout",
            content=[{"type": "raw_html", "value": '<div data-slot="content"></div>'}],
        )

        # Create block B that uses layout with A in slot
        block_b = ReusableBlock.objects.create(
            name="Block B",
            content=[
                {
                    "type": "reusable_layout",
                    "value": {
                        "layout": layout.id,
                        "slot_content": [
                            {
                                "type": "slot_fill",
                                "value": {
                                    "slot_id": "content",
                                    "content": [
                                        {"type": "reusable_block", "value": block_a.id}
                                    ],
                                },
                            }
                        ],
                    },
                }
            ],
        )

        # Try to update A to reference B (creating a cycle)
        block_a.content = [{"type": "reusable_block", "value": block_b.id}]

        # Should detect circular reference
        with pytest.raises(ValidationError, match="Circular reference detected"):
            block_a.save()

    @pytest.mark.django_db
    def test_self_reference_via_layout(self):
        """Detects self-reference through layout."""
        # Create a block
        block = ReusableBlock.objects.create(
            name="Self Referencing Block",
            content=[{"type": "raw_html", "value": '<div data-slot="main"></div>'}],
        )

        # Try to reference itself via layout
        block.content = [
            {
                "type": "reusable_layout",
                "value": {
                    "layout": block.id,
                    "slot_content": [],
                },
            }
        ]

        # Should detect self-reference
        with pytest.raises(ValidationError, match="Circular reference detected"):
            block.save()

    @pytest.mark.django_db
    def test_three_way_cycle_with_layouts(self):
        """Detects three-way circular reference: A → Layout(B) → Layout(C) → A."""
        # Create three blocks
        block_a = ReusableBlock.objects.create(
            name="Block A",
            content=[{"type": "raw_html", "value": '<div data-slot="main"></div>'}],
        )

        block_b = ReusableBlock.objects.create(
            name="Block B",
            content=[{"type": "raw_html", "value": '<div data-slot="main"></div>'}],
        )

        block_c = ReusableBlock.objects.create(
            name="Block C",
            content=[{"type": "raw_html", "value": '<div data-slot="main"></div>'}],
        )

        # A uses layout B
        block_a.content = [
            {
                "type": "reusable_layout",
                "value": {
                    "layout": block_b.id,
                    "slot_content": [],
                },
            }
        ]
        block_a.save()

        # B uses layout C
        block_b.content = [
            {
                "type": "reusable_layout",
                "value": {
                    "layout": block_c.id,
                    "slot_content": [],
                },
            }
        ]
        block_b.save()

        # Try to make C use layout A (creating cycle)
        block_c.content = [
            {
                "type": "reusable_layout",
                "value": {
                    "layout": block_a.id,
                    "slot_content": [],
                },
            }
        ]

        # Should detect circular reference
        with pytest.raises(ValidationError, match="Circular reference detected"):
            block_c.save()

    @pytest.mark.django_db
    def test_mixed_v1_v2_circular_reference(self):
        """Detects circular reference mixing v0.1.0 and v0.2.0 patterns."""
        # Block A uses ReusableBlockChooserBlock (v0.1.0)
        block_a = ReusableBlock.objects.create(
            name="Block A",
            content=[{"type": "rich_text", "value": "<p>Content A</p>"}],
        )

        # Block B uses ReusableLayoutBlock (v0.2.0)
        block_b = ReusableBlock.objects.create(
            name="Block B",
            content=[{"type": "raw_html", "value": '<div data-slot="main"></div>'}],
        )

        # A references B via v0.1.0 style
        block_a.content = [{"type": "reusable_block", "value": block_b.id}]
        block_a.save()

        # Try to make B reference A via v0.2.0 style (creating cycle)
        block_b.content = [
            {
                "type": "reusable_layout",
                "value": {
                    "layout": block_a.id,
                    "slot_content": [],
                },
            }
        ]

        # Should detect circular reference
        with pytest.raises(ValidationError, match="Circular reference detected"):
            block_b.save()

    @pytest.mark.django_db
    def test_deep_nesting_without_circular_reference(self):
        """Allows deep nesting if no circular reference."""
        # Create a chain: A → Layout(B) → Slot(C) → D
        block_d = ReusableBlock.objects.create(
            name="Block D",
            content=[{"type": "rich_text", "value": "<p>End of chain</p>"}],
        )

        block_c = ReusableBlock.objects.create(
            name="Block C",
            content=[{"type": "reusable_block", "value": block_d.id}],
        )

        block_b = ReusableBlock.objects.create(
            name="Block B",
            content=[{"type": "raw_html", "value": '<div data-slot="main"></div>'}],
        )

        block_a = ReusableBlock.objects.create(
            name="Block A",
            content=[
                {
                    "type": "reusable_layout",
                    "value": {
                        "layout": block_b.id,
                        "slot_content": [
                            {
                                "type": "slot_fill",
                                "value": {
                                    "slot_id": "main",
                                    "content": [
                                        {"type": "reusable_block", "value": block_c.id}
                                    ],
                                },
                            }
                        ],
                    },
                }
            ],
        )

        # Should not raise ValidationError
        block_a.save()

        # Verify all blocks in chain are detected
        refs = block_a._get_referenced_blocks()
        assert block_b in refs
        assert block_c in refs


class TestGetBlocksFromStreamfield:
    """Tests for _get_blocks_from_streamfield helper method."""

    @pytest.fixture(autouse=True)
    def patch_streamfield(self, monkeypatch):
        """Patch ReusableBlock's content field to include ReusableBlockChooserBlock and ReusableLayoutBlock."""
        from wagtail.blocks import StreamBlock

        from wagtail_reusable_blocks.blocks import (
            ReusableBlockChooserBlock,
            ReusableLayoutBlock,
        )

        new_child_blocks = [
            ("rich_text", RichTextBlock()),
            ("raw_html", RawHTMLBlock()),
            ("reusable_block", ReusableBlockChooserBlock()),
            ("reusable_layout", ReusableLayoutBlock()),
        ]

        new_stream_block = StreamBlock(new_child_blocks, required=False)
        monkeypatch.setattr(
            ReusableBlock.content.field, "stream_block", new_stream_block
        )

    @pytest.mark.django_db
    def test_extract_reusable_block_from_streamfield(self):
        """Extracts ReusableBlock from StreamField value."""
        nested = ReusableBlock.objects.create(
            name="Nested",
            content=[{"type": "rich_text", "value": "<p>Nested</p>"}],
        )

        parent = ReusableBlock.objects.create(
            name="Parent",
            content=[{"type": "reusable_block", "value": nested.id}],
        )

        # Get streamfield value
        streamfield_value = parent.content

        # Extract blocks
        blocks = parent._get_blocks_from_streamfield(streamfield_value)

        assert len(blocks) == 1
        assert blocks[0] == nested

    @pytest.mark.django_db
    def test_extract_layout_from_streamfield(self):
        """Extracts layout from StreamField value."""
        layout = ReusableBlock.objects.create(
            name="Layout",
            content=[{"type": "raw_html", "value": '<div data-slot="main"></div>'}],
        )

        parent = ReusableBlock.objects.create(
            name="Parent",
            content=[
                {
                    "type": "reusable_layout",
                    "value": {
                        "layout": layout.id,
                        "slot_content": [],
                    },
                }
            ],
        )

        streamfield_value = parent.content
        blocks = parent._get_blocks_from_streamfield(streamfield_value)

        assert len(blocks) == 1
        assert blocks[0] == layout

    @pytest.mark.django_db
    def test_extract_nested_blocks_recursively(self):
        """Recursively extracts deeply nested blocks."""
        deeply_nested = ReusableBlock.objects.create(
            name="Deeply Nested",
            content=[{"type": "rich_text", "value": "<p>Deep</p>"}],
        )

        layout = ReusableBlock.objects.create(
            name="Layout",
            content=[{"type": "raw_html", "value": '<div data-slot="main"></div>'}],
        )

        parent = ReusableBlock.objects.create(
            name="Parent",
            content=[
                {
                    "type": "reusable_layout",
                    "value": {
                        "layout": layout.id,
                        "slot_content": [
                            {
                                "type": "slot_fill",
                                "value": {
                                    "slot_id": "main",
                                    "content": [
                                        {
                                            "type": "reusable_block",
                                            "value": deeply_nested.id,
                                        }
                                    ],
                                },
                            }
                        ],
                    },
                }
            ],
        )

        streamfield_value = parent.content
        blocks = parent._get_blocks_from_streamfield(streamfield_value)

        assert len(blocks) == 2
        assert layout in blocks
        assert deeply_nested in blocks
