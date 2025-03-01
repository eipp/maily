#!/usr/bin/env python3
"""
ML Pipeline for Maily - Engagement Prediction and Optimization

This module implements the feature store, model registry, and A/B testing framework
for Maily's ML-driven email optimization capabilities.
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union, Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database models
Base = declarative_base()

class FeatureSet(Base):
    """Database model for storing feature sets"""
    __tablename__ = "feature_sets"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    features = Column(JSON)  # List of feature names
    data_sources = Column(JSON)  # List of data sources


class MLModel(Base):
    """Database model for storing ML models metadata"""
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    version = Column(String)
    model_type = Column(String)  # engagement_prediction, subject_optimization, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    metrics = Column(JSON)  # Performance metrics
    parameters = Column(JSON)  # Model hyperparameters
    feature_set_id = Column(Integer)
    s3_path = Column(String)  # Path to model artifacts
    is_active = Column(Integer, default=0)  # 0 = inactive, 1 = active


class ABTest(Base):
    """Database model for A/B test experiments"""
    __tablename__ = "ab_tests"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String)  # running, completed, stopped
    variants = Column(JSON)  # List of variant names
    metrics = Column(JSON)  # Metrics to track
    results = Column(JSON)  # Test results
    winner = Column(String, nullable=True)  # Winning variant


# Pydantic models for API
class FeatureStoreConfig(BaseModel):
    """Configuration for the feature store"""
    data_sources: List[str]
    update_frequency: str = "hourly"  # hourly, daily, weekly
    feature_groups: Optional[Dict[str, List[str]]] = None


class ModelConfig(BaseModel):
    """Configuration for ML models"""
    model_type: str
    feature_set_name: str
    parameters: Dict[str, Any] = {}
    description: Optional[str] = None


class ABTestConfig(BaseModel):
    """Configuration for A/B tests"""
    name: str
    description: Optional[str] = None
    experiment_duration_days: int = 7
    minimum_sample_size: int = 1000
    statistical_significance: float = 0.95
    metrics: List[str] = ["open_rate", "click_rate"]
    variants: List[str] = ["control", "treatment"]


class ModelType(str, Enum):
    """Types of ML models supported"""
    ENGAGEMENT_PREDICTION = "engagement_prediction"
    SUBJECT_OPTIMIZATION = "subject_optimization"
    SEND_TIME_OPTIMIZATION = "send_time_optimization"
    AUDIENCE_SEGMENTATION = "audience_segmentation"


class FeatureStore:
    """
    Feature Store for ML-ready data preparation

    Handles:
    - Feature computation and storage
    - Feature versioning
    - Feature serving for training and inference
    """

    def __init__(self, config: FeatureStoreConfig):
        """Initialize the feature store with configuration"""
        self.config = config
        self.engine = create_engine("sqlite:///ml_features.db", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        logger.info(f"Feature store initialized with sources: {config.data_sources}")

    def create_feature_set(self, name: str, description: str, features: List[str]) -> int:
        """Create a new feature set"""
        session = self.Session()
        try:
            feature_set = FeatureSet(
                name=name,
                description=description,
                features=features,
                data_sources=self.config.data_sources
            )
            session.add(feature_set)
            session.commit()
            logger.info(f"Created feature set '{name}' with {len(features)} features")
            return feature_set.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating feature set: {e}")
            raise
        finally:
            session.close()

    def get_training_features(self, feature_set_name: str, start_date: datetime,
                             end_date: datetime) -> pd.DataFrame:
        """Get features for model training"""
        # In a real implementation, this would query the feature store
        # Here we'll simulate it with random data
        session = self.Session()
        try:
            feature_set = session.query(FeatureSet).filter_by(name=feature_set_name).first()
            if not feature_set:
                raise ValueError(f"Feature set '{feature_set_name}' not found")

            # Simulate feature data
            num_samples = 1000
            feature_data = {}

            for feature in feature_set.features:
                feature_data[feature] = np.random.randn(num_samples)

            # Add some time-based features
            dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days)]
            dates = dates[:num_samples]  # Truncate if needed
            feature_data['date'] = dates[:len(feature_data[list(feature_data.keys())[0]])]

            df = pd.DataFrame(feature_data)
            logger.info(f"Retrieved {len(df)} training samples for feature set '{feature_set_name}'")
            return df
        except Exception as e:
            logger.error(f"Error getting training features: {e}")
            raise
        finally:
            session.close()

    def get_inference_features(self, feature_set_name: str, entity_ids: List[str]) -> pd.DataFrame:
        """Get features for model inference"""
        # Similar to get_training_features but for real-time inference
        session = self.Session()
        try:
            feature_set = session.query(FeatureSet).filter_by(name=feature_set_name).first()
            if not feature_set:
                raise ValueError(f"Feature set '{feature_set_name}' not found")

            # Simulate feature data for inference
            feature_data = {}

            for feature in feature_set.features:
                feature_data[feature] = np.random.randn(len(entity_ids))

            feature_data['entity_id'] = entity_ids

            df = pd.DataFrame(feature_data)
            logger.info(f"Retrieved inference features for {len(entity_ids)} entities")
            return df
        except Exception as e:
            logger.error(f"Error getting inference features: {e}")
            raise
        finally:
            session.close()


class ModelRegistry:
    """
    Model Registry for ML model management

    Handles:
    - Model versioning
    - Model deployment
    - Model monitoring
    - Automatic rollback
    """

    def __init__(self, model_types: List[str], versioning: bool = True, auto_rollback: bool = True):
        """Initialize the model registry"""
        self.model_types = model_types
        self.versioning = versioning
        self.auto_rollback = auto_rollback
        self.engine = create_engine("sqlite:///ml_models.db", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        logger.info(f"Model registry initialized with types: {model_types}")

    def register_model(self, config: ModelConfig, metrics: Dict[str, float],
                      s3_path: str) -> Tuple[str, str]:
        """Register a new model in the registry"""
        session = self.Session()
        try:
            # Generate version
            existing_models = session.query(MLModel).filter_by(
                name=config.model_type
            ).order_by(MLModel.version.desc()).all()

            if not existing_models:
                version = "1.0.0"
            else:
                latest_version = existing_models[0].version
                major, minor, patch = map(int, latest_version.split('.'))
                version = f"{major}.{minor}.{patch + 1}"

            # Get feature set ID
            feature_set = session.query(FeatureSet).filter_by(name=config.feature_set_name).first()
            if not feature_set:
                raise ValueError(f"Feature set '{config.feature_set_name}' not found")

            model = MLModel(
                name=config.model_type,
                version=version,
                model_type=config.model_type,
                metrics=metrics,
                parameters=config.parameters,
                feature_set_id=feature_set.id,
                s3_path=s3_path,
                is_active=0  # Not active by default
            )

            session.add(model)
            session.commit()
            logger.info(f"Registered model {config.model_type} version {version}")
            return config.model_type, version
        except Exception as e:
            session.rollback()
            logger.error(f"Error registering model: {e}")
            raise
        finally:
            session.close()

    def activate_model(self, model_type: str, version: str) -> bool:
        """Activate a specific model version"""
        session = self.Session()
        try:
            # Deactivate current active model
            active_models = session.query(MLModel).filter_by(
                model_type=model_type, is_active=1
            ).all()

            for model in active_models:
                model.is_active = 0

            # Activate the specified model
            model = session.query(MLModel).filter_by(
                model_type=model_type, version=version
            ).first()

            if not model:
                raise ValueError(f"Model {model_type} version {version} not found")

            model.is_active = 1
            session.commit()
            logger.info(f"Activated model {model_type} version {version}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error activating model: {e}")
            raise
        finally:
            session.close()

    def get_active_model(self, model_type: str) -> Optional[Dict[str, Any]]:
        """Get the currently active model for a given type"""
        session = self.Session()
        try:
            model = session.query(MLModel).filter_by(
                model_type=model_type, is_active=1
            ).first()

            if not model:
                logger.warning(f"No active model found for type {model_type}")
                return None

            return {
                "name": model.name,
                "version": model.version,
                "model_type": model.model_type,
                "metrics": model.metrics,
                "parameters": model.parameters,
                "feature_set_id": model.feature_set_id,
                "s3_path": model.s3_path,
                "created_at": model.created_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting active model: {e}")
            raise
        finally:
            session.close()


class ABTestFramework:
    """
    A/B Testing Framework for model evaluation

    Handles:
    - Test setup and configuration
    - Variant assignment
    - Results analysis
    - Statistical significance testing
    """

    def __init__(self, experiment_duration_days: int = 7,
                minimum_sample_size: int = 1000,
                statistical_significance: float = 0.95):
        """Initialize the A/B testing framework"""
        self.experiment_duration_days = experiment_duration_days
        self.minimum_sample_size = minimum_sample_size
        self.statistical_significance = statistical_significance
        self.engine = create_engine("sqlite:///ab_tests.db", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        logger.info("A/B testing framework initialized")

    def create_test(self, config: ABTestConfig) -> int:
        """Create a new A/B test"""
        session = self.Session()
        try:
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=config.experiment_duration_days)

            test = ABTest(
                name=config.name,
                description=config.description,
                start_date=start_date,
                end_date=end_date,
                status="running",
                variants=config.variants,
                metrics=config.metrics,
                results={},
                winner=None
            )

            session.add(test)
            session.commit()
            logger.info(f"Created A/B test '{config.name}' running until {end_date}")
            return test.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating A/B test: {e}")
            raise
        finally:
            session.close()

    def assign_variant(self, test_name: str, user_id: str) -> str:
        """Assign a user to a variant"""
        session = self.Session()
        try:
            test = session.query(ABTest).filter_by(name=test_name).first()
            if not test:
                raise ValueError(f"Test '{test_name}' not found")

            if test.status != "running":
                logger.warning(f"Test '{test_name}' is not running (status: {test.status})")

            # Deterministic assignment based on user_id for consistency
            variant_index = hash(user_id) % len(test.variants)
            variant = test.variants[variant_index]

            logger.debug(f"Assigned user {user_id} to variant '{variant}' in test '{test_name}'")
            return variant
        except Exception as e:
            logger.error(f"Error assigning variant: {e}")
            raise
        finally:
            session.close()

    def record_event(self, test_name: str, user_id: str, variant: str,
                    metric: str, value: float) -> bool:
        """Record a metric event for a user in a test"""
        # In a real implementation, this would store events in a database
        # Here we'll just log it
        logger.info(f"Recorded {metric}={value} for user {user_id} in variant '{variant}' of test '{test_name}'")
        return True

    def analyze_results(self, test_name: str) -> Dict[str, Any]:
        """Analyze test results and determine if there's a winner"""
        session = self.Session()
        try:
            test = session.query(ABTest).filter_by(name=test_name).first()
            if not test:
                raise ValueError(f"Test '{test_name}' not found")

            # In a real implementation, this would query the event database
            # and perform statistical analysis
            # Here we'll simulate results

            results = {}
            for variant in test.variants:
                results[variant] = {}
                for metric in test.metrics:
                    # Simulate metric values with some randomness
                    base_value = 0.2 if metric == "open_rate" else 0.05
                    results[variant][metric] = {
                        "mean": base_value + np.random.uniform(-0.05, 0.05),
                        "std": 0.02,
                        "sample_size": np.random.randint(900, 1500)
                    }

            # Determine winner based on primary metric (first in the list)
            primary_metric = test.metrics[0]
            best_variant = max(test.variants, key=lambda v: results[v][primary_metric]["mean"])

            # Check if sample size is sufficient
            all_sufficient = all(
                results[v][primary_metric]["sample_size"] >= self.minimum_sample_size
                for v in test.variants
            )

            # Update test results
            test.results = results

            if all_sufficient:
                test.winner = best_variant
                test.status = "completed"
                logger.info(f"Test '{test_name}' completed with winner: {best_variant}")
            else:
                logger.info(f"Test '{test_name}' needs more samples before determining a winner")

            session.commit()

            return {
                "name": test.name,
                "status": test.status,
                "results": results,
                "winner": test.winner,
                "sufficient_data": all_sufficient
            }
        except Exception as e:
            session.rollback()
            logger.error(f"Error analyzing results: {e}")
            raise
        finally:
            session.close()


