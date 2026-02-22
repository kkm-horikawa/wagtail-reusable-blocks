"""API module unit tests for wagtail-reusable-blocks.

## DT-LIVE-FILTER: live query parameter parsing

| ID  | live param | expected filter value |
|-----|-----------|----------------------|
| DT1 | "true"    | True                 |
| DT2 | "1"       | True                 |
| DT3 | "yes"     | True                 |
| DT4 | "false"   | False                |
| DT5 | "0"       | False                |
| DT6 | "no"      | False                |
| DT7 | "TRUE"    | True                 |
| DT8 | "True"    | True                 |

## DT-RESOLVE-CLASSES: _resolve_classes class resolution

| ID  | setting value           | expected return        |
|-----|------------------------|------------------------|
| DT1 | None                   | None                   |
| DT2 | ["dotted.path.Class"]  | [<resolved Class>]     |
| DT3 | [ClassObject]          | [ClassObject]          |
| DT4 | ["path.A", ClassB]     | [<A>, ClassB]          |
| DT5 | []                     | []                     |
"""

from unittest import mock

import pytest
from django.utils.text import slugify
from rest_framework import permissions, serializers, status

from wagtail_reusable_blocks.api.serializers import (
    ReusableBlockSerializer,
    StreamFieldField,
)
from wagtail_reusable_blocks.api.views import (
    ReusableBlockAPIViewSet,
    ReusableBlockModelViewSet,
    _resolve_classes,
)
from wagtail_reusable_blocks.conf import DEFAULTS, get_setting


# ---------------------------------------------------------------------------
# conf.py - get_setting
# ---------------------------------------------------------------------------
class TestGetSetting:
    """get_setting configuration resolution tests."""

    def test_api_permission_classes_default(self):
        """Verify that the default value of API_PERMISSION_CLASSES is IsAuthenticated.

        Purpose: Verify that get_setting("API_PERMISSION_CLASSES") returns
                 the IsAuthenticated path as default, ensuring the default
                 API authorization configuration.
        Type: Normal
        Target: get_setting("API_PERMISSION_CLASSES")
        Technique: Equivalence partitioning
        Test data: No user settings (DEFAULTS only)
        """
        result = get_setting("API_PERMISSION_CLASSES")

        assert result == ["rest_framework.permissions.IsAuthenticated"]

    def test_api_authentication_classes_default_is_none(self):
        """Verify that the default value of API_AUTHENTICATION_CLASSES is None.

        Purpose: Verify that get_setting("API_AUTHENTICATION_CLASSES") returns
                 None, ensuring DRF default authentication is used.
        Type: Normal
        Target: get_setting("API_AUTHENTICATION_CLASSES")
        Technique: Equivalence partitioning
        Test data: No user settings (DEFAULTS only)
        """
        result = get_setting("API_AUTHENTICATION_CLASSES")

        assert result is None

    @mock.patch(
        "wagtail_reusable_blocks.conf.settings",
    )
    def test_user_setting_overrides_default(self, mock_settings):
        """Verify that user settings override default values.

        Purpose: Verify that providing WAGTAIL_REUSABLE_BLOCKS with custom
                 settings overrides the defaults, ensuring customization support.
        Type: Normal
        Target: get_setting(key)
        Technique: Equivalence partitioning
        Test data: Override to AllowAny permission
        """
        custom_classes = ["rest_framework.permissions.AllowAny"]
        mock_settings.WAGTAIL_REUSABLE_BLOCKS = {
            "API_PERMISSION_CLASSES": custom_classes,
        }

        result = get_setting("API_PERMISSION_CLASSES")

        assert result == custom_classes

    @mock.patch(
        "wagtail_reusable_blocks.conf.settings",
    )
    def test_user_setting_overrides_none_to_list(self, mock_settings):
        """Verify that a None default can be overridden with a list.

        Purpose: Verify that API_AUTHENTICATION_CLASSES default None can be
                 overridden with a custom list, ensuring authentication
                 customization support.
        Type: Normal
        Target: get_setting("API_AUTHENTICATION_CLASSES")
        Technique: Equivalence partitioning
        Test data: Override to TokenAuthentication
        """
        custom_auth = ["rest_framework.authentication.TokenAuthentication"]
        mock_settings.WAGTAIL_REUSABLE_BLOCKS = {
            "API_AUTHENTICATION_CLASSES": custom_auth,
        }

        result = get_setting("API_AUTHENTICATION_CLASSES")

        assert result == custom_auth

    def test_defaults_dict_contains_all_api_keys(self):
        """Verify that the DEFAULTS dict contains all API-related keys.

        Purpose: Verify that DEFAULTS contains API_PERMISSION_CLASSES and
                 API_AUTHENTICATION_CLASSES, ensuring API settings coverage.
        Type: Normal
        Target: conf.DEFAULTS
        Technique: Equivalence partitioning
        Test data: DEFAULTS dict keys
        """
        expected_keys = {
            "API_PERMISSION_CLASSES",
            "API_AUTHENTICATION_CLASSES",
        }

        assert expected_keys.issubset(set(DEFAULTS.keys()))


