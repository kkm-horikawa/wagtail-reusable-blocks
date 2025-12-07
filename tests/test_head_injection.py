"""Tests for HeadInjectionBlock, preview functionality, and nested ReusableBlock rendering."""

import pytest

from wagtail_reusable_blocks.blocks import HeadInjectionBlock
from wagtail_reusable_blocks.models import ReusableBlock
from wagtail_reusable_blocks.models.reusable_block import _ReusableBlockChooserBlock


class TestHeadInjectionBlock:
    """Tests for HeadInjectionBlock."""

    def test_render_basic_returns_empty_string(self):
        """HeadInjectionBlock renders empty string in normal context."""
        block = HeadInjectionBlock()
        result = block.render_basic("<style>.test{}</style>")
        assert result == ""

    def test_render_basic_with_none_value(self):
        """HeadInjectionBlock handles None value."""
        block = HeadInjectionBlock()
        result = block.render_basic(None)
        assert result == ""

    def test_render_basic_with_context(self):
        """HeadInjectionBlock ignores context and returns empty string."""
        block = HeadInjectionBlock()
        result = block.render_basic("<link href='style.css'>", context={"foo": "bar"})
        assert result == ""

    def test_meta_icon(self):
        """HeadInjectionBlock has correct icon."""
        block = HeadInjectionBlock()
        assert block.meta.icon == "code"

    def test_meta_label(self):
        """HeadInjectionBlock has correct label."""
        block = HeadInjectionBlock()
        assert block.meta.label == "Preview Head Injection"


@pytest.mark.django_db
class TestReusableBlockPreview:
    """Tests for ReusableBlock preview functionality with HeadInjectionBlock."""

    def test_get_preview_template_returns_preview_template(self):
        """get_preview_template returns the preview template path."""
        block = ReusableBlock.objects.create(
            name="Test Block",
            content=[("rich_text", "<p>Test</p>")],
        )
        template = block.get_preview_template()
        assert template == "wagtail_reusable_blocks/preview.html"

    def test_get_preview_context_includes_block(self):
        """get_preview_context includes the block instance."""
        block = ReusableBlock.objects.create(
            name="Test Block",
            content=[("rich_text", "<p>Test</p>")],
        )
        context = block.get_preview_context()
        assert context["block"] == block

    def test_get_preview_context_collects_head_injection_content(self):
        """get_preview_context collects HeadInjectionBlock content."""
        block = ReusableBlock.objects.create(
            name="Test Block",
            content=[
                ("head_injection", "<style>.test{color:red}</style>"),
                ("rich_text", "<p>Test</p>"),
                ("head_injection", "<link href='bootstrap.css'>"),
            ],
        )
        context = block.get_preview_context()
        assert len(context["head_injection_content"]) == 2
        assert "<style>.test{color:red}</style>" in context["head_injection_content"]
        assert "<link href='bootstrap.css'>" in context["head_injection_content"]

    def test_get_preview_context_empty_head_injection(self):
        """get_preview_context returns empty list when no HeadInjectionBlock."""
        block = ReusableBlock.objects.create(
            name="Test Block",
            content=[("rich_text", "<p>Test</p>")],
        )
        context = block.get_preview_context()
        assert context["head_injection_content"] == []

    def test_head_injection_not_rendered_in_normal_output(self):
        """HeadInjectionBlock content is not included in normal render output."""
        block = ReusableBlock.objects.create(
            name="Test Block",
            content=[
                ("head_injection", "<style>.test{color:red}</style>"),
                ("rich_text", "<p>Visible content</p>"),
            ],
        )
        html = block.render()
        assert "<p>Visible content</p>" in html
        assert "<style>.test{color:red}</style>" not in html


@pytest.mark.django_db
class TestPreviewTemplateSettings:
    """Tests for preview template settings."""

    def test_default_preview_template_setting(self):
        """Default PREVIEW_TEMPLATE setting is correct."""
        from wagtail_reusable_blocks.conf import get_setting

        template = get_setting("PREVIEW_TEMPLATE")
        assert template == "wagtail_reusable_blocks/preview.html"

    def test_custom_preview_template_setting(self, settings):
        """Custom PREVIEW_TEMPLATE can be configured."""
        settings.WAGTAIL_REUSABLE_BLOCKS = {"PREVIEW_TEMPLATE": "custom/preview.html"}

        from wagtail_reusable_blocks.conf import get_setting

        template = get_setting("PREVIEW_TEMPLATE")
        assert template == "custom/preview.html"


@pytest.mark.django_db
class TestNestedReusableBlockRendering:
    """Tests for nested ReusableBlock rendering via _ReusableBlockChooserBlock."""

    def test_nested_block_renders_content(self):
        """Nested ReusableBlock renders its content, not just name."""
        inner_block = ReusableBlock.objects.create(
            name="Inner Block",
            content=[("rich_text", "<p>Inner content</p>")],
        )
        outer_block = ReusableBlock.objects.create(
            name="Outer Block",
            content=[("reusable_block", inner_block)],
        )
        html = outer_block.render()
        assert "<p>Inner content</p>" in html
        assert "Inner Block" not in html  # Should not render name

    def test_reusable_block_chooser_block_renders_none(self):
        """_ReusableBlockChooserBlock returns empty string for None value."""
        block = _ReusableBlockChooserBlock()
        result = block.render_basic(None)
        assert result == ""

    def test_reusable_block_chooser_block_renders_content(self):
        """_ReusableBlockChooserBlock renders the block's content."""
        reusable = ReusableBlock.objects.create(
            name="Test",
            content=[("rich_text", "<p>Test content</p>")],
        )
        block = _ReusableBlockChooserBlock()
        result = block.render_basic(reusable)
        assert "<p>Test content</p>" in result

    def test_reusable_block_chooser_block_max_depth(self):
        """_ReusableBlockChooserBlock respects max nesting depth."""
        reusable = ReusableBlock.objects.create(
            name="Test",
            content=[("rich_text", "<p>Test</p>")],
        )
        block = _ReusableBlockChooserBlock()
        # Simulate being at max depth
        context = {"_reusable_block_depth": 5}
        result = block.render_basic(reusable, context=context)
        assert "Maximum nesting depth exceeded" in result
