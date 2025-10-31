"""
OPA Client for RBAC and A2A authorization
Integrates with Open Policy Agent for zero-trust policy enforcement
"""

import logging
import re
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

_PII_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("email", re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)),
    ("phone", re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("credit_card", re.compile(r"\b(?:\d[ -]?){13,19}\b")),
    ("ip", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
)

_SENSITIVE_CONTENT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("sql_injection", re.compile(r"(?i)(?:union\s+select|drop\s+table|or\s+1=1)")),
    ("shell_destruction", re.compile(r"rm\s+-rf")),
    ("credential_leak", re.compile(r"(?i)aws[_-]?secret|api[_-]?key|password")),
)

_URL_PATTERN = re.compile(
    r'https?://(?:[a-zA-Z0-9-]+\.)*([a-zA-Z0-9-]+\.[a-zA-Z]{2,})',
    re.IGNORECASE
)


def _dict_path(parent: str, key: Any) -> str:
    key_str = str(key)
    return f"$.{key_str}" if parent == "$" else f"{parent}.{key_str}"


def _list_path(parent: str, index: int) -> str:
    return f"{parent}[{index}]"


def _normalize_card_number(raw: str) -> str:
    return "".join(ch for ch in raw if ch.isdigit())


def _passes_luhn(number: str) -> bool:
    """Validate credit card numbers using the Luhn checksum."""
    if len(number) < 13 or len(number) > 19:
        return False
    total = 0
    reverse_digits = number[::-1]
    for idx, digit_char in enumerate(reverse_digits):
        digit = ord(digit_char) - 48
        if digit < 0 or digit > 9:
            return False
        if idx % 2 == 1:
            doubled = digit * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += digit
    return total % 10 == 0


def _redact_text(value: str) -> tuple[str, List[Dict[str, Any]]]:
    matches: List[Dict[str, Any]] = []
    redacted = value

    for label, pattern in _PII_PATTERNS:
        def _replacement(match: re.Match) -> str:  # type: ignore[type-arg]
            matched_text = match.group(0)
            if label == "credit_card":
                normalized = _normalize_card_number(matched_text)
                if not normalized or not _passes_luhn(normalized):
                    return matched_text
            matches.append({"type": label, "chars": len(matched_text)})
            return f"[REDACTED:{label.upper()}]"

        redacted = pattern.sub(_replacement, redacted)

    return redacted, matches


def _redact_structure(
    value: Any,
    path: str,
    matches: List[Dict[str, Any]],
    source: str,
) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        redacted_dict: Dict[Any, Any] = {}
        for key, sub_value in value.items():
            redacted_dict[key] = _redact_structure(
                sub_value,
                _dict_path(path, key),
                matches,
                source,
            )
        return redacted_dict
    if isinstance(value, list):
        return [
            _redact_structure(item, _list_path(path, idx), matches, source)
            for idx, item in enumerate(value)
        ]
    if isinstance(value, str):
        redacted_text, occurrences = _redact_text(value)
        for occurrence in occurrences:
            matches.append(
                {
                    "path": path,
                    "type": occurrence["type"],
                    "chars": occurrence["chars"],
                    "source": source,
                }
            )
        return redacted_text
    return value


def _scan_sensitive_terms(
    value: Any,
    path: str,
    matches: List[Dict[str, Any]],
    source: str,
) -> None:
    if value is None:
        return
    if isinstance(value, dict):
        for key, sub_value in value.items():
            _scan_sensitive_terms(sub_value, _dict_path(path, key), matches, source)
        return
    if isinstance(value, list):
        for idx, item in enumerate(value):
            _scan_sensitive_terms(item, _list_path(path, idx), matches, source)
        return
    if isinstance(value, str):
        for label, pattern in _SENSITIVE_CONTENT_PATTERNS:
            if pattern.search(value):
                matches.append(
                    {
                        "path": path,
                        "type": label,
                        "source": source,
                    }
                )