# ---------------------------------------------------------------------------
# _resolve_classes
# ---------------------------------------------------------------------------
class TestResolveClasses:
    """_resolve_classes class resolution tests."""

    @mock.patch("wagtail_reusable_blocks.api.views.get_setting", return_value=None)
    def test_returns_none_when_setting_is_none(self, mock_get_setting):
        """Verify that None is returned when the setting value is None.

        Purpose: Verify that _resolve_classes returns None for a None setting,
                 ensuring fallback to DRF defaults.
        Type: Edge case
        Target: _resolve_classes(setting_key)
        Technique: Equivalence partitioning (DT-RESOLVE-CLASSES DT1)
        Test data: None setting
        """
        result = _resolve_classes("API_AUTHENTICATION_CLASSES")

        assert result is None
        mock_get_setting.assert_called_once_with("API_AUTHENTICATION_CLASSES")

    @mock.patch("wagtail_reusable_blocks.api.views.get_setting")
    @mock.patch("wagtail_reusable_blocks.api.views.import_string")
    def test_resolves_string_path_to_class(self, mock_import, mock_get_setting):
        """Verify that a string path is resolved to a class.

        Purpose: Verify that _resolve_classes resolves dotted path strings
                 to classes via import_string, ensuring class resolution
                 from string paths.
        Type: Normal
        Target: _resolve_classes(setting_key)
        Technique: Equivalence partitioning (DT-RESOLVE-CLASSES DT2)
        Test data: IsAuthenticated string path
        """
        mock_get_setting.return_value = ["rest_framework.permissions.IsAuthenticated"]
        sentinel_class = type("SentinelPermission", (), {})
        mock_import.return_value = sentinel_class

        result = _resolve_classes("API_PERMISSION_CLASSES")

        assert result == [sentinel_class]
        mock_import.assert_called_once_with(
            "rest_framework.permissions.IsAuthenticated"
        )

    @mock.patch("wagtail_reusable_blocks.api.views.get_setting")
    def test_passes_through_class_objects(self, mock_get_setting):
        """Verify that direct class objects are passed through as-is.

        Purpose: Verify that _resolve_classes returns class objects directly
                 without transformation, ensuring direct class specification
                 support.
        Type: Normal
        Target: _resolve_classes(setting_key)
        Technique: Equivalence partitioning (DT-RESOLVE-CLASSES DT3)
        Test data: IsAuthenticated class object
        """
        mock_get_setting.return_value = [permissions.IsAuthenticated]

        result = _resolve_classes("API_PERMISSION_CLASSES")

        assert result == [permissions.IsAuthenticated]

    @mock.patch("wagtail_reusable_blocks.api.views.get_setting")
    @mock.patch("wagtail_reusable_blocks.api.views.import_string")
    def test_resolves_mixed_strings_and_classes(self, mock_import, mock_get_setting):
        """Verify that a mixed list of strings and class objects is resolved.

        Purpose: Verify that _resolve_classes correctly resolves a mixed list
                 of string paths and class objects, ensuring compatibility
                 with mixed specification.
        Type: Normal
        Target: _resolve_classes(setting_key)
        Technique: Equivalence partitioning (DT-RESOLVE-CLASSES DT4)
        Test data: 1 string path + 1 class object
        """
        resolved_class = type("ResolvedPerm", (), {})
        mock_import.return_value = resolved_class
        mock_get_setting.return_value = [
            "some.module.PermA",
            permissions.AllowAny,
        ]

        result = _resolve_classes("API_PERMISSION_CLASSES")

        assert result is not None
        assert len(result) == 2
        assert result[0] is resolved_class
        assert result[1] is permissions.AllowAny

    @mock.patch("wagtail_reusable_blocks.api.views.get_setting", return_value=[])
    def test_returns_empty_list_for_empty_setting(self, mock_get_setting):
        """Verify that an empty list is returned for an empty setting.

        Purpose: Verify that _resolve_classes returns an empty list for an
                 empty setting, ensuring permission disabling support.
        Type: Edge case
        Target: _resolve_classes(setting_key)
        Technique: Boundary analysis (DT-RESOLVE-CLASSES DT5)
        Test data: Empty list
        """
        result = _resolve_classes("API_PERMISSION_CLASSES")

        assert result == []

    @mock.patch("wagtail_reusable_blocks.api.views.get_setting")
    @mock.patch("wagtail_reusable_blocks.api.views.import_string")
    def test_raises_import_error_for_invalid_path(self, mock_import, mock_get_setting):
        """Verify that ImportError is raised for an invalid string path.

        Purpose: Verify that _resolve_classes raises ImportError for a
                 non-existent module path, ensuring invalid configuration
                 detection.
        Type: Error
        Target: _resolve_classes(setting_key)
        Technique: Error guessing
        Test data: Non-existent module path
        """
        mock_get_setting.return_value = ["nonexistent.module.Class"]
        mock_import.side_effect = ImportError("No module named 'nonexistent'")

        with pytest.raises(ImportError, match="No module named"):
            _resolve_classes("API_PERMISSION_CLASSES")


# ---------------------------------------------------------------------------
# ReusableBlockSerializer - field definitions
# ---------------------------------------------------------------------------
class TestReusableBlockSerializerFields:
    """ReusableBlockSerializer field definition tests."""

    def test_meta_fields_contain_expected_fields(self):
        """Verify that Meta.fields contains all expected fields.

        Purpose: Verify that ReusableBlockSerializer.Meta.fields includes
                 all API-specified fields, ensuring response field coverage.
        Type: Normal
        Target: ReusableBlockSerializer.Meta.fields
        Technique: Equivalence partitioning
        Test data: Meta.fields attribute
        """
        expected = ["id", "name", "slug", "content", "live", "created_at", "updated_at"]

        assert ReusableBlockSerializer.Meta.fields == expected

    def test_read_only_fields_are_correct(self):
        """Verify that read_only_fields contains id, created_at, updated_at, and live.

        Purpose: Verify that ReusableBlockSerializer.Meta.read_only_fields
                 includes auto-generated fields, preventing API write-through.
        Type: Normal
        Target: ReusableBlockSerializer.Meta.read_only_fields
        Technique: Equivalence partitioning
        Test data: Meta.read_only_fields attribute
        """
        expected = ["id", "created_at", "updated_at", "live"]

        assert ReusableBlockSerializer.Meta.read_only_fields == expected

    def test_content_field_is_stream_field_field(self):
        """Verify that the content field is defined as StreamFieldField.

        Purpose: Verify that the content field uses StreamFieldField for
                 StreamValue-to-JSON conversion, ensuring StreamField data
                 read/write support.
        Type: Normal
        Target: ReusableBlockSerializer.content
        Technique: Equivalence partitioning
        Test data: content field class
        """
        serializer = ReusableBlockSerializer()

        assert isinstance(serializer.fields["content"], StreamFieldField)

    def test_content_field_not_required(self):
        """Verify that the content field is not required.

        Purpose: Verify that the content field is defined with required=False,
                 ensuring block creation with empty content is supported.
        Type: Normal
        Target: ReusableBlockSerializer.content
        Technique: Equivalence partitioning
        Test data: content field required attribute
        """
        serializer = ReusableBlockSerializer()

        assert serializer.fields["content"].required is False


# ---------------------------------------------------------------------------
# ReusableBlockSerializer - validate_slug
# ---------------------------------------------------------------------------
class TestReusableBlockSerializerValidateSlug:
    """ReusableBlockSerializer.validate_slug slug uniqueness tests."""

    @mock.patch("wagtail_reusable_blocks.api.serializers.ReusableBlock.objects")
    def test_unique_slug_passes_validation(self, mock_objects):
        """Verify that a unique slug passes validation.

        Purpose: Verify that validate_slug accepts a non-duplicate slug,
                 ensuring unique slug acceptance.
        Type: Normal
        Target: ReusableBlockSerializer.validate_slug(value)
        Technique: Equivalence partitioning
        Test data: slug "new-block" not in database
        """
        mock_qs = mock.MagicMock()
        mock_qs.exists.return_value = False
        mock_objects.filter.return_value = mock_qs
        serializer = ReusableBlockSerializer()

        result = serializer.validate_slug("new-block")

        assert result == "new-block"
        mock_objects.filter.assert_called_once_with(slug="new-block")

    @mock.patch("wagtail_reusable_blocks.api.serializers.ReusableBlock.objects")
    def test_duplicate_slug_raises_error_on_create(self, mock_objects):
        """Verify that a duplicate slug raises ValidationError on create.

        Purpose: Verify that validate_slug raises ValidationError for a
                 duplicate slug, ensuring slug uniqueness constraint.
        Type: Error
        Target: ReusableBlockSerializer.validate_slug(value)
        Technique: Equivalence partitioning
        Test data: slug "existing-block" already in database
        """
        mock_qs = mock.MagicMock()
        mock_qs.exists.return_value = True
        mock_objects.filter.return_value = mock_qs
        serializer = ReusableBlockSerializer()

        with pytest.raises(serializers.ValidationError, match="already exists"):
            serializer.validate_slug("existing-block")

    @mock.patch("wagtail_reusable_blocks.api.serializers.ReusableBlock.objects")
    def test_update_excludes_own_pk_from_uniqueness_check(self, mock_objects):
        """Verify that the own PK is excluded from uniqueness check on update.

        Purpose: Verify that validate_slug excludes the current instance's PK
                 from the uniqueness check, ensuring self-exclusion on update.
        Type: Normal
        Target: ReusableBlockSerializer.validate_slug(value)
        Technique: Equivalence partitioning
        Test data: Instance with pk=42 retaining its own slug
        """
        mock_instance = mock.Mock(pk=42)
        mock_qs = mock.MagicMock()
        mock_qs.exclude.return_value = mock_qs
        mock_qs.exists.return_value = False
        mock_objects.filter.return_value = mock_qs
        serializer = ReusableBlockSerializer()
        serializer.instance = mock_instance

        result = serializer.validate_slug("my-block")

        assert result == "my-block"
        mock_qs.exclude.assert_called_once_with(pk=42)

    @mock.patch("wagtail_reusable_blocks.api.serializers.ReusableBlock.objects")
    def test_update_detects_duplicate_slug_from_other_instance(self, mock_objects):
        """Verify that slug duplication with another instance is detected on update.

        Purpose: Verify that validate_slug detects slug duplication with
                 another instance during update, raising ValidationError.
        Type: Error
        Target: ReusableBlockSerializer.validate_slug(value)
        Technique: Equivalence partitioning
        Test data: Instance with pk=42 attempting to use another instance's slug
        """
        mock_instance = mock.Mock(pk=42)
        mock_qs = mock.MagicMock()
        mock_qs.exclude.return_value = mock_qs
        mock_qs.exists.return_value = True
        mock_objects.filter.return_value = mock_qs
        serializer = ReusableBlockSerializer()
        serializer.instance = mock_instance

        with pytest.raises(serializers.ValidationError, match="already exists"):
            serializer.validate_slug("taken-slug")


