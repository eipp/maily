"""Enhanced Anthropic Claude 3 integration for advanced reasoning."""

import os
import logging
import json
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class EnhancedClaudeService:
    """Enhanced Anthropic Claude 3 service for advanced reasoning."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Enhanced Claude service.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not set. Enhanced Claude service will be disabled.")
            self.enabled = False
        else:
            try:
                # Import Anthropic SDK
                import anthropic

                # Initialize Anthropic client
                self.client = anthropic.Anthropic(api_key=self.api_key)

                self.enabled = True
                logger.info("Enhanced Claude service initialized successfully")
            except ImportError:
                logger.error("Anthropic SDK not installed. Please install with 'pip install anthropic'.")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Enhanced Claude service: {str(e)}")
                self.enabled = False

    async def generate_content(self,
                              prompt: str,
                              model: str = "claude-3-opus-20240229",
                              system_prompt: Optional[str] = None,
                              temperature: float = 0.7,
                              max_tokens: int = 4000,
                              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate content using Claude 3.

        Args:
            prompt: Prompt to send to Claude
            model: Claude model to use
            system_prompt: Optional system prompt
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            metadata: Optional metadata

        Returns:
            Dictionary containing the generated content and metadata
        """
        if not self.enabled:
            return {"error": "Enhanced Claude service is not enabled"}

        try:
            # Import Anthropic SDK
            import anthropic

            # Create the message
            message_params = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}]
            }

            # Add system prompt if provided
            if system_prompt:
                message_params["system"] = system_prompt

            # Add metadata if provided
            if metadata:
                message_params["metadata"] = metadata

            # Generate the content
            response = await self.client.messages.create(**message_params)

            # Extract the content
            content = response.content[0].text

            return {
                "content": content,
                "model": model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "id": response.id
            }
        except Exception as e:
            logger.error(f"Failed to generate content with Claude 3: {str(e)}")
            return {"error": str(e)}

    async def analyze_email_campaign(self,
                                    campaign_data: Dict[str, Any],
                                    model: str = "claude-3-opus-20240229") -> Dict[str, Any]:
        """Analyze an email campaign using Claude 3.

        Args:
            campaign_data: Email campaign data
            model: Claude model to use

        Returns:
            Dictionary containing the analysis
        """
        if not self.enabled:
            return {"error": "Enhanced Claude service is not enabled"}

        try:
            # Create the prompt
            prompt = f"""
            Please analyze the following email campaign and provide insights:

            Campaign Name: {campaign_data.get('name', 'N/A')}
            Subject: {campaign_data.get('subject', 'N/A')}
            Target Audience: {campaign_data.get('audience', 'N/A')}

            Email Content:
            {campaign_data.get('content', 'N/A')}

            Please provide:
            1. Overall assessment of the campaign
            2. Strengths of the campaign
            3. Areas for improvement
            4. Suggestions for A/B testing
            5. Predicted performance metrics
            """

            # Generate the analysis
            response = await self.generate_content(
                prompt=prompt,
                model=model,
                system_prompt="You are an expert email marketing analyst. Provide detailed, actionable insights for email campaigns.",
                temperature=0.3
            )

            return response
        except Exception as e:
            logger.error(f"Failed to analyze email campaign with Claude 3: {str(e)}")
            return {"error": str(e)}

    async def generate_email_variations(self,
                                       email_data: Dict[str, Any],
                                       num_variations: int = 3,
                                       model: str = "claude-3-opus-20240229") -> Dict[str, Any]:
        """Generate variations of an email using Claude 3.

        Args:
            email_data: Email data
            num_variations: Number of variations to generate
            model: Claude model to use

        Returns:
            Dictionary containing the generated variations
        """
        if not self.enabled:
            return {"error": "Enhanced Claude service is not enabled"}

        try:
            # Create the prompt
            prompt = f"""
            Please generate {num_variations} variations of the following email:

            Subject: {email_data.get('subject', 'N/A')}
            Target Audience: {email_data.get('audience', 'N/A')}

            Original Email Content:
            {email_data.get('content', 'N/A')}

            For each variation, provide:
            1. A new subject line
            2. The full email content
            3. A brief explanation of the changes made and why

            Return the results in JSON format with the following structure:
            {{
                "variations": [
                    {{
                        "subject": "New subject line",
                        "content": "New email content",
                        "explanation": "Explanation of changes"
                    }},
                    ...
                ]
            }}
            """

            # Generate the variations
            response = await self.generate_content(
                prompt=prompt,
                model=model,
                system_prompt="You are an expert email copywriter. Generate creative and effective email variations.",
                temperature=0.7
            )

            # Parse the JSON response
            try:
                content = response.get("content", "{}")
                # Extract JSON from the content (it might be wrapped in markdown code blocks)
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                variations = json.loads(content)
                return {
                    "variations": variations.get("variations", []),
                    "model": model,
                    "usage": response.get("usage", {})
                }
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw content
                return {
                    "error": "Failed to parse JSON response",
                    "raw_content": response.get("content", "")
                }
        except Exception as e:
            logger.error(f"Failed to generate email variations with Claude 3: {str(e)}")
            return {"error": str(e)}

    async def generate_personalized_content(self,
                                          template: str,
                                          user_data: Dict[str, Any],
                                          model: str = "claude-3-opus-20240229") -> Dict[str, Any]:
        """Generate personalized content using Claude 3.

        Args:
            template: Content template with placeholders
            user_data: User data for personalization
            model: Claude model to use

        Returns:
            Dictionary containing the personalized content
        """
        if not self.enabled:
            return {"error": "Enhanced Claude service is not enabled"}

        try:
            # Create the prompt
            prompt = f"""
            Please personalize the following content template for a specific user:

            Template:
            {template}

            User Data:
            {json.dumps(user_data, indent=2)}

            Generate personalized content that incorporates the user's data in a natural way.
            The personalization should feel authentic and tailored to the user's specific characteristics.
            """

            # Generate the personalized content
            response = await self.generate_content(
                prompt=prompt,
                model=model,
                system_prompt="You are an expert in personalized content creation. Create highly tailored content that feels authentic and relevant to each user.",
                temperature=0.5
            )

            return response
        except Exception as e:
            logger.error(f"Failed to generate personalized content with Claude 3: {str(e)}")
            return {"error": str(e)}

    async def analyze_campaign_performance(self,
                                         campaign_metrics: Dict[str, Any],
                                         model: str = "claude-3-opus-20240229") -> Dict[str, Any]:
        """Analyze campaign performance using Claude 3.

        Args:
            campaign_metrics: Campaign performance metrics
            model: Claude model to use

        Returns:
            Dictionary containing the analysis
        """
        if not self.enabled:
            return {"error": "Enhanced Claude service is not enabled"}

        try:
            # Create the prompt
            prompt = f"""
            Please analyze the following email campaign performance metrics and provide insights:

            Campaign Metrics:
            {json.dumps(campaign_metrics, indent=2)}

            Please provide:
            1. Overall performance assessment
            2. Key insights from the metrics
            3. Comparison to industry benchmarks (if applicable)
            4. Recommendations for future campaigns
            5. Specific actions to improve performance
            """

            # Generate the analysis
            response = await self.generate_content(
                prompt=prompt,
                model=model,
                system_prompt="You are an expert email marketing analyst with deep knowledge of industry benchmarks and best practices. Provide detailed, actionable insights based on campaign performance metrics.",
                temperature=0.3
            )

            return response
        except Exception as e:
            logger.error(f"Failed to analyze campaign performance with Claude 3: {str(e)}")
            return {"error": str(e)}

    async def generate_subject_lines(self,
                                   email_content: str,
                                   audience: str,
                                   num_variations: int = 5,
                                   model: str = "claude-3-opus-20240229") -> Dict[str, Any]:
        """Generate email subject line variations using Claude 3.

        Args:
            email_content: Email content
            audience: Target audience
            num_variations: Number of variations to generate
            model: Claude model to use

        Returns:
            Dictionary containing the generated subject lines
        """
        if not self.enabled:
            return {"error": "Enhanced Claude service is not enabled"}

        try:
            # Create the prompt
            prompt = f"""
            Please generate {num_variations} compelling subject line variations for the following email:

            Target Audience: {audience}

            Email Content:
            {email_content}

            For each subject line, provide:
            1. The subject line text
            2. A brief explanation of why it would be effective
            3. What emotional trigger or value proposition it emphasizes

            Return the results in JSON format with the following structure:
            {{
                "subject_lines": [
                    {{
                        "text": "Subject line text",
                        "explanation": "Explanation of effectiveness",
                        "emphasis": "Emotional trigger or value proposition"
                    }},
                    ...
                ]
            }}
            """

            # Generate the subject lines
            response = await self.generate_content(
                prompt=prompt,
                model=model,
                system_prompt="You are an expert email marketer specializing in crafting high-converting subject lines. Create subject lines that grab attention, generate curiosity, and drive opens.",
                temperature=0.7
            )

            # Parse the JSON response
            try:
                content = response.get("content", "{}")
                # Extract JSON from the content (it might be wrapped in markdown code blocks)
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                subject_lines = json.loads(content)
                return {
                    "subject_lines": subject_lines.get("subject_lines", []),
                    "model": model,
                    "usage": response.get("usage", {})
                }
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw content
                return {
                    "error": "Failed to parse JSON response",
                    "raw_content": response.get("content", "")
                }
        except Exception as e:
            logger.error(f"Failed to generate subject lines with Claude 3: {str(e)}")
            return {"error": str(e)}

# Create a singleton instance
enhanced_claude_service = EnhancedClaudeService()
