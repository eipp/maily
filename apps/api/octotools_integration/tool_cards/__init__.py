from octotools import ToolCard
from typing import Dict, Any, List, Optional

class MailyToolCard(ToolCard):
    """Base class for all Maily-specific tool cards."""

    def __init__(
        self,
        tool_name: str,
        tool_description: str,
        input_types: Dict[str, str],
        output_type: str,
        demo_commands: Optional[List[Dict[str, str]]] = None,
        user_metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            tool_name=tool_name,
            tool_description=tool_description,
            input_types=input_types,
            output_type=output_type,
            demo_commands=demo_commands or [],
            user_metadata=user_metadata or {}
        )

    def _log_execution(self, inputs: Dict[str, Any], output: Any) -> None:
        """Log the execution of the tool for tracking and debugging."""
        # In a production environment, this would log to a monitoring service
        print(f"Executed {self.tool_name} with inputs: {inputs}")
