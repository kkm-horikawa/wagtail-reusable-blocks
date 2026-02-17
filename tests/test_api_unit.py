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
from rest_framework import permissions, serializers

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
        """API_PERMISSION_CLASSESのデフォルト値がIsAuthenticatedであることを確認する。

        【目的】get_settingでAPI_PERMISSION_CLASSESを取得し、デフォルト値として
               IsAuthenticatedのパスが返却されることをもって、API認可のデフォルト
               設定要件を保証する
        【種別】正常系テスト
        【対象】get_setting("API_PERMISSION_CLASSES")
        【技法】同値分割
        【テストデータ】ユーザー設定なし（DEFAULTSのみ）
        """
        result = get_setting("API_PERMISSION_CLASSES")

        assert result == ["rest_framework.permissions.IsAuthenticated"]

    def test_api_authentication_classes_default_is_none(self):
        """API_AUTHENTICATION_CLASSESのデフォルト値がNoneであることを確認する。

        【目的】get_settingでAPI_AUTHENTICATION_CLASSESを取得し、Noneが返却される
               ことをもって、DRFデフォルト認証使用の設定要件を保証する
        【種別】正常系テスト
        【対象】get_setting("API_AUTHENTICATION_CLASSES")
        【技法】同値分割
        【テストデータ】ユーザー設定なし（DEFAULTSのみ）
        """
        result = get_setting("API_AUTHENTICATION_CLASSES")

        assert result is None

    @mock.patch(
        "wagtail_reusable_blocks.conf.settings",
    )
    def test_user_setting_overrides_default(self, mock_settings):
        """ユーザー設定がデフォルト値をオーバーライドすることを確認する。

        【目的】WAGTAIL_REUSABLE_BLOCKSにカスタム設定を与え、デフォルト値が
               上書きされることをもって、設定カスタマイズ要件を保証する
        【種別】正常系テスト
        【対象】get_setting(key)
        【技法】同値分割
        【テストデータ】AllowAnyパーミッションへのオーバーライド
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
        """None デフォルトをリストでオーバーライドできることを確認する。

        【目的】API_AUTHENTICATION_CLASSESのデフォルトNoneをリストで上書きし、
               カスタム認証クラスが設定可能であることをもって、認証カスタマイズ
               要件を保証する
        【種別】正常系テスト
        【対象】get_setting("API_AUTHENTICATION_CLASSES")
        【技法】同値分割
        【テストデータ】TokenAuthenticationへのオーバーライド
        """
        custom_auth = ["rest_framework.authentication.TokenAuthentication"]
        mock_settings.WAGTAIL_REUSABLE_BLOCKS = {
            "API_AUTHENTICATION_CLASSES": custom_auth,
        }

        result = get_setting("API_AUTHENTICATION_CLASSES")

        assert result == custom_auth

    def test_api_filter_fields_default(self):
        """API_FILTER_FIELDSのデフォルト値が正しいことを確認する。

        【目的】get_settingでAPI_FILTER_FIELDSを取得し、slug/liveが返却される
               ことをもって、フィルタ対象フィールドの設定要件を保証する
        【種別】正常系テスト
        【対象】get_setting("API_FILTER_FIELDS")
        【技法】同値分割
        【テストデータ】ユーザー設定なし（DEFAULTSのみ）
        """
        result = get_setting("API_FILTER_FIELDS")

        assert result == ["slug", "live"]

    def test_api_search_fields_default(self):
        """API_SEARCH_FIELDSのデフォルト値が正しいことを確認する。

        【目的】get_settingでAPI_SEARCH_FIELDSを取得し、name/slugが返却される
               ことをもって、検索対象フィールドの設定要件を保証する
        【種別】正常系テスト
        【対象】get_setting("API_SEARCH_FIELDS")
        【技法】同値分割
        【テストデータ】ユーザー設定なし（DEFAULTSのみ）
        """
        result = get_setting("API_SEARCH_FIELDS")

        assert result == ["name", "slug"]

    def test_defaults_dict_contains_all_api_keys(self):
        """DEFAULTS辞書にAPI関連の全キーが含まれることを確認する。

        【目的】DEFAULTS辞書にAPI_PERMISSION_CLASSES, API_AUTHENTICATION_CLASSES,
               API_FILTER_FIELDS, API_SEARCH_FIELDSが含まれることをもって、
               API設定の網羅性を保証する
        【種別】正常系テスト
        【対象】conf.DEFAULTS
        【技法】同値分割
        【テストデータ】DEFAULTS辞書のキー
        """
        expected_keys = {
            "API_PERMISSION_CLASSES",
            "API_AUTHENTICATION_CLASSES",
            "API_FILTER_FIELDS",
            "API_SEARCH_FIELDS",
        }

        assert expected_keys.issubset(set(DEFAULTS.keys()))


# ---------------------------------------------------------------------------
# _resolve_classes
# ---------------------------------------------------------------------------
class TestResolveClasses:
    """_resolve_classes class resolution tests."""

    @mock.patch("wagtail_reusable_blocks.api.views.get_setting", return_value=None)
    def test_returns_none_when_setting_is_none(self, mock_get_setting):
        """設定値がNoneの場合にNoneが返ることを確認する。

        【目的】_resolve_classesにNone設定を与え、Noneが返却されることをもって、
               DRFデフォルトへのフォールバック要件を保証する
        【種別】エッジケース
        【対象】_resolve_classes(setting_key)
        【技法】同値分割（DT-RESOLVE-CLASSES DT1）
        【テストデータ】None設定
        """
        result = _resolve_classes("API_AUTHENTICATION_CLASSES")

        assert result is None
        mock_get_setting.assert_called_once_with("API_AUTHENTICATION_CLASSES")

    @mock.patch("wagtail_reusable_blocks.api.views.get_setting")
    @mock.patch("wagtail_reusable_blocks.api.views.import_string")
    def test_resolves_string_path_to_class(self, mock_import, mock_get_setting):
        """文字列パスからクラスが解決されることを確認する。

        【目的】_resolve_classesにdotted path文字列リストを与え、import_stringで
               解決されたクラスリストが返却されることをもって、文字列パスからの
               クラス解決要件を保証する
        【種別】正常系テスト
        【対象】_resolve_classes(setting_key)
        【技法】同値分割（DT-RESOLVE-CLASSES DT2）
        【テストデータ】IsAuthenticated文字列パス
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
        """クラスオブジェクト直接指定がそのまま返されることを確認する。

        【目的】_resolve_classesにクラスオブジェクトを直接与え、そのまま返却される
               ことをもって、クラスオブジェクト直接指定の要件を保証する
        【種別】正常系テスト
        【対象】_resolve_classes(setting_key)
        【技法】同値分割（DT-RESOLVE-CLASSES DT3）
        【テストデータ】IsAuthenticatedクラスオブジェクト
        """
        mock_get_setting.return_value = [permissions.IsAuthenticated]

        result = _resolve_classes("API_PERMISSION_CLASSES")

        assert result == [permissions.IsAuthenticated]

    @mock.patch("wagtail_reusable_blocks.api.views.get_setting")
    @mock.patch("wagtail_reusable_blocks.api.views.import_string")
    def test_resolves_mixed_strings_and_classes(self, mock_import, mock_get_setting):
        """文字列とクラスオブジェクトの混在リストが解決されることを確認する。

        【目的】_resolve_classesに文字列パスとクラスオブジェクトの混在リストを与え、
               全て正しく解決されることをもって、混在指定の互換性要件を保証する
        【種別】正常系テスト
        【対象】_resolve_classes(setting_key)
        【技法】同値分割（DT-RESOLVE-CLASSES DT4）
        【テストデータ】文字列パス1つ + クラスオブジェクト1つ
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
        """空リスト設定で空リストが返ることを確認する。

        【目的】_resolve_classesに空リストを与え、空リストが返却されることをもって、
               パーミッション無効化の要件を保証する
        【種別】エッジケース
        【対象】_resolve_classes(setting_key)
        【技法】境界値分析（DT-RESOLVE-CLASSES DT5）
        【テストデータ】空リスト
        """
        result = _resolve_classes("API_PERMISSION_CLASSES")

        assert result == []

    @mock.patch("wagtail_reusable_blocks.api.views.get_setting")
    @mock.patch("wagtail_reusable_blocks.api.views.import_string")
    def test_raises_import_error_for_invalid_path(self, mock_import, mock_get_setting):
        """不正な文字列パスでImportErrorが発生することを確認する。

        【目的】_resolve_classesに存在しないモジュールパスを与え、ImportErrorが
               発生することをもって、不正設定検出の要件を保証する
        【種別】異常系テスト
        【対象】_resolve_classes(setting_key)
        【技法】エラー推測
        【テストデータ】存在しないモジュールパス
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
        """Metaクラスのfieldsに期待するフィールドが全て含まれることを確認する。

        【目的】ReusableBlockSerializer.Meta.fieldsにAPI仕様で定義された全フィールドが
               含まれることをもって、APIレスポンスのフィールド網羅性要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockSerializer.Meta.fields
        【技法】同値分割
        【テストデータ】Metaクラスのfields属性
        """
        expected = ["id", "name", "slug", "content", "live", "created_at", "updated_at"]

        assert ReusableBlockSerializer.Meta.fields == expected

    def test_read_only_fields_are_correct(self):
        """read_only_fieldsにid, created_at, updated_at, liveが含まれることを確認する。

        【目的】ReusableBlockSerializer.Meta.read_only_fieldsに自動設定フィールドが
               含まれることをもって、API経由でのフィールド書き換え防止要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockSerializer.Meta.read_only_fields
        【技法】同値分割
        【テストデータ】Metaクラスのread_only_fields属性
        """
        expected = ["id", "created_at", "updated_at", "live"]

        assert ReusableBlockSerializer.Meta.read_only_fields == expected

    def test_content_field_is_stream_field_field(self):
        """contentフィールドがStreamFieldFieldとして定義されていることを確認する。

        【目的】contentフィールドがStreamFieldFieldで定義されていることをもって、
               StreamValue→JSON変換を含むStreamFieldデータの読み書き要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockSerializer.content
        【技法】同値分割
        【テストデータ】contentフィールドのクラス
        """
        serializer = ReusableBlockSerializer()

        assert isinstance(serializer.fields["content"], StreamFieldField)

    def test_content_field_not_required(self):
        """contentフィールドが必須でないことを確認する。

        【目的】contentフィールドがrequired=Falseで定義されていることをもって、
               空コンテンツでのブロック作成要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockSerializer.content
        【技法】同値分割
        【テストデータ】contentフィールドのrequired属性
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
        """一意なslugがバリデーションを通過することを確認する。

        【目的】validate_slugに重複のないslugを与え、そのまま返却されることをもって、
               一意slug受け入れ要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockSerializer.validate_slug(value)
        【技法】同値分割
        【テストデータ】DBに存在しないslug "new-block"
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
        """新規作成時に重複slugでValidationErrorが発生することを確認する。

        【目的】validate_slugに既存と同じslugを与え、ValidationErrorが発生する
               ことをもって、slug一意性制約の要件を保証する
        【種別】異常系テスト
        【対象】ReusableBlockSerializer.validate_slug(value)
        【技法】同値分割
        【テストデータ】DBに既存のslug "existing-block"
        """
        mock_qs = mock.MagicMock()
        mock_qs.exists.return_value = True
        mock_objects.filter.return_value = mock_qs
        serializer = ReusableBlockSerializer()

        with pytest.raises(serializers.ValidationError, match="already exists"):
            serializer.validate_slug("existing-block")

    @mock.patch("wagtail_reusable_blocks.api.serializers.ReusableBlock.objects")
    def test_update_excludes_own_pk_from_uniqueness_check(self, mock_objects):
        """更新時に自身のPKがユニークチェックから除外されることを確認する。

        【目的】validate_slugに更新対象インスタンスを設定した状態で同じslugを与え、
               自身のPKが除外されてバリデーションを通過することをもって、
               更新時の自身除外要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockSerializer.validate_slug(value)
        【技法】同値分割
        【テストデータ】pk=42の既存インスタンスが自身のslugを保持するケース
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
        """更新時に他インスタンスとのslug重複が検出されることを確認する。

        【目的】validate_slugに更新対象を設定し他インスタンスと同じslugを与え、
               ValidationErrorが発生することをもって、他インスタンスとのslug
               重複検出要件を保証する
        【種別】異常系テスト
        【対象】ReusableBlockSerializer.validate_slug(value)
        【技法】同値分割
        【テストデータ】pk=42のインスタンスが他のインスタンスのslugを使おうとするケース
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
        """slug未指定時にnameからslugが自動生成されることを確認する。

        【目的】validateにslug未指定・name指定のデータを与え、slugifyされた値が
               attrsに設定されることをもって、slug自動生成要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockSerializer.validate(attrs)
        【技法】同値分割
        【テストデータ】slug空・name="My New Block"
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
        """slugキーが存在しない場合にnameからslugが自動生成されることを確認する。

        【目的】validateにslugキーなし・name指定のデータを与え、slugifyされた値が
               設定されることをもって、slug省略時の自動生成要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockSerializer.validate(attrs)
        【技法】同値分割
        【テストデータ】slugキーなし・name="Test Block"
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
        """明示的に指定されたslugが保持されることを確認する。

        【目的】validateにslug指定のデータを与え、指定値がそのまま保持される
               ことをもって、明示的slug指定の優先要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockSerializer.validate(attrs)
        【技法】同値分割
        【テストデータ】slug="custom-slug"を明示指定
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
        """自動生成slugが既存と重複する場合にValidationErrorが発生することを確認する。

        【目的】validateでslug自動生成時に既存slugと重複した場合、ValidationErrorが
               発生することをもって、自動生成slug一意性チェック要件を保証する
        【種別】異常系テスト
        【対象】ReusableBlockSerializer.validate(attrs)
        【技法】エラー推測
        【テストデータ】自動生成slug "my-block" がDBに既存のケース
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
        """更新時の自動生成slugで自身のPKが除外されることを確認する。

        【目的】validateに更新対象インスタンスを設定し、slug自動生成時に自身のPKが
               一意性チェックから除外されることをもって、更新時の自動生成slug
               自身除外要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockSerializer.validate(attrs)
        【技法】同値分割
        【テストデータ】pk=10のインスタンス更新で自動生成slug
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
        """name未指定かつslug未指定の場合にslugが生成されないことを確認する。

        【目的】validateにname/slugともに未指定のデータを与え、slugが生成されず
               attrsにslugキーが追加されないことをもって、nameなし時のslug
               非生成要件を保証する
        【種別】エッジケース
        【対象】ReusableBlockSerializer.validate(attrs)
        【技法】境界値分析
        【テストデータ】name/slugともに未指定
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
        """createで新規インスタンスの保存とリビジョン作成が行われることを確認する。

        【目的】createにvalidated_dataを与え、full_clean, save, save_revisionが
               順に呼ばれることをもって、作成時のリビジョン管理要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockSerializer.create(validated_data)
        【技法】同値分割
        【テストデータ】name="New Block", slug="new-block"
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
        """createでfull_clean -> save -> save_revisionの順に呼ばれることを確認する。

        【目的】createの呼び出し順序がfull_clean -> save -> save_revisionであることを
               もって、バリデーション後の保存・リビジョン作成の順序要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockSerializer.create(validated_data)
        【技法】同値分割
        【テストデータ】name="Order Test"
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
        """updateで属性設定、保存、リビジョン作成が行われることを確認する。

        【目的】updateにインスタンスとvalidated_dataを与え、属性設定後にfull_clean,
               save, save_revisionが呼ばれることをもって、更新時のリビジョン管理
               要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockSerializer.update(instance, validated_data)
        【技法】同値分割
        【テストデータ】name="Updated Name"への更新
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
        """updateで複数属性が正しく設定されることを確認する。

        【目的】updateに複数フィールドのvalidated_dataを与え、全て正しく設定される
               ことをもって、複数フィールド同時更新要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockSerializer.update(instance, validated_data)
        【技法】同値分割
        【テストデータ】name, slug, contentの同時更新
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
        """updateでfull_clean -> save -> save_revisionの順に呼ばれることを確認する。

        【目的】updateの呼び出し順序がfull_clean -> save -> save_revisionであることを
               もって、バリデーション後の保存・リビジョン作成の順序要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockSerializer.update(instance, validated_data)
        【技法】同値分割
        【テストデータ】name="Order Test"
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
        """get_querysetがlive=Trueでフィルタすることを確認する。

        【目的】get_querysetが常にlive=Trueでフィルタした結果を返すことをもって、
               公開済みブロックのみ公開APIで提供する要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockAPIViewSet.get_queryset()
        【技法】同値分割
        【テストデータ】フィルタ条件 live=True
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
        """フィルタパラメータなしで全件が返されることを確認する。

        【目的】get_querysetにフィルタパラメータなしでアクセスし、全件が返却される
               ことをもって、デフォルトの全件取得要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockModelViewSet.get_queryset()
        【技法】同値分割
        【テストデータ】空のquery_params
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
        """slugパラメータでフィルタされることを確認する。

        【目的】get_querysetにslugパラメータを与え、slug=値でフィルタされた
               結果が返却されることをもって、slugフィルタ要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockModelViewSet.get_queryset()
        【技法】同値分割
        【テストデータ】slug="hero-block"
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
        """liveパラメータの各値が正しくブール値に変換されることを確認する。

        【目的】get_querysetにliveパラメータの各表現を与え、正しいブール値で
               フィルタされることをもって、liveフィルタのパース要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockModelViewSet.get_queryset()
        【技法】デシジョンテーブル（DT-LIVE-FILTER参照）
        【テストデータ】DT-LIVE-FILTERの全パターン
        """
        mock_qs = mock.MagicMock()
        mock_objects.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        viewset = self._make_viewset({"live": live_param})

        viewset.get_queryset()

        mock_qs.filter.assert_any_call(live=expected_bool)

    @mock.patch("wagtail_reusable_blocks.api.views.ReusableBlock.objects")
    def test_search_filter(self, mock_objects):
        """searchパラメータでname__icontainsフィルタが適用されることを確認する。

        【目的】get_querysetにsearchパラメータを与え、name__icontainsでフィルタ
               されることをもって、名前検索要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockModelViewSet.get_queryset()
        【技法】同値分割
        【テストデータ】search="hero"
        """
        mock_qs = mock.MagicMock()
        mock_objects.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        viewset = self._make_viewset({"search": "hero"})

        viewset.get_queryset()

        mock_qs.filter.assert_any_call(name__icontains="hero")

    @mock.patch("wagtail_reusable_blocks.api.views.ReusableBlock.objects")
    def test_combined_filters(self, mock_objects):
        """slug, live, searchの全フィルタが同時に適用されることを確認する。

        【目的】get_querysetにslug, live, searchの全パラメータを与え、全フィルタが
               チェーン適用されることをもって、複合フィルタ要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockModelViewSet.get_queryset()
        【技法】デシジョンテーブル
        【テストデータ】slug="hero", live="true", search="hero"
        """
        mock_qs = mock.MagicMock()
        mock_objects.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        viewset = self._make_viewset({"slug": "hero", "live": "true", "search": "hero"})

        viewset.get_queryset()

        assert mock_qs.filter.call_count == 3

    @mock.patch("wagtail_reusable_blocks.api.views.ReusableBlock.objects")
    def test_empty_string_slug_is_not_filtered(self, mock_objects):
        """空文字slugではフィルタが適用されないことを確認する。

        【目的】get_querysetに空文字slugを与え、slugフィルタが適用されないことを
               もって、空値パラメータの無視要件を保証する
        【種別】エッジケース
        【対象】ReusableBlockModelViewSet.get_queryset()
        【技法】境界値分析
        【テストデータ】slug=""
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
        """空文字searchではフィルタが適用されないことを確認する。

        【目的】get_querysetに空文字searchを与え、searchフィルタが適用されない
               ことをもって、空検索クエリの無視要件を保証する
        【種別】エッジケース
        【対象】ReusableBlockModelViewSet.get_queryset()
        【技法】境界値分析
        【テストデータ】search=""
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
        """get_permissionsが設定からパーミッションクラスを解決することを確認する。

        【目的】get_permissionsが_resolve_classesを呼んで設定からクラスを解決し、
               インスタンスリストを返すことをもって、パーミッション設定解決要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockModelViewSet.get_permissions()
        【技法】同値分割
        【テストデータ】IsAuthenticatedパーミッション
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
        """設定がNoneの場合に空リストが返されることを確認する。

        【目的】get_permissionsで_resolve_classesがNoneを返す場合に空リストが返却
               されることをもって、パーミッション無効化時の動作要件を保証する
        【種別】エッジケース
        【対象】ReusableBlockModelViewSet.get_permissions()
        【技法】同値分割
        【テストデータ】None設定（_resolve_classesがNoneを返す）
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
        """認証クラスがNoneの場合にDRFデフォルトが使用されることを確認する。

        【目的】get_authenticatorsで_resolve_classesがNoneを返す場合にsuper()の
               デフォルト認証が使用されることをもって、DRFデフォルトフォールバック
               要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockModelViewSet.get_authenticators()
        【技法】同値分割
        【テストデータ】None設定（DRFデフォルト使用）
        """
        mock_resolve.return_value = None
        viewset = ReusableBlockModelViewSet()

        result = viewset.get_authenticators()

        mock_resolve.assert_called_once_with("API_AUTHENTICATION_CLASSES")
        mock_super_auth.assert_called_once()
        assert len(result) == 1

    @mock.patch("wagtail_reusable_blocks.api.views._resolve_classes")
    def test_get_authenticators_resolves_from_settings(self, mock_resolve):
        """設定から認証クラスが解決されることを確認する。

        【目的】get_authenticatorsが_resolve_classesで設定からクラスを解決し、
               インスタンスリストを返すことをもって、カスタム認証設定要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockModelViewSet.get_authenticators()
        【技法】同値分割
        【テストデータ】カスタム認証クラス
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
        """複数パーミッションクラスが全てインスタンス化されることを確認する。

        【目的】get_permissionsに複数クラスの設定を与え、全てがインスタンス化されて
               返却されることをもって、複数パーミッション併用要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlockModelViewSet.get_permissions()
        【技法】同値分割
        【テストデータ】2つのパーミッションクラス
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
        """api_fieldsに期待するフィールド名が全て含まれることを確認する。

        【目的】ReusableBlock.api_fieldsにname, slug, content, created_at,
               updated_at, liveが含まれることをもって、Wagtail API v2の
               レスポンスフィールド要件を保証する
        【種別】正常系テスト
        【対象】ReusableBlock.api_fields
        【技法】同値分割
        【テストデータ】api_fieldsのフィールド名リスト
        """
        from wagtail_reusable_blocks.models import ReusableBlock

        field_names = [field.name for field in ReusableBlock.api_fields]
        expected = ["name", "slug", "content", "created_at", "updated_at", "live"]

        assert field_names == expected

    def test_api_fields_count(self):
        """api_fieldsのフィールド数が正しいことを確認する。

        【目的】ReusableBlock.api_fieldsのフィールド数が6であることをもって、
               不要なフィールド露出や必要フィールドの欠落がないことを保証する
        【種別】正常系テスト
        【対象】ReusableBlock.api_fields
        【技法】同値分割
        【テストデータ】api_fieldsの長さ
        """
        from wagtail_reusable_blocks.models import ReusableBlock

        assert len(ReusableBlock.api_fields) == 6