# ---------------------------------------------------------------------------
# ReusableBlockSerializer - validate (auto-slug generation)
# ---------------------------------------------------------------------------
class TestReusableBlockSerializerValidate:
    """ReusableBlockSerializer.validate auto-slug generation tests."""

    @mock.patch("wagtail_reusable_blocks.api.serializers.ReusableBlock.objects")
    def test_auto_generates_slug_from_name_when_slug_is_empty(self, mock_objects):
        """Verify that slug is auto-generated from name when slug is empty.

        Purpose: Verify that validate generates a slugified value from name
                 when slug is empty, ensuring auto-slug generation.
        Type: Normal
        Target: ReusableBlockSerializer.validate(attrs)
        Technique: Equivalence partitioning
        Test data: Empty slug, name="My New Block"
        """
        mock_qs = mock.MagicMock()
        mock_qs.exists.return_value = False
        mock_objects.filter.return_value = mock_qs
        serializer = ReusableBlockSerializer()
        attrs = {"name": "My New Block", "slug": ""}

        result = serializer.validate(attrs)

        assert result["slug"] == slugify("My New Block")
        assert result["slug"] == "my-new-block"

    @mock.patch("wagtail_reusable_blocks.api.serializers.ReusableBlock.objects")
    def test_auto_generates_slug_when_slug_not_provided(self, mock_objects):
        """Verify that slug is auto-generated when slug key is not present.

        Purpose: Verify that validate generates a slugified value when the
                 slug key is absent, ensuring auto-generation when slug
                 is omitted.
        Type: Normal
        Target: ReusableBlockSerializer.validate(attrs)
        Technique: Equivalence partitioning
        Test data: No slug key, name="Test Block"
        """
        mock_qs = mock.MagicMock()
        mock_qs.exists.return_value = False
        mock_objects.filter.return_value = mock_qs
        serializer = ReusableBlockSerializer()
        attrs = {"name": "Test Block"}

        result = serializer.validate(attrs)

        assert result["slug"] == "test-block"

    @mock.patch("wagtail_reusable_blocks.api.serializers.ReusableBlock.objects")
    def test_explicit_slug_is_preserved(self, mock_objects):
        """Verify that an explicitly specified slug is preserved.

        Purpose: Verify that validate preserves the explicitly specified slug,
                 ensuring explicit slug takes priority.
        Type: Normal
        Target: ReusableBlockSerializer.validate(attrs)
        Technique: Equivalence partitioning
        Test data: slug="custom-slug" explicitly specified
        """
        mock_qs = mock.MagicMock()
        mock_qs.exists.return_value = False
        mock_objects.filter.return_value = mock_qs
        serializer = ReusableBlockSerializer()
        attrs = {"name": "My Block", "slug": "custom-slug"}

        result = serializer.validate(attrs)

        assert result["slug"] == "custom-slug"

    @mock.patch("wagtail_reusable_blocks.api.serializers.ReusableBlock.objects")
    def test_auto_generated_slug_uniqueness_check(self, mock_objects):
        """Verify that ValidationError is raised when auto-generated slug already exists.

        Purpose: Verify that validate raises ValidationError when the auto-generated
                 slug duplicates an existing one, ensuring auto-generated slug
                 uniqueness check.
        Type: Error
        Target: ReusableBlockSerializer.validate(attrs)
        Technique: Error guessing
        Test data: Auto-generated slug "my-block" already exists in database
        """
        mock_qs = mock.MagicMock()
        mock_qs.exists.return_value = True
        mock_objects.filter.return_value = mock_qs
        serializer = ReusableBlockSerializer()
        attrs = {"name": "My Block"}

        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate(attrs)

        assert "slug" in exc_info.value.detail

    @mock.patch("wagtail_reusable_blocks.api.serializers.ReusableBlock.objects")
    def test_auto_generated_slug_excludes_self_on_update(self, mock_objects):
        """Verify that the own PK is excluded from auto-generated slug uniqueness check on update.

        Purpose: Verify that validate excludes the current instance's PK
                 from the auto-generated slug uniqueness check during update.
        Type: Normal
        Target: ReusableBlockSerializer.validate(attrs)
        Technique: Equivalence partitioning
        Test data: Instance with pk=10, auto-generated slug on update
        """
        mock_instance = mock.Mock(pk=10)
        mock_qs = mock.MagicMock()
        mock_qs.exclude.return_value = mock_qs
        mock_qs.exists.return_value = False
        mock_objects.filter.return_value = mock_qs
        serializer = ReusableBlockSerializer()
        serializer.instance = mock_instance
        attrs = {"name": "Updated Block", "slug": ""}

        result = serializer.validate(attrs)

        assert result["slug"] == "updated-block"
        mock_qs.exclude.assert_called_once_with(pk=10)

    @mock.patch("wagtail_reusable_blocks.api.serializers.ReusableBlock.objects")
    def test_no_slug_no_name_does_not_generate_slug(self, mock_objects):
        """Verify that slug is not generated when neither name nor slug is provided.

        Purpose: Verify that validate does not generate a slug when both name
                 and slug are absent, ensuring no slug is added without a name.
        Type: Edge case
        Target: ReusableBlockSerializer.validate(attrs)
        Technique: Boundary analysis
        Test data: Neither name nor slug provided
        """
        serializer = ReusableBlockSerializer()
        attrs = {"content": []}

        result = serializer.validate(attrs)

        assert "slug" not in result or not result.get("slug")