class Pipeline:
    """
    Main ML Pipeline that integrates all components

    Provides a unified interface for:
    - Feature engineering
    - Model training and evaluation
    - Model deployment
    - A/B testing
    """

    def __init__(self, feature_store: FeatureStore, model_registry: ModelRegistry,
                ab_test_framework: ABTestFramework):
        """Initialize the ML pipeline with its components"""
        self.feature_store = feature_store
        self.model_registry = model_registry
        self.ab_test_framework = ab_test_framework
        logger.info("ML Pipeline initialized")

    def train_engagement_model(self, feature_set_name: str,
                              start_date: datetime, end_date: datetime) -> Tuple[str, str]:
        """Train an engagement prediction model"""
        logger.info(f"Training engagement model with feature set '{feature_set_name}'")

        # Get training data
        features_df = self.feature_store.get_training_features(
            feature_set_name, start_date, end_date
        )

        # In a real implementation, this would:
        # 1. Preprocess the data
        # 2. Train the model
        # 3. Evaluate performance
        # 4. Save the model artifacts

        # Simulate model training
        logger.info(f"Training model on {len(features_df)} samples")

        # Simulate model metrics
        metrics = {
            "auc": 0.82,
            "precision": 0.76,
            "recall": 0.71,
            "f1": 0.73
        }

        # Simulate model parameters
        parameters = {
            "learning_rate": 0.01,
            "max_depth": 5,
            "num_estimators": 100
        }

        # Simulate S3 path
        s3_path = f"s3://maily-models/engagement/{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Register the model
        model_config = ModelConfig(
            model_type=ModelType.ENGAGEMENT_PREDICTION,
            feature_set_name=feature_set_name,
            parameters=parameters,
            description="Engagement prediction model"
        )

        model_name, version = self.model_registry.register_model(
            model_config, metrics, s3_path
        )

        logger.info(f"Registered model {model_name} version {version}")

        # Activate the model if it's better than the current one
        current_model = self.model_registry.get_active_model(ModelType.ENGAGEMENT_PREDICTION)

        if not current_model or metrics["auc"] > current_model["metrics"]["auc"]:
            self.model_registry.activate_model(model_name, version)
            logger.info(f"Activated new model {model_name} version {version}")
        else:
            logger.info(f"New model {version} not activated as it doesn't improve on current model")

        return model_name, version

    def predict_engagement(self, email_ids: List[str]) -> Dict[str, float]:
        """Predict engagement probability for a list of emails"""
        logger.info(f"Predicting engagement for {len(email_ids)} emails")

        # Get active model
        model_info = self.model_registry.get_active_model(ModelType.ENGAGEMENT_PREDICTION)
        if not model_info:
            raise ValueError("No active engagement prediction model found")

        # Get feature set ID from model
        feature_set_id = model_info["feature_set_id"]

        # In a real implementation, this would:
        # 1. Get the feature set name from the ID
        # 2. Get inference features for the emails
        # 3. Load the model from S3
        # 4. Make predictions

        # Simulate predictions
        predictions = {}
        for email_id in email_ids:
            # Generate a random prediction between 0 and 1
            # In reality, this would be the output of the model
            predictions[email_id] = float(np.random.beta(2, 5))

        logger.info(f"Generated predictions for {len(predictions)} emails")
        return predictions

    def optimize_subject_line(self, subject_lines: List[str], audience_segment: str) -> Dict[str, float]:
        """Predict which subject line will perform best for a given audience segment"""
        logger.info(f"Optimizing {len(subject_lines)} subject lines for segment '{audience_segment}'")

        # Get active model
        model_info = self.model_registry.get_active_model(ModelType.SUBJECT_OPTIMIZATION)
        if not model_info:
            raise ValueError("No active subject optimization model found")

        # In a real implementation, this would:
        # 1. Extract features from the subject lines
        # 2. Load the model
        # 3. Make predictions for each subject line

        # Simulate predictions
        scores = {}
        for i, subject in enumerate(subject_lines):
            # Generate a score between 0 and 1
            # Higher is better
            base_score = 0.5
            length_factor = min(len(subject) / 50, 1.0) * 0.1  # Prefer medium length
            question_factor = 0.05 if "?" in subject else 0
            personalization_factor = 0.1 if audience_segment.lower() in subject.lower() else 0

            score = base_score + length_factor + question_factor + personalization_factor
            score += np.random.normal(0, 0.05)  # Add some noise
            score = max(0, min(1, score))  # Clamp between 0 and 1

            scores[subject] = float(score)

        logger.info(f"Generated scores for {len(scores)} subject lines")
        return scores

    def setup_ab_test(self, name: str, variants: List[str],
                     metrics: List[str], duration_days: int = 7) -> int:
        """Set up an A/B test for model evaluation"""
        logger.info(f"Setting up A/B test '{name}' with {len(variants)} variants")

        config = ABTestConfig(
            name=name,
            description=f"A/B test for {name}",
            experiment_duration_days=duration_days,
            variants=variants,
            metrics=metrics
        )

        test_id = self.ab_test_framework.create_test(config)
        logger.info(f"Created A/B test with ID {test_id}")

        return test_id


