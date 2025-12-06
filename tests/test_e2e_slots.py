"""End-to-end tests for slot-based templating system.

These tests verify the complete user journey from creating layouts
to rendering them on pages.
"""

import pytest

from wagtail_reusable_blocks.blocks import ReusableLayoutBlock
from wagtail_reusable_blocks.models import ReusableBlock


@pytest.mark.django_db
class TestSlotBasedTemplatingE2E:
    """End-to-end tests for the complete slot workflow."""

    def test_complete_slot_workflow(self):
        """Test the full workflow from layout creation to rendering.

        This test verifies:
        1. Creating a ReusableBlock with slots
        2. Creating a ReusableLayoutBlock value
        3. Filling slots with content
        4. Rendering the final HTML
        """
        # 1. Create a layout with slots
        layout = ReusableBlock.objects.create(
            name="Two Column Layout",
            content=[
                {
                    "type": "raw_html",
                    "value": """
                        <div class="layout">
                            <aside data-slot="sidebar" data-slot-label="Sidebar">
                                <p>Default sidebar</p>
                            </aside>
                            <main data-slot="main" data-slot-label="Main Content">
                                <p>Default main</p>
                            </main>
                        </div>
                    """,
                }
            ],
        )

        # 2. Create a ReusableLayoutBlock instance
        block = ReusableLayoutBlock()

        # 3. Create block value with slot fills
        value = block.to_python(
            {
                "layout": layout.pk,
                "slot_content": [
                    {
                        "type": "slot_fill",
                        "value": {
                            "slot_id": "main",
                            "content": [
                                {
                                    "type": "rich_text",
                                    "value": "<p>Article content here</p>",
                                }
                            ],
                        },
                    },
                    {
                        "type": "slot_fill",
                        "value": {
                            "slot_id": "sidebar",
                            "content": [
                                {
                                    "type": "raw_html",
                                    "value": "<div>Custom sidebar</div>",
                                }
                            ],
                        },
                    },
                ],
            }
        )

        # 4. Render the block
        html = block.render(value)

        # 5. Verify slots were filled correctly
        assert "Article content here" in html
        assert "Custom sidebar" in html
        assert "Default sidebar" not in html  # Replaced
        assert "Default main" not in html  # Replaced

    def test_unfilled_slots_show_default_content(self):
        """Test that unfilled slots display their default content."""
        # Create layout with default content
        layout = ReusableBlock.objects.create(
            name="Layout with Defaults",
            content=[
                {
                    "type": "raw_html",
                    "value": """
                        <div>
                            <div data-slot="slot1">
                                <p>Default for slot1</p>
                            </div>
                            <div data-slot="slot2">
                                <p>Default for slot2</p>
                            </div>
                        </div>
                    """,
                }
            ],
        )

        block = ReusableLayoutBlock()

        # Create value that only fills slot1
        value = block.to_python(
            {
                "layout": layout.pk,
                "slot_content": [
                    {
                        "type": "slot_fill",
                        "value": {
                            "slot_id": "slot1",
                            "content": [
                                {"type": "raw_html", "value": "<p>Custom slot1</p>"}
                            ],
                        },
                    }
                    # slot2 not filled
                ],
            }
        )

        # Render
        html = block.render(value)

        # Verify slot1 is custom, slot2 is default
        assert "Custom slot1" in html
        assert "Default for slot1" not in html
        assert "Default for slot2" in html  # Unfilled, shows default

    def test_nested_layouts(self):
        """Test nested ReusableLayoutBlock within slots."""
        # Create outer layout
        outer_layout = ReusableBlock.objects.create(
            name="Page Wrapper",
            content=[
                {
                    "type": "raw_html",
                    "value": """
                        <div class="page">
                            <header>Site Header</header>
                            <div data-slot="content"></div>
                            <footer>Site Footer</footer>
                        </div>
                    """,
                }
            ],
        )

        # Create inner layout
        inner_layout = ReusableBlock.objects.create(
            name="Two Column",
            content=[
                {
                    "type": "raw_html",
                    "value": """
                        <div class="columns">
                            <aside data-slot="sidebar"></aside>
                            <main data-slot="main"></main>
                        </div>
                    """,
                }
            ],
        )

        block = ReusableLayoutBlock()

        # Create value with nested layouts
        value = block.to_python(
            {
                "layout": outer_layout.pk,
                "slot_content": [
                    {
                        "type": "slot_fill",
                        "value": {
                            "slot_id": "content",
                            "content": [
                                {
                                    "type": "reusable_layout",  # Nested layout!
                                    "value": {
                                        "layout": inner_layout.pk,
                                        "slot_content": [
                                            {
                                                "type": "slot_fill",
                                                "value": {
                                                    "slot_id": "main",
                                                    "content": [
                                                        {
                                                            "type": "rich_text",
                                                            "value": "<p>Nested content</p>",
                                                        }
                                                    ],
                                                },
                                            }
                                        ],
                                    },
                                }
                            ],
                        },
                    }
                ],
            }
        )

        # Render
        html = block.render(value)

        # Verify nesting worked
        assert "Site Header" in html
        assert "Site Footer" in html
        assert "Nested content" in html

    def test_mixing_v1_and_v2_blocks(self):
        """Test using ReusableBlockChooserBlock inside a slot."""
        # Create v0.1.0 content block
        content_block = ReusableBlock.objects.create(
            name="Promo Banner",
            content=[{"type": "rich_text", "value": "<div class='promo'>Sale!</div>"}],
        )

        # Create v0.2.0 layout
        layout = ReusableBlock.objects.create(
            name="Layout",
            content=[{"type": "raw_html", "value": "<div data-slot='main'></div>"}],
        )

        block = ReusableLayoutBlock()

        # Create value using both
        value = block.to_python(
            {
                "layout": layout.pk,
                "slot_content": [
                    {
                        "type": "slot_fill",
                        "value": {
                            "slot_id": "main",
                            "content": [
                                {
                                    "type": "reusable_block",  # v0.1.0 block in v0.2.0 slot
                                    "value": content_block.pk,
                                },
                                {
                                    "type": "rich_text",
                                    "value": "<p>Main content</p>",
                                },
                            ],
                        },
                    }
                ],
            }
        )

        # Render
        html = block.render(value)

        # Both should render
        assert "Sale!" in html
        assert "Main content" in html

    def test_multiple_slots_same_layout(self):
        """Test filling multiple slots in the same layout."""
        layout = ReusableBlock.objects.create(
            name="Three Slot Layout",
            content=[
                {
                    "type": "raw_html",
                    "value": """
                        <div>
                            <header data-slot="header">Default Header</header>
                            <main data-slot="main">Default Main</main>
                            <footer data-slot="footer">Default Footer</footer>
                        </div>
                    """,
                }
            ],
        )

        block = ReusableLayoutBlock()

        value = block.to_python(
            {
                "layout": layout.pk,
                "slot_content": [
                    {
                        "type": "slot_fill",
                        "value": {
                            "slot_id": "header",
                            "content": [
                                {"type": "raw_html", "value": "<h1>Custom Header</h1>"}
                            ],
                        },
                    },
                    {
                        "type": "slot_fill",
                        "value": {
                            "slot_id": "main",
                            "content": [
                                {
                                    "type": "rich_text",
                                    "value": "<p>Custom Main</p>",
                                }
                            ],
                        },
                    },
                    {
                        "type": "slot_fill",
                        "value": {
                            "slot_id": "footer",
                            "content": [
                                {
                                    "type": "raw_html",
                                    "value": "<p>Custom Footer</p>",
                                }
                            ],
                        },
                    },
                ],
            }
        )

        html = block.render(value)

        # All slots should be filled
        assert "Custom Header" in html
        assert "Custom Main" in html
        assert "Custom Footer" in html
        assert "Default Header" not in html
        assert "Default Main" not in html
        assert "Default Footer" not in html

    def test_complex_slot_content(self):
        """Test slots containing multiple blocks."""
        layout = ReusableBlock.objects.create(
            name="Single Slot",
            content=[
                {
                    "type": "raw_html",
                    "value": "<div data-slot='content'></div>",
                }
            ],
        )

        block = ReusableLayoutBlock()

        value = block.to_python(
            {
                "layout": layout.pk,
                "slot_content": [
                    {
                        "type": "slot_fill",
                        "value": {
                            "slot_id": "content",
                            "content": [
                                {
                                    "type": "rich_text",
                                    "value": "<h2>First Block</h2>",
                                },
                                {
                                    "type": "raw_html",
                                    "value": "<div>Second Block</div>",
                                },
                                {
                                    "type": "rich_text",
                                    "value": "<p>Third Block</p>",
                                },
                            ],
                        },
                    }
                ],
            }
        )

        html = block.render(value)

        # All blocks should render in order
        assert "First Block" in html
        assert "Second Block" in html
        assert "Third Block" in html

        # Verify order (basic check)
        assert html.index("First Block") < html.index("Second Block")
        assert html.index("Second Block") < html.index("Third Block")

    def test_empty_layout_renders_without_error(self):
        """Test that layouts with no slots render correctly."""
        layout = ReusableBlock.objects.create(
            name="No Slots",
            content=[
                {
                    "type": "raw_html",
                    "value": "<div><p>Static content only</p></div>",
                }
            ],
        )

        block = ReusableLayoutBlock()

        value = block.to_python(
            {
                "layout": layout.pk,
                "slot_content": [],  # No slots to fill
            }
        )

        html = block.render(value)

        assert "Static content only" in html

    def test_slot_with_reusable_block_reference(self):
        """Test filling a slot with a v0.1.0 ReusableBlockChooserBlock."""
        # Create a reusable content block
        reusable_content = ReusableBlock.objects.create(
            name="Call to Action",
            content=[
                {
                    "type": "rich_text",
                    "value": "<button>Click Here!</button>",
                }
            ],
        )

        # Create a layout
        layout = ReusableBlock.objects.create(
            name="Layout with CTA Slot",
            content=[
                {
                    "type": "raw_html",
                    "value": "<div data-slot='cta'></div>",
                }
            ],
        )

        block = ReusableLayoutBlock()

        # Create value that fills the slot with a ReusableBlockChooserBlock
        value = block.to_python(
            {
                "layout": layout.pk,
                "slot_content": [
                    {
                        "type": "slot_fill",
                        "value": {
                            "slot_id": "cta",
                            "content": [
                                {
                                    "type": "reusable_block",
                                    "value": reusable_content.pk,
                                }
                            ],
                        },
                    }
                ],
            }
        )

        html = block.render(value)

        assert "Click Here!" in html
