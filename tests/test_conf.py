"""Tests for settings configuration system."""

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from wagtail_reusable_blocks.conf import DEFAULTS, get_setting


class TestGetSetting:
    """Tests for get_setting() function."""

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

    def test_get_setting_with_custom_default_parameter(self):
        """get_setting uses provided default parameter."""
        custom_default = "custom_value"
        result = get_setting("NONEXISTENT_KEY", default=custom_default)

        assert result == custom_default

    def test_get_setting_partial_configuration(self):
        """get_setting uses defaults for missing keys in partial config."""
        with override_settings(WAGTAIL_REUSABLE_BLOCKS={"TEMPLATE": "custom.html"}):
            # Custom value
            assert get_setting("TEMPLATE") == "custom.html"
            # Default value for unconfigured key
            assert (
                get_setting("REGISTER_DEFAULT_SNIPPET")
                == DEFAULTS["REGISTER_DEFAULT_SNIPPET"]
            )


class TestAppConfigValidation:
    """Tests for settings validation in AppConfig.ready()."""

    def test_invalid_template_not_string(self):
        """AppConfig raises error when TEMPLATE is not a string."""
        from wagtail_reusable_blocks.apps import WagtailReusableBlocksConfig

        config = WagtailReusableBlocksConfig.create("wagtail_reusable_blocks")

        with override_settings(WAGTAIL_REUSABLE_BLOCKS={"TEMPLATE": 123}):
            with pytest.raises(
                ImproperlyConfigured, match="TEMPLATE.*must be a string"
            ):
                config.ready()

    def test_valid_custom_configuration(self):
        """AppConfig accepts valid custom configuration."""
        from wagtail_reusable_blocks.apps import WagtailReusableBlocksConfig

        config = WagtailReusableBlocksConfig.create("wagtail_reusable_blocks")

        custom_config = {
            "TEMPLATE": "custom/template.html",
            "REGISTER_DEFAULT_SNIPPET": False,
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
                "UNKNOWN_FUTURE_SETTING": "some_value",
            }
        ):
            # Should not raise any exceptions
            config.ready()


class TestRegisterDefaultSnippet:
    """Tests for REGISTER_DEFAULT_SNIPPET setting."""

    def test_default_snippet_enabled_by_default(self):
        """Default snippet registration is enabled by default."""
        from wagtail_reusable_blocks.conf import get_setting

        assert get_setting("REGISTER_DEFAULT_SNIPPET") is True

    def test_default_snippet_can_be_disabled(self):
        """Default snippet registration can be disabled via settings."""
        from wagtail_reusable_blocks.conf import get_setting

        with override_settings(
            WAGTAIL_REUSABLE_BLOCKS={"REGISTER_DEFAULT_SNIPPET": False}
        ):
            assert get_setting("REGISTER_DEFAULT_SNIPPET") is False
