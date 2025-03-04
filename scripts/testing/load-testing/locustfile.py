from locust import HttpUser, task, between
from locust.contrib.fasthttp import FastHttpUser
import json
import random

class JustMailyUser(FastHttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Log in at the start of each user session."""
        self.login()
        self.get_campaigns()

    def login(self):
        """Authenticate user."""
        response = self.client.post("/api/auth/login", json={
            "email": f"user{random.randint(1, 1000)}@example.com",
            "password": "testpassword123"
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.client.headers = {"Authorization": f"Bearer {self.token}"}

    def get_campaigns(self):
        """Get user's campaigns."""
        response = self.client.get("/api/campaigns")
        if response.status_code == 200:
            self.campaigns = response.json()

    @task(3)
    def view_dashboard(self):
        """View dashboard with analytics."""
        self.client.get("/api/dashboard/stats")
        self.client.get("/api/dashboard/recent-campaigns")
        self.client.get("/api/dashboard/performance")

    @task(2)
    def create_campaign(self):
        """Create a new campaign."""
        campaign_data = {
            "name": f"Test Campaign {random.randint(1, 1000)}",
            "subject": "Test Subject",
            "content": "Test content for email campaign",
            "segment_id": "all",
            "schedule": None
        }
        self.client.post("/api/campaigns", json=campaign_data)

    @task(2)
    def view_campaign_stats(self):
        """View campaign statistics."""
        if hasattr(self, 'campaigns') and self.campaigns:
            campaign = random.choice(self.campaigns)
            self.client.get(f"/api/campaigns/{campaign['id']}/stats")
            self.client.get(f"/api/campaigns/{campaign['id']}/clicks")
            self.client.get(f"/api/campaigns/{campaign['id']}/opens")

    @task(1)
    def manage_subscribers(self):
        """Manage subscriber lists."""
        # Get subscribers
        self.client.get("/api/subscribers")

        # Add new subscriber
        subscriber_data = {
            "email": f"subscriber{random.randint(1, 1000)}@example.com",
            "name": "Test Subscriber",
            "custom_fields": {
                "company": "Test Company",
                "role": "Test Role"
            }
        }
        self.client.post("/api/subscribers", json=subscriber_data)

    @task(1)
    def use_ai_features(self):
        """Use AI-powered features."""
        prompt_data = {
            "type": "email_subject",
            "context": "Black Friday sale promotion",
            "tone": "professional",
            "length": "short"
        }
        self.client.post("/api/ai/generate", json=prompt_data)

    @task(1)
    def manage_templates(self):
        """Work with email templates."""
        # Get templates
        self.client.get("/api/templates")

        # Create template
        template_data = {
            "name": f"Test Template {random.randint(1, 1000)}",
            "subject": "Test Subject",
            "content": "<h1>Test Template</h1><p>{{content}}</p>",
            "category": "promotional"
        }
        self.client.post("/api/templates", json=template_data)

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def view_home(self):
        """View homepage and main sections."""
        self.client.get("/")
        self.client.get("/features")
        self.client.get("/pricing")

    @task(1)
    def view_docs(self):
        """Browse documentation."""
        self.client.get("/docs")
        self.client.get("/docs/api")
        self.client.get("/docs/guides")

class APIUser(FastHttpUser):
    wait_time = between(0.1, 1)

    def on_start(self):
        """Set up API authentication."""
        self.client.headers = {
            "X-API-Key": f"test-api-key-{random.randint(1, 100)}"
        }

    @task(3)
    def api_requests(self):
        """Make API requests."""
        self.client.get("/api/health")
        self.client.get("/api/status")

        campaign_data = {
            "name": f"API Campaign {random.randint(1, 1000)}",
            "subject": "API Test",
            "content": "Test content",
            "recipients": ["test@example.com"]
        }
        self.client.post("/api/campaigns", json=campaign_data)
