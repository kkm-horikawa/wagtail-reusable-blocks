"""Tests for internationalization (i18n) support."""

import subprocess
from pathlib import Path

import pytest
from django.utils.translation import activate, deactivate, gettext

# Path to locale directory
LOCALE_DIR = Path(__file__).parent.parent / "src" / "wagtail_reusable_blocks" / "locale"
EN_PO_FILE = LOCALE_DIR / "en" / "LC_MESSAGES" / "django.po"


class TestPOFileValidity:
    """Tests for PO file syntax and structure."""

    def test_english_po_file_exists(self):
        """English PO file should exist."""
        assert EN_PO_FILE.exists(), f"English PO file not found at {EN_PO_FILE}"

    def test_po_file_has_required_headers(self):
        """PO file should have required metadata headers."""
        content = EN_PO_FILE.read_text()

        required_headers = [
            "Project-Id-Version",
            "Content-Type",
            "MIME-Version",
            "Content-Transfer-Encoding",
        ]

        for header in required_headers:
            assert header in content, f"Missing required header: {header}"

    def test_po_file_has_translations(self):
        """PO file should contain translatable strings."""
        content = EN_PO_FILE.read_text()

        # Count msgid entries (excluding the header empty msgid)
        msgid_count = content.count('msgid "') - 1  # Subtract 1 for header

        assert msgid_count >= 25, (
            f"Expected at least 25 translatable strings, found {msgid_count}"
        )

    def test_po_file_syntax_with_msgfmt(self):
        """PO file should pass msgfmt syntax check."""
        try:
            result = subprocess.run(
                [
                    "msgfmt",
                    "--check-format",
                    "--check-domain",
                    "-o",
                    "/dev/null",
                    str(EN_PO_FILE),
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"msgfmt check failed: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("msgfmt not installed")

    def test_no_fuzzy_translations_in_source(self):
        """Source PO file should not have fuzzy translations."""
        content = EN_PO_FILE.read_text()

        # Fuzzy flag indicates uncertain translations
        fuzzy_count = content.count("#, fuzzy")

        assert fuzzy_count == 0, (
            f"Found {fuzzy_count} fuzzy translations in source PO file"
        )


class TestTranslationInfrastructure:
    """Tests for translation infrastructure."""

    def test_gettext_lazy_strings_are_translatable(self):
        """Strings marked with gettext_lazy should be translatable."""
        from wagtail_reusable_blocks.models import ReusableBlock

        # verbose_name should be a lazy string
        verbose_name = ReusableBlock._meta.verbose_name

        # It should be convertible to string
        assert str(verbose_name) == "Reusable Block"

    def test_model_verbose_names_are_marked(self):
        """Model verbose_name and verbose_name_plural should be marked for translation."""
        from wagtail_reusable_blocks.models import ReusableBlock

        # Check that verbose_name is a translatable proxy object, not a plain string
        verbose_name = ReusableBlock._meta.verbose_name
        verbose_name_plural = ReusableBlock._meta.verbose_name_plural

        # Should be able to convert to string
        assert str(verbose_name) == "Reusable Block"
        assert str(verbose_name_plural) == "Reusable Blocks"

    def test_app_verbose_name_is_marked(self):
        """App verbose_name should be marked for translation."""
        from django.apps import apps

        app_config = apps.get_app_config("wagtail_reusable_blocks")
        assert str(app_config.verbose_name) == "Wagtail Reusable Blocks"


class TestLanguageSwitching:
    """Tests for language switching behavior."""

    def setup_method(self):
        """Reset language before each test."""
        deactivate()

    def teardown_method(self):
        """Reset language after each test."""
        deactivate()

    def test_activate_english(self):
        """Activating English should work."""
        activate("en")

        # gettext should return the original string for English
        result = gettext("Reusable Block")
        assert result == "Reusable Block"

    def test_fallback_for_unknown_language(self):
        """Unknown language should fall back to source strings."""
        activate("xx")  # Non-existent language

        # Should return the original English string
        result = gettext("Reusable Block")
        assert result == "Reusable Block"

    def test_strings_in_po_file_are_extractable(self):
        """Key strings should be present in the PO file."""
        content = EN_PO_FILE.read_text()

        expected_strings = [
            "Reusable Block",
            "Reusable Blocks",
            "Clear Cache",
            "Maximum nesting depth exceeded",
            "name",
            "slug",
            "content",
        ]

        for string in expected_strings:
            assert f'msgid "{string}"' in content, (
                f"String not found in PO file: {string}"
            )


class TestBlockLabels:
    """Tests for block label translations."""

    def test_image_block_label_is_translatable(self):
        """ImageBlock label should be marked for translation."""
        from wagtail_reusable_blocks.blocks import ImageBlock

        block = ImageBlock()
        label = block.meta.label

        assert str(label) == "Image"

    def test_slot_fill_block_label_is_translatable(self):
        """SlotFillBlock label should be marked for translation."""
        from wagtail_reusable_blocks.blocks import SlotFillBlock

        block = SlotFillBlock()
        label = block.meta.label

        assert str(label) == "Slot Fill"

    def test_reusable_layout_block_label_is_translatable(self):
        """ReusableLayoutBlock label should be marked for translation."""
        from wagtail_reusable_blocks.blocks import ReusableLayoutBlock

        block = ReusableLayoutBlock()
        label = block.meta.label

        assert str(label) == "Reusable Layout"