# ---------------------------------------------------------------------------
# ReusableBlockSerializer - create / update
# ---------------------------------------------------------------------------
class TestReusableBlockSerializerCreate:
    """ReusableBlockSerializer.create revision creation tests."""

    @mock.patch("wagtail_reusable_blocks.api.serializers.ReusableBlock")
    def test_create_saves_instance_and_revision(self, MockReusableBlock):
        """Verify that create saves the instance and creates a revision.

        Purpose: Verify that create calls full_clean, save, and save_revision
                 in sequence, ensuring revision management on creation.
        Type: Normal
        Target: ReusableBlockSerializer.create(validated_data)
        Technique: Equivalence partitioning
        Test data: name="New Block", slug="new-block"
        """
        mock_instance = mock.MagicMock()
        MockReusableBlock.return_value = mock_instance
        serializer = ReusableBlockSerializer()
        validated_data = {"name": "New Block", "slug": "new-block", "content": []}

        result = serializer.create(validated_data)

        assert result is mock_instance
        MockReusableBlock.assert_called_once_with(**validated_data)
        mock_instance.full_clean.assert_called_once()
        mock_instance.save.assert_called_once()
        mock_instance.save_revision.assert_called_once()

    @mock.patch("wagtail_reusable_blocks.api.serializers.ReusableBlock")
    def test_create_calls_methods_in_order(self, MockReusableBlock):
        """Verify that create calls full_clean -> save -> save_revision in order.

        Purpose: Verify that the method call order is full_clean -> save ->
                 save_revision, ensuring validation before save and revision.
        Type: Normal
        Target: ReusableBlockSerializer.create(validated_data)
        Technique: Equivalence partitioning
        Test data: name="Order Test"
        """
        mock_instance = mock.MagicMock()
        call_order = []
        mock_instance.full_clean.side_effect = lambda: call_order.append("full_clean")
        mock_instance.save.side_effect = lambda: call_order.append("save")
        mock_instance.save_revision.side_effect = lambda: call_order.append(
            "save_revision"
        )
        MockReusableBlock.return_value = mock_instance
        serializer = ReusableBlockSerializer()

        serializer.create({"name": "Order Test", "slug": "order-test"})

        assert call_order == ["full_clean", "save", "save_revision"]


class TestReusableBlockSerializerUpdate:
    """ReusableBlockSerializer.update revision creation tests."""

    def test_update_sets_attributes_and_saves_revision(self):
        """Verify that update sets attributes, saves, and creates a revision.

        Purpose: Verify that update sets attributes on the instance and then
                 calls full_clean, save, and save_revision, ensuring revision
                 management on update.
        Type: Normal
        Target: ReusableBlockSerializer.update(instance, validated_data)
        Technique: Equivalence partitioning
        Test data: name="Updated Name" update
        """
        mock_instance = mock.MagicMock()
        serializer = ReusableBlockSerializer()
        validated_data = {"name": "Updated Name"}

        result = serializer.update(mock_instance, validated_data)

        assert result is mock_instance
        assert mock_instance.name == "Updated Name"
        mock_instance.full_clean.assert_called_once()
        mock_instance.save.assert_called_once()
        mock_instance.save_revision.assert_called_once()

    def test_update_sets_multiple_attributes(self):
        """Verify that multiple attributes are set correctly on update.

        Purpose: Verify that update sets all provided fields correctly,
                 ensuring multi-field simultaneous update support.
        Type: Normal
        Target: ReusableBlockSerializer.update(instance, validated_data)
        Technique: Equivalence partitioning
        Test data: Simultaneous update of name, slug, and content
        """
        mock_instance = mock.MagicMock()
        serializer = ReusableBlockSerializer()
        content_data = [{"type": "rich_text", "value": "<p>Hello</p>"}]
        validated_data = {
            "name": "Updated",
            "slug": "updated",
            "content": content_data,
        }

        serializer.update(mock_instance, validated_data)

        assert mock_instance.name == "Updated"
        assert mock_instance.slug == "updated"
        assert mock_instance.content == content_data

    def test_update_calls_methods_in_order(self):
        """Verify that update calls full_clean -> save -> save_revision in order.

        Purpose: Verify that the method call order is full_clean -> save ->
                 save_revision, ensuring validation before save and revision.
        Type: Normal
        Target: ReusableBlockSerializer.update(instance, validated_data)
        Technique: Equivalence partitioning
        Test data: name="Order Test"
        """
        mock_instance = mock.MagicMock()
        call_order = []
        mock_instance.full_clean.side_effect = lambda: call_order.append("full_clean")
        mock_instance.save.side_effect = lambda: call_order.append("save")
        mock_instance.save_revision.side_effect = lambda: call_order.append(
            "save_revision"
        )
        serializer = ReusableBlockSerializer()

        serializer.update(mock_instance, {"name": "Order Test"})

        assert call_order == ["full_clean", "save", "save_revision"]


# ---------------------------------------------------------------------------
# ReusableBlockAPIViewSet
# ---------------------------------------------------------------------------
class TestReusableBlockAPIViewSet:
    """ReusableBlockAPIViewSet queryset tests."""

    @mock.patch("wagtail_reusable_blocks.api.views.ReusableBlock.objects")
    def test_get_queryset_filters_live_true(self, mock_objects):
        """Verify that get_queryset filters by live=True.

        Purpose: Verify that get_queryset always returns results filtered
                 by live=True, ensuring only published blocks are served
                 via the public API.
        Type: Normal
        Target: ReusableBlockAPIViewSet.get_queryset()
        Technique: Equivalence partitioning
        Test data: Filter condition live=True
        """
        mock_qs = mock.MagicMock()
        mock_objects.filter.return_value = mock_qs
        viewset = ReusableBlockAPIViewSet()

        result = viewset.get_queryset()

        mock_objects.filter.assert_called_once_with(live=True)
        assert result is mock_qs


