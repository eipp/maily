from typing import Dict, Any, List, Optional
import logging
import json
import asyncio

from apps.api.octotools_integration.tool_cards import MailyToolCard

logger = logging.getLogger(__name__)

class SmartSegmentationTool(MailyToolCard):
    def __init__(self):
        super().__init__(
            tool_name="Smart_Segmentation_Tool",
            tool_description="A tool that intelligently segments contacts based on various criteria and strategies.",
            input_types={
                "contacts": "list - List of contacts to segment",
                "segmentation_strategy": "str - Strategy to use: 'auto', 'behavioral', 'firmographic', 'technographic', 'intent_based', or 'hybrid'",
                "max_segments": "int - Maximum number of segments to create (default: 10)"
            },
            output_type="dict - Contains segmented contacts and metadata",
            demo_commands=[
                {
                    "command": 'execution = tool.execute(contacts=[{"email": "john@example.com", "role": "CTO"}], segmentation_strategy="auto", max_segments=5)',
                    "description": "Automatically segment contacts into up to 5 segments"
                }
            ],
            user_metadata={
                "limitations": [
                    "Segmentation quality depends on the richness of contact data",
                    "Some strategies require specific data fields (e.g., behavioral requires engagement history)",
                    "Maximum of 20 segments can be created regardless of max_segments parameter"
                ],
                "best_practices": [
                    "Use 'auto' strategy when unsure which approach is best",
                    "Ensure contacts have complete profiles for better segmentation",
                    "Limit max_segments to keep segments manageable (5-10 is ideal)"
                ]
            }
        )

    async def execute(
        self,
        contacts: List[Dict[str, Any]],
        segmentation_strategy: str = "auto",
        max_segments: int = 10
    ) -> Dict[str, Any]:
        """
        Segment contacts based on the specified strategy.

        Args:
            contacts: List of contacts to segment
            segmentation_strategy: Strategy to use for segmentation
            max_segments: Maximum number of segments to create

        Returns:
            Dictionary containing segmented contacts and metadata
        """
        self._log_execution(
            {"contacts_count": len(contacts), "segmentation_strategy": segmentation_strategy, "max_segments": max_segments},
            "Executing smart segmentation"
        )

        try:
            # Validate inputs
            self._validate_inputs(contacts, segmentation_strategy, max_segments)

            # Extract features for segmentation
            contact_features = await self._extract_segmentation_features(contacts)

            # Determine optimal segmentation strategy if 'auto'
            if segmentation_strategy == "auto":
                segmentation_strategy = await self._determine_optimal_strategy(contact_features)

            # Apply selected segmentation algorithm
            if segmentation_strategy == "behavioral":
                segments = await self._apply_behavioral_segmentation(contact_features)
            elif segmentation_strategy == "firmographic":
                segments = await self._apply_firmographic_segmentation(contact_features)
            elif segmentation_strategy == "technographic":
                segments = await self._apply_technographic_segmentation(contact_features)
            elif segmentation_strategy == "intent_based":
                segments = await self._apply_intent_based_segmentation(contact_features)
            elif segmentation_strategy == "hybrid":
                segments = await self._apply_hybrid_segmentation(contact_features)
            else:
                raise ValueError(f"Unsupported segmentation strategy: {segmentation_strategy}")

            # Limit to maximum number of segments if needed
            if len(segments) > max_segments:
                segments = await self._consolidate_segments(segments, max_segments)

            # Generate segment insights
            segment_insights = await self._generate_segment_insights(segments)

            # Calculate segment distribution
            segment_distribution = await self._calculate_segment_distribution(segments)

            return {
                "segments": segments,
                "strategy_used": segmentation_strategy,
                "segment_count": len(segments),
                "segment_insights": segment_insights,
                "segment_distribution": segment_distribution
            }
        except Exception as e:
            logger.error(f"Smart segmentation failed: {str(e)}")
            return {
                "error": str(e),
                "segments": [],
                "strategy_used": segmentation_strategy,
                "segment_count": 0,
                "segment_insights": {},
                "segment_distribution": {}
            }

    def _validate_inputs(self, contacts, segmentation_strategy, max_segments):
        """Validate input parameters."""
        if not contacts:
            raise ValueError("Contacts list cannot be empty")

        valid_strategies = ["auto", "behavioral", "firmographic", "technographic", "intent_based", "hybrid"]
        if segmentation_strategy not in valid_strategies:
            raise ValueError(f"Segmentation strategy must be one of: {', '.join(valid_strategies)}")

        if not isinstance(max_segments, int) or max_segments < 1:
            raise ValueError("max_segments must be a positive integer")

    async def _extract_segmentation_features(self, contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract features for segmentation from contacts."""
        features = []

        for contact in contacts:
            # Basic features
            contact_features = {
                "id": contact.get("id", ""),
                "email": contact.get("email", ""),
                "role": contact.get("role", ""),
                "company": contact.get("company", ""),
                "industry": contact.get("industry", ""),
                "company_size": contact.get("company_size", ""),
                "location": contact.get("location", ""),
            }

            # Behavioral features
            contact_features["engagement_score"] = contact.get("engagement_score", 0)
            contact_features["open_rate"] = contact.get("open_rate", 0)
            contact_features["click_rate"] = contact.get("click_rate", 0)
            contact_features["response_rate"] = contact.get("response_rate", 0)
            contact_features["last_engagement"] = contact.get("last_engagement", "")

            # Technographic features
            contact_features["technologies"] = contact.get("technologies", [])
            contact_features["platforms"] = contact.get("platforms", [])

            # Intent features
            contact_features["recent_searches"] = contact.get("recent_searches", [])
            contact_features["content_interests"] = contact.get("content_interests", [])

            features.append(contact_features)

        return features

    async def _determine_optimal_strategy(self, contact_features: List[Dict[str, Any]]) -> str:
        """Determine the optimal segmentation strategy based on available data."""
        # Count contacts with different types of data
        behavioral_count = sum(1 for f in contact_features if f["engagement_score"] > 0 or f["open_rate"] > 0)
        firmographic_count = sum(1 for f in contact_features if f["company"] and f["industry"])
        technographic_count = sum(1 for f in contact_features if f["technologies"])
        intent_count = sum(1 for f in contact_features if f["recent_searches"] or f["content_interests"])

        # Calculate data quality scores
        total_contacts = len(contact_features)
        behavioral_score = behavioral_count / total_contacts if total_contacts > 0 else 0
        firmographic_score = firmographic_count / total_contacts if total_contacts > 0 else 0
        technographic_score = technographic_count / total_contacts if total_contacts > 0 else 0
        intent_score = intent_count / total_contacts if total_contacts > 0 else 0

        # Determine best strategy based on data quality
        if behavioral_score > 0.7 and firmographic_score > 0.7:
            return "hybrid"
        elif behavioral_score > 0.7:
            return "behavioral"
        elif firmographic_score > 0.7:
            return "firmographic"
        elif technographic_score > 0.5:
            return "technographic"
        elif intent_score > 0.5:
            return "intent_based"
        else:
            return "firmographic"  # Default to firmographic if no clear winner

    async def _apply_behavioral_segmentation(self, contact_features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply behavioral segmentation algorithm."""
        # Define behavioral segments
        segments = [
            {
                "id": "high_engagers",
                "name": "High Engagers",
                "description": "Contacts with high engagement scores and frequent interactions",
                "criteria": lambda f: f["engagement_score"] > 0.7 or f["open_rate"] > 0.5,
                "contacts": []
            },
            {
                "id": "moderate_engagers",
                "name": "Moderate Engagers",
                "description": "Contacts with moderate engagement and occasional interactions",
                "criteria": lambda f: 0.3 < f["engagement_score"] <= 0.7 or 0.2 < f["open_rate"] <= 0.5,
                "contacts": []
            },
            {
                "id": "low_engagers",
                "name": "Low Engagers",
                "description": "Contacts with low engagement who rarely interact",
                "criteria": lambda f: f["engagement_score"] <= 0.3 or f["open_rate"] <= 0.2,
                "contacts": []
            },
            {
                "id": "recent_engagers",
                "name": "Recent Engagers",
                "description": "Contacts who engaged recently regardless of frequency",
                "criteria": lambda f: f["last_engagement"] and f["last_engagement"] > "2023-01-01",
                "contacts": []
            },
            {
                "id": "inactive",
                "name": "Inactive",
                "description": "Contacts with no recent engagement",
                "criteria": lambda f: not f["last_engagement"] or f["last_engagement"] <= "2023-01-01",
                "contacts": []
            }
        ]

        # Assign contacts to segments
        for feature in contact_features:
            for segment in segments:
                if segment["criteria"](feature):
                    segment["contacts"].append(feature["id"])

        # Remove empty segments
        segments = [s for s in segments if s["contacts"]]

        # Clean up segments for return
        for segment in segments:
            del segment["criteria"]

        return segments

    async def _apply_firmographic_segmentation(self, contact_features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply firmographic segmentation algorithm."""
        # Define industry segments
        industry_segments = {}

        # Group contacts by industry
        for feature in contact_features:
            industry = feature.get("industry", "Unknown")
            if industry not in industry_segments:
                industry_segments[industry] = {
                    "id": f"industry_{industry.lower().replace(' ', '_')}",
                    "name": f"{industry} Industry",
                    "description": f"Contacts in the {industry} industry",
                    "contacts": []
                }
            industry_segments[industry]["contacts"].append(feature["id"])

        # Define company size segments
        size_segments = {
            "enterprise": {
                "id": "company_size_enterprise",
                "name": "Enterprise",
                "description": "Contacts from enterprise companies (1000+ employees)",
                "contacts": []
            },
            "mid_market": {
                "id": "company_size_mid_market",
                "name": "Mid-Market",
                "description": "Contacts from mid-market companies (100-999 employees)",
                "contacts": []
            },
            "small_business": {
                "id": "company_size_small_business",
                "name": "Small Business",
                "description": "Contacts from small businesses (1-99 employees)",
                "contacts": []
            }
        }

        # Assign contacts to company size segments
        for feature in contact_features:
            company_size = feature.get("company_size", "")
            if company_size:
                try:
                    size = int(company_size)
                    if size >= 1000:
                        size_segments["enterprise"]["contacts"].append(feature["id"])
                    elif size >= 100:
                        size_segments["mid_market"]["contacts"].append(feature["id"])
                    else:
                        size_segments["small_business"]["contacts"].append(feature["id"])
                except (ValueError, TypeError):
                    # Handle non-numeric company sizes
                    pass

        # Combine segments
        segments = list(industry_segments.values()) + [s for s in size_segments.values() if s["contacts"]]

        return segments

    async def _apply_technographic_segmentation(self, contact_features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply technographic segmentation algorithm."""
        # Placeholder implementation
        # In a real implementation, this would use more sophisticated clustering

        # Define technology segments
        tech_segments = {}

        # Group contacts by technology
        for feature in contact_features:
            technologies = feature.get("technologies", [])
            for tech in technologies:
                if tech not in tech_segments:
                    tech_segments[tech] = {
                        "id": f"tech_{tech.lower().replace(' ', '_')}",
                        "name": f"{tech} Users",
                        "description": f"Contacts using {tech} technology",
                        "contacts": []
                    }
                tech_segments[tech]["contacts"].append(feature["id"])

        # Return non-empty segments
        segments = [s for s in tech_segments.values() if s["contacts"]]

        return segments

    async def _apply_intent_based_segmentation(self, contact_features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply intent-based segmentation algorithm."""
        # Placeholder implementation
        # In a real implementation, this would use more sophisticated intent analysis

        # Define intent segments
        intent_segments = {}

        # Group contacts by content interests
        for feature in contact_features:
            interests = feature.get("content_interests", [])
            for interest in interests:
                if interest not in intent_segments:
                    intent_segments[interest] = {
                        "id": f"intent_{interest.lower().replace(' ', '_')}",
                        "name": f"{interest} Interest",
                        "description": f"Contacts interested in {interest}",
                        "contacts": []
                    }
                intent_segments[interest]["contacts"].append(feature["id"])

        # Return non-empty segments
        segments = [s for s in intent_segments.values() if s["contacts"]]

        return segments

    async def _apply_hybrid_segmentation(self, contact_features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply hybrid segmentation algorithm combining multiple approaches."""
        # Get segments from different strategies
        behavioral_segments = await self._apply_behavioral_segmentation(contact_features)
        firmographic_segments = await self._apply_firmographic_segmentation(contact_features)

        # Create intersection segments for high-value combinations
        high_value_segments = []

        # Find high-engaging decision makers
        high_engagers = next((s for s in behavioral_segments if s["id"] == "high_engagers"), None)

        if high_engagers:
            # Create segments for high-engaging contacts in each industry
            for industry_segment in [s for s in firmographic_segments if s["id"].startswith("industry_")]:
                intersection = list(set(high_engagers["contacts"]) & set(industry_segment["contacts"]))
                if intersection:
                    high_value_segments.append({
                        "id": f"high_engaging_{industry_segment['id']}",
                        "name": f"High-Engaging {industry_segment['name']}",
                        "description": f"Highly engaged contacts in the {industry_segment['name']}",
                        "contacts": intersection
                    })

        # Combine all segments
        segments = behavioral_segments + firmographic_segments + high_value_segments

        return segments

    async def _consolidate_segments(self, segments: List[Dict[str, Any]], max_segments: int) -> List[Dict[str, Any]]:
        """Consolidate segments to reduce to the maximum number."""
        if len(segments) <= max_segments:
            return segments

        # Sort segments by size (number of contacts)
        sorted_segments = sorted(segments, key=lambda s: len(s["contacts"]), reverse=True)

        # Keep the largest segments up to max_segments - 1
        kept_segments = sorted_segments[:max_segments - 1]

        # Combine the remaining segments into an "Other" segment
        other_segments = sorted_segments[max_segments - 1:]
        other_contacts = []
        for segment in other_segments:
            other_contacts.extend(segment["contacts"])

        # Remove duplicates
        other_contacts = list(set(other_contacts))

        # Create the "Other" segment
        other_segment = {
            "id": "other",
            "name": "Other",
            "description": "Contacts that don't fit into the primary segments",
            "contacts": other_contacts
        }

        # Add the "Other" segment to the kept segments
        kept_segments.append(other_segment)

        return kept_segments

    async def _generate_segment_insights(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights for each segment."""
        insights = {}

        for segment in segments:
            segment_id = segment["id"]
            contact_count = len(segment["contacts"])

            insights[segment_id] = {
                "contact_count": contact_count,
                "percentage_of_total": 0,  # Will be calculated later
                "recommended_approach": self._get_recommended_approach(segment),
                "optimal_content_types": self._get_optimal_content_types(segment),
                "engagement_potential": self._calculate_engagement_potential(segment)
            }

        # Calculate percentage of total
        total_contacts = sum(len(s["contacts"]) for s in segments)
        for segment_id, insight in insights.items():
            insight["percentage_of_total"] = round(insight["contact_count"] / total_contacts * 100, 2) if total_contacts > 0 else 0

        return insights

    def _get_recommended_approach(self, segment: Dict[str, Any]) -> str:
        """Get recommended marketing approach for a segment."""
        segment_id = segment["id"]

        # Behavioral segment recommendations
        if segment_id == "high_engagers":
            return "Direct sales outreach with personalized messaging"
        elif segment_id == "moderate_engagers":
            return "Nurture with valuable content and occasional direct outreach"
        elif segment_id == "low_engagers":
            return "Re-engagement campaigns with high-value content"
        elif segment_id == "recent_engagers":
            return "Follow up on recent interactions with next steps"
        elif segment_id == "inactive":
            return "Re-engagement or win-back campaign"

        # Firmographic segment recommendations
        elif segment_id.startswith("industry_"):
            return "Industry-specific content and case studies"
        elif segment_id == "company_size_enterprise":
            return "Enterprise-focused messaging with ROI emphasis"
        elif segment_id == "company_size_mid_market":
            return "Growth-focused messaging with scalability emphasis"
        elif segment_id == "company_size_small_business":
            return "Value-focused messaging with quick implementation emphasis"

        # Technology segment recommendations
        elif segment_id.startswith("tech_"):
            return "Integration-focused messaging with technical content"

        # Intent segment recommendations
        elif segment_id.startswith("intent_"):
            return "Content aligned with expressed interests and buying signals"

        # Hybrid segment recommendations
        elif segment_id.startswith("high_engaging_"):
            return "Priority sales outreach with industry-specific messaging"

        # Default recommendation
        else:
            return "General messaging with value proposition"

    def _get_optimal_content_types(self, segment: Dict[str, Any]) -> List[str]:
        """Get optimal content types for a segment."""
        segment_id = segment["id"]

        # Behavioral segment content types
        if segment_id == "high_engagers":
            return ["Case studies", "Product demos", "Exclusive webinars"]
        elif segment_id == "moderate_engagers":
            return ["Whitepapers", "Industry reports", "Webinars"]
        elif segment_id == "low_engagers":
            return ["Blog posts", "Infographics", "Short videos"]
        elif segment_id == "recent_engagers":
            return ["Follow-up content", "Next steps guides", "ROI calculators"]
        elif segment_id == "inactive":
            return ["Re-introduction content", "Industry trends", "Special offers"]

        # Firmographic segment content types
        elif segment_id.startswith("industry_"):
            industry = segment_id.replace("industry_", "").replace("_", " ").title()
            return [f"{industry} case studies", f"{industry} best practices", "Industry benchmarks"]
        elif segment_id == "company_size_enterprise":
            return ["Enterprise case studies", "ROI analysis", "Implementation guides"]
        elif segment_id == "company_size_mid_market":
            return ["Growth strategies", "Scalability guides", "Competitive analysis"]
        elif segment_id == "company_size_small_business":
            return ["Quick-start guides", "Cost-effective solutions", "DIY implementation"]

        # Technology segment content types
        elif segment_id.startswith("tech_"):
            tech = segment_id.replace("tech_", "").replace("_", " ").title()
            return [f"{tech} integration guides", "Technical documentation", "API examples"]

        # Intent segment content types
        elif segment_id.startswith("intent_"):
            interest = segment_id.replace("intent_", "").replace("_", " ").title()
            return [f"{interest} deep dives", f"{interest} best practices", "Expert interviews"]

        # Hybrid segment content types
        elif segment_id.startswith("high_engaging_"):
            return ["Personalized case studies", "Custom ROI analysis", "Executive briefings"]

        # Default content types
        else:
            return ["Product overviews", "Industry insights", "Customer testimonials"]

    def _calculate_engagement_potential(self, segment: Dict[str, Any]) -> str:
        """Calculate engagement potential for a segment."""
        segment_id = segment["id"]

        # High potential segments
        high_potential = ["high_engagers", "recent_engagers"]
        if segment_id in high_potential or segment_id.startswith("high_engaging_"):
            return "High"

        # Medium potential segments
        medium_potential = ["moderate_engagers", "company_size_enterprise", "company_size_mid_market"]
        if segment_id in medium_potential or segment_id.startswith("intent_"):
            return "Medium"

        # Low potential segments
        low_potential = ["low_engagers", "inactive", "company_size_small_business"]
        if segment_id in low_potential:
            return "Low"

        # Default potential
        return "Medium"

    async def _calculate_segment_distribution(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate segment distribution statistics."""
        # Count contacts in each segment
        segment_counts = {s["id"]: len(s["contacts"]) for s in segments}

        # Calculate total contacts
        total_contacts = sum(segment_counts.values())

        # Calculate percentages
        segment_percentages = {
            s_id: round(count / total_contacts * 100, 2) if total_contacts > 0 else 0
            for s_id, count in segment_counts.items()
        }

        # Find largest and smallest segments
        largest_segment = max(segment_counts.items(), key=lambda x: x[1]) if segment_counts else ("none", 0)
        smallest_segment = min(segment_counts.items(), key=lambda x: x[1]) if segment_counts else ("none", 0)

        return {
            "total_contacts": total_contacts,
            "segment_counts": segment_counts,
            "segment_percentages": segment_percentages,
            "largest_segment": {
                "id": largest_segment[0],
                "count": largest_segment[1],
                "percentage": segment_percentages.get(largest_segment[0], 0)
            },
            "smallest_segment": {
                "id": smallest_segment[0],
                "count": smallest_segment[1],
                "percentage": segment_percentages.get(smallest_segment[0], 0)
            }
        }
