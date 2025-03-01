"""Contact discovery tools for OctoTools."""

import logging
import asyncio
import aiohttp
import json
import re
from typing import Dict, Any, List, Optional

from octotools import ToolCard

from ai.config import CONTACT_DISCOVERY_TOOL_CONFIG, LOOKALIKE_AUDIENCE_TOOL_CONFIG

logger = logging.getLogger(__name__)

class ContactDiscoveryTool(ToolCard):
    """Tool for discovering and enriching contacts based on target criteria."""

    def __init__(self):
        """Initialize the contact discovery tool."""
        super().__init__(
            tool_name="Contact_Discovery_Tool",
            tool_description="An advanced tool that discovers and enriches contacts based on target criteria.",
            input_types={
                "target_criteria": "dict - Specifications for the target audience (industry, role, company size, etc.)",
                "discovery_depth": "str - Depth of discovery: 'basic', 'standard', or 'deep'",
                "enrichment_level": "str - Level of contact enrichment: 'minimal', 'standard', or 'comprehensive'"
            },
            output_type="dict - Contains discovered contacts and metadata about the discovery process",
            demo_commands=[
                {
                    "command": 'execution = tool.execute(target_criteria={"industry": "SaaS", "role": "CTO", "company_size": "50-200"}, discovery_depth="standard", enrichment_level="standard")',
                    "description": "Discover contacts who are CTOs in SaaS companies with 50-200 employees"
                }
            ],
            user_metadata={
                "limitations": [
                    "Discovery is subject to rate limits of various data sources",
                    "Contact information is only collected from publicly available sources",
                    "Accuracy of discovery depends on data quality from source platforms"
                ],
                "best_practices": [
                    "Provide specific target criteria for more accurate results",
                    "Start with 'standard' discovery and enrichment levels for balance of speed and quality",
                    "Use 'deep' discovery for critical campaigns where quality outweighs speed"
                ]
            }
        )

        # Initialize configuration
        self.config = CONTACT_DISCOVERY_TOOL_CONFIG

    async def execute(
        self,
        target_criteria: Dict[str, Any],
        discovery_depth: str = "standard",
        enrichment_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Discover and enrich contacts based on target criteria.

        Args:
            target_criteria: Dictionary of target audience criteria
            discovery_depth: Level of discovery depth
            enrichment_level: Level of contact enrichment

        Returns:
            Dictionary containing discovered contacts and metadata
        """
        logger.info(f"Executing contact discovery with depth={discovery_depth}, enrichment={enrichment_level}")

        try:
            # Validate inputs
            self._validate_inputs(target_criteria, discovery_depth, enrichment_level)

            # Determine optimal sources for discovery
            sources = await self._determine_optimal_sources(target_criteria)

            # Execute discovery tasks for each source
            discovery_tasks = [
                self._search_web_data(target_criteria, discovery_depth),
                self._query_business_directories(target_criteria, discovery_depth),
                self._analyze_company_websites(target_criteria, discovery_depth),
                self._process_news_sources(target_criteria, discovery_depth)
            ]

            # Add social media sources if applicable
            if sources.get("social_media", False):
                discovery_tasks.append(self._search_social_media(target_criteria, discovery_depth))

            # Add specialized databases if applicable
            if sources.get("specialized_databases", False):
                discovery_tasks.append(self._query_specialized_databases(target_criteria, discovery_depth))

            # Execute discovery tasks asynchronously
            raw_contacts = await self._execute_parallel_tasks(discovery_tasks)

            # Standardize and deduplicate contacts
            standardized_contacts = await self._standardize_contacts(raw_contacts)

            # Enrich contacts based on specified level
            enriched_contacts = await self._enrich_contacts(standardized_contacts, enrichment_level)

            # Validate and score contact quality
            validated_contacts = await self._validate_and_score(enriched_contacts)

            # Log discovery metrics
            high_quality_contacts = sum(1 for c in validated_contacts if c.get("quality_score", 0) > 0.8)
            logger.info(f"Discovered {len(raw_contacts)} contacts, {len(standardized_contacts)} unique, {high_quality_contacts} high quality")

            return {
                "contacts": validated_contacts,
                "discovery_metrics": {
                    "total_discovered": len(raw_contacts),
                    "unique_contacts": len(standardized_contacts),
                    "high_quality_contacts": high_quality_contacts,
                    "sources_used": list(sources.keys())
                }
            }
        except Exception as e:
            logger.error(f"Contact discovery failed: {str(e)}")
            return {
                "error": str(e),
                "contacts": [],
                "discovery_metrics": {
                    "total_discovered": 0,
                    "unique_contacts": 0,
                    "high_quality_contacts": 0
                }
            }

    def _validate_inputs(self, target_criteria, discovery_depth, enrichment_level):
        """Validate input parameters."""
        if not target_criteria or not isinstance(target_criteria, dict):
            raise ValueError("Target criteria must be a non-empty dictionary")

        valid_depths = self.config["discovery_depths"]
        if discovery_depth not in valid_depths:
            raise ValueError(f"Discovery depth must be one of: {', '.join(valid_depths)}")

        valid_levels = self.config["enrichment_levels"]
        if enrichment_level not in valid_levels:
            raise ValueError(f"Enrichment level must be one of: {', '.join(valid_levels)}")

    async def _determine_optimal_sources(self, target_criteria):
        """Determine the optimal sources for contact discovery based on criteria."""
        # In a real implementation, this would use ML to determine the best sources
        sources = {source: True for source in self.config["data_sources"]}

        # Add specialized sources based on criteria
        sources["social_media"] = "industry" in target_criteria
        sources["specialized_databases"] = (
            "industry" in target_criteria and
            target_criteria["industry"] in ["SaaS", "Fintech", "Healthcare"]
        )

        return sources

    async def _search_web_data(self, target_criteria, discovery_depth):
        """Search web data for contacts matching criteria."""
        # Simulate web search results
        await asyncio.sleep(0.5)  # Simulate API call

        # In a real implementation, this would call actual search APIs
        sample_contacts = [
            {
                "name": "John Smith",
                "email": "john.smith@example.com",
                "role": target_criteria.get("role", ""),
                "company": "Example Corp",
                "source": "web_search"
            },
            {
                "name": "Jane Doe",
                "email": "jane.doe@example.com",
                "role": target_criteria.get("role", ""),
                "company": "Example Inc",
                "source": "web_search"
            },
            {
                "name": "Bob Johnson",
                "email": "bob.johnson@example.com",
                "role": target_criteria.get("role", ""),
                "company": "Example LLC",
                "source": "web_search"
            }
        ]

        # Return different number of contacts based on discovery depth
        if discovery_depth == "basic":
            return sample_contacts[:3]
        elif discovery_depth == "standard":
            return sample_contacts[:5]
        else:  # deep
            return sample_contacts[:10]

    async def _query_business_directories(self, target_criteria, discovery_depth):
        """Query business directories for contacts."""
        # Simulate directory search
        await asyncio.sleep(0.7)  # Simulate API call

        # Sample results
        sample_contacts = [
            {
                "name": "Alice Brown",
                "email": "alice.brown@company.com",
                "role": target_criteria.get("role", ""),
                "company": "Company Inc",
                "source": "business_directory"
            },
            {
                "name": "Charlie Davis",
                "email": "charlie.davis@company.com",
                "role": target_criteria.get("role", ""),
                "company": "Company Inc",
                "source": "business_directory"
            },
            {
                "name": "David Wilson",
                "email": "david.wilson@enterprise.com",
                "role": target_criteria.get("role", ""),
                "company": "Enterprise Corp",
                "source": "business_directory"
            }
        ]

        # Return different number of contacts based on discovery depth
        if discovery_depth == "basic":
            return sample_contacts[:2]
        elif discovery_depth == "standard":
            return sample_contacts[:4]
        else:  # deep
            return sample_contacts[:8]

    async def _analyze_company_websites(self, target_criteria, discovery_depth):
        """Analyze company websites for contacts."""
        # Simulate website analysis
        await asyncio.sleep(0.8)  # Simulate API call

        # Sample results
        sample_contacts = [
            {
                "name": "Emily Johnson",
                "email": "emily.johnson@tech.com",
                "role": target_criteria.get("role", ""),
                "company": "Tech Solutions",
                "source": "company_website"
            },
            {
                "name": "Frank Miller",
                "email": "frank.miller@tech.com",
                "role": target_criteria.get("role", ""),
                "company": "Tech Solutions",
                "source": "company_website"
            }
        ]

        # Return different number of contacts based on discovery depth
        if discovery_depth == "basic":
            return sample_contacts[:1]
        elif discovery_depth == "standard":
            return sample_contacts[:3]
        else:  # deep
            return sample_contacts[:6]

    async def _process_news_sources(self, target_criteria, discovery_depth):
        """Process news sources for contacts."""
        # Simulate news processing
        await asyncio.sleep(0.6)  # Simulate API call

        # Sample results
        sample_contacts = [
            {
                "name": "Grace Lee",
                "email": "grace.lee@newco.com",
                "role": target_criteria.get("role", ""),
                "company": "NewCo",
                "source": "news_source"
            },
            {
                "name": "Henry Wang",
                "email": "henry.wang@startup.com",
                "role": target_criteria.get("role", ""),
                "company": "Startup Inc",
                "source": "news_source"
            }
        ]

        # Return different number of contacts based on discovery depth
        if discovery_depth == "basic":
            return sample_contacts[:1]
        elif discovery_depth == "standard":
            return sample_contacts[:2]
        else:  # deep
            return sample_contacts[:4]

    async def _search_social_media(self, target_criteria, discovery_depth):
        """Search social media for contacts."""
        # Simulate social media search
        await asyncio.sleep(0.9)  # Simulate API call

        # Sample results
        sample_contacts = [
            {
                "name": "Irene Chen",
                "email": "irene.chen@social.com",
                "role": target_criteria.get("role", ""),
                "company": "Social Network",
                "source": "social_media"
            },
            {
                "name": "Jack Thompson",
                "email": "jack.thompson@connect.com",
                "role": target_criteria.get("role", ""),
                "company": "Connect Ltd",
                "source": "social_media"
            }
        ]

        # Return different number of contacts based on discovery depth
        if discovery_depth == "basic":
            return sample_contacts[:1]
        elif discovery_depth == "standard":
            return sample_contacts[:2]
        else:  # deep
            return sample_contacts[:5]

    async def _query_specialized_databases(self, target_criteria, discovery_depth):
        """Query specialized databases for contacts."""
        # Simulate specialized database query
        await asyncio.sleep(1.0)  # Simulate API call

        # Sample results
        sample_contacts = [
            {
                "name": "Karen Martinez",
                "email": "karen.martinez@specialized.com",
                "role": target_criteria.get("role", ""),
                "company": "Specialized Inc",
                "source": "specialized_database"
            },
            {
                "name": "Larry Robinson",
                "email": "larry.robinson@industry.com",
                "role": target_criteria.get("role", ""),
                "company": "Industry Solutions",
                "source": "specialized_database"
            }
        ]

        # Return different number of contacts based on discovery depth
        if discovery_depth == "basic":
            return sample_contacts[:1]
        elif discovery_depth == "standard":
            return sample_contacts[:2]
        else:  # deep
            return sample_contacts[:4]

    async def _execute_parallel_tasks(self, tasks):
        """Execute discovery tasks in parallel."""
        results = await asyncio.gather(*tasks)

        # Flatten the results
        contacts = []
        for result in results:
            contacts.extend(result)

        return contacts

    async def _standardize_contacts(self, contacts):
        """Standardize and deduplicate contacts."""
        # Standardize contact format
        standardized = []
        seen_emails = set()

        for contact in contacts:
            # Skip if no email or already seen
            if not contact.get("email") or contact["email"] in seen_emails:
                continue

            # Standardize format
            standardized_contact = {
                "name": contact.get("name", ""),
                "email": contact.get("email", "").lower(),
                "role": contact.get("role", ""),
                "company": contact.get("company", ""),
                "source": contact.get("source", "unknown")
            }

            standardized.append(standardized_contact)
            seen_emails.add(standardized_contact["email"])

        return standardized

    async def _enrich_contacts(self, contacts, enrichment_level):
        """Enrich contacts with additional information."""
        enriched_contacts = []

        for contact in contacts:
            # Create a copy of the contact
            enriched = contact.copy()

            # Add basic enrichment
            if enrichment_level in ["minimal", "standard", "comprehensive"]:
                enriched["first_name"] = contact["name"].split()[0] if contact["name"] else ""
                enriched["last_name"] = contact["name"].split()[-1] if contact["name"] and len(contact["name"].split()) > 1 else ""

            # Add standard enrichment
            if enrichment_level in ["standard", "comprehensive"]:
                enriched["company_domain"] = contact["email"].split("@")[-1] if contact["email"] else ""
                enriched["company_size"] = "Unknown"
                enriched["industry"] = "Unknown"

                # Simulate API call for company information
                await asyncio.sleep(0.2)

            # Add comprehensive enrichment
            if enrichment_level == "comprehensive":
                enriched["social_profiles"] = {
                    "linkedin": f"https://linkedin.com/in/{enriched['first_name'].lower()}-{enriched['last_name'].lower()}"
                }
                enriched["contact_history"] = []
                enriched["interests"] = []

                # Simulate API call for comprehensive information
                await asyncio.sleep(0.3)

            enriched_contacts.append(enriched)

        return enriched_contacts

    async def _validate_and_score(self, contacts):
        """Validate contacts and assign quality scores."""
        validated_contacts = []

        for contact in contacts:
            # Create a copy of the contact
            validated = contact.copy()

            # Validate email format
            email_valid = bool(re.match(r"[^@]+@[^@]+\.[^@]+", contact["email"]))

            # Calculate quality score (0.0 to 1.0)
            quality_factors = {
                "has_name": bool(contact.get("name")),
                "has_valid_email": email_valid,
                "has_role": bool(contact.get("role")),
                "has_company": bool(contact.get("company")),
                "has_first_name": bool(contact.get("first_name")),
                "has_last_name": bool(contact.get("last_name")),
                "has_company_domain": bool(contact.get("company_domain")),
                "has_social_profiles": bool(contact.get("social_profiles"))
            }

            # Count the number of positive factors
            positive_factors = sum(1 for factor in quality_factors.values() if factor)

            # Calculate score (0.0 to 1.0)
            quality_score = positive_factors / len(quality_factors)

            # Add validation info to contact
            validated["email_valid"] = email_valid
            validated["quality_score"] = quality_score

            validated_contacts.append(validated)

        # Sort by quality score (highest first)
        validated_contacts.sort(key=lambda x: x["quality_score"], reverse=True)

        return validated_contacts


class LookalikeAudienceTool(ToolCard):
    """Tool for generating lookalike audiences based on seed contacts."""

    def __init__(self):
        """Initialize the lookalike audience tool."""
        super().__init__(
            tool_name="Lookalike_Audience_Tool",
            tool_description="A tool that generates lookalike audiences based on seed contacts.",
            input_types={
                "seed_contacts": "list - List of seed contacts to use as the basis for lookalike generation",
                "expansion_factor": "int - Factor by which to expand the audience (default: 3)",
                "similarity_threshold": "float - Minimum similarity score for inclusion (0.0-1.0, default: 0.7)"
            },
            output_type="dict - Contains generated lookalike contacts and metrics",
            demo_commands=[
                {
                    "command": 'execution = tool.execute(seed_contacts=[{"email": "john@example.com", "role": "CTO"}], expansion_factor=3, similarity_threshold=0.7)',
                    "description": "Generate lookalike contacts based on a seed contact, expanding by factor of 3"
                }
            ],
            user_metadata={
                "limitations": [
                    "Lookalike quality depends on the quality and quantity of seed contacts",
                    "Higher similarity thresholds produce more relevant but fewer contacts",
                    "Algorithm performs best with at least 10 seed contacts"
                ],
                "best_practices": [
                    "Use high-quality seed contacts with complete profiles",
                    "Start with default similarity threshold of 0.7, then adjust based on results",
                    "For B2B, include industry and role information in seed contacts"
                ]
            }
        )

        # Initialize configuration
        self.config = LOOKALIKE_AUDIENCE_TOOL_CONFIG

    async def execute(
        self,
        seed_contacts: List[Dict[str, Any]],
        expansion_factor: int = 3,
        similarity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate lookalike contacts based on seed contacts.

        Args:
            seed_contacts: List of seed contacts to use as basis
            expansion_factor: Factor by which to expand the audience
            similarity_threshold: Minimum similarity score (0.0-1.0)

        Returns:
            Dictionary containing lookalike contacts and metrics
        """
        logger.info(f"Executing lookalike audience generation with {len(seed_contacts)} seed contacts")

        try:
            # Validate inputs
            self._validate_inputs(seed_contacts, expansion_factor, similarity_threshold)

            # Extract features from seed contacts
            seed_features = await self._extract_contact_features(seed_contacts)

            # Generate embeddings for seed contacts
            seed_embeddings = await self._generate_embeddings(seed_features)

            # Find similar profiles
            candidate_contacts = await self._find_similar_profiles(seed_embeddings, expansion_factor)

            # Filter candidates by similarity threshold
            filtered_candidates = [
                contact for contact in candidate_contacts
                if contact.get("similarity_score", 0) >= similarity_threshold
            ]

            # Enrich lookalike contacts
            enriched_lookalikes = await self._enrich_lookalike_contacts(filtered_candidates)

            # Segment lookalikes into clusters
            segmented_lookalikes = await self._segment_lookalikes(enriched_lookalikes)

            # Log lookalike metrics
            logger.info(f"Generated {len(enriched_lookalikes)} lookalike contacts in {len(segmented_lookalikes)} segments")

            return {
                "lookalike_contacts": enriched_lookalikes,
                "segments": segmented_lookalikes,
                "metrics": {
                    "seed_size": len(seed_contacts),
                    "lookalike_size": len(enriched_lookalikes),
                    "average_similarity": sum(c.get("similarity_score", 0) for c in enriched_lookalikes) / max(len(enriched_lookalikes), 1),
                    "segment_count": len(segmented_lookalikes)
                }
            }
        except Exception as e:
            logger.error(f"Lookalike audience generation failed: {str(e)}")
            return {
                "error": str(e),
                "lookalike_contacts": [],
                "segments": [],
                "metrics": {
                    "seed_size": len(seed_contacts),
                    "lookalike_size": 0,
                    "average_similarity": 0,
                    "segment_count": 0
                }
            }

    def _validate_inputs(self, seed_contacts, expansion_factor, similarity_threshold):
        """Validate input parameters."""
        if not seed_contacts or not isinstance(seed_contacts, list):
            raise ValueError("Seed contacts must be a non-empty list")

        if len(seed_contacts) < self.config["min_seed_contacts"]:
            logger.warning(f"Seed contacts count ({len(seed_contacts)}) is below recommended minimum ({self.config['min_seed_contacts']})")

        if expansion_factor < 1 or expansion_factor > self.config["max_expansion_factor"]:
            raise ValueError(f"Expansion factor must be between 1 and {self.config['max_expansion_factor']}")

        if similarity_threshold < self.config["min_similarity_threshold"] or similarity_threshold > 1.0:
            raise ValueError(f"Similarity threshold must be between {self.config['min_similarity_threshold']} and 1.0")

    async def _extract_contact_features(self, contacts):
        """Extract features from seed contacts."""
        # Simulate feature extraction
        await asyncio.sleep(0.5)  # Simulate processing

        features = []
        for contact in contacts:
            # Extract features from contact
            feature = {
                "email_domain": contact.get("email", "").split("@")[-1] if contact.get("email") else "",
                "role": contact.get("role", ""),
                "company": contact.get("company", ""),
                "industry": contact.get("industry", ""),
                "company_size": contact.get("company_size", "")
            }

            features.append(feature)

        return features

    async def _generate_embeddings(self, features):
        """Generate embeddings for contact features."""
        # Simulate embedding generation
        await asyncio.sleep(0.7)  # Simulate processing

        # In a real implementation, this would use a vector embedding model
        # For now, we'll just return the features as is
        return features

    async def _find_similar_profiles(self, seed_embeddings, expansion_factor):
        """Find similar profiles based on seed embeddings."""
        # Simulate similarity search
        await asyncio.sleep(1.0)  # Simulate API call

        # Calculate the number of lookalikes to generate
        num_lookalikes = len(seed_embeddings) * expansion_factor

        # Generate sample lookalike contacts
        lookalikes = []
        for i in range(num_lookalikes):
            # Generate a sample lookalike contact
            similarity_score = 0.5 + (0.5 * (num_lookalikes - i) / num_lookalikes)  # Decreasing similarity

            lookalike = {
                "name": f"Lookalike Contact {i+1}",
                "email": f"lookalike{i+1}@example.com",
                "role": seed_embeddings[i % len(seed_embeddings)].get("role", ""),
                "company": f"Lookalike Company {i+1}",
                "similarity_score": similarity_score
            }

            lookalikes.append(lookalike)

        return lookalikes

    async def _enrich_lookalike_contacts(self, contacts):
        """Enrich lookalike contacts with additional information."""
        # Simulate enrichment
        await asyncio.sleep(0.8)  # Simulate API call

        enriched_contacts = []
        for contact in contacts:
            # Create a copy of the contact
            enriched = contact.copy()

            # Add enrichment data
            enriched["first_name"] = contact["name"].split()[0] if contact["name"] else ""
            enriched["last_name"] = contact["name"].split()[-1] if contact["name"] and len(contact["name"].split()) > 1 else ""
            enriched["company_domain"] = contact["email"].split("@")[-1] if contact["email"] else ""
            enriched["industry"] = "Technology"  # Sample industry
            enriched["company_size"] = "50-200"  # Sample company size

            enriched_contacts.append(enriched)

        return enriched_contacts

    async def _segment_lookalikes(self, contacts):
        """Segment lookalike contacts into clusters."""
        # Simulate segmentation
        await asyncio.sleep(0.6)  # Simulate processing

        # In a real implementation, this would use clustering algorithms
        # For now, we'll create simple segments based on role and industry

        # Group contacts by role
        role_segments = {}
        for contact in contacts:
            role = contact.get("role", "Unknown")
            if role not in role_segments:
                role_segments[role] = []

            role_segments[role].append(contact)

        # Create segment objects
        segments = []
        for role, segment_contacts in role_segments.items():
            segment = {
                "name": f"{role} Segment",
                "criteria": {"role": role},
                "size": len(segment_contacts),
                "average_similarity": sum(c.get("similarity_score", 0) for c in segment_contacts) / max(len(segment_contacts), 1)
            }

            segments.append(segment)

        # Sort segments by size (largest first)
        segments.sort(key=lambda x: x["size"], reverse=True)

        # Limit to max segments
        return segments[:self.config["max_segments"]]
