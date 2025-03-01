import strawberry
from typing import List, Optional
from datetime import datetime
from strawberry.fastapi import GraphQLRouter


# User Type Definition
@strawberry.type
class User:
    id: str
    email: str
    name: Optional[str] = None
    created_at: datetime


# Campaign Type Definition
@strawberry.type
class Campaign:
    id: str
    name: str
    subject: str
    status: str
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    open_rate: Optional[float] = None
    click_rate: Optional[float] = None
    total_recipients: int


# Subscriber Type Definition
@strawberry.type
class Subscriber:
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: str
    created_at: datetime
    tags: List[str]


# Template Type Definition
@strawberry.type
class Template:
    id: str
    name: str
    description: Optional[str] = None
    content: str
    created_at: datetime
    updated_at: datetime


# Input Types for Mutations
@strawberry.input
class CampaignInput:
    name: str
    subject: str
    content: str
    scheduled_at: Optional[datetime] = None


@strawberry.input
class SubscriberInput:
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tags: Optional[List[str]] = None


# Mock Data Functions (to be replaced with actual data fetching)
def get_current_user() -> User:
    return User(
        id="user_1",
        email="user@example.com",
        name="Test User",
        created_at=datetime.now(),
    )


def get_campaigns() -> List[Campaign]:
    return [
        Campaign(
            id="camp_1",
            name="Summer Product Launch",
            subject="Introducing our new summer products",
            status="sent",
            created_at=datetime(2023, 6, 20),
            scheduled_at=None,
            sent_at=datetime(2023, 6, 25, 14, 30),
            open_rate=32.8,
            click_rate=5.4,
            total_recipients=5400,
        ),
        Campaign(
            id="camp_2",
            name="Monthly Newsletter - July",
            subject="Your July Newsletter",
            status="scheduled",
            created_at=datetime(2023, 7, 1),
            scheduled_at=datetime(2023, 7, 10, 9, 0),
            sent_at=None,
            open_rate=None,
            click_rate=None,
            total_recipients=8500,
        ),
    ]


def get_subscribers() -> List[Subscriber]:
    return [
        Subscriber(
            id="sub_1",
            email="john.doe@example.com",
            first_name="John",
            last_name="Doe",
            status="active",
            created_at=datetime(2023, 5, 15),
            tags=["customer", "newsletter"],
        ),
        Subscriber(
            id="sub_2",
            email="jane.smith@example.com",
            first_name="Jane",
            last_name="Smith",
            status="active",
            created_at=datetime(2023, 6, 2),
            tags=["prospect", "webinar"],
        ),
    ]


def get_templates() -> List[Template]:
    return [
        Template(
            id="templ_1",
            name="Welcome Email",
            description="Template for welcoming new subscribers",
            content="<h1>Welcome to our newsletter!</h1><p>We're glad to have you on board.</p>",
            created_at=datetime(2023, 4, 10),
            updated_at=datetime(2023, 5, 5),
        ),
        Template(
            id="templ_2",
            name="Product Announcement",
            description="Template for new product announcements",
            content="<h1>New Product Announcement</h1><p>We're excited to introduce our latest product.</p>",
            created_at=datetime(2023, 3, 20),
            updated_at=datetime(2023, 3, 20),
        ),
    ]


def create_campaign(campaign_input: CampaignInput) -> Campaign:
    # This is a mock implementation
    return Campaign(
        id="camp_new",
        name=campaign_input.name,
        subject=campaign_input.subject,
        status="draft",
        created_at=datetime.now(),
        scheduled_at=campaign_input.scheduled_at,
        sent_at=None,
        open_rate=None,
        click_rate=None,
        total_recipients=0,
    )


def create_subscriber(subscriber_input: SubscriberInput) -> Subscriber:
    # This is a mock implementation
    return Subscriber(
        id="sub_new",
        email=subscriber_input.email,
        first_name=subscriber_input.first_name,
        last_name=subscriber_input.last_name,
        status="active",
        created_at=datetime.now(),
        tags=subscriber_input.tags or [],
    )


# Query Type
@strawberry.type
class Query:
    @strawberry.field
    def me(self) -> User:
        return get_current_user()

    @strawberry.field
    def campaigns(self) -> List[Campaign]:
        return get_campaigns()

    @strawberry.field
    def campaign(self, id: str) -> Optional[Campaign]:
        campaigns = get_campaigns()
        for campaign in campaigns:
            if campaign.id == id:
                return campaign
        return None

    @strawberry.field
    def subscribers(self) -> List[Subscriber]:
        return get_subscribers()

    @strawberry.field
    def subscriber(self, id: str) -> Optional[Subscriber]:
        subscribers = get_subscribers()
        for subscriber in subscribers:
            if subscriber.id == id:
                return subscriber
        return None

    @strawberry.field
    def templates(self) -> List[Template]:
        return get_templates()

    @strawberry.field
    def template(self, id: str) -> Optional[Template]:
        templates = get_templates()
        for template in templates:
            if template.id == id:
                return template
        return None


# Mutation Type
@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_campaign(self, campaign_input: CampaignInput) -> Campaign:
        return create_campaign(campaign_input)

    @strawberry.mutation
    def create_subscriber(self, subscriber_input: SubscriberInput) -> Subscriber:
        return create_subscriber(subscriber_input)


# Schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

# FastAPI integration
graphql_router = GraphQLRouter(schema)
