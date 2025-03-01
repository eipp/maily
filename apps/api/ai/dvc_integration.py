"""DVC integration for model versioning."""

import os
import subprocess
import logging
import json
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class DVCModelVersioning:
    """DVC model versioning integration."""

    def __init__(self, models_dir: str = "models"):
        """Initialize the DVC model versioning.

        Args:
            models_dir: Directory for model storage
        """
        self.models_dir = models_dir

        # Ensure the models directory exists
        os.makedirs(self.models_dir, exist_ok=True)

        # Check if DVC is installed
        try:
            subprocess.run(["dvc", "--version"], check=True, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("DVC not installed. Please install with 'pip install dvc'.")
            self.enabled = False
            return

        # Check if DVC is initialized
        if not os.path.exists(".dvc"):
            try:
                subprocess.run(["dvc", "init"], check=True)
                logger.info("DVC initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize DVC: {str(e)}")
                self.enabled = False
                return

        self.enabled = True
        logger.info("DVC model versioning initialized successfully")

    def add_model(self,
                 model_name: str,
                 model_version: str,
                 model_data: Dict[str, Any]) -> bool:
        """Add a model to DVC.

        Args:
            model_name: Name of the model
            model_version: Version of the model
            model_data: Model data to save

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Create the model directory
            model_dir = os.path.join(self.models_dir, model_name, model_version)
            os.makedirs(model_dir, exist_ok=True)

            # Save the model data
            with open(os.path.join(model_dir, "model.json"), "w") as f:
                json.dump(model_data, f, indent=2)

            # Add the model to DVC
            subprocess.run(["dvc", "add", model_dir], check=True)

            # Commit the changes
            try:
                subprocess.run(["git", "add", f"{model_dir}.dvc"], check=True)
                subprocess.run(["git", "commit", "-m", f"Add model {model_name} version {model_version}"], check=True)
                logger.info(f"Model {model_name} version {model_version} added to DVC and committed to Git")
            except subprocess.SubprocessError as e:
                logger.warning(f"Failed to commit model to Git: {str(e)}. Model is still tracked by DVC.")

            return True
        except Exception as e:
            logger.error(f"Failed to add model to DVC: {str(e)}")
            return False

    def get_model(self,
                 model_name: str,
                 model_version: str) -> Optional[Dict[str, Any]]:
        """Get a model from DVC.

        Args:
            model_name: Name of the model
            model_version: Version of the model

        Returns:
            Model data if successful, None otherwise
        """
        if not self.enabled:
            return None

        try:
            # Get the model path
            model_dir = os.path.join(self.models_dir, model_name, model_version)
            model_file = os.path.join(model_dir, "model.json")

            # Check if the model file exists locally
            if not os.path.exists(model_file):
                # Pull the model from DVC
                try:
                    subprocess.run(["dvc", "pull", f"{model_dir}.dvc"], check=True)
                except subprocess.SubprocessError as e:
                    logger.error(f"Failed to pull model from DVC: {str(e)}")
                    return None

            # Load the model data
            with open(model_file, "r") as f:
                model_data = json.load(f)

            return model_data
        except Exception as e:
            logger.error(f"Failed to get model from DVC: {str(e)}")
            return None

    def list_models(self) -> List[Dict[str, Any]]:
        """List all models in DVC.

        Returns:
            List of model metadata
        """
        if not self.enabled:
            return []

        try:
            models = []

            # Check if models directory exists
            if not os.path.exists(self.models_dir):
                return []

            # List all model directories
            for model_name in os.listdir(self.models_dir):
                model_dir = os.path.join(self.models_dir, model_name)
                if os.path.isdir(model_dir):
                    for model_version in os.listdir(model_dir):
                        version_dir = os.path.join(model_dir, model_version)
                        if os.path.isdir(version_dir):
                            # Try to load model metadata
                            model_file = os.path.join(version_dir, "model.json")
                            metadata = {}
                            if os.path.exists(model_file):
                                try:
                                    with open(model_file, "r") as f:
                                        metadata = json.load(f)
                                except json.JSONDecodeError:
                                    pass

                            models.append({
                                "name": model_name,
                                "version": model_version,
                                "path": version_dir,
                                "metadata": metadata
                            })

            return models
        except Exception as e:
            logger.error(f"Failed to list models from DVC: {str(e)}")
            return []

    def push_model(self, model_name: str, model_version: str) -> bool:
        """Push a model to the remote DVC storage.

        Args:
            model_name: Name of the model
            model_version: Version of the model

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Get the model path
            model_dir = os.path.join(self.models_dir, model_name, model_version)

            # Push the model to the remote
            subprocess.run(["dvc", "push", f"{model_dir}.dvc"], check=True)

            logger.info(f"Model {model_name} version {model_version} pushed to remote")
            return True
        except Exception as e:
            logger.error(f"Failed to push model to remote: {str(e)}")
            return False

    def compare_models(self,
                      model_name: str,
                      version_a: str,
                      version_b: str) -> Dict[str, Any]:
        """Compare two model versions.

        Args:
            model_name: Name of the model
            version_a: First version to compare
            version_b: Second version to compare

        Returns:
            Dictionary containing comparison results
        """
        if not self.enabled:
            return {"error": "DVC not enabled"}

        try:
            # Get both models
            model_a = self.get_model(model_name, version_a)
            model_b = self.get_model(model_name, version_b)

            if not model_a or not model_b:
                return {"error": "Failed to load one or both models"}

            # Compare the models
            comparison = {
                "model_name": model_name,
                "version_a": version_a,
                "version_b": version_b,
                "differences": {}
            }

            # Compare metadata fields
            all_keys = set(model_a.keys()) | set(model_b.keys())
            for key in all_keys:
                if key not in model_a:
                    comparison["differences"][key] = {
                        "in_a": False,
                        "in_b": True,
                        "value_b": model_b[key]
                    }
                elif key not in model_b:
                    comparison["differences"][key] = {
                        "in_a": True,
                        "in_b": False,
                        "value_a": model_a[key]
                    }
                elif model_a[key] != model_b[key]:
                    comparison["differences"][key] = {
                        "in_a": True,
                        "in_b": True,
                        "value_a": model_a[key],
                        "value_b": model_b[key]
                    }

            return comparison
        except Exception as e:
            logger.error(f"Failed to compare models: {str(e)}")
            return {"error": str(e)}

# Create a singleton instance
dvc_versioning = DVCModelVersioning()