# ---------------------------------------------------------------------------
# ReusableBlockModelViewSet - get_queryset
# ---------------------------------------------------------------------------
class TestReusableBlockModelViewSetGetQueryset:
    """ReusableBlockModelViewSet.get_queryset filtering tests."""

    def _make_viewset(self, query_params=None):
        """Helper to create a viewset with mocked request."""
        viewset = ReusableBlockModelViewSet()
        viewset.request = mock.Mock()
        viewset.request.query_params = query_params or {}
        return viewset

    @mock.patch("wagtail_reusable_blocks.api.views.ReusableBlock.objects")
    def test_no_filters_returns_all(self, mock_objects):
        """Verify that all records are returned when no filter parameters are given.

        Purpose: Verify that get_queryset returns all records without filters,
                 ensuring the default full retrieval behavior.
        Type: Normal
        Target: ReusableBlockModelViewSet.get_queryset()
        Technique: Equivalence partitioning
        Test data: Empty query_params
        """
        mock_qs = mock.MagicMock()
        mock_objects.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        viewset = self._make_viewset()

        result = viewset.get_queryset()

        mock_objects.all.assert_called_once()
        assert result is mock_qs

    @mock.patch("wagtail_reusable_blocks.api.views.ReusableBlock.objects")
    def test_slug_filter(self, mock_objects):
        """Verify that the slug parameter triggers a slug filter.

        Purpose: Verify that get_queryset filters by slug=value when a slug
                 parameter is provided.
        Type: Normal
        Target: ReusableBlockModelViewSet.get_queryset()
        Technique: Equivalence partitioning
        Test data: slug="hero-block"
        """
        mock_qs = mock.MagicMock()
        mock_objects.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        viewset = self._make_viewset({"slug": "hero-block"})

        viewset.get_queryset()

        mock_qs.filter.assert_any_call(slug="hero-block")

    @pytest.mark.parametrize(
        "live_param,expected_bool",
        [
            pytest.param("true", True, id="DT1-true"),
            pytest.param("1", True, id="DT2-1"),
            pytest.param("yes", True, id="DT3-yes"),
            pytest.param("false", False, id="DT4-false"),
            pytest.param("0", False, id="DT5-0"),
            pytest.param("no", False, id="DT6-no"),
            pytest.param("TRUE", True, id="DT7-TRUE-uppercase"),
            pytest.param("True", True, id="DT8-True-titlecase"),
        ],
    )
    @mock.patch("wagtail_reusable_blocks.api.views.ReusableBlock.objects")
    def test_live_filter_parsing(self, mock_objects, live_param, expected_bool):
        """Verify that each live parameter value is correctly parsed to a boolean.

        Purpose: Verify that get_queryset correctly parses various live
                 parameter representations to boolean values for filtering.
        Type: Normal
        Target: ReusableBlockModelViewSet.get_queryset()
        Technique: Decision table (see DT-LIVE-FILTER)
        Test data: All DT-LIVE-FILTER patterns
        """
        mock_qs = mock.MagicMock()
        mock_objects.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        viewset = self._make_viewset({"live": live_param})

        viewset.get_queryset()

        mock_qs.filter.assert_any_call(live=expected_bool)

    @mock.patch("wagtail_reusable_blocks.api.views.ReusableBlock.objects")
    def test_search_filter(self, mock_objects):
        """Verify that the search parameter applies a name__icontains filter.

        Purpose: Verify that get_queryset filters by name__icontains when
                 a search parameter is provided, ensuring name search support.
        Type: Normal
        Target: ReusableBlockModelViewSet.get_queryset()
        Technique: Equivalence partitioning
        Test data: search="hero"
        """
        mock_qs = mock.MagicMock()
        mock_objects.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        viewset = self._make_viewset({"search": "hero"})

        viewset.get_queryset()

        mock_qs.filter.assert_any_call(name__icontains="hero")

    @mock.patch("wagtail_reusable_blocks.api.views.ReusableBlock.objects")
    def test_combined_filters(self, mock_objects):
        """Verify that slug, live, and search filters are all applied simultaneously.

        Purpose: Verify that get_queryset applies all filters in chain when
                 slug, live, and search parameters are all provided.
        Type: Normal
        Target: ReusableBlockModelViewSet.get_queryset()
        Technique: Decision table
        Test data: slug="hero", live="true", search="hero"
        """
        mock_qs = mock.MagicMock()
        mock_objects.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        viewset = self._make_viewset({"slug": "hero", "live": "true", "search": "hero"})

        viewset.get_queryset()

        assert mock_qs.filter.call_count == 3

    @mock.patch("wagtail_reusable_blocks.api.views.ReusableBlock.objects")
    def test_empty_string_slug_is_not_filtered(self, mock_objects):
        """Verify that an empty string slug does not trigger a filter.

        Purpose: Verify that get_queryset ignores an empty slug parameter,
                 ensuring empty value parameter handling.
        Type: Edge case
        Target: ReusableBlockModelViewSet.get_queryset()
        Technique: Boundary analysis
        Test data: slug=""
        """
        mock_qs = mock.MagicMock()
        mock_objects.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        viewset = self._make_viewset({"slug": ""})

        viewset.get_queryset()

        for call in mock_qs.filter.call_args_list:
            assert "slug" not in call.kwargs

    @mock.patch("wagtail_reusable_blocks.api.views.ReusableBlock.objects")
    def test_empty_string_search_is_not_filtered(self, mock_objects):
        """Verify that an empty string search does not trigger a filter.

        Purpose: Verify that get_queryset ignores an empty search parameter,
                 ensuring empty search query handling.
        Type: Edge case
        Target: ReusableBlockModelViewSet.get_queryset()
        Technique: Boundary analysis
        Test data: search=""
        """
        mock_qs = mock.MagicMock()
        mock_objects.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        viewset = self._make_viewset({"search": ""})

        viewset.get_queryset()

        for call in mock_qs.filter.call_args_list:
            assert "name__icontains" not in call.kwargs


# ---------------------------------------------------------------------------
# ReusableBlockModelViewSet - permissions / authentication
# ---------------------------------------------------------------------------
class TestReusableBlockModelViewSetPermissions:
    """ReusableBlockModelViewSet permission and authentication tests."""

    @mock.patch("wagtail_reusable_blocks.api.views._resolve_classes")
    def test_get_permissions_resolves_from_settings(self, mock_resolve):
        """Verify that get_permissions resolves permission classes from settings.

        Purpose: Verify that get_permissions calls _resolve_classes to resolve
                 classes from settings and returns instances.
        Type: Normal
        Target: ReusableBlockModelViewSet.get_permissions()
        Technique: Equivalence partitioning
        Test data: IsAuthenticated permission
        """
        mock_perm_class = mock.Mock()
        mock_perm_instance = mock.Mock()
        mock_perm_class.return_value = mock_perm_instance
        mock_resolve.return_value = [mock_perm_class]
        viewset = ReusableBlockModelViewSet()

        result = viewset.get_permissions()

        mock_resolve.assert_called_once_with("API_PERMISSION_CLASSES")
        assert len(result) == 1
        assert result[0] is mock_perm_instance

    @mock.patch("wagtail_reusable_blocks.api.views._resolve_classes")
    def test_get_permissions_returns_empty_list_when_none(self, mock_resolve):
        """Verify that an empty list is returned when the setting is None.

        Purpose: Verify that get_permissions returns an empty list when
                 _resolve_classes returns None, ensuring permission disable
                 behavior.
        Type: Edge case
        Target: ReusableBlockModelViewSet.get_permissions()
        Technique: Equivalence partitioning
        Test data: None setting (_resolve_classes returns None)
        """
        mock_resolve.return_value = None
        viewset = ReusableBlockModelViewSet()

        result = viewset.get_permissions()

        assert result == []

    @mock.patch("wagtail_reusable_blocks.api.views._resolve_classes")
    @mock.patch(
        "rest_framework.viewsets.ModelViewSet.get_authenticators",
        return_value=[mock.Mock()],
    )
    def test_get_authenticators_uses_drf_defaults_when_none(
        self, mock_super_auth, mock_resolve
    ):
        """Verify that DRF defaults are used when authentication classes are None.

        Purpose: Verify that get_authenticators uses super()'s default
                 authentication when _resolve_classes returns None, ensuring
                 DRF default fallback.
        Type: Normal
        Target: ReusableBlockModelViewSet.get_authenticators()
        Technique: Equivalence partitioning
        Test data: None setting (use DRF defaults)
        """
        mock_resolve.return_value = None
        viewset = ReusableBlockModelViewSet()

        result = viewset.get_authenticators()

        mock_resolve.assert_called_once_with("API_AUTHENTICATION_CLASSES")
        mock_super_auth.assert_called_once()
        assert len(result) == 1

    @mock.patch("wagtail_reusable_blocks.api.views._resolve_classes")
    def test_get_authenticators_resolves_from_settings(self, mock_resolve):
        """Verify that authentication classes are resolved from settings.

        Purpose: Verify that get_authenticators resolves classes from settings
                 via _resolve_classes and returns instances, ensuring custom
                 authentication support.
        Type: Normal
        Target: ReusableBlockModelViewSet.get_authenticators()
        Technique: Equivalence partitioning
        Test data: Custom authentication class
        """
        mock_auth_class = mock.Mock()
        mock_auth_instance = mock.Mock()
        mock_auth_class.return_value = mock_auth_instance
        mock_resolve.return_value = [mock_auth_class]
        viewset = ReusableBlockModelViewSet()

        result = viewset.get_authenticators()

        mock_resolve.assert_called_once_with("API_AUTHENTICATION_CLASSES")
        assert len(result) == 1
        assert result[0] is mock_auth_instance

    @mock.patch("wagtail_reusable_blocks.api.views._resolve_classes")
    def test_get_permissions_instantiates_multiple_classes(self, mock_resolve):
        """Verify that multiple permission classes are all instantiated.

        Purpose: Verify that get_permissions instantiates all classes when
                 multiple permission classes are configured.
        Type: Normal
        Target: ReusableBlockModelViewSet.get_permissions()
        Technique: Equivalence partitioning
        Test data: 2 permission classes
        """
        cls_a = mock.Mock()
        cls_b = mock.Mock()
        mock_resolve.return_value = [cls_a, cls_b]
        viewset = ReusableBlockModelViewSet()

        result = viewset.get_permissions()

        assert len(result) == 2
        cls_a.assert_called_once()
        cls_b.assert_called_once()


