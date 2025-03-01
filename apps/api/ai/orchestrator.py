"""OctoTools orchestrator for autonomous workflows."""

import logging
from typing import Dict, Any, List, Optional

from ai.config import OCTOTOOLS_CONFIG

logger = logging.getLogger(__name__)

class OctoToolsOrchestrator:
    """Orchestrator for autonomous OctoTools workflows."""

    def __init__(self, octotools):
        """Initialize the orchestrator with OctoTools instance."""
        self.octotools = octotools
        self.workflows = {
            "contact_discovery": self._contact_discovery_workflow,
            "platform_integration": self._platform_integration_workflow,
            "email_campaign": self._email_campaign_workflow,
            "audience_segmentation": self._audience_segmentation_workflow,
            "multi_platform_campaign": self._multi_platform_campaign_workflow,
        }

    async def run_workflow(
        self,
        workflow_name: str,
        workflow_data: Dict[str, Any],
        langfuse_client=None
    ) -> Dict[str, Any]:
        """
        Run an autonomous workflow.

        Args:
            workflow_name: Name of the workflow to run
            workflow_data: Data for the workflow
            langfuse_client: Optional Langfuse client for tracing

        Returns:
            Dictionary containing workflow results
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")

        # Get the workflow function
        workflow_func = self.workflows[workflow_name]

        # Run the workflow
        if langfuse_client:
            # Create a trace
            trace = langfuse_client.trace(
                name=f"workflow_{workflow_name}",
                user_id=str(workflow_data.get("user_id", "unknown")),
                metadata={"workflow_name": workflow_name}
            )

            try:
                # Create a span for the workflow
                with trace.span(name="workflow_execution") as span:
                    # Execute the workflow
                    result = await workflow_func(workflow_data)

                    # Add the result to the span
                    span.add_observation(
                        name="workflow_result",
                        value=result
                    )

                return result
            except Exception as e:
                # Log the error
                trace.error(
                    name="workflow_error",
                    message=str(e)
                )
                # Re-raise the exception
                raise
        else:
            # Run the workflow without tracing
            return await workflow_func(workflow_data)

    async def _contact_discovery_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the contact discovery workflow.

        This workflow:
        1. Discovers contacts based on target criteria
        2. Enriches the contacts with additional information
        3. Segments the contacts into audiences

        Args:
            workflow_data: Data for the workflow

        Returns:
            Dictionary containing workflow results
        """
        logger.info("Starting contact discovery workflow")

        # Step 1: Discover contacts
        discovery_query = f"Discover contacts for {workflow_data.get('objective')} with criteria: {workflow_data.get('target_criteria')}."
        discovery_result = await self.octotools.execute(
            query=discovery_query,
            toolset=["Contact_Discovery_Tool"],
            context=workflow_data,
            max_steps=OCTOTOOLS_CONFIG["model"]["max_steps"]
        )

        # Extract contacts from the result
        contacts = discovery_result.final_answer.get("contacts", [])
        logger.info(f"Discovered {len(contacts)} contacts")

        # Step 2: Enrich contacts if needed
        if workflow_data.get("enrich_contacts", True) and contacts:
            enrichment_query = "Enrich these contacts with additional information."
            enrichment_result = await self.octotools.execute(
                query=enrichment_query,
                toolset=["Contact_Discovery_Tool"],
                context={"contacts": contacts, **workflow_data},
                max_steps=OCTOTOOLS_CONFIG["model"]["max_steps"]
            )

            # Update contacts with enriched information
            contacts = enrichment_result.final_answer.get("contacts", contacts)
            logger.info(f"Enriched {len(contacts)} contacts")

        # Step 3: Segment contacts if needed
        if workflow_data.get("segment_contacts", True) and contacts:
            segmentation_query = "Segment these contacts into audiences based on their characteristics."
            segmentation_result = await self.octotools.execute(
                query=segmentation_query,
                toolset=["Lookalike_Audience_Tool"],
                context={"contacts": contacts, **workflow_data},
                max_steps=OCTOTOOLS_CONFIG["model"]["max_steps"]
            )

            # Get segments from the result
            segments = segmentation_result.final_answer.get("segments", [])
            logger.info(f"Created {len(segments)} segments")

            return {
                "status": "success",
                "contacts": contacts,
                "segments": segments,
                "discovery_metrics": {
                    "total_discovered": len(contacts),
                    "segments_created": len(segments)
                },
                "steps": [
                    {"name": "discovery", "tools_used": discovery_result.tools_used},
                    {"name": "enrichment", "tools_used": enrichment_result.tools_used},
                    {"name": "segmentation", "tools_used": segmentation_result.tools_used}
                ]
            }

        return {
            "status": "success",
            "contacts": contacts,
            "discovery_metrics": {
                "total_discovered": len(contacts)
            },
            "steps": [
                {"name": "discovery", "tools_used": discovery_result.tools_used}
            ]
        }

    async def _platform_integration_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the platform integration workflow.

        This workflow:
        1. Connects to the specified platform
        2. Retrieves data from the platform
        3. Processes the data for use in Maily

        Args:
            workflow_data: Data for the workflow

        Returns:
            Dictionary containing workflow results
        """
        logger.info(f"Starting platform integration workflow for {workflow_data.get('platform')}")

        # Step 1: Connect to the platform
        connection_query = f"Connect to {workflow_data.get('platform')} using the provided credentials."
        connection_result = await self.octotools.execute(
            query=connection_query,
            toolset=["Platform_Integration_Tool"],
            context=workflow_data,
            max_steps=OCTOTOOLS_CONFIG["model"]["max_steps"]
        )

        # Extract connection info from the result
        connection_info = connection_result.final_answer

        # Step 2: Retrieve data from the platform
        if workflow_data.get("retrieve_data", True):
            retrieval_query = f"Retrieve {workflow_data.get('data_type', 'contacts')} data from {workflow_data.get('platform')}."
            retrieval_result = await self.octotools.execute(
                query=retrieval_query,
                toolset=["Platform_Integration_Tool"],
                context={"connection_info": connection_info, **workflow_data},
                max_steps=OCTOTOOLS_CONFIG["model"]["max_steps"]
            )

            # Extract data from the result
            platform_data = retrieval_result.final_answer.get("data", {})

            # Step 3: Process the data if needed
            if workflow_data.get("process_data", True) and platform_data:
                processing_query = f"Process the retrieved data for use in Maily."
                processing_result = await self.octotools.execute(
                    query=processing_query,
                    toolset=["Platform_Integration_Tool"],
                    context={"platform_data": platform_data, **workflow_data},
                    max_steps=OCTOTOOLS_CONFIG["model"]["max_steps"]
                )

                # Extract processed data from the result
                processed_data = processing_result.final_answer.get("data", platform_data)

                return {
                    "status": "success",
                    "platform": workflow_data.get("platform"),
                    "connection_info": connection_info,
                    "data": processed_data,
                    "steps": [
                        {"name": "connection", "tools_used": connection_result.tools_used},
                        {"name": "retrieval", "tools_used": retrieval_result.tools_used},
                        {"name": "processing", "tools_used": processing_result.tools_used}
                    ]
                }

            return {
                "status": "success",
                "platform": workflow_data.get("platform"),
                "connection_info": connection_info,
                "data": platform_data,
                "steps": [
                    {"name": "connection", "tools_used": connection_result.tools_used},
                    {"name": "retrieval", "tools_used": retrieval_result.tools_used}
                ]
            }

        return {
            "status": "success",
            "platform": workflow_data.get("platform"),
            "connection_info": connection_info,
            "steps": [
                {"name": "connection", "tools_used": connection_result.tools_used}
            ]
        }

    async def _email_campaign_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the email campaign workflow.

        This workflow:
        1. Generates email content
        2. Creates attachments if needed
        3. Sends the campaign

        Args:
            workflow_data: Data for the workflow

        Returns:
            Dictionary containing workflow results
        """
        logger.info("Starting email campaign workflow")

        # Step 1: Generate email content
        content_query = f"Generate email content for {workflow_data.get('objective')} targeting {workflow_data.get('audience')}."
        content_result = await self.octotools.execute(
            query=content_query,
            toolset=["Email_Content_Generator"],
            context=workflow_data,
            max_steps=OCTOTOOLS_CONFIG["model"]["max_steps"]
        )

        # Extract content from the result
        content = content_result.final_answer

        # Step 2: Create attachments if needed
        attachments = []
        if workflow_data.get("attachments"):
            attachment_query = "Create attachments for the email campaign."
            attachment_result = await self.octotools.execute(
                query=attachment_query,
                toolset=["Attachment_Generator"],
                context={"content": content, **workflow_data},
                max_steps=OCTOTOOLS_CONFIG["model"]["max_steps"]
            )

            # Extract attachments from the result
            attachments = attachment_result.final_answer.get("attachments", [])

        # Step 3: Send the campaign
        if workflow_data.get("send_campaign", True):
            send_query = "Send the email campaign to the recipients."
            send_result = await self.octotools.execute(
                query=send_query,
                toolset=["Email_Sender"],
                context={
                    "content": content,
                    "attachments": attachments,
                    **workflow_data
                },
                max_steps=OCTOTOOLS_CONFIG["model"]["max_steps"]
            )

            # Extract send info from the result
            send_info = send_result.final_answer

            return {
                "status": "success",
                "campaign_id": send_info.get("campaign_id", ""),
                "content": content,
                "attachments": attachments,
                "send_info": send_info,
                "steps": [
                    {"name": "content_generation", "tools_used": content_result.tools_used},
                    {"name": "attachment_creation", "tools_used": attachment_result.tools_used if workflow_data.get("attachments") else []},
                    {"name": "campaign_sending", "tools_used": send_result.tools_used}
                ]
            }

        return {
            "status": "success",
            "content": content,
            "attachments": attachments,
            "steps": [
                {"name": "content_generation", "tools_used": content_result.tools_used},
                {"name": "attachment_creation", "tools_used": attachment_result.tools_used if workflow_data.get("attachments") else []}
            ]
        }

    async def _audience_segmentation_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the audience segmentation workflow.

        This workflow:
        1. Analyzes the contact list
        2. Creates segments based on criteria
        3. Generates personalized content for each segment

        Args:
            workflow_data: Data for the workflow

        Returns:
            Dictionary containing workflow results
        """
        logger.info("Starting audience segmentation workflow")

        # Step 1: Analyze the contact list
        analysis_query = "Analyze the contact list to identify patterns and segments."
        analysis_result = await self.octotools.execute(
            query=analysis_query,
            toolset=["Lookalike_Audience_Tool"],
            context=workflow_data,
            max_steps=OCTOTOOLS_CONFIG["model"]["max_steps"]
        )

        # Extract analysis from the result
        analysis = analysis_result.final_answer

        # Step 2: Create segments
        segmentation_query = "Create segments based on the analysis and segmentation criteria."
        segmentation_result = await self.octotools.execute(
            query=segmentation_query,
            toolset=["Lookalike_Audience_Tool"],
            context={"analysis": analysis, **workflow_data},
            max_steps=OCTOTOOLS_CONFIG["model"]["max_steps"]
        )

        # Extract segments from the result
        segments = segmentation_result.final_answer.get("segments", [])

        # Step 3: Generate personalized content for each segment if needed
        personalized_content = {}
        if workflow_data.get("generate_content", True) and segments:
            for segment in segments:
                content_query = f"Generate personalized content for segment: {segment.get('name')}."
                content_result = await self.octotools.execute(
                    query=content_query,
                    toolset=["Email_Content_Generator"],
                    context={"segment": segment, **workflow_data},
                    max_steps=OCTOTOOLS_CONFIG["model"]["max_steps"]
                )

                # Extract content from the result
                personalized_content[segment.get("name")] = content_result.final_answer

        return {
            "status": "success",
            "analysis": analysis,
            "segments": segments,
            "personalized_content": personalized_content,
            "steps": [
                {"name": "analysis", "tools_used": analysis_result.tools_used},
                {"name": "segmentation", "tools_used": segmentation_result.tools_used}
            ]
        }

    async def _multi_platform_campaign_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the multi-platform campaign workflow.

        This workflow:
        1. Integrates with multiple platforms
        2. Creates a unified campaign across platforms
        3. Synchronizes data between platforms

        Args:
            workflow_data: Data for the workflow

        Returns:
            Dictionary containing workflow results
        """
        logger.info("Starting multi-platform campaign workflow")

        platforms = workflow_data.get("platforms", [])
        if not platforms:
            raise ValueError("No platforms specified for multi-platform campaign")

        # Step 1: Integrate with each platform
        platform_results = {}
        for platform in platforms:
            integration_query = f"Integrate with {platform}."
            integration_result = await self.octotools.execute(
                query=integration_query,
                toolset=["Platform_Integration_Tool"],
                context={"platform": platform, **workflow_data},
                max_steps=OCTOTOOLS_CONFIG["model"]["max_steps"]
            )

            # Extract integration info from the result
            platform_results[platform] = integration_result.final_answer

        # Step 2: Create a unified campaign
        campaign_query = "Create a unified campaign across all integrated platforms."
        campaign_result = await self.octotools.execute(
            query=campaign_query,
            toolset=["Email_Content_Generator", "Platform_Integration_Tool"],
            context={"platform_results": platform_results, **workflow_data},
            max_steps=OCTOTOOLS_CONFIG["model"]["max_steps"]
        )

        # Extract campaign info from the result
        campaign_info = campaign_result.final_answer

        # Step 3: Synchronize data between platforms if needed
        if workflow_data.get("sync_data", True):
            sync_query = "Synchronize data between all integrated platforms."
            sync_result = await self.octotools.execute(
                query=sync_query,
                toolset=["Platform_Integration_Tool"],
                context={
                    "platform_results": platform_results,
                    "campaign_info": campaign_info,
                    **workflow_data
                },
                max_steps=OCTOTOOLS_CONFIG["model"]["max_steps"]
            )

            # Extract sync info from the result
            sync_info = sync_result.final_answer

            return {
                "status": "success",
                "campaign_id": campaign_info.get("campaign_id", ""),
                "platform_results": platform_results,
                "campaign_info": campaign_info,
                "sync_info": sync_info,
                "steps": [
                    {"name": "platform_integration", "platforms": list(platform_results.keys())},
                    {"name": "campaign_creation", "tools_used": campaign_result.tools_used},
                    {"name": "data_synchronization", "tools_used": sync_result.tools_used}
                ]
            }

        return {
            "status": "success",
            "campaign_id": campaign_info.get("campaign_id", ""),
            "platform_results": platform_results,
            "campaign_info": campaign_info,
            "steps": [
                {"name": "platform_integration", "platforms": list(platform_results.keys())},
                {"name": "campaign_creation", "tools_used": campaign_result.tools_used}
            ]
        }
