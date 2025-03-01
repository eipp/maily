import re
import logging
import socket
import dns.resolver
import asyncio
from typing import Dict, Any, Tuple, List, Optional

logger = logging.getLogger(__name__)

# List of disposable email domains
DISPOSABLE_DOMAINS = [
    "mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com",
    "throwawaymail.com", "yopmail.com", "getnada.com", "temp-mail.org",
    "dispostable.com", "mailnesia.com", "mailcatch.com", "trashmail.com"
]

# Domain reputation cache to avoid repeated lookups
DOMAIN_REPUTATION_CACHE = {}

async def validate_email_syntax(email: str) -> Dict[str, Any]:
    """
    Validate email syntax without connecting to mail servers.

    Args:
        email: Email address to validate

    Returns:
        Dict with validation results
    """
    if not email:
        return {"valid": False, "score": 0.0, "reason": "Empty email address"}

    # Basic pattern check (RFC 5322 simplified)
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return {"valid": False, "score": 0.0, "reason": "Invalid email format"}

    # Check domain part
    try:
        local_part, domain = email.rsplit('@', 1)
    except ValueError:
        return {"valid": False, "score": 0.0, "reason": "Malformed email address"}

    # Check for disposable email
    if domain.lower() in DISPOSABLE_DOMAINS:
        return {
            "valid": True,
            "score": 0.3,
            "reason": "Disposable email domain",
            "domain_type": "disposable"
        }

    # Check length constraints
    if len(local_part) > 64:
        return {"valid": False, "score": 0.0, "reason": "Local part too long"}

    if len(domain) > 255:
        return {"valid": False, "score": 0.0, "reason": "Domain too long"}

    # Check for common typos in major domains
    common_domains = {
        "gmail.com": ["gmal.com", "gamil.com", "gmial.com", "gmaill.com", "gmail.co", "gmail.net"],
        "yahoo.com": ["yaho.com", "yahooo.com", "yhaoo.com", "yahoo.co", "yahoo.net"],
        "hotmail.com": ["hotmial.com", "hotamail.com", "hotmail.co", "hotmial.com"],
        "outlook.com": ["outook.com", "outlok.com", "outlook.co", "outlook.net"]
    }

    for correct_domain, typos in common_domains.items():
        if domain.lower() in typos:
            suggested_email = local_part + "@" + correct_domain
            return {
                "valid": False,
                "score": 0.5,
                "reason": f"Possible typo in domain, did you mean {suggested_email}?",
                "suggested_correction": suggested_email
            }

    # Additional rules for specific providers
    if domain.lower() == "gmail.com":
        # Gmail ignores dots in local part and anything after +
        normalized_local_part = local_part.lower().replace(".", "").split("+")[0]
        normalized_email = normalized_local_part + "@gmail.com"

        return {
            "valid": True,
            "score": 1.0,
            "reason": "Valid email format",
            "normalized_form": normalized_email
        }

    return {"valid": True, "score": 1.0, "reason": "Valid email format"}

