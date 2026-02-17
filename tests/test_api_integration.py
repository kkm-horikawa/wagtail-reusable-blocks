"""Integration tests for API endpoints (Issue #207).

Tests Wagtail API v2 (read-only) and DRF CRUD endpoints
using Django TestClient with real database.
"""

import pytest
from django.test import Client

from wagtail_reusable_blocks.models import ReusableBlock


@pytest.fixture
def api_client():
    return Client()


@pytest.fixture
def live_block(db):
    block = ReusableBlock.objects.create(
        name="Live Block",
        slug="live-block",
        content=[{"type": "rich_text", "value": "<p>Live content</p>"}],
    )
    return block


@pytest.fixture
def draft_block(db):
    block = ReusableBlock.objects.create(
        name="Draft Block",
        slug="draft-block",
        content=[{"type": "rich_text", "value": "<p>Draft content</p>"}],
    )
    block.live = False
    block.save(update_fields=["live"])
    return block


class TestWagtailAPIv2List:
    """Wagtail API v2 list endpoint tests."""

    @pytest.mark.django_db
    def test_list_returns_only_live_blocks(self, api_client, live_block, draft_block):
        """GET /api/v2/reusable-blocks/ returns only live=True blocks.

        Purpose: Verify that the Wagtail API v2 list endpoint returns only
                 published blocks, ensuring draft blocks are not leaked via
                 the public API.
        Type: Normal
        Technique: API endpoint
        Integration: GET /api/v2/reusable-blocks/ -> ReusableBlockAPIViewSet -> Database
        Test data:
        - 1 block with live=True
        - 1 block with live=False
        Scenario:
        1. Create one live block and one draft block
        2. Call GET /api/v2/reusable-blocks/
        3. Verify that response is 200 and contains only the live block
        """
        response = api_client.get("/api/v2/reusable-blocks/")

        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["total_count"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Live Block"


class TestWagtailAPIv2Detail:
    """Wagtail API v2 detail endpoint tests."""

    @pytest.mark.django_db
    def test_detail_returns_live_block(self, api_client, live_block):
        """GET /api/v2/reusable-blocks/<id>/ returns detail of a live block.

        Purpose: Verify that the Wagtail API v2 detail endpoint returns all
                 fields for a published block.
        Type: Normal
        Technique: API endpoint
        Integration: GET /api/v2/reusable-blocks/<id>/ -> ReusableBlockAPIViewSet -> Database
        Test data:
        - 1 block with live=True
        Scenario:
        1. Create a live block
        2. Call GET /api/v2/reusable-blocks/<id>/
        3. Verify that response is 200 and contains expected fields
        """
        response = api_client.get(f"/api/v2/reusable-blocks/{live_block.pk}/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Live Block"
        assert data["slug"] == "live-block"
        assert data["live"] is True

    @pytest.mark.django_db
    def test_detail_draft_block_returns_404(self, api_client, draft_block):
        """GET /api/v2/reusable-blocks/<id>/ returns 404 for live=False blocks.

        Purpose: Verify that unpublished blocks cannot be accessed via the
                 public API, ensuring content publication control.
        Type: Error
        Technique: API endpoint
        Integration: GET /api/v2/reusable-blocks/<id>/ -> ReusableBlockAPIViewSet -> Database
        Test data:
        - 1 block with live=False (default state)
        Scenario:
        1. Create a draft block
        2. Call GET /api/v2/reusable-blocks/<id>/
        3. Verify that response is 404
        """
        response = api_client.get(f"/api/v2/reusable-blocks/{draft_block.pk}/")

        assert response.status_code == 404


class TestWagtailAPIv2ResponseFields:
    """Wagtail API v2 response field tests."""

    @pytest.mark.django_db
    def test_listing_contains_expected_fields(self, api_client, live_block):
        """GET /api/v2/reusable-blocks/ response contains expected fields.

        Purpose: Verify that the list endpoint response structure matches
                 the API contract.
        Type: Normal
        Technique: API endpoint
        Integration: GET /api/v2/reusable-blocks/ -> ReusableBlockAPIViewSet -> Serializer
        Test data:
        - 1 block with live=True
        Scenario:
        1. Call GET /api/v2/reusable-blocks/
        2. Verify each item contains name, slug, live, and updated_at
        """
        response = api_client.get("/api/v2/reusable-blocks/")

        assert response.status_code == 200
        data = response.json()
        item = data["items"][0]
        assert "name" in item
        assert "slug" in item
        assert "live" in item
        assert "updated_at" in item

    @pytest.mark.django_db
    def test_detail_contains_all_body_fields(self, api_client, live_block):
        """GET /api/v2/reusable-blocks/<id>/ response contains all body_fields.

        Purpose: Verify that the detail endpoint response includes content,
                 created_at, and other body_fields.
        Type: Normal
        Technique: API endpoint
        Integration: GET /api/v2/reusable-blocks/<id>/ -> ReusableBlockAPIViewSet -> Serializer
        Test data:
        - 1 block with live=True
        Scenario:
        1. Call GET /api/v2/reusable-blocks/<id>/
        2. Verify response contains name, slug, content, live, created_at, and updated_at
        """
        response = api_client.get(f"/api/v2/reusable-blocks/{live_block.pk}/")

        assert response.status_code == 200
        data = response.json()
        for field in ["name", "slug", "content", "live", "created_at", "updated_at"]:
            assert field in data, f"Field '{field}' missing from detail response"


class TestDRFListEndpoint:
    """DRF CRUD list endpoint tests."""

    @pytest.mark.django_db
    def test_authenticated_user_can_list_blocks(
        self, api_client, admin_user, live_block
    ):
        """GET /api/reusable-blocks/ returns a list for authenticated users.

        Purpose: Verify that an authenticated user can retrieve a block list
                 via the DRF CRUD endpoint.
        Type: Normal
        Technique: API endpoint, authentication/authorization
        Integration: GET /api/reusable-blocks/ -> ReusableBlockModelViewSet -> Database
        Test data:
        - Admin user
        - 1 block with live=True
        Scenario:
        1. Log in as admin
        2. Call GET /api/reusable-blocks/
        3. Verify response is 200 and contains a block list
        """
        api_client.force_login(admin_user)

        response = api_client.get("/api/reusable-blocks/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @pytest.mark.django_db
    def test_unauthenticated_user_gets_forbidden(self, api_client, live_block):
        """GET /api/reusable-blocks/ returns 403 for unauthenticated users.

        Purpose: Verify that unauthenticated users cannot access the DRF CRUD
                 endpoint, ensuring authentication/authorization requirements.
        Type: Error
        Technique: Authentication/authorization
        Integration: GET /api/reusable-blocks/ -> IsAuthenticated -> 403
        Test data:
        - 1 block (accessed without authentication)
        Scenario:
        1. Call GET /api/reusable-blocks/ without login
        2. Verify response is 403
        """
        response = api_client.get("/api/reusable-blocks/")

        assert response.status_code == 403


class TestDRFCreateEndpoint:
    """DRF CRUD create endpoint tests."""

    @pytest.mark.django_db
    def test_create_block_with_name_and_content(self, api_client, admin_user):
        """POST /api/reusable-blocks/ creates a block.

        Purpose: Verify that an authenticated user can create a block with
                 name and content JSON, and it is saved to the database.
        Type: Normal
        Technique: API endpoint
        Integration: POST /api/reusable-blocks/ -> ReusableBlockSerializer -> Database
        Test data:
        - Admin user
        - name: "API Block", content: StreamField JSON
        Scenario:
        1. Log in as admin
        2. POST to /api/reusable-blocks/ with name and content
        3. Verify response is 201 and returns created block data
        4. Verify block is saved in the database
        """
        api_client.force_login(admin_user)

        response = api_client.post(
            "/api/reusable-blocks/",
            data={
                "name": "API Block",
                "content": [{"type": "rich_text", "value": "<p>API content</p>"}],
            },
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Block"
        assert data["id"] is not None
        assert ReusableBlock.objects.filter(name="API Block").exists()

    @pytest.mark.django_db
    def test_create_block_auto_generates_slug(self, api_client, admin_user):
        """POST /api/reusable-blocks/ auto-generates slug from name.

        Purpose: Verify that slug is automatically generated when only name
                 is provided during block creation.
        Type: Normal
        Technique: API endpoint
        Integration: POST /api/reusable-blocks/ -> ReusableBlockSerializer.validate -> Database
        Test data:
        - Admin user
        - name: "Auto Slug Block" (slug not specified)
        Scenario:
        1. Log in as admin
        2. POST to /api/reusable-blocks/ without slug
        3. Verify the slug is auto-generated from the name
        """
        api_client.force_login(admin_user)

        response = api_client.post(
            "/api/reusable-blocks/",
            data={"name": "Auto Slug Block", "content": []},
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["slug"] == "auto-slug-block"

    @pytest.mark.django_db
    def test_create_block_slug_duplicate_returns_400(self, api_client, admin_user):
        """POST /api/reusable-blocks/ returns 400 for duplicate slug.

        Purpose: Verify that duplicate slug returns a validation error (400)
                 instead of IntegrityError, providing proper error messages
                 to API consumers.
        Type: Error
        Technique: API endpoint
        Integration: POST /api/reusable-blocks/ -> ReusableBlockSerializer.validate -> 400
        Test data:
        - Admin user
        - Existing block with slug: "existing-block"
        - New block creation attempt with same slug
        Scenario:
        1. Create a block with slug="existing-block"
        2. POST to /api/reusable-blocks/ with the same slug
        3. Verify response is 400 with slug error message
        """
        ReusableBlock.objects.create(name="Existing Block", slug="existing-block")
        api_client.force_login(admin_user)

        response = api_client.post(
            "/api/reusable-blocks/",
            data={"name": "New Block", "slug": "existing-block", "content": []},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.json()
        assert "slug" in data

    @pytest.mark.django_db
    def test_create_block_empty_name_returns_400(self, api_client, admin_user):
        """POST /api/reusable-blocks/ returns 400 for empty name.

        Purpose: Verify that a validation error is returned when name is empty.
        Type: Error
        Technique: API endpoint
        Integration: POST /api/reusable-blocks/ -> ReusableBlockSerializer -> 400
        Test data:
        - Admin user
        - name: "" (empty string)
        Scenario:
        1. Log in as admin
        2. POST to /api/reusable-blocks/ with empty name
        3. Verify response is 400
        """
        api_client.force_login(admin_user)

        response = api_client.post(
            "/api/reusable-blocks/",
            data={"name": "", "content": []},
            content_type="application/json",
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_create_duplicate_name_blocks_returns_slug_error(
        self, api_client, admin_user
    ):
        """Creating two blocks with the same name returns slug duplicate error (400, not IntegrityError).

        Purpose: Verify that when creating two blocks with the same name,
                 auto-generated slug duplication returns 400 instead of IntegrityError.
        Type: Error
        Technique: API endpoint
        Integration: POST /api/reusable-blocks/ -> ReusableBlockSerializer.validate -> 400
        Test data:
        - Admin user
        - Existing block with name: "Same Name"
        - New block creation attempt with same name
        Scenario:
        1. Create a block with name="Same Name" via API
        2. POST to /api/reusable-blocks/ with the same name again
        3. Verify response is 400 (not IntegrityError)
        """
        api_client.force_login(admin_user)

        response1 = api_client.post(
            "/api/reusable-blocks/",
            data={"name": "Same Name", "content": []},
            content_type="application/json",
        )
        assert response1.status_code == 201

        response2 = api_client.post(
            "/api/reusable-blocks/",
            data={"name": "Same Name", "content": []},
            content_type="application/json",
        )
        assert response2.status_code == 400

    @pytest.mark.django_db
    def test_create_block_with_streamfield_json_content(self, api_client, admin_user):
        """StreamField JSON data is correctly saved when submitted.

        Purpose: Verify that StreamField JSON format content is correctly
                 saved and retrievable.
        Type: Normal
        Technique: API endpoint
        Integration: POST /api/reusable-blocks/ -> ReusableBlockSerializer -> StreamField -> Database
        Test data:
        - Admin user
        - StreamField JSON with multiple block types
        Scenario:
        1. Log in as admin
        2. POST to /api/reusable-blocks/ with StreamField JSON content
        3. Verify response is 201
        4. Verify content is saved in the database
        """
        api_client.force_login(admin_user)

        content_data = [
            {"type": "rich_text", "value": "<p>First paragraph</p>"},
            {"type": "raw_html", "value": "<div class='custom'>Custom HTML</div>"},
        ]

        response = api_client.post(
            "/api/reusable-blocks/",
            data={"name": "StreamField Block", "content": content_data},
            content_type="application/json",
        )

        assert response.status_code == 201
        block = ReusableBlock.objects.get(slug="streamfield-block")
        assert len(block.content) == 2


class TestDRFDetailEndpoint:
    """DRF CRUD detail endpoint tests."""

    @pytest.mark.django_db
    def test_retrieve_block_by_id(self, api_client, admin_user, live_block):
        """GET /api/reusable-blocks/<id>/ retrieves a single block.

        Purpose: Verify that a block detail can be retrieved by ID.
        Type: Normal
        Technique: API endpoint
        Integration: GET /api/reusable-blocks/<id>/ -> ReusableBlockModelViewSet -> Database
        Test data:
        - Admin user
        - 1 block with live=True
        Scenario:
        1. Log in as admin
        2. Call GET /api/reusable-blocks/<id>/
        3. Verify response is 200 and returns expected block data
        """
        api_client.force_login(admin_user)

        response = api_client.get(f"/api/reusable-blocks/{live_block.pk}/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Live Block"
        assert data["slug"] == "live-block"
        assert data["id"] == live_block.pk


class TestDRFUpdateEndpoint:
    """DRF CRUD update endpoint tests."""

    @pytest.mark.django_db
    def test_put_updates_all_fields(self, api_client, admin_user, live_block):
        """PUT /api/reusable-blocks/<id>/ updates all fields.

        Purpose: Verify that a PUT request updates all fields and the
                 changes are reflected in the database.
        Type: Normal
        Technique: API endpoint
        Integration: PUT /api/reusable-blocks/<id>/ -> ReusableBlockSerializer -> Database
        Test data:
        - Admin user
        - Existing live block
        Scenario:
        1. Log in as admin
        2. PUT to /api/reusable-blocks/<id>/ with all fields
        3. Verify response is 200 and returns updated data
        4. Verify the database block is updated
        """
        api_client.force_login(admin_user)

        response = api_client.put(
            f"/api/reusable-blocks/{live_block.pk}/",
            data={
                "name": "Updated Block",
                "slug": "updated-block",
                "content": [{"type": "rich_text", "value": "<p>Updated</p>"}],
            },
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Block"
        assert data["slug"] == "updated-block"

        live_block.refresh_from_db()
        assert live_block.name == "Updated Block"

    @pytest.mark.django_db
    def test_patch_partial_update(self, api_client, admin_user, live_block):
        """PATCH /api/reusable-blocks/<id>/ performs partial update.

        Purpose: Verify that a PATCH request updates only specified fields
                 while leaving other fields unchanged.
        Type: Normal
        Technique: API endpoint
        Integration: PATCH /api/reusable-blocks/<id>/ -> ReusableBlockSerializer -> Database
        Test data:
        - Admin user
        - Existing live block
        Scenario:
        1. Log in as admin
        2. PATCH to /api/reusable-blocks/<id>/ with name only
        3. Verify name is updated and slug remains unchanged
        """
        api_client.force_login(admin_user)

        response = api_client.patch(
            f"/api/reusable-blocks/{live_block.pk}/",
            data={"name": "Patched Block"},
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Patched Block"
        assert data["slug"] == "live-block"

    @pytest.mark.django_db
    def test_put_nonexistent_id_returns_404(self, api_client, admin_user):
        """PUT /api/reusable-blocks/<id>/ returns 404 for non-existent ID.

        Purpose: Verify that a PUT request for a non-existent ID returns 404.
        Type: Error
        Technique: API endpoint
        Integration: PUT /api/reusable-blocks/<id>/ -> 404
        Test data:
        - Admin user
        - Non-existent ID: 99999
        Scenario:
        1. Log in as admin
        2. PUT to /api/reusable-blocks/99999/
        3. Verify response is 404
        """
        api_client.force_login(admin_user)

        response = api_client.put(
            "/api/reusable-blocks/99999/",
            data={
                "name": "Ghost Block",
                "slug": "ghost-block",
                "content": [],
            },
            content_type="application/json",
        )

        assert response.status_code == 404


class TestDRFDeleteEndpoint:
    """DRF CRUD delete endpoint tests."""

    @pytest.mark.django_db
    def test_delete_removes_block(self, api_client, admin_user, live_block):
        """DELETE /api/reusable-blocks/<id>/ deletes the block.

        Purpose: Verify that a DELETE request removes the block from the database.
        Type: Normal
        Technique: API endpoint
        Integration: DELETE /api/reusable-blocks/<id>/ -> ReusableBlockModelViewSet -> Database
        Test data:
        - Admin user
        - Existing live block
        Scenario:
        1. Log in as admin
        2. DELETE /api/reusable-blocks/<id>/
        3. Verify response is 204
        4. Verify block is removed from the database
        """
        api_client.force_login(admin_user)
        block_pk = live_block.pk

        response = api_client.delete(f"/api/reusable-blocks/{block_pk}/")

        assert response.status_code == 204
        assert not ReusableBlock.objects.filter(pk=block_pk).exists()


class TestDRFFilterEndpoints:
    """DRF CRUD filter endpoint tests."""

    @pytest.mark.django_db
    def test_filter_by_slug(self, api_client, admin_user, live_block, draft_block):
        """GET /api/reusable-blocks/?slug=xxx filters by slug.

        Purpose: Verify that blocks can be filtered by the slug parameter.
        Type: Normal
        Technique: API endpoint
        Integration: GET /api/reusable-blocks/?slug=xxx -> get_queryset -> Database
        Test data:
        - Admin user
        - Multiple blocks
        Scenario:
        1. Log in as admin
        2. Call GET /api/reusable-blocks/?slug=live-block
        3. Verify only the block with slug=live-block is returned
        """
        api_client.force_login(admin_user)

        response = api_client.get("/api/reusable-blocks/?slug=live-block")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["slug"] == "live-block"

    @pytest.mark.django_db
    def test_filter_by_live(self, api_client, admin_user, live_block, draft_block):
        """GET /api/reusable-blocks/?live=true filters by live status.

        Purpose: Verify that blocks can be filtered by the live parameter.
        Type: Normal
        Technique: API endpoint
        Integration: GET /api/reusable-blocks/?live=true -> get_queryset -> Database
        Test data:
        - Admin user
        - 1 block with live=True, 1 block with live=False
        Scenario:
        1. Log in as admin
        2. Call GET /api/reusable-blocks/?live=true
        3. Verify only the live block is returned
        """
        api_client.force_login(admin_user)

        response = api_client.get("/api/reusable-blocks/?live=true")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Live Block"

    @pytest.mark.django_db
    def test_search_by_name(self, api_client, admin_user):
        """GET /api/reusable-blocks/?search=xxx searches by name.

        Purpose: Verify that blocks can be searched by the search parameter.
        Type: Normal
        Technique: API endpoint
        Integration: GET /api/reusable-blocks/?search=xxx -> get_queryset -> Database
        Test data:
        - Admin user
        - 3 blocks with different names
        Scenario:
        1. Create 3 blocks with different names
        2. Log in as admin
        3. Call GET /api/reusable-blocks/?search=header
        4. Verify only blocks containing "header" in name are returned
        """
        ReusableBlock.objects.create(name="Header Block", slug="header-block")
        ReusableBlock.objects.create(name="Footer Block", slug="footer-block")
        ReusableBlock.objects.create(name="Main Header", slug="main-header")
        api_client.force_login(admin_user)

        response = api_client.get("/api/reusable-blocks/?search=header")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        names = {item["name"] for item in data}
        assert names == {"Header Block", "Main Header"}
