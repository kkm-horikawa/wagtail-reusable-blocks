"""E2E tests for API-created content rendering in Wagtail admin.

Verifies that ReusableBlocks created via the DRF API render correctly
in the Wagtail admin snippet editing and preview views.
"""

import pytest
import requests
from playwright.sync_api import Page, expect


@pytest.fixture
def authenticated_page(page: Page, live_server, admin_user) -> Page:
    """Login to Wagtail admin and return authenticated page."""
    page.goto(f"{live_server.url}/login/")
    page.locator("#id_username").fill("admin")
    page.locator("#id_password").fill("password")
    page.locator("button[type='submit']").click()
    page.wait_for_url(f"{live_server.url}/**")
    return page


@pytest.fixture
def api_session(live_server, admin_user) -> requests.Session:
    """Authenticated requests.Session for DRF API calls against live_server."""
    session = requests.Session()
    login_url = f"{live_server.url}/login/"
    resp = session.get(login_url)
    csrftoken = resp.cookies.get("csrftoken", "")
    session.post(
        login_url,
        data={
            "username": "admin",
            "password": "password",
            "csrfmiddlewaretoken": csrftoken,
        },
        headers={"Referer": login_url},
    )
    return session


def _create_block_via_api(
    session: requests.Session,
    base_url: str,
    name: str,
    content: list,
    slug: str | None = None,
) -> dict:
    """Create a ReusableBlock via the DRF API."""
    payload: dict = {"name": name, "content": content}
    if slug:
        payload["slug"] = slug
    csrftoken = session.cookies.get("csrftoken", "")
    resp = session.post(
        f"{base_url}/api/reusable-blocks/",
        json=payload,
        headers={
            "X-CSRFToken": csrftoken,
            "Referer": base_url,
        },
    )
    assert resp.status_code == 201, f"API create failed: {resp.status_code} {resp.text}"
    return resp.json()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_api_created_blocks_render_in_admin(
    authenticated_page: Page,
    api_session: requests.Session,
    live_server,
):
    """API-created rich_text and raw_html blocks render correctly in admin preview.

    Purpose: Verify that ReusableBlocks created via the DRF API (rich_text
             and raw_html) appear in the Wagtail admin snippet listing and
             render correctly in the edit view preview, ensuring the end-to-end
             headless CMS use case.
    Type: Normal
    Technique: Critical path, user journey
    User flow: API creation -> Admin login -> Listing check -> Edit view preview
    Prerequisites:
    - Django live_server is running
    - DRF CRUD endpoint is available at /api/reusable-blocks/
    Test data:
    - ReusableBlock with rich_text (created via API)
    - ReusableBlock with raw_html (created via API)
    Steps:
    1. Create a rich_text block via DRF API
    2. Create a raw_html block via DRF API
    3. Navigate to the snippet listing page while logged in to Wagtail admin
    4. Verify both blocks appear in the listing
    5. Open the rich_text block edit page and check the preview content
    6. Open the raw_html block edit page and check the preview content
    Expected results:
    - Both blocks appear in the listing
    - rich_text preview shows the paragraph text
    - raw_html preview shows the custom HTML
    """
    page = authenticated_page
    base_url = live_server.url

    # --- Step 1: Create rich_text block via API ---
    rich_block = _create_block_via_api(
        api_session,
        base_url,
        name="E2E Rich Text Block",
        slug="e2e-rich-text",
        content=[
            {
                "type": "rich_text",
                "value": "<p>Hello from the API</p>",
            }
        ],
    )
    rich_block_id = rich_block["id"]

    # --- Step 2: Create raw_html block via API ---
    raw_block = _create_block_via_api(
        api_session,
        base_url,
        name="E2E Raw HTML Block",
        slug="e2e-raw-html",
        content=[
            {
                "type": "raw_html",
                "value": (
                    '<div class="hero-banner">'
                    "<h1>Welcome</h1>"
                    "<p>Custom HTML content</p>"
                    "</div>"
                ),
            }
        ],
    )
    raw_block_id = raw_block["id"]

    # --- Step 3: Navigate to snippet listing ---
    listing_url = f"{base_url}/snippets/wagtail_reusable_blocks/reusableblock/"
    page.goto(listing_url)
    page.wait_for_load_state("networkidle")

    # --- Step 4: Both blocks appear in the listing ---
    expect(page.get_by_role("link", name="E2E Rich Text Block")).to_be_visible(
        timeout=10000
    )
    expect(page.get_by_role("link", name="E2E Raw HTML Block")).to_be_visible(
        timeout=10000
    )

    # --- Step 5: Open rich_text block edit and check preview ---
    edit_url = (
        f"{base_url}/snippets/wagtail_reusable_blocks/"
        f"reusableblock/edit/{rich_block_id}/"
    )
    page.goto(edit_url)
    page.wait_for_load_state("networkidle")

    preview_button = page.locator(
        "button:has-text('Preview'), [data-side-panel-toggle='preview']"
    ).first
    expect(preview_button).to_be_visible(timeout=10000)
    preview_button.click()

    preview_frame = page.frame_locator("[data-side-panel='preview'] iframe[src]")
    expect(preview_frame.locator("body")).to_contain_text(
        "Hello from the API", timeout=15000
    )

    # --- Step 6: Open raw_html block edit and check preview ---
    edit_url = (
        f"{base_url}/snippets/wagtail_reusable_blocks/"
        f"reusableblock/edit/{raw_block_id}/"
    )
    page.goto(edit_url)
    page.wait_for_load_state("networkidle")

    preview_button = page.locator(
        "button:has-text('Preview'), [data-side-panel-toggle='preview']"
    ).first
    expect(preview_button).to_be_visible(timeout=10000)
    preview_button.click()

    preview_frame = page.frame_locator("[data-side-panel='preview'] iframe[src]")
    expect(preview_frame.locator("body")).to_contain_text("Welcome", timeout=15000)
    expect(preview_frame.locator("body")).to_contain_text(
        "Custom HTML content", timeout=15000
    )
