"""
Retell SDK service for managing voice agents
"""

import os
import json
import logging
import httpx
from typing import Optional, Dict, Any
from retell import Retell

logger = logging.getLogger(__name__)


class RetellService:
    """Service for interacting with Retell API"""
    
    def __init__(self):
        """Initialize Retell HTTP client"""
        self.api_key = os.getenv("RETELL_API_KEY")
        if not self.api_key:
            raise ValueError("RETELL_API_KEY environment variable is required")
        
        self.base_url = "https://api.retellai.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        logger.info("✅ Retell HTTP client initialized")
    
    def create_conversation_flow(self, conversation_flow_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a conversation flow on Retell
        
        Args:
            conversation_flow_data: The conversationFlow section from HelpPetAI.json
            
        Returns:
            Conversation flow ID if successful, None if failed
        """
        try:
            logger.info(f"🔄 Creating Retell conversation flow...")
            
            # Extract the required parameters for conversation flow creation
            flow_params = {
                "nodes": conversation_flow_data.get("nodes", []),
                "start_speaker": conversation_flow_data.get("start_speaker", "agent"),
            }
            
            # Add model choice if present
            if "model_choice" in conversation_flow_data:
                flow_params["model_choice"] = conversation_flow_data["model_choice"]
            
            # Add global prompt if present
            if "global_prompt" in conversation_flow_data:
                flow_params["global_prompt"] = conversation_flow_data["global_prompt"]
            
            # Add tools if present
            if "tools" in conversation_flow_data:
                flow_params["tools"] = conversation_flow_data["tools"]
            
            # Add start node ID if present
            if "start_node_id" in conversation_flow_data:
                flow_params["start_node_id"] = conversation_flow_data["start_node_id"]
            
            # Add kb_config if present
            if "kb_config" in conversation_flow_data:
                flow_params["kb_config"] = conversation_flow_data["kb_config"]
            
            logger.info(f"🔧 Creating conversation flow with parameters: {list(flow_params.keys())}")
            logger.info(f"📊 Flow contains {len(flow_params.get('nodes', []))} nodes")
            
            # Create the conversation flow using Retell SDK
            response = self.client.conversation_flow.create(**flow_params)
            
            conversation_flow_id = response.conversation_flow_id
            logger.info(f"✅ Successfully created conversation flow: {conversation_flow_id}")
            return conversation_flow_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create conversation flow: {e}")
            logger.error(f"🔍 Flow data keys: {list(conversation_flow_data.keys())}")
            return None
    
    async def create_practice_conversation_flow(self, practice_id: str, timezone: str) -> Optional[str]:
        """
        Create a practice-specific conversation flow with custom global prompt
        
        Args:
            practice_id: UUID of the veterinary practice
            timezone: Timezone for the practice
            
        Returns:
            Conversation flow ID if successful, None if failed
        """
        try:
            logger.info(f"🔄 Creating practice-specific conversation flow for practice {practice_id}")
            
            # Create the practice-specific global prompt
            global_prompt = f"""## Objective
You are an AI agent LaShonda working for a veterinarian. You are to be kind and helpful.

- if someone has an emergency they aren't talking about a person. They are talking about a pet. Do not suggest to call 911

Current time is {{{{current_time}}}}
{{{{practice_id}}}} = "{practice_id}"
{{{{timezone}}}} = "{timezone}"

You are helping customers of this specific veterinary practice. Use the practice_id to look up practice-specific information when needed."""

            # Get the base conversation flow structure from the working flow
            client = Retell(api_key=self.api_key)
            
            # Fetch the base conversation flow to copy its structure
            base_flow_id = "conversation_flow_90c767c52a14"
            base_flow = client.conversation_flow.retrieve(conversation_flow_id=base_flow_id)
            
            # Create new conversation flow with practice-specific global prompt
            flow_params = {
                "nodes": base_flow.nodes,
                "start_speaker": base_flow.start_speaker,
                "model_choice": base_flow.model_choice,
                "global_prompt": global_prompt,  # This is the key change!
                "tools": getattr(base_flow, 'tools', []),
                "start_node_id": getattr(base_flow, 'start_node_id', None),
                "kb_config": getattr(base_flow, 'kb_config', None)
            }
            
            # Remove None values
            flow_params = {k: v for k, v in flow_params.items() if v is not None}
            
            logger.info(f"🔧 Creating conversation flow with practice-specific global prompt")
            
            # Create the new conversation flow
            response = client.conversation_flow.create(**flow_params)
            conversation_flow_id = response.conversation_flow_id
            
            logger.info(f"✅ Successfully created practice-specific conversation flow: {conversation_flow_id}")
            return conversation_flow_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create practice-specific conversation flow: {e}")
            return None
    
    async def create_agent(self, agent_config: Dict[str, Any], practice_id: str = None, timezone: str = "US/Pacific") -> Optional[str]:
        """
        Create a new agent on Retell using the conversation flow approach
        
        Args:
            agent_config: Agent configuration dictionary
            practice_id: UUID of the veterinary practice (for global prompt)
            timezone: Timezone for the practice (for global prompt)
            
        Returns:
            Agent ID if successful, None if failed
        """
        try:
            logger.info(f"🤖 Creating Retell agent: {agent_config.get('agent_name', 'Unknown')}")
            
            # Create practice-specific conversation flow with custom global prompt
            conversation_flow_id = await self.create_practice_conversation_flow(practice_id, timezone)
            if not conversation_flow_id:
                logger.error("❌ Failed to create practice-specific conversation flow")
                return None
            
            # Build agent parameters (using same format as successful curl)
            agent_params = {
                "agent_name": agent_config["agent_name"],  # Practice-specific name
                "voice_id": agent_config.get("voice_id", "11labs-Adrian"),
                "response_engine": {
                    "type": "conversation-flow",
                    "conversation_flow_id": conversation_flow_id
                }
            }
            
            # Add optional parameters
            if agent_config.get("language"):
                agent_params["language"] = agent_config["language"]
            if agent_config.get("webhook_url"):
                agent_params["webhook_url"] = agent_config["webhook_url"]
            if agent_config.get("max_call_duration_ms"):
                agent_params["max_call_duration_ms"] = agent_config["max_call_duration_ms"]
            if agent_config.get("interruption_sensitivity") is not None:
                agent_params["interruption_sensitivity"] = agent_config["interruption_sensitivity"]
            
            logger.info(f"🔧 Creating agent with parameters: {list(agent_params.keys())}")
            
            # Create agent using direct HTTP call (working approach from curl)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/create-agent",
                    headers=self.headers,
                    json=agent_params
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    agent_id = data.get("agent_id")
                    logger.info(f"✅ Successfully created Retell agent: {agent_id}")
                    logger.info(f"🔗 Agent uses conversation flow: {conversation_flow_id}")
                    return agent_id
                else:
                    logger.error(f"❌ Agent creation failed with status {response.status_code}: {response.text}")
                    return None
            
        except Exception as e:
            logger.error(f"❌ Failed to create Retell agent: {e}")
            return None
    
    def update_agent(self, agent_id: str, agent_config: Dict[str, Any]) -> bool:
        """
        Update an existing agent on Retell
        
        Args:
            agent_id: The agent ID to update
            agent_config: Agent configuration dictionary (full HelpPetAI.json)
            
        Returns:
            True if successful, False if failed
        """
        try:
            logger.info(f"🤖 Updating Retell agent: {agent_id}")
            
            # Start with basic update parameters
            update_params = {"agent_id": agent_id}
            
            # Add core parameters that are most likely to be supported
            if "agent_name" in agent_config:
                update_params["agent_name"] = agent_config["agent_name"]
            if "voice_id" in agent_config:
                update_params["voice_id"] = agent_config["voice_id"]
            if "language" in agent_config:
                update_params["language"] = agent_config["language"]
            if "webhook_url" in agent_config:
                update_params["webhook_url"] = agent_config["webhook_url"]
            if "response_engine" in agent_config:
                update_params["response_engine"] = agent_config["response_engine"]
            if "conversationFlow" in agent_config:
                update_params["conversation_flow"] = agent_config["conversationFlow"]
            
            logger.info(f"🔧 Attempting to update agent with core parameters: {list(update_params.keys())}")
            
            # Try to update with core parameters first
            try:
                self.client.agent.update(**update_params)
                logger.info(f"✅ Successfully updated agent with core parameters")
            except Exception as core_error:
                logger.warning(f"⚠️ Core parameter update failed: {core_error}")
                # Try with minimal parameters
                minimal_update = {
                    "agent_id": agent_id,
                    "agent_name": agent_config.get("agent_name")
                }
                self.client.agent.update(**minimal_update)
                logger.info(f"✅ Successfully updated agent with minimal parameters")
            
            # Try to update additional parameters one by one
            additional_params = {
                "max_call_duration_ms": agent_config.get("max_call_duration_ms"),
                "interruption_sensitivity": agent_config.get("interruption_sensitivity"),
                "opt_out_sensitive_data_storage": agent_config.get("opt_out_sensitive_data_storage"),
                "data_storage_setting": agent_config.get("data_storage_setting"),
                "post_call_analysis_model": agent_config.get("post_call_analysis_model"),
            }
            
            for param_name, param_value in additional_params.items():
                if param_value is not None:
                    try:
                        single_update = {"agent_id": agent_id, param_name: param_value}
                        self.client.agent.update(**single_update)
                        logger.info(f"✅ Successfully updated {param_name}")
                    except Exception as param_error:
                        logger.warning(f"⚠️ Could not update {param_name}: {param_error}")
            
            logger.info(f"✅ Agent update process completed for: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update Retell agent {agent_id}: {e}")
            logger.error(f"🔍 Update config keys: {list(agent_config.keys())}")
            return False
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent details from Retell
        
        Args:
            agent_id: The agent ID to retrieve
            
        Returns:
            Agent details if successful, None if failed
        """
        try:
            logger.info(f"🔍 Retrieving Retell agent: {agent_id}")
            
            response = self.client.agent.retrieve(agent_id=agent_id)
            
            logger.info(f"✅ Successfully retrieved Retell agent: {agent_id}")
            return response.__dict__
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve Retell agent {agent_id}: {e}")
            return None
    
    # NOTE: We intentionally do NOT implement a delete_agent method here.
    # Deleting agents from Retell is dangerous and irreversible.
    # Instead, use soft deletion by setting is_active=False in the voice_config table.


def load_helppetai_config(practice_id: str, timezone: str) -> Dict[str, Any]:
    """
    Load HelpPetAI configuration from Retell conversation flow with practice-specific values
    
    Args:
        practice_id: UUID of the veterinary practice
        timezone: Timezone for the practice
    
    Returns:
        Configuration dictionary based on the existing conversation flow with custom global_prompt
    """
    try:
        # Use the existing conversation flow ID from HelpPetAI
        conversation_flow_id = "conversation_flow_40876625b4b2"
        
        # Initialize Retell client
        client = Retell(api_key=os.getenv("RETELL_API_KEY"))
        
        # Fetch the conversation flow from Retell
        logger.info(f"🔄 Fetching conversation flow from Retell: {conversation_flow_id}")
        conversation_flow = client.conversation_flow.retrieve(conversation_flow_id=conversation_flow_id)
        prompt = f"""
## Objective
You are an AI agent LaShonda working for a veterinarian. You are to be kind and helpful.

- if someone has an emergency they aren't talking about a person. They are talking about a pet. Do not suggest to call 911


Current time is {{{{current_time}}}}
{{{{practice_id}}}}= "{practice_id}"
{{{{timezone}}}} = "{timezone}"
        """
        # Create a configuration structure similar to HelpPetAI.json
        config = {
            "agent_name": "HelpPetAI",  # This will be overridden with practice name
            "voice_id": "11labs-adrian",
            "language": "en-US",
            "response_engine": {
                "type": "conversation-flow",
                "conversation_flow_id": conversation_flow_id,
                "global_prompt": prompt
            },
            "conversationFlow": {
                "conversation_flow_id": conversation_flow.conversation_flow_id,
                "version": conversation_flow.version,
                "global_prompt": conversation_flow.global_prompt,
                "nodes": conversation_flow.nodes,
                "start_speaker": conversation_flow.start_speaker,
                "model_choice": conversation_flow.model_choice,
                "tools": getattr(conversation_flow, 'tools', []),
                "start_node_id": getattr(conversation_flow, 'start_node_id', None),
                "kb_config": getattr(conversation_flow, 'kb_config', None)
            },
            "webhook_url": "https://api.helppet.ai/api/v1/retell/webhook",
            "max_call_duration_ms": 900000,
            "interruption_sensitivity": 1
        }
        
        logger.info(f"✅ Loaded configuration from Retell conversation flow: {conversation_flow_id} (version {conversation_flow.version})")
        return config
        
    except Exception as e:
        logger.error(f"❌ Failed to load configuration from Retell: {e}")
        return {}


# Global instance
retell_service = RetellService()