# ---------------------------------------------------------------------------
# ReusableBlock.api_fields
# ---------------------------------------------------------------------------
class TestReusableBlockApiFields:
    """ReusableBlock.api_fields configuration tests."""

    def test_api_fields_contain_expected_names(self):
        """Verify that api_fields contains all expected field names.

        Purpose: Verify that ReusableBlock.api_fields includes name, slug,
                 content, created_at, updated_at, and live, ensuring Wagtail
                 API v2 response field requirements.
        Type: Normal
        Target: ReusableBlock.api_fields
        Technique: Equivalence partitioning
        Test data: api_fields field name list
        """
        from wagtail_reusable_blocks.models import ReusableBlock

        field_names = [field.name for field in ReusableBlock.api_fields]
        expected = ["name", "slug", "content", "created_at", "updated_at", "live"]

        assert field_names == expected

    def test_api_fields_count(self):
        """Verify that the api_fields count is correct.

        Purpose: Verify that ReusableBlock.api_fields has exactly 6 fields,
                 ensuring no unintended field exposure or missing fields.
        Type: Normal
        Target: ReusableBlock.api_fields
        Technique: Equivalence partitioning
        Test data: api_fields length
        """
        from wagtail_reusable_blocks.models import ReusableBlock

        assert len(ReusableBlock.api_fields) == 6


# ---------------------------------------------------------------------------
# API __init__.py - public exports
# ---------------------------------------------------------------------------
class TestApiModuleExports:
    """API module __init__.py public export tests."""

    def test_exports_reusable_block_api_viewset(self):
        """Verify that ReusableBlockAPIViewSet is exported from the module.

        Purpose: Verify that ReusableBlockAPIViewSet can be imported from
                 wagtail_reusable_blocks.api, ensuring public API availability.
        Type: Normal
        Target: wagtail_reusable_blocks.api.__all__
        Technique: Equivalence partitioning
        Test data: Module import
        """
        from wagtail_reusable_blocks.api import ReusableBlockAPIViewSet as cls

        assert cls is ReusableBlockAPIViewSet

    def test_exports_reusable_block_model_viewset(self):
        """Verify that ReusableBlockModelViewSet is exported from the module.

        Purpose: Verify that ReusableBlockModelViewSet can be imported from
                 wagtail_reusable_blocks.api, ensuring public API availability.
        Type: Normal
        Target: wagtail_reusable_blocks.api.__all__
        Technique: Equivalence partitioning
        Test data: Module import
        """
        from wagtail_reusable_blocks.api import ReusableBlockModelViewSet as cls

        assert cls is ReusableBlockModelViewSet

    def test_all_contains_expected_exports(self):
        """Verify that __all__ contains the expected exports.

        Purpose: Verify that wagtail_reusable_blocks.api.__all__ includes
                 both ViewSet classes, ensuring explicit public API definition.
        Type: Normal
        Target: wagtail_reusable_blocks.api.__all__
        Technique: Equivalence partitioning
        Test data: __all__ attribute
        """
        import wagtail_reusable_blocks.api as api_module

        assert set(api_module.__all__) == {
            "ReusableBlockAPIViewSet",
            "ReusableBlockModelViewSet",
        }


