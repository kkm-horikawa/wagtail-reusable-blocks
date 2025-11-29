"""Tests for settings configuration system."""

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from wagtail.blocks import CharBlock, RawHTMLBlock, RichTextBlock

from wagtail_reusable_blocks.conf import DEFAULTS, get_setting


class TestGetSetting:
    """Tests for get_setting() function."""

    def test_get_setting_with_defaults(self):
        """get_setting returns default value when setting not configured."""
        block_types = get_setting("BLOCK_TYPES")

        assert block_types == DEFAULTS["BLOCK_TYPES"]
        assert len(block_types) == 2
        assert block_types[0][0] == "rich_text"
        assert isinstance(block_types[0][1], RichTextBlock)

    def test_get_setting_with_custom_value(self):
        """get_setting returns custom value when configured."""
        custom_blocks = [("char", CharBlock())]

        with override_settings(WAGTAIL_REUSABLE_BLOCKS={"BLOCK_TYPES": custom_blocks}):
            block_types = get_setting("BLOCK_TYPES")
            assert block_types == custom_blocks

    def test_get_setting_with_custom_default_parameter(self):
        """get_setting uses provided default parameter."""
        custom_default = [("custom", CharBlock())]
        result = get_setting("NONEXISTENT_KEY", default=custom_default)

        assert result == custom_default

    def test_get_setting_template_default(self):
        """get_setting returns default template path."""
        template = get_setting("TEMPLATE")

        assert template == "wagtail_reusable_blocks/reusable_block.html"

    def test_get_setting_custom_template(self):
        """get_setting returns custom template path."""
        custom_template = "custom/template.html"

        with override_settings(WAGTAIL_REUSABLE_BLOCKS={"TEMPLATE": custom_template}):
            template = get_setting("TEMPLATE")
            assert template == custom_template

    def test_get_setting_unknown_key_returns_none(self):
        """get_setting returns None for unknown keys without default."""
        result = get_setting("UNKNOWN_KEY")
        assert result is None

    def test_get_setting_partial_configuration(self):
        """get_setting uses defaults for missing keys in partial config."""
        with override_settings(WAGTAIL_REUSABLE_BLOCKS={"TEMPLATE": "custom.html"}):
            # Custom value
            assert get_setting("TEMPLATE") == "custom.html"
            # Default value for unconfigured key
            assert get_setting("BLOCK_TYPES") == DEFAULTS["BLOCK_TYPES"]


class TestAppConfigValidation:
    """Tests for settings validation in AppConfig.ready()."""

    def test_invalid_block_types_not_list(self):
        """AppConfig raises error when BLOCK_TYPES is not a list."""
        from wagtail_reusable_blocks.apps import WagtailReusableBlocksConfig

        config = WagtailReusableBlocksConfig.create("wagtail_reusable_blocks")

        with override_settings(WAGTAIL_REUSABLE_BLOCKS={"BLOCK_TYPES": "invalid"}):
            with pytest.raises(ImproperlyConfigured, match="must be a list"):
                config.ready()

    def test_invalid_block_types_not_tuples(self):
        """AppConfig raises error when BLOCK_TYPES contains non-tuples."""
        from wagtail_reusable_blocks.apps import WagtailReusableBlocksConfig

        config = WagtailReusableBlocksConfig.create("wagtail_reusable_blocks")

        with override_settings(
            WAGTAIL_REUSABLE_BLOCKS={"BLOCK_TYPES": ["not_a_tuple"]}
        ):
            with pytest.raises(ImproperlyConfigured, match="must be a tuple"):
                config.ready()

    def test_invalid_block_types_wrong_tuple_length(self):
        """AppConfig raises error when BLOCK_TYPES tuple has wrong length."""
        from wagtail_reusable_blocks.apps import WagtailReusableBlocksConfig

        config = WagtailReusableBlocksConfig.create("wagtail_reusable_blocks")

        with override_settings(
            WAGTAIL_REUSABLE_BLOCKS={"BLOCK_TYPES": [("single_item",)]}
        ):
            with pytest.raises(ImproperlyConfigured, match="must be a tuple"):
                config.ready()

    def test_invalid_block_types_name_not_string(self):
        """AppConfig raises error when block name is not a string."""
        from wagtail_reusable_blocks.apps import WagtailReusableBlocksConfig

        config = WagtailReusableBlocksConfig.create("wagtail_reusable_blocks")

        with override_settings(
            WAGTAIL_REUSABLE_BLOCKS={"BLOCK_TYPES": [(123, CharBlock())]}
        ):
            with pytest.raises(ImproperlyConfigured, match="name must be a string"):
                config.ready()

    def test_invalid_block_types_not_block_instance(self):
        """AppConfig raises error when block is not a valid Wagtail block."""
        from wagtail_reusable_blocks.apps import WagtailReusableBlocksConfig

        config = WagtailReusableBlocksConfig.create("wagtail_reusable_blocks")

        with override_settings(
            WAGTAIL_REUSABLE_BLOCKS={"BLOCK_TYPES": [("invalid", "not_a_block")]}
        ):
            with pytest.raises(
                ImproperlyConfigured,
                match="does not appear to be a valid Wagtail block",
            ):
                config.ready()

    def test_invalid_template_not_string(self):
        """AppConfig raises error when TEMPLATE is not a string."""
        from wagtail_reusable_blocks.apps import WagtailReusableBlocksConfig

        config = WagtailReusableBlocksConfig.create("wagtail_reusable_blocks")

        with override_settings(WAGTAIL_REUSABLE_BLOCKS={"TEMPLATE": 123}):
            with pytest.raises(
                ImproperlyConfigured, match="TEMPLATE.*must be a string"
            ):
                config.ready()

    def test_empty_block_types_logs_warning(self, caplog):
        """AppConfig logs warning when BLOCK_TYPES is empty."""
        from wagtail_reusable_blocks.apps import WagtailReusableBlocksConfig

        config = WagtailReusableBlocksConfig.create("wagtail_reusable_blocks")

        with override_settings(WAGTAIL_REUSABLE_BLOCKS={"BLOCK_TYPES": []}):
            config.ready()

            assert "BLOCK_TYPES" in caplog.text
            assert "empty" in caplog.text.lower()

    def test_valid_custom_configuration(self):
        """AppConfig accepts valid custom configuration."""
        from wagtail_reusable_blocks.apps import WagtailReusableBlocksConfig

        config = WagtailReusableBlocksConfig.create("wagtail_reusable_blocks")

        custom_config = {
            "BLOCK_TYPES": [
                ("rich_text", RichTextBlock()),
                ("raw_html", RawHTMLBlock()),
                ("char", CharBlock()),
            ],
            "TEMPLATE": "custom/template.html",
        }

        with override_settings(WAGTAIL_REUSABLE_BLOCKS=custom_config):
            # Should not raise any exceptions
            config.ready()

    def test_unknown_settings_ignored(self):
        """AppConfig ignores unknown settings (forward compatibility)."""
        from wagtail_reusable_blocks.apps import WagtailReusableBlocksConfig

        config = WagtailReusableBlocksConfig.create("wagtail_reusable_blocks")

        with override_settings(
            WAGTAIL_REUSABLE_BLOCKS={
                "BLOCK_TYPES": [("rich_text", RichTextBlock())],
                "UNKNOWN_FUTURE_SETTING": "some_value",
            }
        ):
            # Should not raise any exceptions
            config.ready()
