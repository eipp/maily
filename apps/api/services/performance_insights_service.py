"""
Performance Insights Service for Cognitive Canvas

This service provides performance metrics and insights for email campaigns
created with Cognitive Canvas.
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ..cache.redis_client import get_redis_client
from ..utils.metrics import calculate_percentile

logger = logging.getLogger("api.services.performance_insights")

class PerformanceMetric(BaseModel):
    """Performance metric model"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    
class PerformanceInsight(BaseModel):
    """Performance insight model"""
    type: str
    message: str
    severity: str  # info, warning, critical
    related_metrics: List[str]
    timestamp: datetime

class PerformanceInsightsService:
    """Service for providing performance insights"""
    
    def __init__(self):
        self.redis = get_redis_client()
        
    async def get_email_performance_metrics(
        self, 
        canvas_id: str,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance metrics for an email canvas or campaign"""
        try:
            # If campaign_id is provided, get metrics for that campaign
            if campaign_id:
                return await self._get_campaign_metrics(campaign_id)
            
            # Otherwise, get metrics for the canvas based on similar templates
            return await self._get_template_metrics(canvas_id)
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            # Return empty metrics on error
            return {
                "metrics": {},
                "historical_data": [],
                "benchmarks": {}
            }
    
    async def _get_campaign_metrics(self, campaign_id: str) -> Dict[str, Any]:
        """Get performance metrics for a specific campaign"""
        try:
            # In a real implementation, this would fetch metrics from the analytics service
            # For now, we'll return mock data
            
            # Mock metrics
            metrics = {
                "open_rate": {
                    "value": 0.423,
                    "unit": "percentage",
                    "benchmark": 0.35,
                    "trend": "up"
                },
                "click_rate": {
                    "value": 0.187,
                    "unit": "percentage",
                    "benchmark": 0.15,
                    "trend": "up"
                },
                "conversion_rate": {
                    "value": 0.053,
                    "unit": "percentage",
                    "benchmark": 0.04,
                    "trend": "up"
                },
                "bounce_rate": {
                    "value": 0.021,
                    "unit": "percentage",
                    "benchmark": 0.03,
                    "trend": "down"
                },
                "unsubscribe_rate": {
                    "value": 0.005,
                    "unit": "percentage",
                    "benchmark": 0.01,
                    "trend": "down"
                }
            }
            
            # Mock historical data (last 7 days)
            historical_data = []
            for i in range(7):
                day = datetime.utcnow() - timedelta(days=i)
                historical_data.append({
                    "date": day.strftime("%Y-%m-%d"),
                    "open_rate": 0.4 + (0.05 * (i % 3 - 1)),
                    "click_rate": 0.18 + (0.02 * (i % 3 - 1)),
                    "conversion_rate": 0.05 + (0.01 * (i % 3 - 1)),
                    "bounce_rate": 0.02 + (0.005 * (i % 3 - 1)),
                    "unsubscribe_rate": 0.005 + (0.002 * (i % 3 - 1))
                })
            
            # Mock benchmarks
            benchmarks = {
                "industry": {
                    "open_rate": 0.35,
                    "click_rate": 0.15,
                    "conversion_rate": 0.04,
                    "bounce_rate": 0.03,
                    "unsubscribe_rate": 0.01
                },
                "your_average": {
                    "open_rate": 0.38,
                    "click_rate": 0.16,
                    "conversion_rate": 0.045,
                    "bounce_rate": 0.025,
                    "unsubscribe_rate": 0.008
                },
                "top_performers": {
                    "open_rate": 0.45,
                    "click_rate": 0.22,
                    "conversion_rate": 0.07,
                    "bounce_rate": 0.01,
                    "unsubscribe_rate": 0.003
                }
            }
            
            # Generate insights
            insights = self._generate_insights(metrics, benchmarks)
            
            return {
                "metrics": metrics,
                "historical_data": historical_data,
                "benchmarks": benchmarks,
                "insights": insights
            }
            
        except Exception as e:
            logger.error(f"Failed to get campaign metrics: {e}")
            raise
    
    async def _get_template_metrics(self, canvas_id: str) -> Dict[str, Any]:
        """Get performance metrics for a canvas template"""
        try:
            # In a real implementation, this would fetch metrics from similar templates
            # For now, we'll return mock data
            
            # Mock metrics based on similar templates
            metrics = {
                "estimated_open_rate": {
                    "value": 0.39,
                    "unit": "percentage",
                    "confidence": 0.85,
                    "trend": "neutral"
                },
                "estimated_click_rate": {
                    "value": 0.17,
                    "unit": "percentage",
                    "confidence": 0.82,
                    "trend": "neutral"
                },
                "content_score": {
                    "value": 8.2,
                    "unit": "score",
                    "max": 10,
                    "trend": "up"
                },
                "readability_score": {
                    "value": 72,
                    "unit": "score",
                    "max": 100,
                    "trend": "up"
                },
                "load_time": {
                    "value": 1.2,
                    "unit": "seconds",
                    "benchmark": 1.5,
                    "trend": "down"
                }
            }
            
            # Mock historical data from similar templates
            historical_data = []
            for i in range(5):
                template = {
                    "template_id": f"template_{i}",
                    "name": f"Similar Template {i+1}",
                    "open_rate": 0.37 + (0.04 * (i % 3 - 1)),
                    "click_rate": 0.16 + (0.03 * (i % 3 - 1)),
                    "content_score": 7.5 + (0.5 * (i % 3)),
                    "readability_score": 68 + (5 * (i % 3)),
                    "load_time": 1.3 - (0.1 * (i % 3))
                }
                historical_data.append(template)
            
            # Mock benchmarks
            benchmarks = {
                "industry": {
                    "open_rate": 0.35,
                    "click_rate": 0.15,
                    "content_score": 7.0,
                    "readability_score": 65,
                    "load_time": 1.5
                },
                "your_average": {
                    "open_rate": 0.38,
                    "click_rate": 0.16,
                    "content_score": 7.8,
                    "readability_score": 70,
                    "load_time": 1.3
                },
                "top_performers": {
                    "open_rate": 0.45,
                    "click_rate": 0.22,
                    "content_score": 9.0,
                    "readability_score": 85,
                    "load_time": 0.9
                }
            }
            
            # Generate insights
            insights = self._generate_template_insights(metrics, benchmarks)
            
            return {
                "metrics": metrics,
                "historical_data": historical_data,
                "benchmarks": benchmarks,
                "insights": insights
            }
            
        except Exception as e:
            logger.error(f"Failed to get template metrics: {e}")
            raise
    
    def _generate_insights(
        self, 
        metrics: Dict[str, Any],
        benchmarks: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate insights from metrics and benchmarks"""
        insights = []
        
        # Open rate insight
        if metrics["open_rate"]["value"] > benchmarks["industry"]["open_rate"] * 1.2:
            insights.append({
                "type": "positive",
                "message": "Your open rate is 20% above industry average, indicating strong subject lines and sender reputation.",
                "severity": "info",
                "related_metrics": ["open_rate"],
                "timestamp": datetime.utcnow().isoformat()
            })
        elif metrics["open_rate"]["value"] < benchmarks["industry"]["open_rate"] * 0.8:
            insights.append({
                "type": "negative",
                "message": "Your open rate is below industry average. Consider testing different subject lines or sending times.",
                "severity": "warning",
                "related_metrics": ["open_rate"],
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Click rate insight
        if metrics["click_rate"]["value"] > benchmarks["industry"]["click_rate"] * 1.2:
            insights.append({
                "type": "positive",
                "message": "Your click rate is significantly above industry average, indicating engaging content and effective CTAs.",
                "severity": "info",
                "related_metrics": ["click_rate"],
                "timestamp": datetime.utcnow().isoformat()
            })
        elif metrics["click_rate"]["value"] < benchmarks["industry"]["click_rate"] * 0.8:
            insights.append({
                "type": "negative",
                "message": "Your click rate is below industry average. Consider improving your call-to-action buttons and content relevance.",
                "severity": "warning",
                "related_metrics": ["click_rate"],
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Conversion rate insight
        if metrics["conversion_rate"]["value"] > benchmarks["top_performers"]["conversion_rate"] * 0.9:
            insights.append({
                "type": "positive",
                "message": "Your conversion rate is approaching top performer levels, indicating effective targeting and compelling offers.",
                "severity": "info",
                "related_metrics": ["conversion_rate"],
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Bounce rate insight
        if metrics["bounce_rate"]["value"] < benchmarks["industry"]["bounce_rate"] * 0.7:
            insights.append({
                "type": "positive",
                "message": "Your bounce rate is significantly lower than industry average, indicating a healthy email list and good deliverability.",
                "severity": "info",
                "related_metrics": ["bounce_rate"],
                "timestamp": datetime.utcnow().isoformat()
            })
        elif metrics["bounce_rate"]["value"] > benchmarks["industry"]["bounce_rate"] * 1.3:
            insights.append({
                "type": "negative",
                "message": "Your bounce rate is higher than industry average. Consider cleaning your email list and checking for deliverability issues.",
                "severity": "warning",
                "related_metrics": ["bounce_rate"],
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Unsubscribe rate insight
        if metrics["unsubscribe_rate"]["value"] > benchmarks["industry"]["unsubscribe_rate"] * 1.5:
            insights.append({
                "type": "negative",
                "message": "Your unsubscribe rate is significantly higher than industry average. Review your email frequency and content relevance.",
                "severity": "critical",
                "related_metrics": ["unsubscribe_rate"],
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return insights
    
    def _generate_template_insights(
        self, 
        metrics: Dict[str, Any],
        benchmarks: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate insights for template metrics"""
        insights = []
        
        # Content score insight
        if metrics["content_score"]["value"] > 8.5:
            insights.append({
                "type": "positive",
                "message": "Your content score is excellent, indicating high-quality and engaging content.",
                "severity": "info",
                "related_metrics": ["content_score"],
                "timestamp": datetime.utcnow().isoformat()
            })
        elif metrics["content_score"]["value"] < 7.0:
            insights.append({
                "type": "negative",
                "message": "Your content score is below average. Consider improving content quality and relevance.",
                "severity": "warning",
                "related_metrics": ["content_score"],
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Readability score insight
        if metrics["readability_score"]["value"] > 80:
            insights.append({
                "type": "positive",
                "message": "Your readability score is excellent, indicating clear and accessible content.",
                "severity": "info",
                "related_metrics": ["readability_score"],
                "timestamp": datetime.utcnow().isoformat()
            })
        elif metrics["readability_score"]["value"] < 60:
            insights.append({
                "type": "negative",
                "message": "Your readability score is low. Consider simplifying language and shortening sentences.",
                "severity": "warning",
                "related_metrics": ["readability_score"],
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Load time insight
        if metrics["load_time"]["value"] < benchmarks["top_performers"]["load_time"]:
            insights.append({
                "type": "positive",
                "message": "Your email load time is excellent, which will improve user experience and engagement.",
                "severity": "info",
                "related_metrics": ["load_time"],
                "timestamp": datetime.utcnow().isoformat()
            })
        elif metrics["load_time"]["value"] > benchmarks["industry"]["load_time"]:
            insights.append({
                "type": "negative",
                "message": "Your email load time is slower than industry average. Consider optimizing images and reducing email size.",
                "severity": "warning",
                "related_metrics": ["load_time"],
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Estimated metrics insights
        if metrics["estimated_open_rate"]["value"] > benchmarks["industry"]["open_rate"] * 1.1:
            insights.append({
                "type": "positive",
                "message": "Based on similar templates, your estimated open rate is above industry average.",
                "severity": "info",
                "related_metrics": ["estimated_open_rate"],
                "timestamp": datetime.utcnow().isoformat()
            })
        
        if metrics["estimated_click_rate"]["value"] > benchmarks["industry"]["click_rate"] * 1.1:
            insights.append({
                "type": "positive",
                "message": "Based on similar templates, your estimated click rate is above industry average.",
                "severity": "info",
                "related_metrics": ["estimated_click_rate"],
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return insights

# Singleton instance
_instance = None

def get_performance_insights_service():
    """Get singleton instance of PerformanceInsightsService"""
    global _instance
    if _instance is None:
        _instance = PerformanceInsightsService()
    return _instance
