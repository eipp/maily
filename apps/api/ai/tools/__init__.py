"""Tool registry for OctoTools."""

import importlib
import os
import logging
from typing import Dict, Any, List, Optional

from octotools import ToolCard

# Import tool configurations
from ai.config import (
    OCTOTOOLS_CONFIG,
    EMAIL_TOOL_CONFIG,
    CONTENT_TOOL_CONFIG,
    ATTACHMENT_TOOL_CONFIG,
    DOCUMENT_TOOL_CONFIG,
    CONTACT_DISCOVERY_TOOL_CONFIG,
    LOOKALIKE_AUDIENCE_TOOL_CONFIG,
    PLATFORM_INTEGRATION_TOOL_CONFIG,
    ANALYTICS_TOOL_CONFIG,
    OPTIMIZATION_TOOL_CONFIG
)

logger = logging.getLogger(__name__)

# Import tool implementations
from ai.tools.contact_discovery_tool import ContactDiscoveryTool, LookalikeAudienceTool
from ai.tools.platform_integration_tool import PlatformIntegrationTool
from ai.tools.email_content_tool import EmailContentGeneratorTool
from ai.tools.email_sender_tool import EmailSenderTool
from ai.tools.attachment_tool import AttachmentGeneratorTool
from ai.tools.document_generator_tool import DocumentGeneratorTool

def register_tools(toolbox):
    """Register all tools in the toolbox.

    Args:
        toolbox: OctoTools toolbox instance

    Returns:
        The toolbox with registered tools
    """
    # Register email tools
    toolbox.register_tool(EmailContentGeneratorTool())
    toolbox.register_tool(EmailSenderTool())
    toolbox.register_tool(AttachmentGeneratorTool())
    toolbox.register_tool(DocumentGeneratorTool())

    # Register contact discovery tools
    toolbox.register_tool(ContactDiscoveryTool())
    toolbox.register_tool(LookalikeAudienceTool())

    # Register platform integration tools
    toolbox.register_tool(PlatformIntegrationTool())

    # Log registered tools
    logger.info(f"Registered {len(toolbox.tools)} tools")

    return toolbox
