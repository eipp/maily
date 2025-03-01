import pytest
from playwright.sync_api import Page, expect
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test data
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "test@example.com")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "TestPassword123!")
TEST_CAMPAIGN_NAME = "E2E Test AI Campaign"
TEST_CAMPAIGN_SUBJECT = "E2E Test Subject Line"
TEST_CAMPAIGN_AUDIENCE = "Test Audience"


@pytest.mark.e2e
def test_ai_campaign_creation_flow(page: Page):
    """
    End-to-end test for the AI campaign creation flow.

    This test covers:
    1. User login
    2. Navigation to campaign creation
    3. Creating a new AI-assisted campaign
    4. Verifying AI suggestions
    5. Finalizing and saving the campaign
    """
    # Step 1: Login
    login_user(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    # Step 2: Navigate to campaigns page
    page.click("text=Campaigns")
    expect(page).to_have_url("/campaigns")

    # Step 3: Click on "Create Campaign" button
    page.click("text=Create Campaign")
    expect(page).to_have_url("/campaigns/new")

    # Step 4: Fill in campaign details
    page.fill("input[name='campaign-name']", TEST_CAMPAIGN_NAME)
    page.fill("input[name='campaign-subject']", TEST_CAMPAIGN_SUBJECT)

    # Step 5: Select audience
    page.click("text=Select Audience")
    page.click(f"text={TEST_CAMPAIGN_AUDIENCE}")

    # Step 6: Select AI-assisted campaign
    page.click("text=AI-Assisted")

    # Step 7: Fill in campaign goals
    page.fill("textarea[name='campaign-goals']", "Increase product awareness and drive sales for our new product line.")

    # Step 8: Click "Generate Content" button
    page.click("text=Generate Content")

    # Step 9: Wait for AI to generate content (with timeout)
    page.wait_for_selector("text=AI Suggestions", timeout=30000)

    # Step 10: Verify AI suggestions are displayed
    expect(page.locator(".ai-suggestion-card")).to_have_count(3)

    # Step 11: Select the first suggestion
    page.click(".ai-suggestion-card >> nth=0")

    # Step 12: Customize the content
    page.click("text=Customize")

    # Step 13: Edit the content
    editor_frame = page.frame_locator(".tiptap-editor iframe")
    editor_frame.locator("body").click()
    editor_frame.locator("body").type(" This is additional content added during the E2E test.")

    # Step 14: Save the campaign
    page.click("text=Save Campaign")

    # Step 15: Wait for success message
    page.wait_for_selector("text=Campaign saved successfully", timeout=10000)

    # Step 16: Verify we're redirected to the campaign detail page
    expect(page.url).to_contain("/campaigns/")
    expect(page).not_to_have_url("/campaigns/new")

    # Step 17: Verify campaign details are displayed correctly
    expect(page.locator("h1")).to_have_text(TEST_CAMPAIGN_NAME)
    expect(page.locator(".campaign-subject")).to_have_text(TEST_CAMPAIGN_SUBJECT)

    # Step 18: Clean up - delete the test campaign
    page.click("text=Delete Campaign")
    page.click("text=Confirm")

    # Step 19: Verify we're redirected to the campaigns list
    expect(page).to_have_url("/campaigns")

    # Step 20: Verify the campaign is no longer in the list
    expect(page.locator(f"text={TEST_CAMPAIGN_NAME}")).to_have_count(0)


@pytest.mark.e2e
def test_ai_campaign_with_custom_prompt(page: Page):
    """
    End-to-end test for creating an AI campaign with a custom prompt.

    This test covers:
    1. User login
    2. Navigation to campaign creation
    3. Creating a new AI-assisted campaign with a custom prompt
    4. Verifying AI response to the custom prompt
    5. Finalizing and saving the campaign
    """
    # Step 1: Login
    login_user(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    # Step 2: Navigate to campaigns page
    page.click("text=Campaigns")
    expect(page).to_have_url("/campaigns")

    # Step 3: Click on "Create Campaign" button
    page.click("text=Create Campaign")
    expect(page).to_have_url("/campaigns/new")

    # Step 4: Fill in campaign details
    page.fill("input[name='campaign-name']", f"{TEST_CAMPAIGN_NAME} - Custom Prompt")
    page.fill("input[name='campaign-subject']", f"{TEST_CAMPAIGN_SUBJECT} - Custom")

    # Step 5: Select audience
    page.click("text=Select Audience")
    page.click(f"text={TEST_CAMPAIGN_AUDIENCE}")

    # Step 6: Select AI-assisted campaign
    page.click("text=AI-Assisted")

    # Step 7: Click on "Custom Prompt" option
    page.click("text=Custom Prompt")

    # Step 8: Fill in custom prompt
    page.fill("textarea[name='custom-prompt']", "Create an email campaign for a summer sale with 30% off all products. Include a sense of urgency and focus on limited time availability.")

    # Step 9: Click "Generate Content" button
    page.click("text=Generate Content")

    # Step 10: Wait for AI to generate content (with timeout)
    page.wait_for_selector("text=AI Response", timeout=30000)

    # Step 11: Verify AI response is displayed and contains expected content
    ai_response = page.locator(".ai-response-content").text_content()
    assert "summer sale" in ai_response.lower()
    assert "30%" in ai_response

    # Step 12: Apply the AI response
    page.click("text=Apply")

    # Step 13: Save the campaign
    page.click("text=Save Campaign")

    # Step 14: Wait for success message
    page.wait_for_selector("text=Campaign saved successfully", timeout=10000)

    # Step 15: Verify we're redirected to the campaign detail page
    expect(page.url).to_contain("/campaigns/")

    # Step 16: Clean up - delete the test campaign
    page.click("text=Delete Campaign")
    page.click("text=Confirm")

    # Step 17: Verify we're redirected to the campaigns list
    expect(page).to_have_url("/campaigns")


def login_user(page: Page, email: str, password: str):
    """Helper function to log in a user."""
    # Navigate to login page
    page.goto("/login")

    # Fill in login form
    page.fill("input[name='email']", email)
    page.fill("input[name='password']", password)

    # Submit form
    page.click("button[type='submit']")

    # Wait for navigation to complete
    page.wait_for_url("/dashboard")

    # Verify we're logged in
    expect(page).to_have_url("/dashboard")
