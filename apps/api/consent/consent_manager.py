from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..database.models import User, ConsentRecord
from ..errors.exceptions import ConsentNotFoundError

class ConsentPreference(BaseModel):
    marketing_emails: bool
    data_analytics: bool
    third_party_sharing: bool
    personalization: bool
    last_updated: datetime
    ip_address: str
    user_agent: str

class ConsentManager:
    def __init__(self, db: Session):
        self.db = db

    async def get_user_consent(self, user_id: int) -> ConsentPreference:
        """Retrieve current consent preferences for a user."""
        consent = self.db.query(ConsentRecord).filter(
            ConsentRecord.user_id == user_id,
            ConsentRecord.is_active == True
        ).first()

        if not consent:
            raise ConsentNotFoundError(f"No active consent found for user {user_id}")

        return ConsentPreference(
            marketing_emails=consent.marketing_emails,
            data_analytics=consent.data_analytics,
            third_party_sharing=consent.third_party_sharing,
            personalization=consent.personalization,
            last_updated=consent.updated_at,
            ip_address=consent.ip_address,
            user_agent=consent.user_agent
        )

    async def update_consent(
        self,
        user_id: int,
        preferences: ConsentPreference
    ) -> ConsentPreference:
        """Update user consent preferences."""
        # Deactivate current consent
        current_consent = self.db.query(ConsentRecord).filter(
            ConsentRecord.user_id == user_id,
            ConsentRecord.is_active == True
        ).first()

        if current_consent:
            current_consent.is_active = False

        # Create new consent record
        new_consent = ConsentRecord(
            user_id=user_id,
            marketing_emails=preferences.marketing_emails,
            data_analytics=preferences.data_analytics,
            third_party_sharing=preferences.third_party_sharing,
            personalization=preferences.personalization,
            ip_address=preferences.ip_address,
            user_agent=preferences.user_agent,
            is_active=True
        )

        self.db.add(new_consent)
        self.db.commit()

        return preferences

    async def verify_consent(
        self,
        user_id: int,
        consent_type: str
    ) -> bool:
        """Verify if user has given consent for a specific purpose."""
        consent = await self.get_user_consent(user_id)
        return getattr(consent, consent_type, False)

    async def get_consent_history(
        self,
        user_id: int
    ) -> List[ConsentPreference]:
        """Retrieve consent history for a user."""
        history = self.db.query(ConsentRecord).filter(
            ConsentRecord.user_id == user_id
        ).order_by(ConsentRecord.updated_at.desc()).all()

        return [
            ConsentPreference(
                marketing_emails=record.marketing_emails,
                data_analytics=record.data_analytics,
                third_party_sharing=record.third_party_sharing,
                personalization=record.personalization,
                last_updated=record.updated_at,
                ip_address=record.ip_address,
                user_agent=record.user_agent
            )
            for record in history
        ]

    async def withdraw_all_consent(self, user_id: int) -> None:
        """Withdraw all consent for a user."""
        current_consent = self.db.query(ConsentRecord).filter(
            ConsentRecord.user_id == user_id,
            ConsentRecord.is_active == True
        ).first()

        if current_consent:
            current_consent.is_active = False
            current_consent.marketing_emails = False
            current_consent.data_analytics = False
            current_consent.third_party_sharing = False
            current_consent.personalization = False
            self.db.commit()

    async def export_consent_data(self, user_id: int) -> Dict:
        """Export all consent data for a user (GDPR compliance)."""
        history = await self.get_consent_history(user_id)
        return {
            "user_id": user_id,
            "current_preferences": await self.get_user_consent(user_id),
            "consent_history": history
        }