# ---------------------------------------------------------------------------
# ReusableBlockModelViewSet - publish action
# ---------------------------------------------------------------------------
class TestReusableBlockModelViewSetPublish:
    """ReusableBlockModelViewSet.publish action tests."""

    def _call_publish(self):
        """Helper to create a viewset and invoke the publish action.

        Returns a tuple of (response, mock_instance, mock_request, viewset).
        """
        viewset = ReusableBlockModelViewSet()
        mock_instance = mock.MagicMock()
        mock_revision = mock.Mock()
        mock_instance.save_revision.return_value = mock_revision
        mock_request = mock.Mock()
        mock_request.user = mock.Mock()
        viewset.get_object = mock.Mock(return_value=mock_instance)
        mock_serializer = mock.Mock()
        mock_serializer.data = {"id": 1, "name": "Block", "live": True}
        viewset.get_serializer = mock.Mock(return_value=mock_serializer)
        viewset.request = mock_request

        response = viewset.publish(mock_request)
        return response, mock_instance, mock_request, viewset, mock_revision

    def test_publish_creates_revision_then_publishes(self):
        """Verify that publish() creates a revision and passes it to publish().

        Purpose: Verify that the publish action first creates a revision via
                 save_revision(user=request.user), then delegates to
                 DraftStateMixin.publish(revision, user=request.user),
                 ensuring the Wagtail revision workflow is triggered correctly.
        Type: Normal
        Target: ReusableBlockModelViewSet.publish(request)
        Technique: Equivalence partitioning
        Test data: Authenticated user request
        """
        _response, mock_instance, mock_request, _viewset, mock_revision = (
            self._call_publish()
        )

        mock_instance.save_revision.assert_called_once_with(user=mock_request.user)
        mock_instance.publish.assert_called_once_with(
            mock_revision, user=mock_request.user, skip_permission_checks=True
        )

    def test_publish_calls_refresh_from_db(self):
        """Verify that refresh_from_db() is called after publish.

        Purpose: Verify that the publish action refreshes the instance
                 from the database after publishing, ensuring the response
                 reflects the latest DB state (e.g. updated timestamps).
        Type: Normal
        Target: ReusableBlockModelViewSet.publish(request)
        Technique: Equivalence partitioning
        Test data: Authenticated user request
        """
        _response, mock_instance, _mock_request, _viewset, _ = self._call_publish()

        mock_instance.refresh_from_db.assert_called_once()

    def test_publish_returns_serializer_data(self):
        """Verify that the response body contains serialized instance data.

        Purpose: Verify that the publish action returns the serialized
                 instance data in the response, ensuring clients receive
                 the updated block representation.
        Type: Normal
        Target: ReusableBlockModelViewSet.publish(request)
        Technique: Equivalence partitioning
        Test data: Authenticated user request
        """
        response, _mock_instance, _mock_request, _viewset, _ = self._call_publish()

        assert response.data == {"id": 1, "name": "Block", "live": True}

    def test_publish_returns_200_status(self):
        """Verify that the response status code is 200 OK.

        Purpose: Verify that the publish action returns HTTP 200 OK,
                 ensuring the idempotent publish operation signals success.
        Type: Normal
        Target: ReusableBlockModelViewSet.publish(request)
        Technique: Equivalence partitioning
        Test data: Authenticated user request
        """
        response, _mock_instance, _mock_request, _viewset, _ = self._call_publish()

        assert response.status_code == status.HTTP_200_OK

    def test_publish_serializes_refreshed_instance(self):
        """Verify that get_serializer is called with the refreshed instance.

        Purpose: Verify that the publish action passes the instance
                 (after refresh_from_db) to get_serializer, ensuring
                 the serialized response reflects post-publish state.
        Type: Normal
        Target: ReusableBlockModelViewSet.publish(request)
        Technique: Equivalence partitioning
        Test data: Authenticated user request
        """
        _response, mock_instance, _mock_request, viewset, _ = self._call_publish()

        viewset.get_serializer.assert_called_once_with(mock_instance)

    def test_publish_calls_methods_in_order(self):
        """Verify that save_revision -> publish -> refresh_from_db -> get_serializer are called in order.

        Purpose: Verify the correct sequence of operations: create a revision,
                 publish with it, refresh from DB, then serialize, ensuring
                 data consistency in the response.
        Type: Normal
        Target: ReusableBlockModelViewSet.publish(request)
        Technique: Equivalence partitioning
        Test data: Authenticated user request
        """
        viewset = ReusableBlockModelViewSet()
        mock_instance = mock.MagicMock()
        mock_revision = mock.Mock()
        mock_request = mock.Mock()
        mock_request.user = mock.Mock()
        viewset.get_object = mock.Mock(return_value=mock_instance)
        mock_serializer = mock.Mock()
        mock_serializer.data = {}
        viewset.get_serializer = mock.Mock(return_value=mock_serializer)
        viewset.request = mock_request
        call_order = []
        mock_instance.save_revision.side_effect = lambda **kw: (
            call_order.append("save_revision"),
            mock_revision,
        )[1]
        mock_instance.publish.side_effect = lambda *a, **kw: call_order.append(
            "publish"
        )
        mock_instance.refresh_from_db.side_effect = lambda: call_order.append(
            "refresh_from_db"
        )
        viewset.get_serializer.side_effect = lambda inst: (
            call_order.append("get_serializer"),
            mock_serializer,
        )[1]

        viewset.publish(mock_request)

        assert call_order == [
            "save_revision",
            "publish",
            "refresh_from_db",
            "get_serializer",
        ]


# ---------------------------------------------------------------------------
# ReusableBlockModelViewSet - unpublish action
# ---------------------------------------------------------------------------
class TestReusableBlockModelViewSetUnpublish:
    """ReusableBlockModelViewSet.unpublish action tests."""

    def _call_unpublish(self):
        """Helper to create a viewset and invoke the unpublish action.

        Returns a tuple of (response, mock_instance, mock_request, viewset,
        mock_action_cls, mock_action_instance).
        """
        viewset = ReusableBlockModelViewSet()
        mock_instance = mock.MagicMock()
        mock_request = mock.Mock()
        mock_request.user = mock.Mock()
        viewset.get_object = mock.Mock(return_value=mock_instance)
        mock_serializer = mock.Mock()
        mock_serializer.data = {"id": 1, "name": "Block", "live": False}
        viewset.get_serializer = mock.Mock(return_value=mock_serializer)
        viewset.request = mock_request

        mock_action_instance = mock.Mock()
        with mock.patch(
            "wagtail_reusable_blocks.api.views.UnpublishAction",
            return_value=mock_action_instance,
        ) as mock_action_cls:
            response = viewset.unpublish(mock_request)
        return (
            response,
            mock_instance,
            mock_request,
            viewset,
            mock_action_cls,
            mock_action_instance,
        )

    def test_unpublish_creates_action_with_instance_and_user(self):
        """Verify that UnpublishAction is instantiated with (instance, user=request.user).

        Purpose: Verify that the unpublish action creates an UnpublishAction
                 with the correct instance and user, ensuring the Wagtail
                 unpublish workflow is configured correctly.
        Type: Normal
        Target: ReusableBlockModelViewSet.unpublish(request)
        Technique: Equivalence partitioning
        Test data: Authenticated user request
        """
        (
            _response,
            mock_instance,
            mock_request,
            _viewset,
            mock_action_cls,
            _mock_action_instance,
        ) = self._call_unpublish()

        mock_action_cls.assert_called_once_with(mock_instance, user=mock_request.user)

    def test_unpublish_executes_with_skip_permission_checks(self):
        """Verify that execute(skip_permission_checks=True) is called.

        Purpose: Verify that the unpublish action calls execute with
                 skip_permission_checks=True since DRF ViewSet already
                 handles authentication/authorization.
        Type: Normal
        Target: ReusableBlockModelViewSet.unpublish(request)
        Technique: Equivalence partitioning
        Test data: Authenticated user request
        """
        (
            _response,
            _mock_instance,
            _mock_request,
            _viewset,
            _mock_action_cls,
            mock_action_instance,
        ) = self._call_unpublish()

        mock_action_instance.execute.assert_called_once_with(
            skip_permission_checks=True
        )

    def test_unpublish_calls_refresh_from_db(self):
        """Verify that refresh_from_db() is called after unpublish.

        Purpose: Verify that the unpublish action refreshes the instance
                 from the database after unpublishing, ensuring the response
                 reflects the latest DB state.
        Type: Normal
        Target: ReusableBlockModelViewSet.unpublish(request)
        Technique: Equivalence partitioning
        Test data: Authenticated user request
        """
        (
            _response,
            mock_instance,
            _mock_request,
            _viewset,
            _mock_action_cls,
            _mock_action_instance,
        ) = self._call_unpublish()

        mock_instance.refresh_from_db.assert_called_once()

    def test_unpublish_returns_serializer_data(self):
        """Verify that the response body contains serialized instance data.

        Purpose: Verify that the unpublish action returns the serialized
                 instance data in the response, ensuring clients receive
                 the updated block representation with live=False.
        Type: Normal
        Target: ReusableBlockModelViewSet.unpublish(request)
        Technique: Equivalence partitioning
        Test data: Authenticated user request
        """
        (
            response,
            _mock_instance,
            _mock_request,
            _viewset,
            _mock_action_cls,
            _mock_action_instance,
        ) = self._call_unpublish()

        assert response.data == {"id": 1, "name": "Block", "live": False}

    def test_unpublish_returns_200_status(self):
        """Verify that the response status code is 200 OK.

        Purpose: Verify that the unpublish action returns HTTP 200 OK,
                 ensuring the idempotent unpublish operation signals success.
        Type: Normal
        Target: ReusableBlockModelViewSet.unpublish(request)
        Technique: Equivalence partitioning
        Test data: Authenticated user request
        """
        (
            response,
            _mock_instance,
            _mock_request,
            _viewset,
            _mock_action_cls,
            _mock_action_instance,
        ) = self._call_unpublish()

        assert response.status_code == status.HTTP_200_OK

    def test_unpublish_serializes_refreshed_instance(self):
        """Verify that get_serializer is called with the refreshed instance.

        Purpose: Verify that the unpublish action passes the instance
                 (after refresh_from_db) to get_serializer, ensuring
                 the serialized response reflects post-unpublish state.
        Type: Normal
        Target: ReusableBlockModelViewSet.unpublish(request)
        Technique: Equivalence partitioning
        Test data: Authenticated user request
        """
        (
            _response,
            mock_instance,
            _mock_request,
            viewset,
            _mock_action_cls,
            _mock_action_instance,
        ) = self._call_unpublish()

        viewset.get_serializer.assert_called_once_with(mock_instance)

    def test_unpublish_calls_methods_in_order(self):
        """Verify that UnpublishAction.execute -> refresh_from_db -> get_serializer are called in order.

        Purpose: Verify the correct sequence of operations: execute the
                 unpublish action, refresh from DB, then serialize, ensuring
                 data consistency in the response.
        Type: Normal
        Target: ReusableBlockModelViewSet.unpublish(request)
        Technique: Equivalence partitioning
        Test data: Authenticated user request
        """
        viewset = ReusableBlockModelViewSet()
        mock_instance = mock.MagicMock()
        mock_request = mock.Mock()
        mock_request.user = mock.Mock()
        viewset.get_object = mock.Mock(return_value=mock_instance)
        mock_serializer = mock.Mock()
        mock_serializer.data = {}
        viewset.get_serializer = mock.Mock(return_value=mock_serializer)
        viewset.request = mock_request
        call_order = []
        mock_action_instance = mock.Mock()
        mock_action_instance.execute.side_effect = lambda **kw: call_order.append(
            "execute"
        )
        mock_instance.refresh_from_db.side_effect = lambda: call_order.append(
            "refresh_from_db"
        )
        viewset.get_serializer.side_effect = lambda inst: (
            call_order.append("get_serializer"),
            mock_serializer,
        )[1]

        with mock.patch(
            "wagtail_reusable_blocks.api.views.UnpublishAction",
            return_value=mock_action_instance,
        ):
            viewset.unpublish(mock_request)

        assert call_order == ["execute", "refresh_from_db", "get_serializer"]


