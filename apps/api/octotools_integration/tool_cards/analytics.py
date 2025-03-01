from typing import Dict, Any, List, Optional
import logging
import json
import asyncio
import datetime

from apps.api.octotools_integration.tool_cards import MailyToolCard

logger = logging.getLogger(__name__)

class EngagementPredictionTool(MailyToolCard):
    def __init__(self):
        super().__init__(
            tool_name="Engagement_Prediction_Tool",
            tool_description="A tool that predicts contact engagement based on historical data and campaign parameters.",
            input_types={
                "contacts": "list - List of contacts to predict engagement for",
                "campaign_data": "dict - Data about the planned campaign"
            },
            output_type="dict - Contains engagement predictions and recommendations",
            demo_commands=[
                {
                    "command": 'execution = tool.execute(contacts=[{"email": "john@example.com", "role": "CTO"}], campaign_data={"subject": "New Product Launch", "content_type": "announcement"})',
                    "description": "Predict engagement for contacts with a product launch campaign"
                }
            ],
            user_metadata={
                "limitations": [
                    "Prediction accuracy depends on quality of historical engagement data",
                    "Limited predictive power for new contacts with no engagement history",
                    "Predictions are estimates and may not reflect actual outcomes"
                ],
                "best_practices": [
                    "Include as much campaign data as possible for better predictions",
                    "Use predictions as guidance rather than absolute truth",
                    "Combine with A/B testing for optimal results"
                ]
            }
        )

    async def execute(
        self,
        contacts: List[Dict[str, Any]],
        campaign_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict engagement for contacts based on campaign data.

        Args:
            contacts: List of contacts to predict engagement for
            campaign_data: Data about the planned campaign

        Returns:
            Dictionary containing engagement predictions and recommendations
        """
        self._log_execution(
            {"contacts_count": len(contacts), "campaign_type": campaign_data.get("type", "unknown")},
            "Executing engagement prediction"
        )

        try:
            # Validate inputs
            self._validate_inputs(contacts, campaign_data)

            # Extract features for prediction
            contact_features = await self._extract_engagement_features(contacts)
            campaign_features = await self._extract_campaign_features(campaign_data)

            # Generate combined feature vectors
            feature_vectors = await self._combine_features(contact_features, campaign_features)

            # Apply predictive models
            engagement_scores = await self._predict_engagement(feature_vectors)

            # Generate content recommendations
            content_recommendations = await self._generate_content_recommendations(
                contacts, engagement_scores, campaign_data
            )

            # Recommend optimal send times
            send_time_recommendations = await self._recommend_send_times(contacts, engagement_scores)

            # Prioritize contacts by predicted engagement
            prioritized_contacts = await self._prioritize_contacts(contacts, engagement_scores)

            return {
                "engagement_predictions": engagement_scores,
                "content_recommendations": content_recommendations,
                "send_time_recommendations": send_time_recommendations,
                "contact_priority": prioritized_contacts,
                "prediction_confidence": await self._calculate_prediction_confidence(engagement_scores)
            }
        except Exception as e:
            logger.error(f"Engagement prediction failed: {str(e)}")
            return {
                "error": str(e),
                "engagement_predictions": {},
                "content_recommendations": {},
                "send_time_recommendations": {},
                "contact_priority": [],
                "prediction_confidence": 0.0
            }

    def _validate_inputs(self, contacts, campaign_data):
        """Validate input parameters."""
        if not contacts:
            raise ValueError("Contacts list cannot be empty")

        if not campaign_data:
            raise ValueError("Campaign data cannot be empty")

        required_campaign_fields = ["subject", "content_type"]
        missing_fields = [field for field in required_campaign_fields if field not in campaign_data]
        if missing_fields:
            raise ValueError(f"Campaign data missing required fields: {', '.join(missing_fields)}")

    async def _extract_engagement_features(self, contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract engagement features from contacts."""
        features = []

        for contact in contacts:
            # Basic contact info
            contact_id = contact.get("id", "")

            # Historical engagement metrics
            engagement_history = contact.get("engagement_history", [])

            # Calculate engagement metrics
            open_rate = self._calculate_open_rate(engagement_history)
            click_rate = self._calculate_click_rate(engagement_history)
            response_rate = self._calculate_response_rate(engagement_history)

            # Time-based metrics
            last_engagement = self._get_last_engagement_date(engagement_history)
            engagement_frequency = self._calculate_engagement_frequency(engagement_history)

            # Preferred content types
            content_preferences = self._extract_content_preferences(engagement_history)

            # Preferred engagement times
            time_preferences = self._extract_time_preferences(engagement_history)

            # Combine features
            features.append({
                "contact_id": contact_id,
                "open_rate": open_rate,
                "click_rate": click_rate,
                "response_rate": response_rate,
                "last_engagement": last_engagement,
                "engagement_frequency": engagement_frequency,
                "content_preferences": content_preferences,
                "time_preferences": time_preferences,
                "industry": contact.get("industry", ""),
                "role": contact.get("role", ""),
                "company_size": contact.get("company_size", "")
            })

        return features

    def _calculate_open_rate(self, engagement_history: List[Dict[str, Any]]) -> float:
        """Calculate email open rate from engagement history."""
        if not engagement_history:
            return 0.0

        sent_count = sum(1 for e in engagement_history if e.get("type") == "email_sent")
        open_count = sum(1 for e in engagement_history if e.get("type") == "email_opened")

        return open_count / sent_count if sent_count > 0 else 0.0

    def _calculate_click_rate(self, engagement_history: List[Dict[str, Any]]) -> float:
        """Calculate email click rate from engagement history."""
        if not engagement_history:
            return 0.0

        open_count = sum(1 for e in engagement_history if e.get("type") == "email_opened")
        click_count = sum(1 for e in engagement_history if e.get("type") == "email_clicked")

        return click_count / open_count if open_count > 0 else 0.0

    def _calculate_response_rate(self, engagement_history: List[Dict[str, Any]]) -> float:
        """Calculate email response rate from engagement history."""
        if not engagement_history:
            return 0.0

        sent_count = sum(1 for e in engagement_history if e.get("type") == "email_sent")
        response_count = sum(1 for e in engagement_history if e.get("type") == "email_replied")

        return response_count / sent_count if sent_count > 0 else 0.0

    def _get_last_engagement_date(self, engagement_history: List[Dict[str, Any]]) -> Optional[str]:
        """Get the date of the last engagement."""
        if not engagement_history:
            return None

        engagement_types = ["email_opened", "email_clicked", "email_replied"]
        engagements = [e for e in engagement_history if e.get("type") in engagement_types]

        if not engagements:
            return None

        # Sort by timestamp and get the most recent
        sorted_engagements = sorted(engagements, key=lambda e: e.get("timestamp", ""), reverse=True)
        return sorted_engagements[0].get("timestamp")

    def _calculate_engagement_frequency(self, engagement_history: List[Dict[str, Any]]) -> str:
        """Calculate engagement frequency (daily, weekly, monthly, etc.)."""
        if not engagement_history:
            return "unknown"

        engagement_types = ["email_opened", "email_clicked", "email_replied"]
        engagements = [e for e in engagement_history if e.get("type") in engagement_types]

        if len(engagements) < 2:
            return "unknown"

        # Sort by timestamp
        sorted_engagements = sorted(engagements, key=lambda e: e.get("timestamp", ""))

        # Calculate average days between engagements
        timestamps = [e.get("timestamp", "") for e in sorted_engagements]
        dates = [datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")) for ts in timestamps if ts]

        if len(dates) < 2:
            return "unknown"

        time_diffs = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        avg_days = sum(time_diffs) / len(time_diffs)

        if avg_days < 1:
            return "daily"
        elif avg_days < 7:
            return "weekly"
        elif avg_days < 30:
            return "monthly"
        else:
            return "infrequent"

    def _extract_content_preferences(self, engagement_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extract content type preferences from engagement history."""
        if not engagement_history:
            return {}

        # Count engagements by content type
        content_engagements = {}
        total_engagements = 0

        for engagement in engagement_history:
            if engagement.get("type") in ["email_opened", "email_clicked", "email_replied"]:
                content_type = engagement.get("content_type", "unknown")
                content_engagements[content_type] = content_engagements.get(content_type, 0) + 1
                total_engagements += 1

        # Calculate preference scores
        preferences = {
            content_type: count / total_engagements
            for content_type, count in content_engagements.items()
        } if total_engagements > 0 else {}

        return preferences

    def _extract_time_preferences(self, engagement_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extract time of day preferences from engagement history."""
        if not engagement_history:
            return {}

        # Count engagements by time of day
        time_engagements = {
            "morning": 0,   # 6-11
            "afternoon": 0, # 12-17
            "evening": 0,   # 18-23
            "night": 0      # 0-5
        }
        total_engagements = 0

        for engagement in engagement_history:
            if engagement.get("type") in ["email_opened", "email_clicked", "email_replied"]:
                timestamp = engagement.get("timestamp", "")
                if timestamp:
                    try:
                        dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        hour = dt.hour

                        if 6 <= hour < 12:
                            time_engagements["morning"] += 1
                        elif 12 <= hour < 18:
                            time_engagements["afternoon"] += 1
                        elif 18 <= hour < 24:
                            time_engagements["evening"] += 1
                        else:
                            time_engagements["night"] += 1

                        total_engagements += 1
                    except ValueError:
                        pass

        # Calculate preference scores
        preferences = {
            time_of_day: count / total_engagements
            for time_of_day, count in time_engagements.items()
        } if total_engagements > 0 else {}

        return preferences

    async def _extract_campaign_features(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features from campaign data."""
        features = {
            "subject": campaign_data.get("subject", ""),
            "content_type": campaign_data.get("content_type", ""),
            "content_length": campaign_data.get("content_length", "medium"),
            "has_images": campaign_data.get("has_images", False),
            "has_links": campaign_data.get("has_links", False),
            "has_attachments": campaign_data.get("has_attachments", False),
            "personalized": campaign_data.get("personalized", False),
            "send_time": campaign_data.get("send_time", ""),
            "send_day": campaign_data.get("send_day", ""),
            "campaign_goal": campaign_data.get("goal", "information")
        }

        # Extract subject line features
        subject = features["subject"]
        features["subject_length"] = len(subject)
        features["subject_has_question"] = "?" in subject
        features["subject_has_number"] = any(c.isdigit() for c in subject)
        features["subject_has_emoji"] = self._contains_emoji(subject)

        return features

    def _contains_emoji(self, text: str) -> bool:
        """Check if text contains emoji."""
        # Simple emoji detection - would be more sophisticated in production
        emoji_patterns = [
            "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇",
            "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚"
        ]
        return any(emoji in text for emoji in emoji_patterns)

    async def _combine_features(
        self,
        contact_features: List[Dict[str, Any]],
        campaign_features: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Combine contact and campaign features for prediction."""
        combined_features = []

        for contact in contact_features:
            # Create a copy of campaign features
            features = campaign_features.copy()

            # Add contact features
            features["contact_id"] = contact["contact_id"]
            features["open_rate"] = contact["open_rate"]
            features["click_rate"] = contact["click_rate"]
            features["response_rate"] = contact["response_rate"]
            features["last_engagement"] = contact["last_engagement"]
            features["engagement_frequency"] = contact["engagement_frequency"]
            features["industry"] = contact["industry"]
            features["role"] = contact["role"]
            features["company_size"] = contact["company_size"]

            # Calculate content type match score
            content_preferences = contact["content_preferences"]
            campaign_content_type = campaign_features["content_type"]
            content_match_score = content_preferences.get(campaign_content_type, 0.0)
            features["content_match_score"] = content_match_score

            # Calculate time match score
            time_preferences = contact["time_preferences"]
            campaign_send_time = campaign_features["send_time"]
            time_match_score = 0.0

            if campaign_send_time:
                try:
                    hour = int(campaign_send_time.split(":")[0])
                    if 6 <= hour < 12:
                        time_match_score = time_preferences.get("morning", 0.0)
                    elif 12 <= hour < 18:
                        time_match_score = time_preferences.get("afternoon", 0.0)
                    elif 18 <= hour < 24:
                        time_match_score = time_preferences.get("evening", 0.0)
                    else:
                        time_match_score = time_preferences.get("night", 0.0)
                except (ValueError, IndexError):
                    pass

            features["time_match_score"] = time_match_score

            combined_features.append(features)

        return combined_features

    async def _predict_engagement(self, feature_vectors: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Predict engagement scores for contacts."""
        engagement_scores = {}

        for features in feature_vectors:
            contact_id = features["contact_id"]

            # Calculate base scores
            open_score = self._predict_open_score(features)
            click_score = self._predict_click_score(features)
            response_score = self._predict_response_score(features)

            engagement_scores[contact_id] = {
                "open_probability": open_score,
                "click_probability": click_score,
                "response_probability": response_score,
                "overall_engagement": (open_score + click_score + response_score) / 3
            }

        return engagement_scores

    def _predict_open_score(self, features: Dict[str, Any]) -> float:
        """Predict email open probability."""
        # Base score from historical open rate
        base_score = features.get("open_rate", 0.0)

        # Adjust based on subject line features
        subject_length = features.get("subject_length", 0)
        if subject_length < 30:
            base_score *= 1.1  # Short subjects tend to perform better
        elif subject_length > 60:
            base_score *= 0.9  # Long subjects tend to perform worse

        if features.get("subject_has_question", False):
            base_score *= 1.15  # Questions increase open rates

        if features.get("subject_has_number", False):
            base_score *= 1.1  # Numbers increase open rates

        if features.get("subject_has_emoji", False):
            base_score *= 1.05  # Emojis slightly increase open rates

        # Adjust based on time match
        time_match_score = features.get("time_match_score", 0.0)
        base_score *= (1 + time_match_score * 0.2)

        # Adjust based on recency of engagement
        last_engagement = features.get("last_engagement", "")
        if last_engagement:
            try:
                last_date = datetime.datetime.fromisoformat(last_engagement.replace("Z", "+00:00"))
                now = datetime.datetime.now(datetime.timezone.utc)
                days_since = (now - last_date).days

                if days_since < 7:
                    base_score *= 1.2  # Recent engagement increases open probability
                elif days_since < 30:
                    base_score *= 1.1
                elif days_since > 90:
                    base_score *= 0.8  # Long time since engagement decreases open probability
            except ValueError:
                pass

        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, base_score))

    def _predict_click_score(self, features: Dict[str, Any]) -> float:
        """Predict email click probability."""
        # Base score from historical click rate
        base_score = features.get("click_rate", 0.0)

        # Adjust based on content match
        content_match_score = features.get("content_match_score", 0.0)
        base_score *= (1 + content_match_score * 0.3)

        # Adjust based on content features
        if features.get("has_links", False):
            base_score *= 1.2  # Links increase click probability

        if features.get("has_images", False):
            base_score *= 1.1  # Images increase click probability

        # Adjust based on personalization
        if features.get("personalized", False):
            base_score *= 1.15  # Personalization increases click probability

        # Adjust based on campaign goal
        campaign_goal = features.get("campaign_goal", "")
        if campaign_goal == "conversion":
            base_score *= 1.1  # Conversion-focused campaigns often have stronger CTAs

        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, base_score))

    def _predict_response_score(self, features: Dict[str, Any]) -> float:
        """Predict email response probability."""
        # Base score from historical response rate
        base_score = features.get("response_rate", 0.0)

        # Adjust based on personalization
        if features.get("personalized", False):
            base_score *= 1.25  # Personalization significantly increases response probability

        # Adjust based on content type
        content_type = features.get("content_type", "")
        if content_type in ["question", "request", "survey"]:
            base_score *= 1.2  # Content types that prompt responses

        # Adjust based on role
        role = features.get("role", "").lower()
        if "ceo" in role or "cto" in role or "founder" in role:
            base_score *= 0.8  # Executives are less likely to respond

        # Adjust based on content length
        content_length = features.get("content_length", "medium")
        if content_length == "short":
            base_score *= 1.1  # Short emails are more likely to get responses
        elif content_length == "long":
            base_score *= 0.9  # Long emails are less likely to get responses

        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, base_score))

    async def _generate_content_recommendations(
        self,
        contacts: List[Dict[str, Any]],
        engagement_scores: Dict[str, Dict[str, float]],
        campaign_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate content recommendations based on predictions."""
        # Analyze overall engagement
        overall_scores = [scores["overall_engagement"] for scores in engagement_scores.values()]
        avg_engagement = sum(overall_scores) / len(overall_scores) if overall_scores else 0

        # Generate subject line recommendations
        subject_recommendations = self._generate_subject_recommendations(
            campaign_data, avg_engagement
        )

        # Generate content recommendations
        content_recommendations = self._generate_content_type_recommendations(
            contacts, engagement_scores, campaign_data
        )

        # Generate personalization recommendations
        personalization_recommendations = self._generate_personalization_recommendations(
            contacts, engagement_scores
        )

        return {
            "subject_line": subject_recommendations,
            "content": content_recommendations,
            "personalization": personalization_recommendations
        }

    def _generate_subject_recommendations(
        self,
        campaign_data: Dict[str, Any],
        avg_engagement: float
    ) -> List[str]:
        """Generate subject line recommendations."""
        current_subject = campaign_data.get("subject", "")
        content_type = campaign_data.get("content_type", "")

        recommendations = []

        # Check subject length
        if len(current_subject) > 60:
            recommendations.append("Consider shortening the subject line to under 60 characters for better open rates")

        # Check for questions
        if "?" not in current_subject:
            recommendations.append("Consider adding a question to the subject line to increase engagement")

        # Check for numbers
        if not any(c.isdigit() for c in current_subject):
            recommendations.append("Consider adding numbers to the subject line (e.g., '5 ways to...')")

        # Content type specific recommendations
        if content_type == "newsletter":
            recommendations.append("For newsletters, consider adding the month or date to the subject")
        elif content_type == "announcement":
            recommendations.append("For announcements, consider adding 'New:' or 'Introducing:' to the subject")
        elif content_type == "event":
            recommendations.append("For events, include the date and a clear value proposition in the subject")

        # If engagement is predicted to be low
        if avg_engagement < 0.3:
            recommendations.append("Consider A/B testing multiple subject lines for this campaign")
            recommendations.append("Add urgency or exclusivity to the subject line to boost engagement")

        return recommendations

    def _generate_content_type_recommendations(
        self,
        contacts: List[Dict[str, Any]],
        engagement_scores: Dict[str, Dict[str, float]],
        campaign_data: Dict[str, Any]
    ) -> List[str]:
        """Generate content type recommendations."""
        content_type = campaign_data.get("content_type", "")
        has_images = campaign_data.get("has_images", False)
        has_links = campaign_data.get("has_links", False)

        recommendations = []

        # Basic content recommendations
        if not has_images:
            recommendations.append("Consider adding relevant images to increase engagement")

        if not has_links:
            recommendations.append("Include clear call-to-action links to drive click-through rates")

        # Content type specific recommendations
        if content_type == "newsletter":
            recommendations.append("Keep newsletters scannable with clear section headers and brief content blocks")
            recommendations.append("Include a mix of content types (news, tips, success stories) to appeal to different interests")
        elif content_type == "announcement":
            recommendations.append("Focus on benefits rather than features in product announcements")
            recommendations.append("Include social proof or testimonials to support your announcement")
        elif content_type == "event":
            recommendations.append("Clearly highlight date, time, and how to register/attend")
            recommendations.append("Include a brief agenda or highlight key speakers/topics")

        # Analyze engagement scores for content length recommendation
        click_scores = [scores["click_probability"] for scores in engagement_scores.values()]
        avg_click = sum(click_scores) / len(click_scores) if click_scores else 0

        if avg_click < 0.2:
            recommendations.append("Consider shortening content and focusing on a single, clear call-to-action")

        return recommendations

    def _generate_personalization_recommendations(
        self,
        contacts: List[Dict[str, Any]],
        engagement_scores: Dict[str, Dict[str, float]]
    ) -> List[str]:
        """Generate personalization recommendations."""
        recommendations = []

        # Check if we have industry data
        industries = [contact.get("industry") for contact in contacts if contact.get("industry")]
        if industries:
            recommendations.append("Segment your campaign by industry for more targeted messaging")

        # Check if we have role data
        roles = [contact.get("role") for contact in contacts if contact.get("role")]
        if roles:
            recommendations.append("Customize content based on job roles (e.g., technical vs. business focus)")

        # General personalization recommendations
        recommendations.append("Use recipient's name in both subject line and email body")
        recommendations.append("Reference previous interactions or purchases when applicable")

        # Advanced personalization for high-value contacts
        high_value_contacts = [
            contact_id for contact_id, scores in engagement_scores.items()
            if scores["overall_engagement"] > 0.6
        ]

        if high_value_contacts:
            recommendations.append(f"Consider creating personalized content for your {len(high_value_contacts)} highest-value contacts")

        return recommendations

    async def _recommend_send_times(
        self,
        contacts: List[Dict[str, Any]],
        engagement_scores: Dict[str, Dict[str, float]]
    ) -> Dict[str, Any]:
        """Recommend optimal send times for the campaign."""
        # Analyze contact time preferences
        time_preferences = {
            "morning": 0,
            "afternoon": 0,
            "evening": 0,
            "night": 0
        }

        # Count contacts with each time preference
        for contact in contacts:
            engagement_history = contact.get("engagement_history", [])
            if engagement_history:
                prefs = self._extract_time_preferences(engagement_history)
                max_pref = max(prefs.items(), key=lambda x: x[1])[0] if prefs else None
                if max_pref:
                    time_preferences[max_pref] += 1

        # Determine optimal time of day
        optimal_time = max(time_preferences.items(), key=lambda x: x[1])[0] if any(time_preferences.values()) else "morning"

        # Map time of day to hour ranges
        hour_ranges = {
            "morning": "8:00 AM - 10:00 AM",
            "afternoon": "1:00 PM - 3:00 PM",
            "evening": "6:00 PM - 8:00 PM",
            "night": "9:00 PM - 11:00 PM"
        }

        # Determine optimal day of week
        # In a real implementation, this would analyze historical data
        optimal_day = "Tuesday"  # Default to Tuesday as it's generally a good day for email

        # Generate time zone recommendations if we have location data
        time_zone_recommendations = []
        locations = [contact.get("location") for contact in contacts if contact.get("location")]
        if len(set(locations)) > 1:
            time_zone_recommendations.append("Consider scheduling separate sends for different time zones")
            time_zone_recommendations.append("Prioritize sends based on your highest-value regions")

        return {
            "optimal_time": hour_ranges[optimal_time],
            "optimal_day": optimal_day,
            "time_distribution": time_preferences,
            "time_zone_recommendations": time_zone_recommendations
        }

    async def _prioritize_contacts(
        self,
        contacts: List[Dict[str, Any]],
        engagement_scores: Dict[str, Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """Prioritize contacts based on predicted engagement."""
        # Create a list of contacts with their engagement scores
        contact_priorities = []

        for contact in contacts:
            contact_id = contact.get("id", "")
            if contact_id in engagement_scores:
                scores = engagement_scores[contact_id]

                contact_priorities.append({
                    "id": contact_id,
                    "name": contact.get("name", ""),
                    "email": contact.get("email", ""),
                    "overall_engagement": scores["overall_engagement"],
                    "open_probability": scores["open_probability"],
                    "click_probability": scores["click_probability"],
                    "response_probability": scores["response_probability"],
                    "priority_tier": self._assign_priority_tier(scores["overall_engagement"])
                })

        # Sort by overall engagement score
        sorted_contacts = sorted(
            contact_priorities,
            key=lambda x: x["overall_engagement"],
            reverse=True
        )

        return sorted_contacts

    def _assign_priority_tier(self, engagement_score: float) -> str:
        """Assign a priority tier based on engagement score."""
        if engagement_score >= 0.7:
            return "High"
        elif engagement_score >= 0.4:
            return "Medium"
        else:
            return "Low"

    async def _calculate_prediction_confidence(self, engagement_scores: Dict[str, Dict[str, float]]) -> float:
        """Calculate overall confidence in the predictions."""
        # If no scores, return 0 confidence
        if not engagement_scores:
            return 0.0

        # Calculate variance in predictions
        overall_scores = [scores["overall_engagement"] for scores in engagement_scores.values()]
        avg_score = sum(overall_scores) / len(overall_scores)
        variance = sum((score - avg_score) ** 2 for score in overall_scores) / len(overall_scores)

        # Higher variance means less confidence
        variance_factor = max(0.0, 1.0 - variance)

        # Calculate data quality factor based on number of contacts
        data_size_factor = min(1.0, len(engagement_scores) / 100)

        # Calculate average historical data quality
        # (In a real implementation, this would be more sophisticated)
        historical_data_quality = 0.8

        # Combine factors for overall confidence
        confidence = (variance_factor * 0.4 + data_size_factor * 0.3 + historical_data_quality * 0.3)

        return round(confidence, 2)