def build_ml_pipeline():
    """Build and configure the ML pipeline"""
    # Set up feature store
    feature_store_config = FeatureStoreConfig(
        data_sources=["campaigns", "user_events", "email_metrics"],
        update_frequency="hourly"
    )
    feature_store = FeatureStore(feature_store_config)

    # Set up model registry
    model_registry = ModelRegistry(
        model_types=[
            ModelType.ENGAGEMENT_PREDICTION,
            ModelType.SUBJECT_OPTIMIZATION,
            ModelType.SEND_TIME_OPTIMIZATION
        ],
        versioning=True,
        auto_rollback=True
    )

    # Set up A/B test framework
    ab_test_framework = ABTestFramework(
        experiment_duration_days=7,
        minimum_sample_size=1000,
        statistical_significance=0.95
    )

    # Create and return the pipeline
    return Pipeline(feature_store, model_registry, ab_test_framework)


if __name__ == "__main__":
    # Example usage
    pipeline = build_ml_pipeline()

    # Create a feature set
    feature_store = pipeline.feature_store
    feature_store.create_feature_set(
        name="email_engagement_features",
        description="Features for predicting email engagement",
        features=[
            "user_open_rate_30d",
            "user_click_rate_30d",
            "email_word_count",
            "email_subject_length",
            "email_image_count",
            "day_of_week",
            "hour_of_day",
            "days_since_last_open"
        ]
    )

    # Train a model
    start_date = datetime.utcnow() - timedelta(days=90)
    end_date = datetime.utcnow() - timedelta(days=1)

    model_name, version = pipeline.train_engagement_model(
        "email_engagement_features",
        start_date,
        end_date
    )

    print(f"Trained model: {model_name} v{version}")

    # Make predictions
    email_ids = [f"email_{i}" for i in range(5)]
    predictions = pipeline.predict_engagement(email_ids)

    print("Engagement predictions:")
    for email_id, score in predictions.items():
        print(f"  {email_id}: {score:.4f}")

    # Set up an A/B test
    test_id = pipeline.setup_ab_test(
        name="subject_line_test_2023_06",
        variants=["control", "emoji", "question"],
        metrics=["open_rate", "click_rate"],
        duration_days=7
    )

    print(f"Created A/B test with ID: {test_id}")
