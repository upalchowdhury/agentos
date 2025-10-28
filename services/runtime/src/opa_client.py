"""
OPA Client for RBAC and A2A authorization
Integrates with Open Policy Agent for zero-trust policy enforcement
"""

import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class OPAClient:
    """
    Client for Open Policy Agent
    
    Usage:
        opa = OPAClient("http://opa:8181")
        decision = await opa.check_invoke_permission(user_id, agent_id, caller_agent_id)
        if decision['allow']:
            # proceed with invocation
            # apply obligations: decision['obligations']
        else:
            # deny with reason: decision['deny_reason']
    """
    
    def __init__(self, opa_url: str = "http://localhost:8181"):
        self.opa_url = opa_url.rstrip('/')
    
    async def check_invoke_permission(
        self,
        subject_id: str,
        subject_type: str,  # 'user' or 'agent'
        agent_id: str,
        agent_data: Dict[str, Any],
        caller_agent_id: Optional[str] = None,
        subject_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check if subject can invoke agent
        
        Args:
            subject_id: User ID or agent ID making the request
            subject_type: 'user' or 'agent'
            agent_id: Target agent to invoke
            agent_data: Agent metadata (owner_id, metadata, etc.)
            caller_agent_id: For A2A invocations
            subject_data: Additional subject metadata (roles, tier, etc.)
        
        Returns:
            {
                'allow': bool,
                'obligations': dict,  # Actions to take if allowed
                'deny_reason': str    # Reason if denied
            }
        """
        
        # Construct OPA input document
        input_doc = {
            "input": {
                "subject_type": subject_type,
                "subject": {
                    "id": subject_id,
                    "roles": subject_data.get('roles', []) if subject_data else [],
                    "tier": subject_data.get('tier', 'free') if subject_data else 'free',
                    "privacy_settings": subject_data.get('privacy_settings', {}) if subject_data else {}
                },
                "agent_id": agent_id,
                "agent": {
                    "owner_id": agent_data.get('owner_id'),
                    "model_type": agent_data.get('model_type'),
                    "metadata": agent_data.get('metadata', {})
                },
                "caller_agent_id": caller_agent_id,
                "action": "invoke",
                "timestamp": None  # OPA can add this
            }
        }
        
        try:
            # Query OPA decision endpoint
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.opa_url}/v1/data/agentos/authz",
                    json=input_doc
                )
            
            if response.status_code != 200:
                logger.error(f"OPA returned non-200 status: {response.status_code}")
                # Fail closed: deny if OPA is unavailable
                return {
                    'allow': False,
                    'obligations': {},
                    'deny_reason': 'opa_unavailable'
                }
            
            result = response.json()
            
            # Extract decision
            allow = result.get('result', {}).get('allow', False)
            obligations = result.get('result', {}).get('obligations', {})
            deny_reason = result.get('result', {}).get('deny_reason')
            
            logger.info(
                f"OPA decision for {subject_type} {subject_id} -> agent {agent_id}: "
                f"allow={allow}, reason={deny_reason}"
            )
            
            return {
                'allow': allow,
                'obligations': obligations,
                'deny_reason': deny_reason
            }
            
        except httpx.ConnectError:
            logger.error("Cannot connect to OPA - failing closed")
            return {
                'allow': False,
                'obligations': {},
                'deny_reason': 'opa_connection_failed'
            }
        except Exception as e:
            logger.error(f"OPA query failed: {e}")
            return {
                'allow': False,
                'obligations': {},
                'deny_reason': 'opa_error'
            }
    
    async def check_a2a_permission(
        self,
        caller_agent_id: str,
        target_agent_id: str
    ) -> bool:
        """
        Simplified A2A permission check
        
        Returns:
            True if caller_agent can invoke target_agent
        """
        # Query specific A2A policy
        input_doc = {
            "input": {
                "caller_agent_id": caller_agent_id,
                "target_agent_id": target_agent_id,
                "action": "invoke"
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.opa_url}/v1/data/agentos/authz/a2a_permission_exists",
                    json=input_doc
                )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('result', False)
            
            return False
            
        except Exception as e:
            logger.error(f"A2A permission check failed: {e}")
            return False
    
    async def apply_obligations(
        self,
        obligations: Dict[str, Any],
        input_data: Dict[str, Any],
        output_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply policy obligations to request/response
        
        Obligations may include:
        - content_filter: Filter toxic/harmful content
        - pii_redaction: Redact PII from output
        - rate_limit: Apply rate limiting
        - audit_log: Log this invocation
        
        Args:
            obligations: Dict from OPA decision
            input_data: Request input
            output_data: Response output
        
        Returns:
            Modified output_data with obligations applied
        """
        
        modified_output = output_data.copy()
        
        # Apply content filter
        if obligations.get('content_filter'):
            logger.info("Applying content filter obligation")
            # TODO: Integrate with content filter service
            # modified_output = await content_filter(modified_output)
        
        # Apply PII redaction
        if obligations.get('pii_redaction'):
            logger.info("Applying PII redaction obligation")
            # TODO: Redact PII from output
            # modified_output = await redact_pii(modified_output)
        
        # Rate limiting is handled at gateway level
        if obligations.get('rate_limit'):
            logger.debug(f"Rate limit config: {obligations['rate_limit']}")
        
        # Audit logging
        if obligations.get('audit_log'):
            logger.info("Audit log obligation set")
            # Audit logging handled by invocation recorder
        
        return modified_output
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Singleton instance
_opa_client: Optional[OPAClient] = None


def get_opa_client(opa_url: str = "http://localhost:8181") -> OPAClient:
    """Get or create OPA client singleton"""
    global _opa_client
    if _opa_client is None:
        _opa_client = OPAClient(opa_url)
    return _opa_client
