"""Arize AI integration for ML observability."""

import os
import logging
import uuid
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class ArizeAIObservability:
    """Arize AI observability integration."""

    def __init__(self, api_key: Optional[str] = None, space_key: Optional[str] = None):
        """Initialize the Arize AI observability.

        Args:
            api_key: Arize AI API key (defaults to ARIZE_API_KEY env var)
            space_key: Arize AI space key (defaults to ARIZE_SPACE_KEY env var)
        """
        self.api_key = api_key or os.getenv("ARIZE_API_KEY")
        self.space_key = space_key or os.getenv("ARIZE_SPACE_KEY")

        if not self.api_key or not self.space_key:
            logger.warning("ARIZE_API_KEY or ARIZE_SPACE_KEY not set. ML observability will be disabled.")
            self.enabled = False
        else:
            try:
                # Import Arize AI SDK
                import arize
                from arize.api import Client

                # Initialize Arize AI client
                self.client = Client(
                    api_key=self.api_key,
                    space_key=self.space_key
                )

                self.enabled = True
                logger.info("Arize AI observability initialized successfully")
            except ImportError:
                logger.error("Arize AI SDK not installed. Please install with 'pip install arize'.")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Arize AI: {str(e)}")
                self.enabled = False

    def log_prediction(self,
                      model_id: str,
                      model_version: str,
                      prediction_id: Optional[str] = None,
                      features: Optional[Dict[str, Any]] = None,
                      prediction: Optional[Union[str, float, int, Dict[str, Any]]] = None,
                      actual: Optional[Union[str, float, int, Dict[str, Any]]] = None,
                      prediction_timestamp: Optional[str] = None,
                      tags: Optional[Dict[str, str]] = None) -> bool:
        """Log a prediction to Arize AI.

        Args:
            model_id: ID of the model
            model_version: Version of the model
            prediction_id: Optional prediction ID (defaults to a UUID)
            features: Optional features used for the prediction
            prediction: Optional prediction value
            actual: Optional actual value
            prediction_timestamp: Optional prediction timestamp
            tags: Optional tags

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Import Arize AI SDK
            import arize
            from arize.utils.types import ModelTypes, Environments

            # Generate a prediction ID if not provided
            if not prediction_id:
                prediction_id = str(uuid.uuid4())

            # Set prediction timestamp if not provided
            if not prediction_timestamp:
                prediction_timestamp = datetime.now().isoformat()

            # Determine model type based on prediction type
            model_type = ModelTypes.SCORE_CATEGORICAL
            if isinstance(prediction, (int, float)) or (isinstance(prediction, dict) and all(isinstance(v, (int, float)) for v in prediction.values())):
                model_type = ModelTypes.SCORE_NUMERIC

            # Log the prediction
            response = self.client.log(
                model_id=model_id,
                model_version=model_version,
                model_type=model_type,
                environment=Environments.PRODUCTION,
                prediction_id=prediction_id,
                features=features or {},
                prediction_score=prediction,
                actual_score=actual,
                prediction_timestamp=prediction_timestamp,
                tags=tags or {}
            )

            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to log prediction to Arize AI: {str(e)}")
            return False

    def log_llm_prediction(self,
                          model_id: str,
                          model_version: str,
                          prompt: str,
                          response: str,
                          prediction_id: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None,
                          tags: Optional[Dict[str, str]] = None) -> bool:
        """Log an LLM prediction to Arize AI.

        Args:
            model_id: ID of the model
            model_version: Version of the model
            prompt: Prompt sent to the model
            response: Response from the model
            prediction_id: Optional prediction ID (defaults to a UUID)
            metadata: Optional metadata
            tags: Optional tags

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Import Arize AI SDK
            import arize
            from arize.utils.types import ModelTypes, Environments

            # Generate a prediction ID if not provided
            if not prediction_id:
                prediction_id = str(uuid.uuid4())

            # Prepare features and prediction
            features = {
                "prompt": prompt,
                **(metadata or {})
            }

            prediction_score = {"response": response}

            # Prepare embedding feature names and values
            embedding_feature_names = ["prompt"]
            embedding_feature_values = [prompt]

            # Log the prediction
            response = self.client.log(
                model_id=model_id,
                model_version=model_version,
                model_type=ModelTypes.GENERATIVE_LLM,
                environment=Environments.PRODUCTION,
                prediction_id=prediction_id,
                features=features,
                prediction_score=prediction_score,
                tags=tags or {},
                embedding_feature_names=embedding_feature_names,
                embedding_feature_values=embedding_feature_values
            )

            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to log LLM prediction to Arize AI: {str(e)}")
            return False

    def log_feedback(self,
                    model_id: str,
                    prediction_id: str,
                    feedback_id: Optional[str] = None,
                    feedback_type: str = "human",
                    feedback_score: Union[float, int, str] = None,
                    feedback_metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Log feedback for a prediction to Arize AI.

        Args:
            model_id: ID of the model
            prediction_id: ID of the prediction to provide feedback for
            feedback_id: Optional feedback ID (defaults to a UUID)
            feedback_type: Type of feedback (e.g., "human", "model", "system")
            feedback_score: Feedback score or rating
            feedback_metadata: Optional feedback metadata

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Import Arize AI SDK
            import arize

            # Generate a feedback ID if not provided
            if not feedback_id:
                feedback_id = str(uuid.uuid4())

            # Log the feedback
            response = self.client.log_feedback(
                model_id=model_id,
                prediction_id=prediction_id,
                feedback_id=feedback_id,
                feedback_type=feedback_type,
                feedback_score=feedback_score,
                feedback_metadata=feedback_metadata or {}
            )

            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to log feedback to Arize AI: {str(e)}")
            return False

    def log_prompt_evaluation(self,
                             model_id: str,
                             model_version: str,
                             prompt_template: str,
                             prompt_inputs: Dict[str, Any],
                             final_prompt: str,
                             response: str,
                             evaluation_score: Optional[float] = None,
                             evaluation_metrics: Optional[Dict[str, float]] = None,
                             tags: Optional[Dict[str, str]] = None) -> bool:
        """Log a prompt evaluation to Arize AI.

        Args:
            model_id: ID of the model
            model_version: Version of the model
            prompt_template: Template used to generate the prompt
            prompt_inputs: Inputs used in the prompt template
            final_prompt: Final prompt sent to the model
            response: Response from the model
            evaluation_score: Optional overall evaluation score
            evaluation_metrics: Optional evaluation metrics
            tags: Optional tags

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Import Arize AI SDK
            import arize
            from arize.utils.types import ModelTypes, Environments

            # Generate a prediction ID
            prediction_id = str(uuid.uuid4())

            # Prepare features
            features = {
                "prompt_template": prompt_template,
                "final_prompt": final_prompt,
                **{f"input_{k}": v for k, v in prompt_inputs.items()}
            }

            # Prepare prediction score
            prediction_score = {"response": response}

            # Prepare tags
            all_tags = {
                "evaluation_type": "prompt_evaluation",
                **(tags or {})
            }

            # Add evaluation metrics to tags if provided
            if evaluation_metrics:
                for metric_name, metric_value in evaluation_metrics.items():
                    all_tags[f"metric_{metric_name}"] = str(metric_value)

            # Add overall evaluation score to tags if provided
            if evaluation_score is not None:
                all_tags["evaluation_score"] = str(evaluation_score)

            # Log the prediction
            response = self.client.log(
                model_id=model_id,
                model_version=model_version,
                model_type=ModelTypes.GENERATIVE_LLM,
                environment=Environments.PRODUCTION,
                prediction_id=prediction_id,
                features=features,
                prediction_score=prediction_score,
                tags=all_tags,
                embedding_feature_names=["final_prompt"],
                embedding_feature_values=[final_prompt]
            )

            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to log prompt evaluation to Arize AI: {str(e)}")
            return False

# Create a singleton instance
arize_observability = ArizeAIObservability()
