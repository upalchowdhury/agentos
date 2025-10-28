"""
External Agent Proxy for Model B
Handles proxying requests to external agent endpoints (OpenAI, Agentforce, MCP, custom HTTP)
"""

import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class ExternalAgentProxy:
    """
    Proxy for external agent endpoints (Model B)
    
    Supports:
    - OpenAI Assistants API
    - Anthropic Claude
    - Google Gemini
    - Salesforce Agentforce
    - MCP agents
    - Custom HTTP endpoints
    """
    
    def __init__(
        self,
        endpoint_url: str,
        auth_config: Dict[str, Any],
        timeout: int = 30,
        rate_limit: Optional[Dict[str, Any]] = None
    ):
        self.endpoint_url = endpoint_url
        self.auth_config = auth_config
        self.timeout = timeout
        self.rate_limit = rate_limit or {"rps": 10, "burst": 20}
    
    async def invoke(
        self,
        input_data: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Proxy invocation to external agent
        
        Args:
            input_data: Input payload to send
            timeout: Override default timeout
        
        Returns:
            {
                'result': dict,  # Agent response
                'metadata': dict,  # Provider info, tokens used, etc.
                'cost': float  # Estimated cost if available
            }
        """
        
        timeout = timeout or self.timeout
        
        try:
            # Build headers with auth
            headers = self._build_auth_headers()
            headers['Content-Type'] = 'application/json'
            
            # Make request to external endpoint
            logger.info(f"Proxying request to {self.endpoint_url}")
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    self.endpoint_url,
                    json=input_data,
                    headers=headers,
                    timeout=timeout
                )
            
            if response.status_code != 200:
                logger.error(f"External agent returned {response.status_code}: {response.text}")
                raise Exception(f"External agent error: {response.status_code}")
            
            result_data = response.json()
            
            # Extract cost info if available (provider-specific)
            cost = self._extract_cost(result_data, headers)
            
            return {
                'result': result_data,
                'metadata': {
                    'endpoint': self.endpoint_url,
                    'provider': self._detect_provider(),
                    'response_time_ms': int(response.elapsed.total_seconds() * 1000)
                },
                'cost': cost
            }
            
        except httpx.TimeoutException:
            logger.error(f"Timeout calling external agent {self.endpoint_url}")
            raise Exception("External agent timeout")
        
        except httpx.ConnectError:
            logger.error(f"Connection failed to {self.endpoint_url}")
            raise Exception("External agent unreachable")
        
        except Exception as e:
            logger.error(f"External agent invocation failed: {e}")
            raise
    
    async def health_check(self, health_path: str = "/health") -> bool:
        """
        Check if external endpoint is healthy
        
        Args:
            health_path: Health check endpoint path
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            health_url = f"{self.endpoint_url.rstrip('/')}{health_path}"
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    health_url,
                    headers=self._build_auth_headers(),
                )
            
            is_healthy = response.status_code == 200
            
            logger.info(f"Health check for {self.endpoint_url}: {'✓' if is_healthy else '✗'}")
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"Health check failed for {self.endpoint_url}: {e}")
            return False
    
    def _build_auth_headers(self) -> Dict[str, str]:
        """Build authentication headers based on auth config"""
        
        headers = {}
        auth_type = self.auth_config.get('type', 'none')
        
        if auth_type == 'bearer':
            token = self.auth_config.get('value')
            if token:
                headers['Authorization'] = f'Bearer {token}'
        
        elif auth_type == 'header':
            header_name = self.auth_config.get('header_name')
            header_value = self.auth_config.get('value')
            if header_name and header_value:
                headers[header_name] = header_value
        
        return headers
    
    def _detect_provider(self) -> str:
        """Detect provider from endpoint URL"""
        
        url_lower = self.endpoint_url.lower()
        
        if 'openai' in url_lower or 'api.openai.com' in url_lower:
            return 'openai'
        elif 'anthropic' in url_lower or 'claude' in url_lower:
            return 'anthropic'
        elif 'google' in url_lower or 'gemini' in url_lower:
            return 'google'
        elif 'salesforce' in url_lower or 'agentforce' in url_lower:
            return 'salesforce'
        else:
            return 'custom'
    
    def _extract_cost(self, response_data: Dict[str, Any], headers: Dict[str, str]) -> float:
        """
        Extract cost from response (provider-specific)
        
        Different providers return token usage differently:
        - OpenAI: response.usage.total_tokens
        - Anthropic: response.usage.input_tokens + output_tokens
        - Google: response.usage_metadata.total_token_count
        """
        
        provider = self._detect_provider()
        cost = 0.0
        
        try:
            if provider == 'openai':
                usage = response_data.get('usage', {})
                total_tokens = usage.get('total_tokens', 0)
                # Rough estimate: $0.00003/token for GPT-4
                cost = total_tokens * 0.00003
            
            elif provider == 'anthropic':
                usage = response_data.get('usage', {})
                input_tokens = usage.get('input_tokens', 0)
                output_tokens = usage.get('output_tokens', 0)
                # Claude pricing: input $0.000015, output $0.000075
                cost = (input_tokens * 0.000015) + (output_tokens * 0.000075)
            
            elif provider == 'google':
                usage = response_data.get('usage_metadata', {})
                total_tokens = usage.get('total_token_count', 0)
                # Gemini pricing: $0.0000005/token
                cost = total_tokens * 0.0000005
            
            else:
                # Custom providers: default flat rate
                cost = 0.01
        
        except Exception as e:
            logger.warning(f"Failed to extract cost: {e}")
            cost = 0.01  # Default fallback
        
        return cost
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


