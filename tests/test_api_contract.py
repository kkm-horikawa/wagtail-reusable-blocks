"""Response schema validation tests for DRF API endpoints.

schemathesis-based fuzzing is skipped because OpenAPI schema is not yet introduced.
Each CRUD endpoint's response structure is verified against the expected schema.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from wagtail_reusable_blocks.models import ReusableBlock

User = get_user_model()

LIST_FIELDS = {"id", "name", "slug", "content", "live", "created_at", "updated_at"}
DETAIL_FIELDS = LIST_FIELDS
READ_ONLY_FIELDS = {"id", "created_at", "updated_at", "live"}


@pytest.fixture
def api_admin_user(db):
    return User.objects.create_superuser(
        username="api_admin", email="api_admin@example.com", password="password"
    )


@pytest.fixture
def api_client(api_admin_user):
    client = APIClient()
    client.force_authenticate(user=api_admin_user)
    return client


@pytest.fixture
def sample_block(db):
    block = ReusableBlock(
        name="Sample Block",
        slug="sample-block",
        content=[{"type": "rich_text", "value": "<p>Hello</p>"}],
    )
    block.save()
    return block


@pytest.fixture
def multiple_blocks(db):
    blocks = []
    for i in range(3):
        block = ReusableBlock(
            name=f"Block {i}",
            slug=f"block-{i}",
            content=[{"type": "rich_text", "value": f"<p>Content {i}</p>"}],
        )
        block.save()
        blocks.append(block)
    return blocks


def _assert_field_types(data):
    """Validate field types for a single block response."""
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["slug"], str)
    assert isinstance(data["content"], list)
    assert isinstance(data["live"], bool)
    assert isinstance(data["created_at"], str)
    assert isinstance(data["updated_at"], str)


class TestListEndpointSchema:
    """GET /api/reusable-blocks/ response schema validation."""

    @pytest.mark.django_db
    def test_list_returns_array(self, api_client, multiple_blocks):
        """Verify that the list endpoint returns an array."""
        response = api_client.get("/api/reusable-blocks/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.django_db
    def test_list_item_has_all_fields(self, api_client, sample_block):
        """Verify that each item in the list contains all expected fields."""
        response = api_client.get("/api/reusable-blocks/")
        data = response.json()
        assert len(data) >= 1
        assert set(data[0].keys()) == LIST_FIELDS

    @pytest.mark.django_db
    def test_list_item_field_types(self, api_client, sample_block):
        """Verify field types for each item in the list."""
        response = api_client.get("/api/reusable-blocks/")
        _assert_field_types(response.json()[0])

    @pytest.mark.django_db
    def test_empty_list(self, api_client, db):
        """Verify that an empty array is returned when no blocks exist."""
        response = api_client.get("/api/reusable-blocks/")
        assert response.status_code == 200
        assert response.json() == []


class TestRetrieveEndpointSchema:
    """GET /api/reusable-blocks/{id}/ response schema validation."""

    @pytest.mark.django_db
    def test_retrieve_has_all_fields(self, api_client, sample_block):
        """Verify that the detail endpoint contains all expected fields."""
        response = api_client.get(f"/api/reusable-blocks/{sample_block.pk}/")
        assert response.status_code == 200
        assert set(response.json().keys()) == DETAIL_FIELDS

    @pytest.mark.django_db
    def test_retrieve_field_types(self, api_client, sample_block):
        """Verify field types of the detail endpoint response."""
        response = api_client.get(f"/api/reusable-blocks/{sample_block.pk}/")
        _assert_field_types(response.json())

    @pytest.mark.django_db
    def test_retrieve_field_values(self, api_client, sample_block):
        """Verify that field values match the model."""
        response = api_client.get(f"/api/reusable-blocks/{sample_block.pk}/")
        data = response.json()
        assert data["id"] == sample_block.pk
        assert data["name"] == "Sample Block"
        assert data["slug"] == "sample-block"

    @pytest.mark.django_db
    def test_retrieve_not_found(self, api_client, db):
        """Verify that a 404 is returned for a non-existent ID."""
        response = api_client.get("/api/reusable-blocks/99999/")
        assert response.status_code == 404


class TestCreateEndpointSchema:
    """POST /api/reusable-blocks/ response schema validation."""

    @pytest.mark.django_db
    def test_create_returns_all_fields(self, api_client):
        """Verify that the creation response contains all expected fields."""
        payload = {
            "name": "New Block",
            "slug": "new-block",
            "content": [{"type": "rich_text", "value": "<p>New</p>"}],
        }
        response = api_client.post("/api/reusable-blocks/", payload, format="json")
        assert response.status_code == 201
        assert set(response.json().keys()) == DETAIL_FIELDS

    @pytest.mark.django_db
    def test_create_field_types(self, api_client):
        """Verify field types of the creation response."""
        payload = {
            "name": "Typed Block",
            "slug": "typed-block",
            "content": [],
        }
        response = api_client.post("/api/reusable-blocks/", payload, format="json")
        assert response.status_code == 201
        _assert_field_types(response.json())

    @pytest.mark.django_db
    def test_create_read_only_fields_ignored(self, api_client):
        """Verify that read-only fields in input are ignored."""
        payload = {
            "name": "Readonly Test",
            "slug": "readonly-test",
            "content": [],
            "id": 99999,
            "live": True,
        }
        response = api_client.post("/api/reusable-blocks/", payload, format="json")
        assert response.status_code == 201
        data = response.json()
        assert data["id"] != 99999

    @pytest.mark.django_db
    def test_create_auto_slug(self, api_client):
        """Verify that slug is auto-generated from the name."""
        payload = {"name": "Auto Slug Test", "content": []}
        response = api_client.post("/api/reusable-blocks/", payload, format="json")
        assert response.status_code == 201
        assert response.json()["slug"] == "auto-slug-test"

    @pytest.mark.django_db
    def test_create_validation_error_schema(self, api_client, sample_block):
        """Verify the response structure of a validation error."""
        payload = {
            "name": "Duplicate",
            "slug": "sample-block",
            "content": [],
        }
        response = api_client.post("/api/reusable-blocks/", payload, format="json")
        assert response.status_code == 400
        data = response.json()
        assert isinstance(data, dict)

    @pytest.mark.django_db
    def test_create_missing_name(self, api_client):
        """Verify that a validation error is returned when name is missing."""
        payload = {"content": []}
        response = api_client.post("/api/reusable-blocks/", payload, format="json")
        assert response.status_code == 400


class TestUpdateEndpointSchema:
    """PUT /api/reusable-blocks/{id}/ response schema validation."""

    @pytest.mark.django_db
    def test_update_returns_all_fields(self, api_client, sample_block):
        """Verify that the update response contains all expected fields."""
        payload = {
            "name": "Updated Block",
            "slug": "updated-block",
            "content": [],
        }
        response = api_client.put(
            f"/api/reusable-blocks/{sample_block.pk}/", payload, format="json"
        )
        assert response.status_code == 200
        assert set(response.json().keys()) == DETAIL_FIELDS

    @pytest.mark.django_db
    def test_update_field_types(self, api_client, sample_block):
        """Verify field types of the update response."""
        payload = {
            "name": "Type Check",
            "slug": "type-check",
            "content": [{"type": "rich_text", "value": "<p>Updated</p>"}],
        }
        response = api_client.put(
            f"/api/reusable-blocks/{sample_block.pk}/", payload, format="json"
        )
        _assert_field_types(response.json())

    @pytest.mark.django_db
    def test_update_reflects_changes(self, api_client, sample_block):
        """Verify that updated values are reflected in the response."""
        payload = {
            "name": "Changed Name",
            "slug": "changed-name",
            "content": [],
        }
        response = api_client.put(
            f"/api/reusable-blocks/{sample_block.pk}/", payload, format="json"
        )
        data = response.json()
        assert data["name"] == "Changed Name"
        assert data["slug"] == "changed-name"
        assert data["id"] == sample_block.pk


class TestPartialUpdateEndpointSchema:
    """PATCH /api/reusable-blocks/{id}/ response schema validation."""

    @pytest.mark.django_db
    def test_partial_update_returns_all_fields(self, api_client, sample_block):
        """Verify that the partial update response contains all expected fields."""
        payload = {"name": "Patched Block"}
        response = api_client.patch(
            f"/api/reusable-blocks/{sample_block.pk}/", payload, format="json"
        )
        assert response.status_code == 200
        assert set(response.json().keys()) == DETAIL_FIELDS

    @pytest.mark.django_db
    def test_partial_update_preserves_unchanged(self, api_client, sample_block):
        """Verify that unchanged fields are preserved during partial update."""
        payload = {"name": "Only Name Changed"}
        response = api_client.patch(
            f"/api/reusable-blocks/{sample_block.pk}/", payload, format="json"
        )
        data = response.json()
        assert data["name"] == "Only Name Changed"
        assert data["slug"] == "sample-block"


class TestDeleteEndpointSchema:
    """DELETE /api/reusable-blocks/{id}/ response schema validation."""

    @pytest.mark.django_db
    def test_delete_returns_204(self, api_client, sample_block):
        """Verify that delete returns 204 No Content."""
        response = api_client.delete(f"/api/reusable-blocks/{sample_block.pk}/")
        assert response.status_code == 204

    @pytest.mark.django_db
    def test_delete_no_body(self, api_client, sample_block):
        """Verify that the delete response has no body."""
        response = api_client.delete(f"/api/reusable-blocks/{sample_block.pk}/")
        assert response.content == b""

    @pytest.mark.django_db
    def test_delete_not_found(self, api_client, db):
        """Verify that deleting a non-existent ID returns 404."""
        response = api_client.delete("/api/reusable-blocks/99999/")
        assert response.status_code == 404


class TestContentFieldSchema:
    """content field (StreamField JSON) schema validation."""

    @pytest.mark.django_db
    def test_content_is_list(self, api_client, sample_block):
        """Verify that the content field is a list."""
        response = api_client.get(f"/api/reusable-blocks/{sample_block.pk}/")
        assert isinstance(response.json()["content"], list)

    @pytest.mark.django_db
    def test_empty_content(self, api_client):
        """Verify that a block can be created with empty content."""
        payload = {"name": "Empty Content", "slug": "empty-content", "content": []}
        response = api_client.post("/api/reusable-blocks/", payload, format="json")
        assert response.status_code == 201
        assert response.json()["content"] == []

    @pytest.mark.django_db
    def test_content_with_stream_blocks(self, api_client, sample_block):
        """Verify that the content field contains StreamBlock structure."""
        response = api_client.get(f"/api/reusable-blocks/{sample_block.pk}/")
        content = response.json()["content"]
        assert len(content) >= 1
        block = content[0]
        assert "type" in block
        assert "value" in block
        assert "id" in block


class TestAuthenticationSchema:
    """Unauthenticated request response schema validation."""

    @pytest.mark.django_db
    def test_unauthenticated_list(self, db):
        """Verify that an unauthenticated list request returns 403."""
        client = APIClient()
        response = client.get("/api/reusable-blocks/")
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_unauthenticated_create(self, db):
        """Verify that an unauthenticated create request returns 403."""
        client = APIClient()
        payload = {"name": "Unauth", "slug": "unauth", "content": []}
        response = client.post("/api/reusable-blocks/", payload, format="json")
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_unauthenticated_error_schema(self, db):
        """Verify that the unauthenticated error response contains a detail field."""
        client = APIClient()
        response = client.get("/api/reusable-blocks/")
        data = response.json()
        assert "detail" in data
