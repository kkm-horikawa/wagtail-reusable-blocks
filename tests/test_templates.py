"""Tests for template rendering system."""

import pytest
from django.template import TemplateDoesNotExist
from django.test import override_settings

from wagtail_reusable_blocks.models import ReusableBlock


class TestTemplateRendering:
    """Tests for ReusableBlock.render() method."""

    @pytest.fixture
    def block(self, db):
        """Create a test ReusableBlock."""
        return ReusableBlock.objects.create(
            name="Test Block",
            content=[
                ("rich_text", "<p>Hello World</p>"),
            ],
        )

    def test_render_with_default_template(self, block):
        """render() uses default template."""
        html = block.render()

        # Default template simply renders the content
        assert "<p>Hello World</p>" in html

    def test_render_with_custom_template_via_settings(self, block, tmp_path, settings):
        """render() uses custom template from settings."""
        # Create custom template
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        custom_template = template_dir / "custom_block.html"
        custom_template.write_text(
            "{% load wagtailcore_tags %}"
            '<div class="custom">{% include_block block.content %}</div>'
        )

        # Configure settings
        templates = settings.TEMPLATES.copy()
        templates[0] = templates[0].copy()
        templates[0]["DIRS"] = [str(template_dir)]

        with override_settings(
            TEMPLATES=templates,
            WAGTAIL_REUSABLE_BLOCKS={"TEMPLATE": "custom_block.html"},
        ):
            html = block.render()

        assert '<div class="custom">' in html
        assert "<p>Hello World</p>" in html

    def test_render_with_custom_template_via_parameter(self, block, tmp_path, settings):
        """render() uses custom template from parameter."""
        # Create custom template
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        custom_template = template_dir / "param_template.html"
        custom_template.write_text(
            "{% load wagtailcore_tags %}"
            '<div class="param-override">{% include_block block.content %}</div>'
        )

        # Configure settings
        templates = settings.TEMPLATES.copy()
        templates[0] = templates[0].copy()
        templates[0]["DIRS"] = [str(template_dir)]

        with override_settings(TEMPLATES=templates):
            html = block.render(template="param_template.html")

        assert '<div class="param-override">' in html
        assert "<p>Hello World</p>" in html

    def test_render_with_context_passing(self, block, tmp_path, settings):
        """render() passes context to template."""
        # Create custom template that uses context
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        custom_template = template_dir / "context_template.html"
        custom_template.write_text(
            "{% load wagtailcore_tags %}"
            '<div data-page="{{ page_title }}">'
            "{% include_block block.content %}"
            "</div>"
        )

        # Configure settings
        templates = settings.TEMPLATES.copy()
        templates[0] = templates[0].copy()
        templates[0]["DIRS"] = [str(template_dir)]

        with override_settings(TEMPLATES=templates):
            html = block.render(
                context={"page_title": "My Page"}, template="context_template.html"
            )

        assert 'data-page="My Page"' in html

    def test_render_with_empty_content(self, db):
        """render() handles empty content gracefully."""
        block = ReusableBlock.objects.create(
            name="Empty Block",
            content=[],
        )

        html = block.render()

        # Empty content renders as empty string (just whitespace from template)
        assert html.strip() == ""

    def test_render_template_does_not_exist(self, block):
        """render() raises TemplateDoesNotExist for missing template."""
        with pytest.raises(
            TemplateDoesNotExist, match="Template 'nonexistent/template.html' not found"
        ):
            block.render(template="nonexistent/template.html")

    def test_render_helpful_error_message_for_custom_template(self, block):
        """render() provides helpful error message for custom template."""
        with pytest.raises(
            TemplateDoesNotExist,
            match="Make sure it exists in one of your TEMPLATES\\['DIRS'\\]",
        ):
            block.render(template="custom/missing.html")

    def test_render_parameter_precedence(self, block, tmp_path, settings):
        """Template parameter takes precedence over settings."""
        # Create both templates
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        settings_template = template_dir / "settings_template.html"
        settings_template.write_text(
            "{% load wagtailcore_tags %}"
            '<div class="from-settings">{% include_block block.content %}</div>'
        )

        param_template = template_dir / "param_template.html"
        param_template.write_text(
            "{% load wagtailcore_tags %}"
            '<div class="from-param">{% include_block block.content %}</div>'
        )

        # Configure settings
        templates = settings.TEMPLATES.copy()
        templates[0] = templates[0].copy()
        templates[0]["DIRS"] = [str(template_dir)]

        with override_settings(
            TEMPLATES=templates,
            WAGTAIL_REUSABLE_BLOCKS={"TEMPLATE": "settings_template.html"},
        ):
            # Parameter should override settings
            html = block.render(template="param_template.html")

        assert '<div class="from-param">' in html
        assert '<div class="from-settings">' not in html


class TestTemplateContextVariables:
    """Tests for template context variables."""

    @pytest.fixture
    def block(self, db):
        """Create a test ReusableBlock."""
        return ReusableBlock.objects.create(
            name="Context Test",
            content=[("rich_text", "<p>Content</p>")],
        )

    def test_block_variable_in_context(self, block, tmp_path, settings):
        """Template receives 'block' variable."""
        # Create custom template that uses block variable
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        custom_template = template_dir / "block_var_template.html"
        custom_template.write_text(
            "{% load wagtailcore_tags %}"
            '<div data-slug="{{ block.slug }}">{% include_block block.content %}</div>'
        )

        # Configure settings
        templates = settings.TEMPLATES.copy()
        templates[0] = templates[0].copy()
        templates[0]["DIRS"] = [str(template_dir)]

        with override_settings(TEMPLATES=templates):
            html = block.render(template="block_var_template.html")

        assert 'data-slug="context-test"' in html

    def test_custom_context_merged(self, block, tmp_path, settings):
        """Custom context is merged with default context."""
        # Create custom template that uses both custom and block context
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        custom_template = template_dir / "merged_context.html"
        custom_template.write_text(
            "{% load wagtailcore_tags %}<div>{{ custom_var }}|{{ block.name }}</div>"
        )

        # Configure settings
        templates = settings.TEMPLATES.copy()
        templates[0] = templates[0].copy()
        templates[0]["DIRS"] = [str(template_dir)]

        with override_settings(TEMPLATES=templates):
            html = block.render(
                context={"custom_var": "test"}, template="merged_context.html"
            )

        assert "test|Context Test" in html
