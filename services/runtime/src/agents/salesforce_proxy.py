"""
Salesforce Agentforce Proxy
Specialized proxy for Salesforce Einstein Agentforce agents
"""

import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

from .proxy import ExternalAgentProxy

logger = logging.getLogger(__name__)


class SalesforceAgentforceProxy(ExternalAgentProxy):
    """
    Specialized proxy for Salesforce Agentforce
    
    Agentforce API specifics:
    - OAuth 2.0 authentication
    - Salesforce API endpoints
    - Conversation context management
    - CRM data access
    
    Example usage:
        proxy = SalesforceAgentforceProxy(
            instance_url="https://mycompany.salesforce.com",
            agent_id="0Xx...",
            access_token="00D...!AR8..."
        )
        result = await proxy.invoke({
            "message": "What's the status of lead 12345?",
            "context": {"user_id": "005..."}
        })
    """
    
    def __init__(
        self,
        instance_url: str,
        agent_id: str,
        access_token: str,
        api_version: str = "v59.0",
        timeout: int = 30
    ):
        """
        Initialize Salesforce Agentforce proxy
        
        Args:
            instance_url: Salesforce instance URL (e.g., https://mycompany.salesforce.com)
            agent_id: Agentforce agent ID (starts with 0Xx)
            access_token: Salesforce OAuth access token
            api_version: Salesforce API version (default: v59.0)
            timeout: Request timeout in seconds
        """
        
        # Construct Agentforce endpoint
        endpoint = f"{instance_url}/services/data/{api_version}/einstein/ai-foundation/agents/{agent_id}/invoke"
        
        # Setup auth
        auth_config = {
            "type": "bearer",
            "value": access_token
        }
        
        super().__init__(
            endpoint_url=endpoint,
            auth_config=auth_config,
            timeout=timeout
        )
        
        self.instance_url = instance_url
        self.agent_id = agent_id
        self.api_version = api_version
    
    async def invoke(
        self,
        input_data: Dict[str, Any],
        timeout: Optional[int] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Invoke Salesforce Agentforce agent
        
        Args:
            input_data: Input payload with message and optional context
            timeout: Override default timeout
            conversation_id: Optional conversation ID for context continuity
        
        Returns:
            {
                'result': {
                    'message': str,  # Agent response
                    'conversation_id': str,  # For follow-ups
                    'metadata': dict  # Salesforce metadata
                },
                'metadata': dict,
                'cost': float
            }
        """
        
        timeout = timeout or self.timeout
        
        # Build Agentforce request payload
        payload = {
            "message": input_data.get("message", str(input_data)),
            "parameters": input_data.get("parameters", {}),
        }
        
        # Add conversation context if provided
        if conversation_id:
            payload["conversationId"] = conversation_id
        
        # Add user context for CRM data access
        if "user_context" in input_data:
            payload["userContext"] = input_data["user_context"]
        
        try:
            # Build headers
            headers = self._build_auth_headers()
            headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Sforce-Call-Options': 'client=AgentOS'
            })
            
            logger.info(f"Invoking Salesforce Agentforce agent {self.agent_id}")
            
            # Make request to Agentforce
            response = await self.client.post(
                self.endpoint_url,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code != 200:
                error_body = response.text
                logger.error(f"Agentforce returned {response.status_code}: {error_body}")
                
                # Parse Salesforce error
                try:
                    error_data = response.json()
                    error_msg = error_data[0].get('message', error_body) if isinstance(error_data, list) else error_body
                except:
                    error_msg = error_body
                
                raise Exception(f"Salesforce Agentforce error: {error_msg}")
            
            result_data = response.json()
            
            # Extract Agentforce response
            agent_response = {
                'message': result_data.get('message', ''),
                'conversation_id': result_data.get('conversationId'),
                'confidence': result_data.get('confidence'),
                'intent': result_data.get('detectedIntent'),
                'entities': result_data.get('entities', []),
                'actions_taken': result_data.get('actionsTaken', []),
                'salesforce_metadata': {
                    'agent_id': self.agent_id,
                    'api_version': self.api_version,
                    'response_time_ms': int(response.elapsed.total_seconds() * 1000)
                }
            }
            
            # Estimate cost (Salesforce charges per message)
            # Typical: $0.02 per message for Agentforce
            cost = 0.02
            
            return {
                'result': agent_response,
                'metadata': {
                    'provider': 'salesforce',
                    'product': 'agentforce',
                    'instance_url': self.instance_url,
                    'response_time_ms': int(response.elapsed.total_seconds() * 1000)
                },
                'cost': cost
            }
            
        except httpx.TimeoutException:
            logger.error(f"Timeout calling Salesforce Agentforce")
            raise Exception("Salesforce Agentforce timeout")
        
        except httpx.ConnectError:
            logger.error(f"Connection failed to Salesforce")
            raise Exception("Salesforce unreachable")
        
        except Exception as e:
            logger.error(f"Agentforce invocation failed: {e}")
            raise
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> list:
        """
        Retrieve conversation history from Salesforce
        
        Args:
            conversation_id: Conversation ID
            limit: Max messages to retrieve
        
        Returns:
            List of messages in the conversation
        """
        
        try:
            url = f"{self.instance_url}/services/data/{self.api_version}/einstein/ai-foundation/conversations/{conversation_id}"
            
            response = await self.client.get(
                url,
                headers=self._build_auth_headers(),
                params={"limit": limit}
            )
            
            if response.status_code == 200:
                return response.json().get('messages', [])
            else:
                logger.error(f"Failed to get conversation history: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []
    
    async def get_agent_metadata(self) -> Dict[str, Any]:
        """
        Retrieve Agentforce agent metadata
        
        Returns:
            Agent configuration and capabilities
        """
        
        try:
            url = f"{self.instance_url}/services/data/{self.api_version}/einstein/ai-foundation/agents/{self.agent_id}"
            
            response = await self.client.get(
                url,
                headers=self._build_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get agent metadata: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error retrieving agent metadata: {e}")
            return {}
    
    async def list_available_actions(self) -> list:
        """
        List actions available to this Agentforce agent
        
        Returns:
            List of action definitions
        """
        
        try:
            url = f"{self.instance_url}/services/data/{self.api_version}/einstein/ai-foundation/agents/{self.agent_id}/actions"
            
            response = await self.client.get(
                url,
                headers=self._build_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json().get('actions', [])
            else:
                logger.error(f"Failed to list actions: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error listing actions: {e}")
            return []
    
    @staticmethod
    def from_oauth(
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
        security_token: str,
        instance_url: str,
        agent_id: str
    ) -> 'SalesforceAgentforceProxy':
        """
        Create proxy using OAuth password flow
        
        Args:
            client_id: Connected app client ID
            client_secret: Connected app secret
            username: Salesforce username
            password: Salesforce password
            security_token: User security token
            instance_url: Salesforce instance URL
            agent_id: Agentforce agent ID
        
        Returns:
            Configured SalesforceAgentforceProxy
        """
        
        import asyncio
        
        async def get_token():
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{instance_url}/services/oauth2/token",
                    data={
                        'grant_type': 'password',
                        'client_id': client_id,
                        'client_secret': client_secret,
                        'username': username,
                        'password': password + security_token
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"OAuth failed: {response.text}")
                
                return response.json()['access_token']
        
        # Get access token synchronously
        access_token = asyncio.run(get_token())
        
        return SalesforceAgentforceProxy(
            instance_url=instance_url,
            agent_id=agent_id,
            access_token=access_token
        )


class SalesforceAgentBuilder:
    """
    Helper to easily create Salesforce Agentforce registrations
    """
    
    @staticmethod
    def build_registration(
        name: str,
        instance_url: str,
        agent_id: str,
        access_token: str,
        api_version: str = "v59.0"
    ) -> Dict[str, Any]:
        """
        Build Model B registration payload for Agentforce
        
        Returns:
            Ready-to-use CreateModelBRequest payload
        """
        
        endpoint_url = f"{instance_url}/services/data/{api_version}/einstein/ai-foundation/agents/{agent_id}/invoke"
        
        return {
            "name": name,
            "endpoint_url": endpoint_url,
            "auth": {
                "type": "bearer",
                "value": access_token
            },
            "rate_limit": {
                "rps": 5.0,  # Salesforce has rate limits
                "burst": 10
            },
            "health_check_path": f"/services/data/{api_version}/einstein/ai-foundation/agents/{agent_id}",
            "timeout_seconds": 30
        }
