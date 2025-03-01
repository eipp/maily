"""OctoTools configuration."""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

OCTOTOOLS_CONFIG: Dict[str, Any] = {
    "model": {
        "planner": os.getenv("OCTOTOOLS_PLANNER_MODEL", "gpt-4o"),
        "executor": os.getenv("OCTOTOOLS_EXECUTOR_MODEL", "gpt-4o"),
        "max_steps": int(os.getenv("OCTOTOOLS_MAX_STEPS", "10")),
        "timeout": int(os.getenv("OCTOTOOLS_TIMEOUT", "300")),
    },
    "tools_directory": os.path.join(os.path.dirname(__file__), "tools"),
    "cache_directory": os.path.join(os.path.dirname(__file__), "../cache"),
    "api_keys": {
        "openai": os.getenv("OPENAI_API_KEY"),
        "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "google": os.getenv("GOOGLE_API_KEY"),
        "resend": os.getenv("RESEND_API_KEY"),
        "sendgrid": os.getenv("SENDGRID_API_KEY"),
        "mailgun": os.getenv("MAILGUN_API_KEY"),
        "linkedin": os.getenv("LINKEDIN_API_KEY"),
        "twitter": os.getenv("TWITTER_API_KEY"),
        "gmail": os.getenv("GMAIL_API_KEY"),
        "outlook": os.getenv("OUTLOOK_API_KEY"),
    }
}

# Tool configurations
EMAIL_TOOL_CONFIG = {
    "max_retries": 3,
    "retry_delay": 1,  # seconds
    "timeout": 30,  # seconds
    "providers": ["resend", "sendgrid", "mailgun"],
}

CONTENT_TOOL_CONFIG = {
    "max_tokens": 4000,
    "temperature": 0.7,
    "top_p": 0.95,
}

ATTACHMENT_TOOL_CONFIG = {
    "max_file_size": 25 * 1024 * 1024,  # 25MB
    "allowed_types": ["pdf", "pptx", "xlsx", "docx"],
    "storage_path": os.path.join(os.path.dirname(__file__), "../storage/attachments"),
}

CONTACT_DISCOVERY_TOOL_CONFIG = {
    "max_contacts_per_request": 100,
    "enrichment_levels": ["minimal", "standard", "comprehensive"],
    "discovery_depths": ["basic", "standard", "deep"],
    "rate_limits": {
        "requests_per_minute": 10,
        "requests_per_day": 1000,
    },
    "data_sources": ["web_search", "business_directories", "company_websites", "news_sources", "social_media"],
}

LOOKALIKE_AUDIENCE_TOOL_CONFIG = {
    "min_seed_contacts": 5,
    "max_expansion_factor": 10,
    "default_similarity_threshold": 0.7,
    "min_similarity_threshold": 0.5,
    "max_segments": 10,
}

PLATFORM_INTEGRATION_TOOL_CONFIG = {
    "supported_platforms": ["linkedin", "twitter", "gmail", "outlook"],
    "max_retries": 3,
    "retry_delay": 1,  # seconds
    "timeout": 60,  # seconds
    "cache_ttl": 3600,  # seconds
    "max_batch_size": 50,
}

ANALYTICS_TOOL_CONFIG = {
    "metrics": [
        "open_rate", "click_rate", "bounce_rate", "conversion_rate",
        "unsubscribe_rate", "spam_complaint_rate", "revenue"
    ],
    "time_periods": ["day", "week", "month", "quarter", "year"],
    "comparison_periods": ["previous_period", "same_period_last_year", "all_time"],
    "visualization_types": ["line", "bar", "pie", "table"],
}

OPTIMIZATION_TOOL_CONFIG = {
    "optimization_targets": ["open_rate", "click_rate", "conversion_rate", "revenue"],
    "test_types": ["a_b_test", "multivariate_test"],
    "min_sample_size": 100,
    "confidence_level": 0.95,
}

# Document Tool Configuration
DOCUMENT_TOOL_CONFIG = {
    "storage_path": os.path.join(os.environ.get("DOCUMENT_STORAGE_PATH", "storage/documents")),
    "allowed_types": ["pdf", "pptx", "xlsx", "docx"],
    "advanced_types": ["smart_pdf", "dynamic_presentation", "live_spreadsheet", "custom_report"],
    "max_document_size": 25 * 1024 * 1024,  # 25MB
    "max_batch_size": 10,
    "default_template_path": "templates/documents",
    "analytics_enabled": True,
    "blockchain_verification": {
        "enabled": True,
        "provider": "ethereum",
        "contract_address": os.environ.get("DOCUMENT_VERIFICATION_CONTRACT", "")
    },
    "visualization_libraries": ["d3", "chart.js"],
    "interactive_elements": ["forms", "calculators", "charts", "navigation"],
    "allowed_data_sources": ["crm", "analytics", "user_data", "external_api"],
    "model_config": {
        "claude": {
            "model_id": "claude-3-7-sonnet",
            "temperature": 0.3,
            "max_tokens": 4000
        },
        "gpt4o": {
            "model_id": "gpt-4o",
            "temperature": 0.4,
            "max_tokens": 4000
        },
        "gemini": {
            "model_id": "gemini-pro",
            "temperature": 0.2,
            "max_tokens": 4000
        }
    }
}