class OpenAIAssistantProxy(ExternalAgentProxy):
    """
    Specialized proxy for OpenAI Assistants API
    
    Usage:
        proxy = OpenAIAssistantProxy(assistant_id="asst_123", api_key="sk-...")
        result = await proxy.invoke({"message": "Hello"})
    """
    
    def __init__(self, assistant_id: str, api_key: str):
        super().__init__(
            endpoint_url="https://api.openai.com/v1/assistants",
            auth_config={"type": "bearer", "value": api_key}
        )
        self.assistant_id = assistant_id
    
    async def invoke(self, input_data: Dict[str, Any], timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Invoke OpenAI Assistant
        
        Flow:
        1. Create thread
        2. Add message
        3. Run assistant
        4. Poll for completion
        5. Get messages
        """
        
        try:
            # Create thread
            thread_response = await self.client.post(
                f"{self.endpoint_url}/threads",
                headers=self._build_auth_headers(),
                json={}
            )
            thread_id = thread_response.json()['id']
            
            # Add message
            await self.client.post(
                f"{self.endpoint_url}/threads/{thread_id}/messages",
                headers=self._build_auth_headers(),
                json={
                    "role": "user",
                    "content": input_data.get('message', str(input_data))
                }
            )
            
            # Run assistant
            run_response = await self.client.post(
                f"{self.endpoint_url}/threads/{thread_id}/runs",
                headers=self._build_auth_headers(),
                json={"assistant_id": self.assistant_id}
            )
            run_id = run_response.json()['id']
            
            # Poll for completion (simplified - should use streaming in production)
            import asyncio
            max_polls = 30
            for _ in range(max_polls):
                run_status = await self.client.get(
                    f"{self.endpoint_url}/threads/{thread_id}/runs/{run_id}",
                    headers=self._build_auth_headers()
                )
                status = run_status.json()['status']
                
                if status == 'completed':
                    break
                elif status in ['failed', 'cancelled', 'expired']:
                    raise Exception(f"Run {status}")
                
                await asyncio.sleep(1)
            
            # Get messages
            messages_response = await self.client.get(
                f"{self.endpoint_url}/threads/{thread_id}/messages",
                headers=self._build_auth_headers()
            )
            messages = messages_response.json()['data']
            
            # Extract assistant's response
            assistant_message = next(
                (m for m in messages if m['role'] == 'assistant'),
                None
            )
            
            if not assistant_message:
                raise Exception("No assistant response found")
            
            result = {
                'response': assistant_message['content'][0]['text']['value'],
                'thread_id': thread_id,
                'run_id': run_id
            }
            
            return {
                'result': result,
                'metadata': {
                    'provider': 'openai',
                    'assistant_id': self.assistant_id
                },
                'cost': 0.01  # Estimate
            }
            
        except Exception as e:
            logger.error(f"OpenAI Assistant invocation failed: {e}")
            raise


class MCPAgentProxy(ExternalAgentProxy):
    """
    Specialized proxy for MCP (Model Context Protocol) agents
    
    MCP agents expose tools via a standard protocol
    """
    
    def __init__(self, endpoint_url: str, auth_config: Dict[str, Any]):
        super().__init__(endpoint_url, auth_config)
    
    async def list_tools(self) -> list:
        """List available tools from MCP agent"""
        
        response = await self.client.get(
            f"{self.endpoint_url}/tools",
            headers=self._build_auth_headers()
        )
        
        return response.json().get('tools', [])
    
    async def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke specific tool"""
        
        response = await self.client.post(
            f"{self.endpoint_url}/tools/{tool_name}",
            headers=self._build_auth_headers(),
            json=arguments
        )
        
        return response.json()