def enforce_obligations(
    obligations: Dict[str, Any],
    *,
    input_data: Optional[Any] = None,
    output_data: Optional[Any] = None,
    metadata: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Apply policy obligations to invocation artifacts and return sanitized copies.
    """

    sanitized_input = input_data
    sanitized_output = output_data
    sanitized_metadata = metadata
    applied: Dict[str, Any] = {}

    if not obligations:
        return {
            "input_data": sanitized_input,
            "output_data": sanitized_output,
            "metadata": sanitized_metadata,
            "applied": applied,
        }

    if obligations.get("pii_redaction"):
        logger.info("Applying PII redaction obligation")
        pii_matches: List[Dict[str, Any]] = []
        if input_data is not None:
            sanitized_input = _redact_structure(input_data, "$", pii_matches, "input")
        if output_data is not None:
            sanitized_output = _redact_structure(output_data, "$", pii_matches, "output")
        if metadata is not None:
            sanitized_metadata = _redact_structure(metadata, "$", pii_matches, "metadata")
        applied["pii_redaction"] = {
            "total_matches": len(pii_matches),
            "matches": pii_matches,
        }

    if obligations.get("content_filter"):
        logger.info("Applying content filter obligation")
        flagged_terms: List[Dict[str, Any]] = []
        _scan_sensitive_terms(sanitized_input, "$", flagged_terms, "input")
        _scan_sensitive_terms(sanitized_output, "$", flagged_terms, "output")
        _scan_sensitive_terms(sanitized_metadata, "$", flagged_terms, "metadata")
        applied["content_filter"] = {"flagged": flagged_terms}
        if flagged_terms:
            if sanitized_metadata is None or not isinstance(sanitized_metadata, dict):
                sanitized_metadata = {}
            policy_alerts = sanitized_metadata.setdefault("policy_alerts", {})
            policy_alerts["content_filter"] = {"flagged": flagged_terms}

    rate_limit_obligation = obligations.get("rate_limit")
    if isinstance(rate_limit_obligation, dict):
        applied["rate_limit"] = rate_limit_obligation

    if obligations.get("audit_log"):
        applied["audit_log"] = True

    # Domain allowlist enforcement
    domain_allowlist = obligations.get("domain_allowlist")
    if domain_allowlist and isinstance(domain_allowlist, list):
        logger.info(f"Applying domain allowlist: {domain_allowlist}")
        blocked_domains: List[Dict[str, Any]] = []
        
        def _check_domains(value: Any, path: str, source: str) -> Any:
            if isinstance(value, str):
                matches = _URL_PATTERN.findall(value)
                for domain in matches:
                    normalized_domain = domain.lower()
                    if not any(
                        normalized_domain == allowed.lower() or 
                        normalized_domain.endswith(f".{allowed.lower()}")
                        for allowed in domain_allowlist
                    ):
                        blocked_domains.append({
                            "domain": normalized_domain,
                            "path": path,
                            "source": source,
                        })
            elif isinstance(value, dict):
                return {k: _check_domains(v, f"{path}.{k}", source) for k, v in value.items()}
            elif isinstance(value, list):
                return [_check_domains(item, f"{path}[{idx}]", source) for idx, item in enumerate(value)]
            return value
        
        if sanitized_input is not None:
            _check_domains(sanitized_input, "$", "input")
        if sanitized_output is not None:
            _check_domains(sanitized_output, "$", "output")
        if sanitized_metadata is not None:
            _check_domains(sanitized_metadata, "$", "metadata")
        
        applied["domain_allowlist"] = {
            "allowed": domain_allowlist,
            "blocked_count": len(blocked_domains),
            "blocked": blocked_domains,
        }
        
        if blocked_domains:
            if sanitized_metadata is None or not isinstance(sanitized_metadata, dict):
                sanitized_metadata = {}
            policy_alerts = sanitized_metadata.setdefault("policy_alerts", {})
            policy_alerts["domain_allowlist"] = {
                "blocked": blocked_domains,
                "message": f"Blocked {len(blocked_domains)} external domain(s) not in allowlist"
            }

    return {
        "input_data": sanitized_input,
        "output_data": sanitized_output,
        "metadata": sanitized_metadata,
        "applied": applied,
    }


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
        *,
        input_data: Optional[Any] = None,
        output_data: Optional[Any] = None,
        metadata: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Apply policy obligations to request/response/metadata payloads.

        Returns sanitized copies of the input/output/metadata artefacts along with
        a summary of which obligations were enforced.
        """

        return enforce_obligations(
            obligations or {},
            input_data=input_data,
            output_data=output_data,
            metadata=metadata,
        )
    
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
