"""Weights & Biases integration for model versioning and experiment tracking."""

import os
import logging
from typing import Dict, Any, Optional, List
import time

logger = logging.getLogger(__name__)

class WandbModelRegistry:
    """Weights & Biases model registry integration."""

    def __init__(self, api_key: Optional[str] = None, project_name: str = "maily-ai"):
        """Initialize the Weights & Biases model registry.

        Args:
            api_key: Weights & Biases API key (defaults to WANDB_API_KEY env var)
            project_name: Weights & Biases project name
        """
        self.api_key = api_key or os.getenv("WANDB_API_KEY")
        self.project_name = project_name

        if not self.api_key:
            logger.warning("WANDB_API_KEY not set. Model versioning will be disabled.")
            self.enabled = False
        else:
            try:
                # Import wandb here to avoid import errors if not installed
                import wandb
                wandb.login(key=self.api_key)
                self.enabled = True
                logger.info("Weights & Biases model registry initialized successfully")
            except ImportError:
                logger.error("Weights & Biases not installed. Please install with 'pip install wandb'.")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Weights & Biases: {str(e)}")
                self.enabled = False

    def log_model_usage(self,
                        model_name: str,
                        provider: str,
                        prompt: str,
                        response: str,
                        metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Log model usage to Weights & Biases.

        Args:
            model_name: Name of the model
            provider: Provider of the model (e.g., openai, anthropic)
            prompt: Prompt sent to the model
            response: Response from the model
            metadata: Additional metadata

        Returns:
            Run ID if successful, None otherwise
        """
        if not self.enabled:
            return None

        try:
            # Import wandb here to avoid import errors if not installed
            import wandb

            # Initialize a new W&B run
            run = wandb.init(
                project=self.project_name,
                job_type="inference",
                config={
                    "model_name": model_name,
                    "provider": provider,
                    "timestamp": time.time(),
                    **(metadata or {})
                }
            )

            # Log the prompt and response
            wandb.log({
                "prompt": prompt,
                "response": response,
                "prompt_tokens": len(prompt.split()),
                "response_tokens": len(response.split()),
                "total_tokens": len(prompt.split()) + len(response.split())
            })

            # Finish the run
            run_id = run.id
            run.finish()

            return run_id
        except Exception as e:
            logger.error(f"Failed to log model usage to Weights & Biases: {str(e)}")
            return None

    def start_experiment(self,
                        experiment_name: str,
                        config: Dict[str, Any]) -> Optional[str]:
        """Start a new experiment in Weights & Biases.

        Args:
            experiment_name: Name of the experiment
            config: Experiment configuration

        Returns:
            Run ID if successful, None otherwise
        """
        if not self.enabled:
            return None

        try:
            # Import wandb here to avoid import errors if not installed
            import wandb

            # Initialize a new W&B run
            run = wandb.init(
                project=self.project_name,
                name=experiment_name,
                job_type="experiment",
                config=config
            )

            return run.id
        except Exception as e:
            logger.error(f"Failed to start experiment in Weights & Biases: {str(e)}")
            return None

    def log_experiment_metrics(self,
                              run_id: str,
                              metrics: Dict[str, Any]) -> bool:
        """Log metrics to an existing experiment.

        Args:
            run_id: Run ID of the experiment
            metrics: Metrics to log

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Import wandb here to avoid import errors if not installed
            import wandb

            # Resume the run
            with wandb.init(id=run_id, resume="must") as run:
                # Log the metrics
                wandb.log(metrics)

            return True
        except Exception as e:
            logger.error(f"Failed to log metrics to Weights & Biases: {str(e)}")
            return False

    def register_model(self,
                      model_name: str,
                      model_version: str,
                      metadata: Dict[str, Any],
                      aliases: Optional[List[str]] = None) -> Optional[str]:
        """Register a model in the Weights & Biases model registry.

        Args:
            model_name: Name of the model
            model_version: Version of the model
            metadata: Model metadata
            aliases: Optional list of aliases for the model

        Returns:
            Model ID if successful, None otherwise
        """
        if not self.enabled:
            return None

        try:
            # Import wandb here to avoid import errors if not installed
            import wandb

            # Initialize a new W&B run
            with wandb.init(
                project=self.project_name,
                job_type="model_registration",
                config={
                    "model_name": model_name,
                    "model_version": model_version,
                    **metadata
                }
            ) as run:
                # Log the model to the registry
                artifact = wandb.Artifact(
                    name=model_name,
                    type="model",
                    metadata=metadata
                )

                # Add files to the artifact if needed
                # artifact.add_file("path/to/model/file")

                # Log the artifact
                run.log_artifact(artifact, aliases=aliases or ["latest"])

                return artifact.id
        except Exception as e:
            logger.error(f"Failed to register model in Weights & Biases: {str(e)}")
            return None

    def get_model(self,
                 model_name: str,
                 alias: str = "latest") -> Optional[Dict[str, Any]]:
        """Get a model from the Weights & Biases model registry.

        Args:
            model_name: Name of the model
            alias: Alias of the model version

        Returns:
            Model metadata if successful, None otherwise
        """
        if not self.enabled:
            return None

        try:
            # Import wandb here to avoid import errors if not installed
            import wandb

            # Initialize a new W&B run
            with wandb.init(
                project=self.project_name,
                job_type="model_retrieval"
            ) as run:
                # Get the artifact
                artifact = run.use_artifact(f"{model_name}:{alias}")

                # Return the metadata
                return artifact.metadata
        except Exception as e:
            logger.error(f"Failed to get model from Weights & Biases: {str(e)}")
            return None

# Create a singleton instance
wandb_registry = WandbModelRegistry()
