"""Email content generation tool for OctoTools."""

import logging
import asyncio
from typing import Dict, Any, List, Optional

from octotools import ToolCard

from ai.config import CONTENT_TOOL_CONFIG

logger = logging.getLogger(__name__)

class EmailContentGeneratorTool(ToolCard):
    """Tool for generating email content based on campaign objectives and context."""

    def __init__(self):
        """Initialize the email content generator tool."""
        super().__init__(
            tool_name="Email_Content_Generator",
            tool_description="Generates email content based on campaign objectives and context.",
            input_types={
                "campaign_objective": "str - The objective of the email campaign",
                "target_audience": "str - Description of the target audience",
                "brand_voice": "str - The brand voice to use (e.g., 'professional', 'casual', 'friendly')",
                "key_points": "list - List of key points to include in the email",
                "personalization": "dict - Optional personalization variables"
            },
            output_type="dict - Contains the generated email content (subject, html_body, plain_text)",
            demo_commands=[
                {
                    "command": 'execution = tool.execute(campaign_objective="Promote new product launch", target_audience="Existing customers", brand_voice="professional", key_points=["New features", "Limited time offer"])',
                    "description": "Generate email content for a product launch campaign"
                }
            ],
            user_metadata={
                "limitations": [
                    "Generated content may require human review and editing",
                    "Personalization is limited to the provided variables",
                    "HTML formatting is basic and may need enhancement"
                ],
                "best_practices": [
                    "Provide clear and specific campaign objectives",
                    "Include detailed information about the target audience",
                    "List all key points that must be included in the email",
                    "Review and edit the generated content before sending"
                ]
            }
        )

        # Initialize configuration
        self.config = CONTENT_TOOL_CONFIG

    async def execute(
        self,
        campaign_objective: str,
        target_audience: str,
        brand_voice: str = "professional",
        key_points: List[str] = None,
        personalization: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """
        Generate email content based on campaign objectives and context.

        Args:
            campaign_objective: The objective of the email campaign
            target_audience: Description of the target audience
            brand_voice: The brand voice to use
            key_points: List of key points to include in the email
            personalization: Optional personalization variables

        Returns:
            Dictionary containing the generated email content
        """
        logger.info(f"Generating email content for objective: {campaign_objective}")

        try:
            # Validate inputs
            self._validate_inputs(campaign_objective, target_audience, brand_voice, key_points, personalization)

            # In a real implementation, this would use an LLM to generate content
            # For now, we'll simulate the generation process
            await asyncio.sleep(1.0)  # Simulate LLM processing time

            # Generate subject line
            subject = self._generate_subject(campaign_objective, brand_voice)

            # Generate email body
            html_body, plain_text = self._generate_body(
                campaign_objective,
                target_audience,
                brand_voice,
                key_points or [],
                personalization or {}
            )

            return {
                "subject": subject,
                "html_body": html_body,
                "plain_text": plain_text
            }
        except Exception as e:
            logger.error(f"Email content generation failed: {str(e)}")
            return {
                "error": str(e),
                "subject": f"Error: {str(e)}",
                "html_body": f"<p>Error generating content: {str(e)}</p>",
                "plain_text": f"Error generating content: {str(e)}"
            }

    def _validate_inputs(self, campaign_objective, target_audience, brand_voice, key_points, personalization):
        """Validate input parameters."""
        if not campaign_objective:
            raise ValueError("Campaign objective is required")

        if not target_audience:
            raise ValueError("Target audience is required")

        valid_brand_voices = ["professional", "casual", "friendly", "formal", "technical", "enthusiastic"]
        if brand_voice not in valid_brand_voices:
            logger.warning(f"Brand voice '{brand_voice}' is not in the list of recommended voices: {', '.join(valid_brand_voices)}")

    def _generate_subject(self, campaign_objective, brand_voice):
        """Generate a subject line based on the campaign objective and brand voice."""
        # In a real implementation, this would use an LLM to generate a subject line
        # For now, we'll use a simple template

        if "product launch" in campaign_objective.lower():
            if brand_voice == "professional":
                return "Introducing Our New Product: Elevate Your Experience"
            elif brand_voice == "casual":
                return "Check out what's new! Just launched 🚀"
            else:
                return "Exciting News: Our New Product Has Arrived!"

        elif "newsletter" in campaign_objective.lower():
            if brand_voice == "professional":
                return "Your Monthly Industry Insights and Updates"
            elif brand_voice == "casual":
                return "What's happening this month? Find out inside!"
            else:
                return "Stay Informed: Your Monthly Newsletter"

        elif "promotion" in campaign_objective.lower() or "offer" in campaign_objective.lower():
            if brand_voice == "professional":
                return "Exclusive Offer: Limited Time Opportunity"
            elif brand_voice == "casual":
                return "Don't miss out! Special deal inside 🔥"
            else:
                return "Special Promotion: Act Now and Save"

        else:
            # Generic subject line
            return f"Important Update: {campaign_objective}"

    def _generate_body(self, campaign_objective, target_audience, brand_voice, key_points, personalization):
        """Generate email body content based on inputs."""
        # In a real implementation, this would use an LLM to generate the body
        # For now, we'll use a simple template

        # Apply personalization
        greeting = "Hello"
        if personalization and "first_name" in personalization:
            greeting = f"Hello {personalization['first_name']}"

        # Generate HTML content
        html_parts = [
            f"<h1>{self._generate_subject(campaign_objective, brand_voice)}</h1>",
            f"<p>{greeting},</p>",
            f"<p>We're reaching out to share some important information about {campaign_objective}.</p>"
        ]

        # Add key points
        if key_points:
            html_parts.append("<ul>")
            for point in key_points:
                html_parts.append(f"<li>{point}</li>")
            html_parts.append("</ul>")

        # Add closing
        if brand_voice == "professional":
            html_parts.append("<p>Thank you for your continued support.</p>")
            html_parts.append("<p>Best regards,<br>The Team</p>")
        elif brand_voice == "casual":
            html_parts.append("<p>Thanks for being awesome!</p>")
            html_parts.append("<p>Cheers,<br>The Team</p>")
        else:
            html_parts.append("<p>We appreciate your business.</p>")
            html_parts.append("<p>Sincerely,<br>The Team</p>")

        # Add company info if available
        if personalization and "company_name" in personalization:
            html_parts.append(f"<p><small>{personalization['company_name']}</small></p>")

        html_body = "\n".join(html_parts)

        # Generate plain text version
        plain_text = html_body.replace("<h1>", "").replace("</h1>", "\n\n")
        plain_text = plain_text.replace("<p>", "").replace("</p>", "\n\n")
        plain_text = plain_text.replace("<ul>", "\n").replace("</ul>", "\n")
        plain_text = plain_text.replace("<li>", "- ").replace("</li>", "\n")
        plain_text = plain_text.replace("<br>", "\n")
        plain_text = plain_text.replace("<small>", "").replace("</small>", "")

        return html_body, plain_text
