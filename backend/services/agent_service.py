from autogen import AssistantAgent, GroupChat, GroupChatManager
from fastapi import HTTPException
from loguru import logger
from typing import List
from .langfuse_service import LangfuseLLM

def create_agent(name: str, system_message: str, user_id: int, langfuse_client=None):
    """Create a robust agent with Langfuse integration and error handling."""
    try:
        llm = LangfuseLLM(langfuse_client, user_id)
        
        return AssistantAgent(
            name=name,
            system_message=system_message,
            llm_config={
                "config_list": llm.config_list,
                "temperature": 0.7
            }
        )
    except Exception as e:
        logger.error(f"Failed to create agent {name}: {e}")
        # Return a basic agent with mock adapter as fallback
        return AssistantAgent(
            name=name,
            system_message=system_message,
            llm_config={"config_list": [{"model": "mock", "api_key": "test-api-key"}]}
        )

def create_content_agent(user_id: int, langfuse_client=None):
    return create_agent(
        "ContentAgent",
        "You are an expert in crafting compelling email content. "
        "Generate concise, engaging email subject and body in JSON format: "
        "{'subject': '...', 'body': '...'}",
        user_id,
        langfuse_client
    )

def create_design_agent(user_id: int, langfuse_client=None):
    return create_agent(
        "DesignAgent",
        "You are an expert in email design. Suggest a modern design theme based on the content provided.",
        user_id,
        langfuse_client
    )

def create_analytics_agent(user_id: int, langfuse_client=None):
    return create_agent(
        "AnalyticsAgent",
        "You are an expert in campaign analytics. Predict open rates based on historical data.",
        user_id,
        langfuse_client
    )

def create_personalization_agent(user_id: int, langfuse_client=None):
    return create_agent(
        "PersonalizationAgent",
        "You are an expert in personalization. Suggest strategies to personalize the email based on recipient data.",
        user_id,
        langfuse_client
    )

def create_delivery_agent(user_id: int, langfuse_client=None):
    return create_agent(
        "DeliveryAgent",
        "You are an expert in email delivery. Suggest the optimal time to send the email based on recipient timezone.",
        user_id,
        langfuse_client
    )

def create_governance_agent(user_id: int, langfuse_client=None):
    return create_agent(
        "GovernanceAgent",
        "You are an expert in compliance. Review the email for regulatory compliance (e.g., GDPR, CAN-SPAM).",
        user_id,
        langfuse_client
    )

def create_group_chat(user_id: int, task: str, langfuse_client=None):
    """Create a group chat with all necessary agents."""
    try:
        agents: List[AssistantAgent] = [
            create_content_agent(user_id, langfuse_client),
            create_design_agent(user_id, langfuse_client),
            create_analytics_agent(user_id, langfuse_client),
            create_personalization_agent(user_id, langfuse_client),
            create_delivery_agent(user_id, langfuse_client),
            create_governance_agent(user_id, langfuse_client)
        ]

        groupchat = GroupChat(
            agents=agents,
            messages=[],
            max_round=12,
            speaker_selection_method="round_robin",
            allow_repeat_speaker=False
        )

        groupchat.messages.append({
            "role": "system",
            "content": f"Collaborate to create an email campaign based on: {task}"
        })

        return GroupChatManager(groupchat=groupchat)
    except Exception as e:
        logger.error(f"Failed to create group chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize agent group chat") 