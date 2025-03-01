from typing import Dict, Any, List, Optional, Tuple, Set
import logging
import time
import uuid
import re
from datetime import datetime, timedelta
from fastapi import HTTPException
import os
import asyncio
from pydantic import EmailStr

from .octotools_service import OctoToolsService
from .blockchain import BlockchainService
from api.models.contact import Contact, ContactHealthScore
from api.utils.email_validator import validate_email_syntax, validate_email_smtp, check_domain_reputation

logger = logging.getLogger(__name__)

# Create service instances
octotools_service = OctoToolsService()
blockchain_service = BlockchainService()

class ContactService:
    """Service for advanced contact intelligence and management."""

    def __init__(self):
        """Initialize the contact service with advanced intelligence capabilities."""
        # Configure validation thresholds
        self.bounce_threshold = 3  # Number of bounces before marking as invalid
        self.engagement_threshold = 90  # Days without engagement before flagging
        self.quality_score_weights = {
            "email_syntax": 0.15,
            "domain_reputation": 0.10,
            "smtp_validation": 0.10,
            "engagement_rate": 0.20,
            "bounce_history": 0.15,
            "cross_platform_verification": 0.15,
            "social_presence": 0.05,
            "consent_level": 0.10
        }

        # Initialize domain intelligence database
        self.domain_reputation_db = {}
        self.esp_change_history = {}
        self.company_status_changes = {}

        # Initialize contact network graph
        self.contact_relationship_graph = {}

        # Known disposable email domains
        self.disposable_domains = set([
            "mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com",
            "throwawaymail.com", "yopmail.com", "getnada.com", "temp-mail.org"
        ])

        # Initialize regulatory compliance rules by region
        self.compliance_rules = {
            "GDPR": {
                "consent_required": True,
                "max_retention_period": 730,  # days
                "requires_double_opt_in": True,
                "countries": ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
                            "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
                            "PL", "PT", "RO", "SK", "SI", "ES", "SE", "GB"]
            },
            "CCPA": {
                "consent_required": True,
                "max_retention_period": 1095,  # days
                "requires_double_opt_in": False,
                "countries": ["US-CA"]
            },
            "CASL": {
                "consent_required": True,
                "max_retention_period": 730,  # days
                "requires_double_opt_in": True,
                "countries": ["CA"]
            }
        }

    async def get_contacts(
        self,
        user_id: str,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "quality_score",
        sort_direction: str = "desc",
        filter_by: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Contact], int]:
        """
        Get contacts for a user with pagination, search and advanced filtering.

        Args:
            user_id: The user ID
            search: Optional search term
            limit: Maximum number of contacts to return
            offset: Offset for pagination
            sort_by: Field to sort results by
            sort_direction: Sort direction (asc/desc)
            filter_by: Advanced filtering options

        Returns:
            Tuple of (list of contacts, total count)
        """
        try:
            # In a real implementation, this would fetch from a database
            # For now, we'll return mock data with enhanced fields

            # Generate mock contacts with enhanced health scores
            all_contacts = [
                Contact(
                    id=f"contact_{i}",
                    name=f"Contact {i}",
                    email=f"contact{i}@example.com",
                    role="Software Engineer" if i % 3 == 0 else "Product Manager" if i % 3 == 1 else "Designer",
                    company="Tech Company" if i % 2 == 0 else "Creative Agency",
                    industry="Technology" if i % 2 == 0 else "Marketing",
                    created_at="2023-01-15T10:30:00Z",
                    updated_at="2023-01-15T10:30:00Z",
                    quality_score=0.8 + (i % 3) * 0.1,
                    health_score=ContactHealthScore(
                        overall=80 + (i % 3) * 5,
                        email_validity=90 + (i % 2) * 5,
                        engagement=75 + (i % 4) * 5,
                        deliverability=85 + (i % 3) * 5,
                        consent_level="explicit" if i % 3 == 0 else "implied" if i % 3 == 1 else "unknown",
                        domain_reputation=0.9 if i % 2 == 0 else 0.8,
                        last_evaluated=datetime.now().isoformat()
                    ),
                    verification_status={
                        "email_syntax": True,
                        "domain_exists": True,
                        "smtp_valid": i % 5 != 0,  # Some contacts have SMTP issues
                        "cross_platform_verified": bool(i % 3),
                        "blockchain_verified": bool(i % 7)
                    },
                    engagement_metrics={
                        "open_rate": 0.4 + (i % 5) * 0.1,
                        "click_rate": 0.2 + (i % 5) * 0.05,
                        "response_rate": 0.1 + (i % 10) * 0.02,
                        "last_engagement": (datetime.now() - timedelta(days=i % 30)).isoformat() if i % 10 != 0 else None
                    },
                    bounce_history={
                        "hard_bounces": i % 10 == 0,  # Some contacts have hard bounces
                        "soft_bounces": i % 5 == 0,   # Some have soft bounces
                        "last_bounce": (datetime.now() - timedelta(days=i % 20)).isoformat() if i % 5 == 0 else None,
                        "bounce_categories": ["mailbox_full"] if i % 5 == 0 else []
                    },
                    social_profiles={
                        "linkedin": f"https://linkedin.com/in/contact{i}" if i % 3 == 0 else None,
                        "twitter": f"https://twitter.com/contact{i}" if i % 4 == 0 else None
                    },
                    tags=["lead"] if i % 5 == 0 else ["customer"] if i % 5 == 1 else [],
                    compliance_info={
                        "consent_timestamp": (datetime.now() - timedelta(days=i % 60)).isoformat(),
                        "consent_source": "web_form" if i % 3 == 0 else "import" if i % 3 == 1 else "api",
                        "applicable_regulations": ["GDPR"] if i % 4 == 0 else ["CCPA"] if i % 4 == 1 else [],
                        "data_retention_limit": (datetime.now() + timedelta(days=730)).isoformat()
                    },
                    decay_prediction={
                        "predicted_inactive_date": (datetime.now() + timedelta(days=90 + i % 100)).isoformat(),
                        "churn_probability": 0.1 + (i % 10) * 0.05,
                        "predicted_lifetime_value": 100 + (i % 10) * 20
                    }
                )
                for i in range(1, 101)
            ]

            # Apply search filter if provided
            if search:
                search_lower = search.lower()
                filtered_contacts = [
                    contact for contact in all_contacts
                    if search_lower in contact.name.lower() or
                       search_lower in contact.email.lower() or
                       (contact.company and search_lower in contact.company.lower()) or
                       (contact.role and search_lower in contact.role.lower())
                ]
            else:
                filtered_contacts = all_contacts

            # Apply advanced filters if provided
            if filter_by:
                if "min_health_score" in filter_by:
                    filtered_contacts = [c for c in filtered_contacts if c.health_score.overall >= filter_by["min_health_score"]]

                if "verification_status" in filter_by:
                    status = filter_by["verification_status"]
                    filtered_contacts = [c for c in filtered_contacts if c.verification_status.get(status, False)]

                if "engagement_threshold" in filter_by:
                    threshold = filter_by["engagement_threshold"]
                    filtered_contacts = [
                        c for c in filtered_contacts
                        if c.engagement_metrics.get("open_rate", 0) >= threshold or
                        c.engagement_metrics.get("click_rate", 0) >= threshold/2
                    ]

                if "bounce_status" in filter_by:
                    if filter_by["bounce_status"] == "has_bounces":
                        filtered_contacts = [
                            c for c in filtered_contacts
                            if c.bounce_history.get("hard_bounces", False) or c.bounce_history.get("soft_bounces", False)
                        ]
                    elif filter_by["bounce_status"] == "no_bounces":
                        filtered_contacts = [
                            c for c in filtered_contacts
                            if not c.bounce_history.get("hard_bounces", False) and not c.bounce_history.get("soft_bounces", False)
                        ]

                if "tags" in filter_by:
                    required_tags = set(filter_by["tags"])
                    filtered_contacts = [
                        c for c in filtered_contacts
                        if required_tags.issubset(set(c.tags))
                    ]

                if "predicted_churn" in filter_by:
                    churn_threshold = filter_by["predicted_churn"]
                    filtered_contacts = [
                        c for c in filtered_contacts
                        if c.decay_prediction.get("churn_probability", 1.0) <= churn_threshold
                    ]

            # Sort results
            reverse = sort_direction.lower() == "desc"
            if sort_by == "quality_score":
                filtered_contacts.sort(key=lambda c: c.quality_score, reverse=reverse)
            elif sort_by == "health_score":
                filtered_contacts.sort(key=lambda c: c.health_score.overall, reverse=reverse)
            elif sort_by == "engagement":
                filtered_contacts.sort(key=lambda c: c.engagement_metrics.get("open_rate", 0), reverse=reverse)
            elif sort_by == "name":
                filtered_contacts.sort(key=lambda c: c.name, reverse=reverse)
            elif sort_by == "email":
                filtered_contacts.sort(key=lambda c: c.email, reverse=reverse)
            elif sort_by == "churn_risk":
                filtered_contacts.sort(key=lambda c: c.decay_prediction.get("churn_probability", 1.0), reverse=not reverse)

            # Apply pagination
            paginated_contacts = filtered_contacts[offset:offset + limit]

            return paginated_contacts, len(filtered_contacts)
        except Exception as e:
            logger.error(f"Failed to get contacts: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get contacts: {str(e)}")

    async def get_contacts_by_ids(
        self,
        user_id: str,
        contact_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get contacts by IDs.

        Args:
            user_id: The user ID
            contact_ids: List of contact IDs

        Returns:
            List of contacts
        """
        try:
            # In a real implementation, this would fetch from a database
            # For now, we'll return mock data

            # Generate mock contacts
            all_contacts = {
                f"contact_{i}": {
                    "id": f"contact_{i}",
                    "name": f"Contact {i}",
                    "email": f"contact{i}@example.com",
                    "role": "Software Engineer" if i % 3 == 0 else "Product Manager" if i % 3 == 1 else "Designer",
                    "company": "Tech Company" if i % 2 == 0 else "Creative Agency",
                    "industry": "Technology" if i % 2 == 0 else "Marketing",
                    "quality_score": 0.8 + (i % 3) * 0.1
                }
                for i in range(1, 101)
            }

            # Filter contacts by IDs
            contacts = [all_contacts[contact_id] for contact_id in contact_ids if contact_id in all_contacts]

            return contacts
        except Exception as e:
            logger.error(f"Failed to get contacts by IDs: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get contacts by IDs: {str(e)}")

    async def discover_contacts(
        self,
        user_id: str,
        target_criteria: Dict[str, Any],
        discovery_depth: str = "standard",
        enrichment_level: str = "standard"
    ) -> List[Contact]:
        """
        Discover contacts based on target criteria.

        Args:
            user_id: The user ID
            target_criteria: The target criteria for contact discovery
            discovery_depth: The depth of discovery
            enrichment_level: The level of contact enrichment

        Returns:
            List of discovered contacts
        """
        try:
            logger.info(f"Discovering contacts for user {user_id} with criteria: {target_criteria}")

            # Execute contact discovery with OctoTools
            result = await octotools_service.discover_contacts(
                user_id=user_id,
                target_criteria=target_criteria,
                discovery_depth=discovery_depth,
                enrichment_level=enrichment_level
            )

            if "error" in result:
                raise HTTPException(status_code=500, detail=result["error"])

            # Convert raw contacts to Contact model
            contacts = []
            for raw_contact in result.get("contacts", []):
                contact_id = str(uuid.uuid4())
                now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

                contacts.append(Contact(
                    id=contact_id,
                    name=raw_contact.get("name", ""),
                    email=raw_contact.get("email", ""),
                    role=raw_contact.get("role"),
                    company=raw_contact.get("company"),
                    industry=raw_contact.get("industry"),
                    created_at=now,
                    updated_at=now,
                    quality_score=raw_contact.get("quality_score"),
                    tags=["discovered"],
                    social_profiles=raw_contact.get("social_profiles", {}),
                    custom_fields=raw_contact.get("custom_fields", {})
                ))

            # In a real implementation, save contacts to database

            logger.info(f"Discovered {len(contacts)} contacts for user {user_id}")
            return contacts
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Contact discovery failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Contact discovery failed: {str(e)}")

    async def generate_lookalike_audience(
        self,
        user_id: str,
        seed_contacts: List[Dict[str, Any]],
        expansion_factor: int = 3,
        similarity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate lookalike audience based on seed contacts.

        Args:
            user_id: The user ID
            seed_contacts: The seed contacts for lookalike generation
            expansion_factor: The factor by which to expand the audience
            similarity_threshold: The minimum similarity threshold

        Returns:
            Dictionary containing lookalike audience
        """
        try:
            logger.info(f"Generating lookalike audience for user {user_id} with {len(seed_contacts)} seed contacts")

            # Execute lookalike audience generation with OctoTools
            result = await octotools_service.generate_lookalike_audience(
                user_id=user_id,
                seed_contacts=seed_contacts,
                expansion_factor=expansion_factor,
                similarity_threshold=similarity_threshold
            )

            if "error" in result:
                raise HTTPException(status_code=500, detail=result["error"])

            # Convert raw contacts to Contact model
            lookalike_contacts = []
            for raw_contact in result.get("lookalike_contacts", []):
                contact_id = str(uuid.uuid4())
                now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

                lookalike_contacts.append(Contact(
                    id=contact_id,
                    name=raw_contact.get("name", ""),
                    email=raw_contact.get("email", ""),
                    role=raw_contact.get("role"),
                    company=raw_contact.get("company"),
                    industry=raw_contact.get("industry"),
                    created_at=now,
                    updated_at=now,
                    quality_score=raw_contact.get("quality_score"),
                    tags=["lookalike"],
                    social_profiles=raw_contact.get("social_profiles", {}),
                    custom_fields={
                        "similarity_score": raw_contact.get("similarity_score", 0),
                        "segment": raw_contact.get("segment", "")
                    }
                ))

            # In a real implementation, save contacts to database

            logger.info(f"Generated {len(lookalike_contacts)} lookalike contacts for user {user_id}")

            return {
                "contacts": lookalike_contacts,
                "segments": result.get("segments", []),
                "metrics": result.get("metrics", {})
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Lookalike audience generation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Lookalike audience generation failed: {str(e)}")

    # New methods for advanced contact intelligence

    async def validate_contact_multi_signal(self, contact: Contact) -> Dict[str, Any]:
        """
        Perform multi-signal validation on a contact.

        Args:
            contact: Contact to validate

        Returns:
            Validation results with confidence scores
        """
        validation_results = {
            "email_syntax": await self._validate_email_syntax(contact.email),
            "domain_reputation": await self._check_domain_reputation(contact.email),
            "smtp_validation": await self._validate_email_smtp(contact.email),
            "cross_platform": await self._cross_platform_verify(contact),
            "behavioral_patterns": await self._analyze_behavioral_patterns(contact),
            "network_validation": await self._validate_network_cluster(contact),
            "overall_validity": False,
            "confidence_score": 0.0
        }

        # Calculate overall validity score
        weighted_score = (
            validation_results["email_syntax"]["score"] * 0.2 +
            validation_results["domain_reputation"]["score"] * 0.2 +
            validation_results["smtp_validation"]["score"] * 0.25 +
            validation_results["cross_platform"]["score"] * 0.15 +
            validation_results["behavioral_patterns"]["score"] * 0.1 +
            validation_results["network_validation"]["score"] * 0.1
        )

        validation_results["confidence_score"] = weighted_score
        validation_results["overall_validity"] = weighted_score > 0.7

        return validation_results

    async def calculate_contact_health_score(self, contact: Contact) -> ContactHealthScore:
        """
        Calculate comprehensive health score for a contact.

        Args:
            contact: Contact to evaluate

        Returns:
            ContactHealthScore object with detailed scoring
        """
        # Initialize scores
        email_validity = await self._calculate_email_validity_score(contact)
        engagement = await self._calculate_engagement_score(contact)
        deliverability = await self._calculate_deliverability_score(contact)
        consent_level = await self._determine_consent_level(contact)
        domain_reputation = await self._check_domain_reputation(contact.email)

        # Calculate overall score (0-100)
        overall = int(
            email_validity * 0.3 +
            engagement * 0.3 +
            deliverability * 0.3 +
            (1.0 if consent_level == "explicit" else 0.7 if consent_level == "implied" else 0.3) * 10
        )

        return ContactHealthScore(
            overall=overall,
            email_validity=email_validity,
            engagement=engagement,
            deliverability=deliverability,
            consent_level=consent_level,
            domain_reputation=domain_reputation["score"],
            last_evaluated=datetime.now().isoformat()
        )

    async def predict_contact_decay(self, contact: Contact) -> Dict[str, Any]:
        """
        Predict when a contact is likely to become inactive.

        Args:
            contact: Contact to analyze

        Returns:
            Decay prediction information
        """
        # Analyze engagement history
        engagement_metrics = contact.engagement_metrics or {}

        # Determine base churn probability from engagement rates
        open_rate = engagement_metrics.get("open_rate", 0)
        click_rate = engagement_metrics.get("click_rate", 0)
        response_rate = engagement_metrics.get("response_rate", 0)

        # Base churn probability calculation
        churn_probability = max(0, min(1, 1.0 - (open_rate + click_rate * 2 + response_rate * 3)))

        # Adjust based on last engagement
        last_engagement_str = engagement_metrics.get("last_engagement")
        days_since_engagement = 999  # Default high value

        if last_engagement_str:
            try:
                last_engagement = datetime.fromisoformat(last_engagement_str)
                days_since_engagement = (datetime.now() - last_engagement).days

                # Increase churn risk as days since engagement increases
                if days_since_engagement > 120:
                    churn_probability += 0.4
                elif days_since_engagement > 90:
                    churn_probability += 0.3
                elif days_since_engagement > 60:
                    churn_probability += 0.2
                elif days_since_engagement > 30:
                    churn_probability += 0.1

                churn_probability = min(0.99, churn_probability)
            except ValueError:
                pass

        # Estimate days until inactive based on churn probability
        days_until_inactive = int(max(0, 365 * (1 - churn_probability)))
        predicted_inactive_date = (datetime.now() + timedelta(days=days_until_inactive)).isoformat()

        # Estimate lifetime value based on engagement and churn risk
        base_value = 100  # Arbitrary base value
        lifetime_value = base_value * (1 - churn_probability) * max(1, (open_rate + click_rate * 2 + response_rate * 3))

        return {
            "predicted_inactive_date": predicted_inactive_date,
            "churn_probability": churn_probability,
            "days_since_last_engagement": days_since_engagement,
            "predicted_lifetime_value": lifetime_value
        }

    # Helper methods for the multi-signal validation matrix

    async def _validate_email_syntax(self, email: str) -> Dict[str, Any]:
        """Validate email syntax and format."""
        if not email:
            return {"valid": False, "score": 0.0, "reason": "Email is empty"}

        # Basic pattern validation
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            return {"valid": False, "score": 0.0, "reason": "Invalid email format"}

        # Check for disposable domains
        domain = email.split('@')[-1].lower()
        if domain in self.disposable_domains:
            return {"valid": True, "score": 0.3, "reason": "Disposable email domain"}

        # Check for common typos in major domains
        common_domains = {
            "gmail.com": ["gmal.com", "gamil.com", "gmial.com", "gmaill.com", "gmail.co", "gmail.net"],
            "yahoo.com": ["yaho.com", "yahooo.com", "yhaoo.com", "yahoo.co", "yahoo.net"],
            "hotmail.com": ["hotmial.com", "hotamail.com", "hotmail.co", "hotmial.com"],
            "outlook.com": ["outook.com", "outlok.com", "outlook.co", "outlook.net"]
        }

        for correct_domain, typos in common_domains.items():
            if domain in typos:
                # This is likely a typo of a common domain
                suggested_email = email.replace(domain, correct_domain)
                return {
                    "valid": False,
                    "score": 0.5,
                    "reason": f"Possible typo in domain, did you mean {suggested_email}?",
                    "suggested_correction": suggested_email
                }

        return {"valid": True, "score": 1.0, "reason": "Valid email format"}

    async def _check_domain_reputation(self, email: str) -> Dict[str, Any]:
        """Check domain reputation and status."""
        if not email or '@' not in email:
            return {"score": 0.0, "reason": "Invalid email format"}

        domain = email.split('@')[-1].lower()

        # Check cached domain reputation
        if domain in self.domain_reputation_db:
            return self.domain_reputation_db[domain]

        # In a real implementation, we would check against reputation databases
        # For this prototype, use some heuristics

        # Check for newly registered domains (high risk)
        if len(domain) > 15 and any(domain.endswith(tld) for tld in [".xyz", ".top", ".space", ".site"]):
            reputation = {
                "score": 0.3,
                "status": "suspicious",
                "reason": "Potentially suspicious domain pattern"
            }
        # Check for free email providers (medium risk for marketing)
        elif domain in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com"]:
            reputation = {
                "score": 0.7,
                "status": "free_provider",
                "reason": "Free email provider"
            }
        # Established business domains (low risk)
        else:
            reputation = {
                "score": 0.9,
                "status": "good",
                "reason": "No negative signals detected"
            }

        # Cache the result
        self.domain_reputation_db[domain] = reputation
        return reputation

    async def _validate_email_smtp(self, email: str) -> Dict[str, Any]:
        """Validate email using SMTP checks without sending mail."""
        # In a real implementation, this would connect to mail servers
        # For this prototype, return a simulated result

        if not email:
            return {"valid": False, "score": 0.0, "reason": "Email is empty"}

        domain = email.split('@')[-1].lower()

        # Simulate SMTP verification
        if domain in self.disposable_domains:
            return {"valid": False, "score": 0.2, "reason": "Disposable email domain"}

        # Randomly simulate some failures for demo purposes
        import random
        if random.random() < 0.1:
            return {"valid": False, "score": 0.0, "reason": "Mailbox does not exist"}
        elif random.random() < 0.05:
            return {"valid": False, "score": 0.3, "reason": "Mailbox full"}
        elif random.random() < 0.05:
            return {"valid": False, "score": 0.2, "reason": "Temporary SMTP error"}

        return {"valid": True, "score": 1.0, "reason": "SMTP verification passed"}

    async def _cross_platform_verify(self, contact: Contact) -> Dict[str, Any]:
        """Verify contact existence across connected platforms."""
        # In a real implementation, this would check against connected platforms
        # For this prototype, return simulated results based on social profiles

        social_profiles = contact.social_profiles or {}
        verification_sources = []
        total_score = 0.0

        if social_profiles.get("linkedin"):
            verification_sources.append("linkedin")
            total_score += 0.4

        if social_profiles.get("twitter"):
            verification_sources.append("twitter")
            total_score += 0.3

        if contact.company:
            # Simulate company database verification
            verification_sources.append("company_database")
            total_score += 0.3

        return {
            "verified": len(verification_sources) > 0,
            "score": min(1.0, total_score),
            "sources": verification_sources,
            "reason": f"Verified against {len(verification_sources)} platforms" if verification_sources else "No cross-platform verification"
        }

    async def _analyze_behavioral_patterns(self, contact: Contact) -> Dict[str, Any]:
        """Analyze historical engagement patterns for predictive detection."""
        # In a real implementation, this would analyze historical engagement data
        # For this prototype, return simulated results

        engagement_metrics = contact.engagement_metrics or {}
        bounce_history = contact.bounce_history or {}

        # Check for bounce patterns
        if bounce_history.get("hard_bounces"):
            return {
                "valid": False,
                "score": 0.1,
                "pattern": "hard_bounce_history",
                "reason": "Contact has hard bounce history"
            }

        # Check for engagement patterns
        open_rate = engagement_metrics.get("open_rate", 0)
        click_rate = engagement_metrics.get("click_rate", 0)

        if open_rate == 0 and click_rate == 0:
            return {
                "valid": False,
                "score": 0.3,
                "pattern": "zero_engagement",
                "reason": "Contact has shown no engagement"
            }

        if open_rate > 0.3 or click_rate > 0.1:
            return {
                "valid": True,
                "score": 0.9,
                "pattern": "active_engagement",
                "reason": "Contact shows active engagement"
            }

        return {
            "valid": True,
            "score": 0.7,
            "pattern": "normal_behavior",
            "reason": "Contact shows normal behavior patterns"
        }

    async def _validate_network_cluster(self, contact: Contact) -> Dict[str, Any]:
        """Validate contact based on relationship network patterns."""
        # In a real implementation, this would analyze the contact's relationship
        # with other contacts in the same company or domain
        # For this prototype, return simulated results

        email = contact.email
        if not email or '@' not in email:
            return {"score": 0.0, "reason": "Invalid email format"}

        domain = email.split('@')[-1].lower()

        # Simulate network validation
        return {
            "valid": True,
            "score": 0.8,
            "cluster_size": 5,  # Mock value
            "reason": "Part of a validated email cluster"
        }

    # Helper methods for health scoring

    async def _calculate_email_validity_score(self, contact: Contact) -> float:
        """Calculate email validity score on a scale of 0-100."""
        # Combine multiple signals for email validity
        syntax_validation = await self._validate_email_syntax(contact.email)
        domain_check = await self._check_domain_reputation(contact.email)
        smtp_validation = await self._validate_email_smtp(contact.email)

        # Calculate weighted score
        weighted_score = (
            syntax_validation.get("score", 0) * 30 +
            domain_check.get("score", 0) * 30 +
            smtp_validation.get("score", 0) * 40
        )

        return min(100, weighted_score * 100)

    async def _calculate_engagement_score(self, contact: Contact) -> float:
        """Calculate engagement score on a scale of 0-100."""
        engagement_metrics = contact.engagement_metrics or {}

        # Base metrics
        open_rate = engagement_metrics.get("open_rate", 0)
        click_rate = engagement_metrics.get("click_rate", 0)
        response_rate = engagement_metrics.get("response_rate", 0)

        # Calculate weighted score
        weighted_score = (
            open_rate * 30 +
            click_rate * 40 +
            response_rate * 30
        )

        # Adjust for recency
        last_engagement_str = engagement_metrics.get("last_engagement")
        if last_engagement_str:
            try:
                last_engagement = datetime.fromisoformat(last_engagement_str)
                days_since = (datetime.now() - last_engagement).days

                # Apply recency factor
                recency_factor = max(0.5, min(1.0, 1.0 - (days_since / 90) * 0.5))
                weighted_score *= recency_factor
            except ValueError:
                pass

        return min(100, weighted_score * 100)

    async def _calculate_deliverability_score(self, contact: Contact) -> float:
        """Calculate deliverability score on a scale of 0-100."""
        bounce_history = contact.bounce_history or {}

        # Base score starts at 100 and gets reduced for issues
        score = 100.0

        # Reduce for hard bounces (major penalty)
        if bounce_history.get("hard_bounces"):
            score -= 70

        # Reduce for soft bounces (minor penalty)
        if bounce_history.get("soft_bounces"):
            score -= 30

        # Adjust based on bounce recency
        last_bounce_str = bounce_history.get("last_bounce")
        if last_bounce_str:
            try:
                last_bounce = datetime.fromisoformat(last_bounce_str)
                days_since = (datetime.now() - last_bounce).days

                # Gradually recover score over time
                recovery_factor = min(1.0, days_since / 90)
                score += (100 - score) * recovery_factor * 0.5
            except ValueError:
                pass

        return max(0, min(100, score))

    async def _determine_consent_level(self, contact: Contact) -> str:
        """Determine the consent level of a contact."""
        compliance_info = contact.compliance_info or {}

        consent_source = compliance_info.get("consent_source", "unknown")

        if consent_source in ["web_form", "double_opt_in", "api_confirmed"]:
            return "explicit"
        elif consent_source in ["import", "api", "partner"]:
            return "implied"
        else:
            return "unknown"

# Singleton instance
contact_service = ContactService()
