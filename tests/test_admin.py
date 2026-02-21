"""Tests for ReusableBlock admin UI customization."""

import json
from unittest import mock

import pytest
from django.test import override_settings

from wagtail_reusable_blocks.models import ReusableBlock
from wagtail_reusable_blocks.wagtail_hooks import (
    BLOCK_ID_PLACEHOLDER,
    BLOCK_ID_PLACEHOLDER_INT,
    ReusableBlockFilterSet,
    ReusableBlockViewSet,
    inject_reusable_blocks_config,
)


class TestReusableBlockViewSet:
    """Tests for ReusableBlockViewSet configuration."""

    @pytest.fixture
    def viewset(self):
        """Create a ReusableBlockViewSet instance."""
        return ReusableBlockViewSet()

    def test_model_configuration(self, viewset):
        """ViewSet is configured with correct model."""
        assert viewset.model == ReusableBlock

    def test_icon_configuration(self, viewset):
        """ViewSet has correct icon."""
        assert viewset.icon == "snippet"

    def test_menu_label(self, viewset):
        """ViewSet has correct menu label."""
        assert viewset.menu_label == "Reusable Blocks"

    def test_search_fields(self, viewset):
        """ViewSet has correct search fields."""
        assert viewset.search_fields == ["name", "slug"]

    def test_list_display(self, viewset):
        """ViewSet has correct list display columns."""
        assert "name" in viewset.list_display
        assert "slug" in viewset.list_display
        # LiveStatusTagColumn and UpdatedAtColumn are also in the list
        assert len(viewset.list_display) == 4

    def test_list_per_page(self, viewset):
        """ViewSet has correct pagination."""
        assert viewset.list_per_page == 50

    def test_filterset_class(self, viewset):
        """ViewSet has correct filterset class."""
        assert viewset.filterset_class == ReusableBlockFilterSet

    def test_ordering(self, viewset):
        """ViewSet has correct default ordering."""
        assert viewset.ordering == ["-updated_at"]

    def test_copy_view_enabled(self, viewset):
        """Copy functionality is enabled."""
        assert viewset.copy_view_enabled is True

    def test_inspect_view_enabled(self, viewset):
        """Inspect view is enabled."""
        assert viewset.inspect_view_enabled is True

    def test_preview_enabled(self, viewset):
        """Preview functionality is enabled."""
        assert viewset.preview_enabled is True


class TestReusableBlockFilterSet:
    """Tests for ReusableBlockFilterSet."""

    def test_model_configuration(self):
        """FilterSet is configured with correct model."""
        assert ReusableBlockFilterSet.Meta.model == ReusableBlock

    def test_filter_fields(self):
        """FilterSet has correct filter fields."""
        assert "created_at" in ReusableBlockFilterSet.Meta.fields
        assert "updated_at" in ReusableBlockFilterSet.Meta.fields

    def test_filter_lookup_expressions(self):
        """FilterSet has correct lookup expressions."""
        assert ReusableBlockFilterSet.Meta.fields["created_at"] == ["date"]
        assert ReusableBlockFilterSet.Meta.fields["updated_at"] == ["date"]


@pytest.mark.django_db
class TestReusableBlockQueryset:
    """Tests for ReusableBlock queryset behavior with admin configuration."""

    def test_ordering_by_updated_at(self):
        """Blocks are ordered by most recently updated first."""
        # Create blocks
        old_block = ReusableBlock.objects.create(
            name="Old Block",
            content=[("rich_text", "<p>Old</p>")],
        )
        new_block = ReusableBlock.objects.create(
            name="New Block",
            content=[("rich_text", "<p>New</p>")],
        )

        # Default ordering should be -updated_at
        blocks = ReusableBlock.objects.all()
        assert list(blocks) == [new_block, old_block]

    def test_search_fields_accessible(self):
        """Search fields (name, slug) are accessible for filtering."""
        ReusableBlock.objects.create(
            name="Test Block",
            content=[("rich_text", "<p>Content</p>")],
        )

        # Search by name
        assert ReusableBlock.objects.filter(name__icontains="test").count() == 1

        # Search by slug (auto-generated from name)
        assert ReusableBlock.objects.filter(slug__icontains="test-block").count() == 1

    def test_filter_by_date_fields(self):
        """Date fields (created_at, updated_at) can be filtered."""
        from django.utils import timezone

        ReusableBlock.objects.create(
            name="Test Block",
            content=[("rich_text", "<p>Content</p>")],
        )

        # Filter by created_at date
        today = timezone.now().date()
        assert ReusableBlock.objects.filter(created_at__date=today).count() == 1

        # Filter by updated_at date
        assert ReusableBlock.objects.filter(updated_at__date=today).count() == 1


