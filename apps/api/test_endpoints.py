from fastapi.testclient import TestClient
import json
import os
import sys
import random
from datetime import datetime, timedelta
import uuid
from enum import Enum
from typing import List, Optional, Dict, Any

# Model definitions
class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"
    PENDING = "pending"

class HealthTrend(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"

class ActionType(str, Enum):
    VERIFICATION = "verification"
    ENRICHMENT = "enrichment"
    CLEANSING = "cleansing"
    RECOVERY = "recovery"

class ActionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class PriorityLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class VerificationType(str, Enum):
    INITIAL = "initial"
    UPDATE = "update"
    CONSENT = "consent"
    VALIDATION = "validation"

class BlockchainVerificationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"

class ComplianceCategory(str, Enum):
    CONSENT = "consent"
    DATA_RETENTION = "data_retention"
    OPT_OUT = "opt_out"
    DATA_PROCESSING = "data_processing"
    MARKETING_PERMISSION = "marketing_permission"

class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# Simple models without Pydantic for testing
class Contact:
    def __init__(self, id, email, name, health_score, last_activity, last_validated,
                 compliance_status, bounce_rate, engagement_score, is_verified, blockchain_verified):
        self.id = id
        self.email = email
        self.name = name
        self.health_score = health_score
        self.last_activity = last_activity
        self.last_validated = last_validated
        self.compliance_status = compliance_status
        self.bounce_rate = bounce_rate
        self.engagement_score = engagement_score
        self.is_verified = is_verified
        self.blockchain_verified = blockchain_verified

class HealthScore:
    def __init__(self, overall, email_validity, engagement, deliverability,
                 consent_level, domain_reputation, last_evaluated):
        self.overall = overall
        self.email_validity = email_validity
        self.engagement = engagement
        self.deliverability = deliverability
        self.consent_level = consent_level
        self.domain_reputation = domain_reputation
        self.last_evaluated = last_evaluated

class ValidationResult:
    def __init__(self, valid, score, reason, suggested_correction=None,
                 sources=None, pattern=None, cluster_size=None):
        self.valid = valid
        self.score = score
        self.reason = reason
        self.suggested_correction = suggested_correction
        self.sources = sources
        self.pattern = pattern
        self.cluster_size = cluster_size

class MultiSignalValidationResults:
    def __init__(self, email_syntax, domain_reputation, smtp_validation,
                 cross_platform, behavioral_patterns, network_validation,
                 overall_validity, confidence_score):
        self.email_syntax = email_syntax
        self.domain_reputation = domain_reputation
        self.smtp_validation = smtp_validation
        self.cross_platform = cross_platform
        self.behavioral_patterns = behavioral_patterns
        self.network_validation = network_validation
        self.overall_validity = overall_validity
        self.confidence_score = confidence_score

class SelfHealingAction:
    def __init__(self, id, type, status, timestamp, description, result=None):
        self.id = id
        self.type = type
        self.status = status
        self.timestamp = timestamp
        self.description = description
        self.result = result

class RecommendedAction:
    def __init__(self, id, type, priority, description, estimated_impact):
        self.id = id
        self.type = type
        self.priority = priority
        self.description = description
        self.estimated_impact = estimated_impact

class ContactLifecycleMetrics:
    def __init__(self, last_activity_date, predicted_decay_date, current_health_score,
                 predicted_health_trend, self_healing_actions, decay_rate, recommended_actions):
        self.last_activity_date = last_activity_date
        self.predicted_decay_date = predicted_decay_date
        self.current_health_score = current_health_score
        self.predicted_health_trend = predicted_health_trend
        self.self_healing_actions = self_healing_actions
        self.decay_rate = decay_rate
        self.recommended_actions = recommended_actions

class VerificationDetails:
    def __init__(self, consent_recorded=None, consent_source=None, consent_date=None,
                 contact_data_verified=None, validation_score=None):
        self.consent_recorded = consent_recorded
        self.consent_source = consent_source
        self.consent_date = consent_date
        self.contact_data_verified = contact_data_verified
        self.validation_score = validation_score

class BlockchainVerification:
    def __init__(self, id, contactId, timestamp, transaction_hash, block_number,
                 network, verification_type, status, data_hash, explorer_url, verification_details):
        self.id = id
        self.contactId = contactId
        self.timestamp = timestamp
        self.transaction_hash = transaction_hash
        self.block_number = block_number
        self.network = network
        self.verification_type = verification_type
        self.status = status
        self.data_hash = data_hash
        self.explorer_url = explorer_url
        self.verification_details = verification_details

class ComplianceCheck:
    def __init__(self, id, regulation, status, last_checked, issue_description,
                 recommended_action, risk_level, category, details):
        self.id = id
        self.regulation = regulation
        self.status = status
        self.last_checked = last_checked
        self.issue_description = issue_description
        self.recommended_action = recommended_action
        self.risk_level = risk_level
        self.category = category
        self.details = details

# Mock data generator functions
def generate_mock_contacts(count: int = 10) -> List[Contact]:
    """Generate mock contact data"""
    contacts = []
    for i in range(count):
        contacts.append(
            Contact(
                id=str(uuid.uuid4()),
                email=f"user{i}@example.com",
                name=f"User {i}",
                health_score=random.randint(30, 95),
                last_activity=datetime.now() - timedelta(days=random.randint(0, 30)),
                last_validated=datetime.now() - timedelta(days=random.randint(0, 60)),
                compliance_status=random.choice(list(ComplianceStatus)),
                bounce_rate=round(random.uniform(0, 0.15), 2),
                engagement_score=random.randint(10, 90),
                is_verified=random.choice([True, False]),
                blockchain_verified=random.choice([True, False])
            )
        )
    return contacts

def generate_health_score() -> HealthScore:
    """Generate mock health score data"""
    overall = random.randint(50, 95)
    return HealthScore(
        overall=overall,
        email_validity=random.randint(max(overall-15, 50), min(overall+15, 100)),
        engagement=random.randint(max(overall-20, 40), min(overall+10, 100)),
        deliverability=random.randint(max(overall-10, 60), min(overall+15, 100)),
        consent_level=random.choice(["explicit", "implied", "unknown"]),
        domain_reputation=round(random.uniform(0.4, 0.95), 2),
        last_evaluated=datetime.now() - timedelta(days=random.randint(0, 7))
    )

def generate_validation_results() -> MultiSignalValidationResults:
    """Generate mock validation results"""
    confidence = round(random.uniform(0.6, 0.95), 2)

    return MultiSignalValidationResults(
        email_syntax=ValidationResult(
            valid=True,
            score=round(random.uniform(0.8, 1.0), 2),
            reason="Email format is valid",
            suggested_correction=None
        ),
        domain_reputation=ValidationResult(
            valid=True,
            score=round(random.uniform(0.6, 0.9), 2),
            reason="Domain has good sending reputation"
        ),
        smtp_validation=ValidationResult(
            valid=random.choice([True, False]),
            score=round(random.uniform(0.5, 1.0), 2),
            reason="SMTP server accepts email"
        ),
        cross_platform=ValidationResult(
            valid=random.choice([True, False]),
            score=round(random.uniform(0.3, 0.9), 2),
            reason="Found on 2 platforms",
            sources=["LinkedIn", "Twitter"]
        ),
        behavioral_patterns=ValidationResult(
            valid=True,
            score=round(random.uniform(0.6, 0.9), 2),
            reason="Shows consistent engagement patterns",
            pattern="active_engagement"
        ),
        network_validation=ValidationResult(
            valid=True,
            score=round(random.uniform(0.5, 0.9), 2),
            reason="Connected to known network clusters",
            cluster_size=random.randint(5, 30)
        ),
        overall_validity=True,
        confidence_score=confidence
    )

def generate_lifecycle_metrics() -> ContactLifecycleMetrics:
    """Generate mock lifecycle metrics"""
    current_health = random.randint(50, 90)

    # Generate self-healing actions
    self_healing_actions = []
    for i in range(random.randint(0, 3)):
        action_type = random.choice(list(ActionType))
        self_healing_actions.append(
            SelfHealingAction(
                id=str(uuid.uuid4()),
                type=action_type,
                status=random.choice(list(ActionStatus)),
                timestamp=datetime.now() - timedelta(days=random.randint(1, 14)),
                description=f"Automated {action_type.value} action",
                result=random.choice([None, "Successfully updated contact", "Fixed email format"])
            )
        )

    # Generate recommended actions
    recommended_actions = []
    for i in range(random.randint(1, 3)):
        action_type = random.choice(list(ActionType))
        recommended_actions.append(
            RecommendedAction(
                id=str(uuid.uuid4()),
                type=action_type,
                priority=random.choice(list(PriorityLevel)),
                description=f"Perform {action_type.value} to improve contact health",
                estimated_impact=random.randint(5, 25)
            )
        )

    decay_rate = round(random.uniform(1.5, 8.0), 1)

    return ContactLifecycleMetrics(
        last_activity_date=datetime.now() - timedelta(days=random.randint(1, 30)),
        predicted_decay_date=datetime.now() + timedelta(days=random.randint(30, 180)),
        current_health_score=current_health,
        predicted_health_trend=random.choice(list(HealthTrend)),
        self_healing_actions=self_healing_actions,
        decay_rate=decay_rate,
        recommended_actions=recommended_actions
    )

def generate_blockchain_verifications(contact_id: str, count: int = 3) -> List[BlockchainVerification]:
    """Generate mock blockchain verifications"""
    verifications = []
    for i in range(count):
        verification_type = random.choice(list(VerificationType))
        status = random.choice(list(BlockchainVerificationStatus))
        network = random.choice(["Ethereum", "Polygon", "Solana"])

        details = VerificationDetails(
            consent_recorded=random.choice([True, False, None]),
            consent_source=random.choice([None, "Website", "Email", "Form"]),
            contact_data_verified=random.choice([True, False, None]),
            validation_score=random.choice([None, random.randint(50, 95)])
        )

        if verification_type == VerificationType.CONSENT:
            details.consent_date = datetime.now() - timedelta(days=random.randint(1, 90))

        tx_hash = "0x" + "".join(random.choices("0123456789abcdef", k=64))

        verifications.append(
            BlockchainVerification(
                id=str(uuid.uuid4()),
                contactId=contact_id,
                timestamp=datetime.now() - timedelta(days=i*random.randint(1, 10)),
                transaction_hash=tx_hash,
                block_number=random.randint(10000000, 15000000) if status == BlockchainVerificationStatus.CONFIRMED else None,
                network=network,
                verification_type=verification_type,
                status=status,
                data_hash="0x" + "".join(random.choices("0123456789abcdef", k=40)),
                explorer_url=f"https://{network.lower()}.etherscan.io/tx/{tx_hash}" if random.choice([True, False]) else None,
                verification_details=details
            )
        )

    return verifications

def generate_compliance_checks(count: int = 5) -> List[ComplianceCheck]:
    """Generate mock compliance checks"""
    checks = []
    regulations = [
        "GDPR Consent Requirements",
        "CAN-SPAM Act Compliance",
        "CCPA Data Processing",
        "Email Marketing Best Practices",
        "Data Retention Policy"
    ]

    for i in range(count):
        category = random.choice(list(ComplianceCategory))
        status = random.choice(list(ComplianceStatus))

        details = {}
        if category == ComplianceCategory.CONSENT:
            details = {
                "consent_date": (datetime.now() - timedelta(days=random.randint(10, 300))).isoformat() if random.choice([True, False]) else None,
                "consent_source": random.choice([None, "website", "form", "email"]),
                "explicit_consent": random.choice([True, False])
            }
        elif category == ComplianceCategory.DATA_RETENTION:
            details = {
                "data_age": random.randint(30, 400),
                "retention_limit": random.randint(365, 730),
                "purge_date": (datetime.now() + timedelta(days=random.randint(10, 300))).isoformat() if random.choice([True, False]) else None
            }
        elif category == ComplianceCategory.OPT_OUT:
            details = {
                "opt_out_requested": random.choice([True, False]),
                "opt_out_date": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat() if random.choice([True, False]) else None,
                "properly_processed": random.choice([True, False])
            }

        issue = None
        action = None

        if status == ComplianceStatus.NON_COMPLIANT:
            if category == ComplianceCategory.CONSENT:
                issue = "No explicit consent record found"
                action = "Obtain explicit consent through verification email"
            elif category == ComplianceCategory.DATA_RETENTION:
                issue = "Data retention period exceeded"
                action = "Schedule data purge or refresh consent"
            elif category == ComplianceCategory.OPT_OUT:
                issue = "Opt-out request not processed within required timeframe"
                action = "Process opt-out request immediately"

        checks.append(
            ComplianceCheck(
                id=str(uuid.uuid4()),
                regulation=random.choice(regulations),
                status=status,
                last_checked=datetime.now() - timedelta(days=random.randint(0, 14)),
                issue_description=issue,
                recommended_action=action,
                risk_level=random.choice(list(RiskLevel)) if status == ComplianceStatus.NON_COMPLIANT else None,
                category=category,
                details=details
            )
        )

    return checks

# Add a simple function to print test results
def test_and_print(name, result, data=None):
    print(f"Test: {name}")
    print(f"Result: {'PASS' if result else 'FAIL'}")
    if data and not result:
        print(f"Data: {json.dumps(data, indent=2, default=str)}")
    print("-" * 50)

# Test the generator functions
def test_generators():
    """Test all data generator functions"""

    # Test contact generation
    contacts = generate_mock_contacts(5)
    test_and_print(
        "Generate Mock Contacts",
        len(contacts) == 5 and all(c.email and c.name for c in contacts)
    )

    # Test health score generation
    health = generate_health_score()
    test_and_print(
        "Generate Health Score",
        0 <= health.overall <= 100 and
        0 <= health.email_validity <= 100 and
        0 <= health.engagement <= 100 and
        0 <= health.deliverability <= 100 and
        health.consent_level in ["explicit", "implied", "unknown"] and
        0 <= health.domain_reputation <= 1
    )

    # Test validation results
    validation = generate_validation_results()
    test_and_print(
        "Generate Validation Results",
        hasattr(validation, "email_syntax") and
        hasattr(validation, "domain_reputation") and
        hasattr(validation, "smtp_validation") and
        hasattr(validation, "cross_platform") and
        hasattr(validation, "behavioral_patterns") and
        hasattr(validation, "network_validation") and
        isinstance(validation.confidence_score, float) and
        isinstance(validation.overall_validity, bool)
    )

    # Test lifecycle metrics
    lifecycle = generate_lifecycle_metrics()
    test_and_print(
        "Generate Lifecycle Metrics",
        hasattr(lifecycle, "current_health_score") and
        hasattr(lifecycle, "predicted_health_trend") and
        hasattr(lifecycle, "self_healing_actions") and
        hasattr(lifecycle, "recommended_actions") and
        isinstance(lifecycle.decay_rate, float)
    )

    # Test blockchain verifications
    verifications = generate_blockchain_verifications("test-id", 3)
    test_and_print(
        "Generate Blockchain Verifications",
        len(verifications) == 3 and
        all(v.contactId == "test-id" for v in verifications)
    )

    # Test compliance checks
    checks = generate_compliance_checks(4)
    test_and_print(
        "Generate Compliance Checks",
        len(checks) == 4 and
        all(hasattr(c, "status") and hasattr(c, "category") for c in checks)
    )

if __name__ == "__main__":
    print("\nTesting Contact Intelligence Data Generators\n" + "=" * 50)
    test_generators()
    print("\nAll tests completed!\n")
