"""
Shared Maily platform models.

This package contains shared data models used across the Maily platform.
"""

from .campaign import Campaign, CampaignContent, CampaignMetrics, CampaignStatus, CampaignType
from .recommendation import Recommendation, RecommendationContext, RecommendationType, RecommendationAction, RecommendationInteraction

__all__ = [
    # Campaign models
    'Campaign',
    'CampaignContent',
    'CampaignMetrics',
    'CampaignStatus',
    'CampaignType',
    
    # Recommendation models
    'Recommendation',
    'RecommendationContext',
    'RecommendationType',
    'RecommendationAction',
    'RecommendationInteraction',
]