# ---------------------------------------------------------------------------
# API __init__.py - public exports
# ---------------------------------------------------------------------------
class TestApiModuleExports:
    """API module __init__.py public export tests."""

    def test_exports_reusable_block_api_viewset(self):
        """ReusableBlockAPIViewSetがモジュールからエクスポートされることを確認する。

        【目的】wagtail_reusable_blocks.apiからReusableBlockAPIViewSetが
               インポート可能であることをもって、公開API要件を保証する
        【種別】正常系テスト
        【対象】wagtail_reusable_blocks.api.__all__
        【技法】同値分割
        【テストデータ】モジュールインポート
        """
        from wagtail_reusable_blocks.api import ReusableBlockAPIViewSet as cls

        assert cls is ReusableBlockAPIViewSet

    def test_exports_reusable_block_model_viewset(self):
        """ReusableBlockModelViewSetがモジュールからエクスポートされることを確認する。

        【目的】wagtail_reusable_blocks.apiからReusableBlockModelViewSetが
               インポート可能であることをもって、公開API要件を保証する
        【種別】正常系テスト
        【対象】wagtail_reusable_blocks.api.__all__
        【技法】同値分割
        【テストデータ】モジュールインポート
        """
        from wagtail_reusable_blocks.api import ReusableBlockModelViewSet as cls

        assert cls is ReusableBlockModelViewSet

    def test_all_contains_expected_exports(self):
        """__all__に期待するエクスポートが含まれることを確認する。

        【目的】wagtail_reusable_blocks.api.__all__に2つのViewSetクラスが
               含まれることをもって、パブリックAPIの明示的定義要件を保証する
        【種別】正常系テスト
        【対象】wagtail_reusable_blocks.api.__all__
        【技法】同値分割
        【テストデータ】__all__属性
        """
        import wagtail_reusable_blocks.api as api_module

        assert set(api_module.__all__) == {
            "ReusableBlockAPIViewSet",
            "ReusableBlockModelViewSet",
        }