# ---------------------------------------------------------------------------
# ReusableBlockModelViewSet - render action
# ---------------------------------------------------------------------------
class TestReusableBlockModelViewSetRender:
    """ReusableBlockModelViewSet.render action tests."""

    def _make_viewset_for_render(self, mock_instance=None):
        """Helper to create a viewset configured for render action tests.

        Returns a tuple of (viewset, mock_instance, mock_request).
        """
        viewset = ReusableBlockModelViewSet()
        if mock_instance is None:
            mock_instance = mock.MagicMock()
        mock_request = mock.Mock()
        viewset.get_object = mock.Mock(return_value=mock_instance)
        viewset.request = mock_request
        return viewset, mock_instance, mock_request

    def test_render_calls_instance_render(self):
        """Verify that render() calls instance.render().

        Purpose: Verify that the render action delegates HTML generation
                 to the model's render() method, ensuring the block's
                 StreamField content is rendered.
        Type: Normal
        Target: ReusableBlockModelViewSet.render(request)
        Technique: Equivalence partitioning
        Test data: Instance with renderable content
        """
        viewset, mock_instance, mock_request = self._make_viewset_for_render()
        mock_instance.render.return_value = "<p>Hello</p>"

        viewset.render(mock_request)

        mock_instance.render.assert_called_once()

    def test_render_returns_html_in_response(self):
        """Verify that the response contains {"html": "..."} with rendered content.

        Purpose: Verify that the render action wraps the rendered HTML
                 in a {"html": ...} JSON envelope, ensuring clients
                 can parse the rendered output.
        Type: Normal
        Target: ReusableBlockModelViewSet.render(request)
        Technique: Equivalence partitioning
        Test data: Instance rendering "<div>Content</div>"
        """
        viewset, mock_instance, mock_request = self._make_viewset_for_render()
        mock_instance.render.return_value = "<div>Content</div>"

        response = viewset.render(mock_request)

        assert response.data == {"html": "<div>Content</div>"}

    def test_render_returns_200_status(self):
        """Verify that the response status code is 200 OK on success.

        Purpose: Verify that the render action returns HTTP 200 OK
                 when rendering succeeds, signaling a successful operation.
        Type: Normal
        Target: ReusableBlockModelViewSet.render(request)
        Technique: Equivalence partitioning
        Test data: Instance with renderable content
        """
        viewset, mock_instance, mock_request = self._make_viewset_for_render()
        mock_instance.render.return_value = "<p>OK</p>"

        response = viewset.render(mock_request)

        assert response.status_code == status.HTTP_200_OK

    def test_render_returns_500_on_exception(self):
        """Verify that a 500 response is returned when render() raises an exception.

        Purpose: Verify that the render action catches exceptions from
                 instance.render() and returns HTTP 500 with an error
                 detail, ensuring graceful error handling for template
                 or rendering failures.
        Type: Error
        Target: ReusableBlockModelViewSet.render(request)
        Technique: Error guessing
        Test data: Instance whose render() raises RuntimeError
        """
        viewset, mock_instance, mock_request = self._make_viewset_for_render()
        mock_instance.render.side_effect = RuntimeError("Template not found")

        response = viewset.render(mock_request)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_render_returns_error_detail_on_exception(self):
        """Verify that the error message is included in the response detail.

        Purpose: Verify that the render action includes the exception
                 message in the {"detail": ...} response body, enabling
                 clients to diagnose rendering failures.
        Type: Error
        Target: ReusableBlockModelViewSet.render(request)
        Technique: Error guessing
        Test data: Instance whose render() raises ValueError with message
        """
        viewset, mock_instance, mock_request = self._make_viewset_for_render()
        mock_instance.render.side_effect = ValueError("Invalid block data")

        response = viewset.render(mock_request)

        assert response.data == {"detail": "Invalid block data"}

    def test_render_returns_empty_html_string(self):
        """Verify that an empty HTML string is returned correctly.

        Purpose: Verify that the render action handles an empty render
                 result (e.g. a block with no content), returning an
                 empty string in the html field.
        Type: Edge case
        Target: ReusableBlockModelViewSet.render(request)
        Technique: Boundary analysis
        Test data: Instance rendering empty string
        """
        viewset, mock_instance, mock_request = self._make_viewset_for_render()
        mock_instance.render.return_value = ""

        response = viewset.render(mock_request)

        assert response.data == {"html": ""}
        assert response.status_code == status.HTTP_200_OK