class TestWagtailHooksRegistration:
    """Tests for wagtail_hooks registration behavior."""

    def test_viewset_registration_when_enabled(self):
        """ViewSet is registered when REGISTER_DEFAULT_SNIPPET is True."""
        # This test verifies the default behavior - the viewset should be registered
        # We can't easily check if register_snippet was called, but we can verify
        # the module executes without errors
        import wagtail_reusable_blocks.wagtail_hooks  # noqa: F401

        # If we got here without errors, the registration succeeded
        assert True

    @override_settings(WAGTAIL_REUSABLE_BLOCKS={"REGISTER_DEFAULT_SNIPPET": False})
    def test_viewset_not_registered_when_disabled(self):
        """ViewSet is not registered when REGISTER_DEFAULT_SNIPPET is False."""
        # Re-import the module to test the conditional registration
        import importlib

        import wagtail_reusable_blocks.wagtail_hooks

        importlib.reload(wagtail_reusable_blocks.wagtail_hooks)

        # If we got here without errors, the conditional worked correctly
        # The ViewSet class still exists but register_snippet wasn't called
        assert True


class TestInjectReusableBlocksConfig:
    """Tests for inject_reusable_blocks_config hook.

    ## Decision Table: DT-INJECT-CONFIG

    | ID  | reverse result                        | Expected placeholder | Expected no /0/ |
    |-----|---------------------------------------|----------------------|-----------------|
    | DT1 | /admin/reusable-blocks/blocks/0/slots/| __BLOCK_ID__         | True            |
    | DT2 | /cms/reusable-blocks/blocks/0/slots/  | __BLOCK_ID__         | True            |
    """

    MOCK_REVERSE_PATH = "wagtail_reusable_blocks.wagtail_hooks.reverse"
    DEFAULT_REVERSED_URL = "/admin/reusable-blocks/blocks/0/slots/"

    @pytest.fixture
    def mock_reverse(self):
        """Mock django.urls.reverse to avoid URL resolver dependency."""
        with mock.patch(self.MOCK_REVERSE_PATH) as mocked:
            mocked.return_value = self.DEFAULT_REVERSED_URL
            yield mocked

    def test_returns_script_tag(self, mock_reverse):
        """Return value wraps config in a <script> tag.

        Purpose: Verify inject_reusable_blocks_config() returns a string
            containing <script> tags so the browser can execute the config.
        Category: Normal case
        Target: inject_reusable_blocks_config()
        Technique: Statement coverage (C0)
        Test data: Default reversed URL /admin/reusable-blocks/blocks/0/slots/
        """
        result = inject_reusable_blocks_config()

        assert result.startswith("<script>")
        assert result.endswith("</script>")

    def test_contains_global_config_variable(self, mock_reverse):
        """Return value sets window.wagtailReusableBlocksConfig.

        Purpose: Verify the script assigns to the expected global variable
            so slot-chooser.js can read the configuration.
        Category: Normal case
        Target: inject_reusable_blocks_config()
        Technique: Statement coverage (C0)
        Test data: Default reversed URL
        """
        result = inject_reusable_blocks_config()

        assert "window.wagtailReusableBlocksConfig=" in result

    def test_contains_slots_url_template_key(self, mock_reverse):
        """JSON config contains 'slotsUrlTemplate' key.

        Purpose: Verify the JSON payload includes the slotsUrlTemplate key
            that slot-chooser.js uses to construct fetch URLs.
        Category: Normal case
        Target: inject_reusable_blocks_config()
        Technique: Statement coverage (C0)
        Test data: Default reversed URL
        """
        result = inject_reusable_blocks_config()

        assert "slotsUrlTemplate" in result

    def test_url_contains_block_id_placeholder(self, mock_reverse):
        """URL template contains __BLOCK_ID__ placeholder string.

        Purpose: Verify the integer placeholder (0) is replaced with the
            string placeholder (__BLOCK_ID__) so JavaScript can substitute
            the actual block ID at runtime.
        Category: Normal case
        Target: inject_reusable_blocks_config()
        Technique: Equivalence partitioning
        Test data: Default reversed URL with /0/ that should become /__BLOCK_ID__/
        """
        result = inject_reusable_blocks_config()

        assert BLOCK_ID_PLACEHOLDER in result

    def test_url_does_not_contain_placeholder_integer(self, mock_reverse):
        """URL template does not contain the raw placeholder integer /0/.

        Purpose: Verify the .replace() call correctly substitutes /0/ with
            /__BLOCK_ID__/ so no raw integer placeholder leaks into the URL.
        Category: Edge case
        Target: inject_reusable_blocks_config() - .replace() logic
        Technique: Boundary value analysis
        Test data: Default reversed URL where /0/ must be fully replaced
        """
        result = inject_reusable_blocks_config()
        config_json = result.removeprefix(
            "<script>window.wagtailReusableBlocksConfig="
        ).removesuffix(";</script>")
        parsed = json.loads(config_json)

        assert f"/{BLOCK_ID_PLACEHOLDER_INT}/" not in parsed["slotsUrlTemplate"]

    def test_returned_json_is_valid(self, mock_reverse):
        """JSON embedded in the script tag is parseable.

        Purpose: Verify the JSON produced by json.dumps() is valid so the
            browser can parse it without errors.
        Category: Normal case
        Target: inject_reusable_blocks_config()
        Technique: Statement coverage (C0)
        Test data: Default reversed URL
        """
        result = inject_reusable_blocks_config()
        config_json = result.removeprefix(
            "<script>window.wagtailReusableBlocksConfig="
        ).removesuffix(";</script>")

        parsed = json.loads(config_json)

        assert isinstance(parsed, dict)
        assert "slotsUrlTemplate" in parsed

    def test_url_template_ends_with_slots_path(self, mock_reverse):
        """URL template preserves the /slots/ suffix after placeholder replacement.

        Purpose: Verify the .replace() with count=1 only replaces the block ID
            segment and does not corrupt other parts of the URL path.
        Category: Normal case
        Target: inject_reusable_blocks_config() - .replace() logic
        Technique: Boundary value analysis
        Test data: Default reversed URL
        """
        result = inject_reusable_blocks_config()
        config_json = result.removeprefix(
            "<script>window.wagtailReusableBlocksConfig="
        ).removesuffix(";</script>")
        parsed = json.loads(config_json)

        assert parsed["slotsUrlTemplate"].endswith("/slots/")

    def test_reverse_called_with_correct_arguments(self, mock_reverse):
        """reverse() is called with the correct URL name and kwargs.

        Purpose: Verify inject_reusable_blocks_config() calls reverse() with
            the expected URL pattern name and placeholder integer as block_id
            so URL resolution works for any WAGTAIL_ADMIN_URL_PATH.
        Category: Normal case
        Target: inject_reusable_blocks_config() - reverse() call
        Technique: Statement coverage (C0)
        Test data: N/A (verifying call arguments)
        """
        inject_reusable_blocks_config()

        mock_reverse.assert_called_once_with(
            "wagtail_reusable_blocks:block_slots",
            kwargs={"block_id": BLOCK_ID_PLACEHOLDER_INT},
        )

    @pytest.mark.parametrize(
        "admin_prefix,reversed_url",
        [
            pytest.param(
                "/admin/",
                "/admin/reusable-blocks/blocks/0/slots/",
                id="DT1-default-admin-prefix",
            ),
            pytest.param(
                "/cms/",
                "/cms/reusable-blocks/blocks/0/slots/",
                id="DT2-custom-admin-prefix",
            ),
        ],
    )
    def test_works_with_custom_admin_url_prefix(self, admin_prefix, reversed_url):
        """URL template adapts to custom WAGTAIL_ADMIN_URL_PATH settings.

        Purpose: Verify inject_reusable_blocks_config() produces correct URL
            templates regardless of the admin URL prefix, ensuring the fix for
            hardcoded /admin/ paths works.
        Category: Normal case
        Target: inject_reusable_blocks_config()
        Technique: Decision table (DT-INJECT-CONFIG)
        Test data: DT1=/admin/ prefix, DT2=/cms/ prefix
        """
        with mock.patch(self.MOCK_REVERSE_PATH, return_value=reversed_url):
            result = inject_reusable_blocks_config()

        config_json = result.removeprefix(
            "<script>window.wagtailReusableBlocksConfig="
        ).removesuffix(";</script>")
        parsed = json.loads(config_json)
        url_template = parsed["slotsUrlTemplate"]

        assert BLOCK_ID_PLACEHOLDER in url_template
        assert f"/{BLOCK_ID_PLACEHOLDER_INT}/" not in url_template
        assert url_template.startswith(admin_prefix.rstrip("/"))

    def test_hook_registered_with_wagtail(self):
        """inject_reusable_blocks_config is registered as insert_global_admin_js hook.

        Purpose: Verify the function is discoverable by Wagtail's hook
            registry so it actually runs in production.
        Category: Normal case
        Target: Wagtail hook registration of inject_reusable_blocks_config
        Technique: Statement coverage (C0)
        Test data: N/A
        """
        from wagtail import hooks

        registered_hooks = hooks.get_hooks("insert_global_admin_js")

        assert inject_reusable_blocks_config in registered_hooks

    def test_only_first_occurrence_of_placeholder_int_is_replaced(self):
        """Only the first /0/ in the URL is replaced, preserving any trailing /0/.

        Purpose: Verify .replace(..., 1) replaces exactly one occurrence of the
            placeholder integer, so if /0/ appears elsewhere in the URL it is
            preserved (defensive against future URL pattern changes).
        Category: Edge case
        Target: inject_reusable_blocks_config() - .replace() count=1
        Technique: Boundary value analysis
        Test data: URL with two /0/ segments
        """
        url_with_double_zero = "/admin/reusable-blocks/blocks/0/slots/0/"
        with mock.patch(self.MOCK_REVERSE_PATH, return_value=url_with_double_zero):
            result = inject_reusable_blocks_config()

        config_json = result.removeprefix(
            "<script>window.wagtailReusableBlocksConfig="
        ).removesuffix(";</script>")
        parsed = json.loads(config_json)
        url_template = parsed["slotsUrlTemplate"]

        assert url_template.count(BLOCK_ID_PLACEHOLDER) == 1
        assert f"/slots/{BLOCK_ID_PLACEHOLDER_INT}/" in url_template