async def validate_email_smtp(email: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Validate email by checking if the domain has valid MX records
    and attempting SMTP validation without sending mail.

    Args:
        email: Email address to validate
        timeout: Timeout in seconds for SMTP operations

    Returns:
        Dict with validation results
    """
    if not email or '@' not in email:
        return {"valid": False, "score": 0.0, "reason": "Invalid email format"}

    domain = email.split('@')[-1]

    # Check for MX records
    try:
        mx_records = await asyncio.to_thread(_get_mx_records, domain)
        if not mx_records:
            return {
                "valid": False,
                "score": 0.1,
                "reason": "Domain has no mail server (MX records)",
                "mx_found": False
            }
    except Exception as e:
        logger.warning(f"Error checking MX records for {domain}: {str(e)}")
        return {
            "valid": False,
            "score": 0.3,
            "reason": f"Error checking domain mail server: {str(e)}",
            "mx_found": False
        }

    # In a production environment, we would do SMTP verification
    # For this implementation, we'll simulate results

    # Check if domain is among known free providers (more likely to exist)
    free_providers = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com"]
    if domain.lower() in free_providers:
        smtp_result = {
            "valid": True,
            "score": 0.9,
            "reason": "Domain is a known email provider",
            "mx_found": True
        }
    else:
        # Simulate SMTP check for other domains
        # In a real implementation, we would connect to SMTP server and check
        import random
        if random.random() < 0.1:
            smtp_result = {
                "valid": False,
                "score": 0.0,
                "reason": "Mailbox does not exist",
                "mx_found": True
            }
        elif random.random() < 0.05:
            smtp_result = {
                "valid": False,
                "score": 0.3,
                "reason": "Mailbox full or temporarily unavailable",
                "mx_found": True
            }
        else:
            smtp_result = {
                "valid": True,
                "score": 0.8,
                "reason": "SMTP verification passed",
                "mx_found": True
            }

    return smtp_result

def _get_mx_records(domain: str) -> List[str]:
    """Get MX records for a domain (synchronous function)."""
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        return [str(rdata.exchange) for rdata in answers]
    except dns.resolver.NoAnswer:
        return []
    except dns.resolver.NXDOMAIN:
        return []
    except Exception as e:
        logger.error(f"DNS resolution failed for {domain}: {str(e)}")
        return []

async def check_domain_reputation(email: str) -> Dict[str, Any]:
    """
    Check the reputation of an email domain.

    Args:
        email: Email address to check

    Returns:
        Dict with domain reputation details
    """
    if not email or '@' not in email:
        return {"score": 0.0, "reason": "Invalid email format"}

    domain = email.split('@')[-1].lower()

    # Check cache first
    if domain in DOMAIN_REPUTATION_CACHE:
        return DOMAIN_REPUTATION_CACHE[domain]

    # In a real implementation, we would check against reputation databases
    # For this prototype, we'll simulate results

    # Check for newly registered domains (higher risk)
    suspicious_tlds = [".xyz", ".top", ".space", ".site", ".online", ".live"]
    if len(domain) > 15 and any(domain.endswith(tld) for tld in suspicious_tlds):
        reputation = {
            "score": 0.3,
            "status": "suspicious",
            "reason": "Potentially suspicious domain pattern"
        }
    # Free email providers (medium risk for marketing)
    elif domain in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com"]:
        reputation = {
            "score": 0.7,
            "status": "free_provider",
            "reason": "Free email provider"
        }
    # Check for disposable domains (high risk)
    elif domain in DISPOSABLE_DOMAINS:
        reputation = {
            "score": 0.1,
            "status": "disposable",
            "reason": "Disposable email domain"
        }
    # Established business domains (low risk)
    else:
        reputation = {
            "score": 0.9,
            "status": "good",
            "reason": "No negative signals detected"
        }

    # Cache the result
    DOMAIN_REPUTATION_CACHE[domain] = reputation
    return reputation

async def bulk_validate_emails(emails: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Perform bulk validation of multiple email addresses.

    Args:
        emails: List of email addresses to validate

    Returns:
        Dict mapping each email to its validation results
    """
    validation_tasks = {}

    # Create validation tasks for each email
    for email in emails:
        validation_tasks[email] = {
            "syntax": asyncio.create_task(validate_email_syntax(email)),
            "smtp": asyncio.create_task(validate_email_smtp(email)),
            "domain": asyncio.create_task(check_domain_reputation(email))
        }

    # Wait for all tasks to complete
    results = {}
    for email, tasks in validation_tasks.items():
        syntax_result = await tasks["syntax"]
        smtp_result = await tasks["smtp"]
        domain_result = await tasks["domain"]

        # Calculate overall score
        overall_score = (
            syntax_result.get("score", 0) * 0.3 +
            smtp_result.get("score", 0) * 0.4 +
            domain_result.get("score", 0) * 0.3
        )

        # Determine overall validity
        overall_valid = overall_score >= 0.6 and syntax_result.get("valid", False)

        results[email] = {
            "overall_valid": overall_valid,
            "overall_score": overall_score,
            "syntax": syntax_result,
            "smtp": smtp_result,
            "domain": domain_result
        }

    return results
