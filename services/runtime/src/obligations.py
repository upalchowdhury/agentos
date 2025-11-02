"""
Obligations Engine - Redaction & Allowlists
US-G2: Policy obligations enforcement
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ObligationType:
    """Types of policy obligations"""
    REDACTION = "redaction"
    ALLOWLIST_DOMAINS = "allowlist_domains"
    ALLOWLIST_TOOLS = "allowlist_tools"
    BUDGET_CAP = "budget_cap"
    RATE_LIMIT = "rate_limit"


class RedactionRule:
    """Rule for redacting sensitive data"""
    
    def __init__(self, pattern: str, replacement: str = "[REDACTED]"):
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.replacement = replacement
    
    def apply(self, text: str) -> tuple[str, bool]:
        """Apply redaction rule, return (redacted_text, was_redacted)"""
        redacted = self.pattern.sub(self.replacement, text)
        was_redacted = redacted != text
        return redacted, was_redacted


class ObligationsEngine:
    """Engine for enforcing policy obligations"""
    
    def __init__(self):
        # Default redaction rules
        self.redaction_rules = {
            "ssn": RedactionRule(r'\b\d{3}-\d{2}-\d{4}\b'),
            "credit_card": RedactionRule(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
            "email": RedactionRule(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "phone": RedactionRule(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            "api_key": RedactionRule(r'\b[A-Za-z0-9]{32,}\b', '[REDACTED_KEY]'),
            "jwt": RedactionRule(r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*', '[REDACTED_TOKEN]'),
        }
    
    def add_redaction_rule(self, rule_name: str, pattern: str, replacement: str = "[REDACTED]"):
        """Add custom redaction rule"""
        self.redaction_rules[rule_name] = RedactionRule(pattern, replacement)
        logger.info(f"Added redaction rule: {rule_name}")
    
    def redact_text(
        self,
        text: str,
        enabled_rules: Optional[List[str]] = None,
    ) -> tuple[str, List[str]]:
        """
        Redact sensitive information from text
        
        Args:
            text: Text to redact
            enabled_rules: List of rule names to apply (None = all rules)
        
        Returns:
            (redacted_text, list_of_applied_rules)
        """
        if not text:
            return text, []
        
        redacted = text
        applied_rules = []
        
        rules_to_apply = enabled_rules if enabled_rules else list(self.redaction_rules.keys())
        
        for rule_name in rules_to_apply:
            if rule_name not in self.redaction_rules:
                continue
            
            rule = self.redaction_rules[rule_name]
            redacted, was_redacted = rule.apply(redacted)
            
            if was_redacted:
                applied_rules.append(rule_name)
                logger.debug(f"Applied redaction rule: {rule_name}")
        
        return redacted, applied_rules
    
    def redact_dict(
        self,
        data: Dict[str, Any],
        enabled_rules: Optional[List[str]] = None,
        fields_to_redact: Optional[List[str]] = None,
    ) -> tuple[Dict[str, Any], List[str]]:
        """
        Redact sensitive information from dictionary
        
        Args:
            data: Dictionary to redact
            enabled_rules: Redaction rules to apply
            fields_to_redact: Specific fields to redact (None = all string fields)
        
        Returns:
            (redacted_dict, list_of_applied_rules)
        """
        redacted_data = {}
        all_applied_rules = set()
        
        for key, value in data.items():
            # Check if this field should be redacted
            should_redact = fields_to_redact is None or key in fields_to_redact
            
            if isinstance(value, str) and should_redact:
                redacted_value, applied = self.redact_text(value, enabled_rules)
                redacted_data[key] = redacted_value
                all_applied_rules.update(applied)
            
            elif isinstance(value, dict):
                redacted_value, applied = self.redact_dict(value, enabled_rules, fields_to_redact)
                redacted_data[key] = redacted_value
                all_applied_rules.update(applied)
            
            elif isinstance(value, list):
                redacted_list = []
                for item in value:
                    if isinstance(item, str) and should_redact:
                        redacted_item, applied = self.redact_text(item, enabled_rules)
                        redacted_list.append(redacted_item)
                        all_applied_rules.update(applied)
                    elif isinstance(item, dict):
                        redacted_item, applied = self.redact_dict(item, enabled_rules, fields_to_redact)
                        redacted_list.append(redacted_item)
                        all_applied_rules.update(applied)
                    else:
                        redacted_list.append(item)
                redacted_data[key] = redacted_list
            
            else:
                redacted_data[key] = value
        
        return redacted_data, list(all_applied_rules)
    
    def check_domain_allowlist(
        self,
        url: str,
        allowed_domains: List[str],
    ) -> tuple[bool, Optional[str]]:
        """
        Check if URL's domain is in allowlist
        
        Returns:
            (is_allowed, denied_domain)
        """
        if not allowed_domains:
            return True, None  # No restrictions
        
        # Extract domain from URL
        domain = self._extract_domain(url)
        
        # Check against allowlist
        for allowed in allowed_domains:
            if domain.endswith(allowed):
                return True, None
        
        return False, domain
    
    def check_tool_allowlist(
        self,
        tool_name: str,
        allowed_tools: List[str],
    ) -> bool:
        """Check if tool is in allowlist"""
        if not allowed_tools:
            return True  # No restrictions
        
        return tool_name in allowed_tools
    
    def extract_urls(self, data: Any) -> List[str]:
        """Extract all URLs from data structure"""
        urls = []
        
        if isinstance(data, str):
            # Simple URL detection
            url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
            urls.extend(url_pattern.findall(data))
        
        elif isinstance(data, dict):
            for value in data.values():
                urls.extend(self.extract_urls(value))
        
        elif isinstance(data, list):
            for item in data:
                urls.extend(self.extract_urls(item))
        
        return urls
    
    def extract_tools(self, data: Dict) -> List[str]:
        """Extract tool names from request data"""
        tools = []
        
        # Common tool field names
        if "tool" in data:
            tools.append(data["tool"])
        
        if "tools" in data and isinstance(data["tools"], list):
            tools.extend(data["tools"])
        
        if "tool_calls" in data and isinstance(data["tool_calls"], list):
            for call in data["tool_calls"]:
                if isinstance(call, dict) and "tool" in call:
                    tools.append(call["tool"])
        
        return tools
    
    def enforce_obligations(
        self,
        request_data: Dict[str, Any],
        obligations: Dict[str, Any],
    ) -> tuple[Dict[str, Any], List[str], List[str]]:
        """
        Enforce all obligations on request data
        
        Args:
            request_data: Request payload to process
            obligations: Obligation configuration
        
        Returns:
            (processed_data, violations, applied_obligations)
        """
        violations = []
        applied = []
        processed_data = request_data.copy()
        
        # 1. Apply redaction
        if obligations.get("redaction_enabled", False):
            redaction_rules = obligations.get("redaction_rules", [])
            fields_to_redact = obligations.get("redaction_fields")
            
            processed_data, redacted_rules = self.redact_dict(
                processed_data,
                enabled_rules=redaction_rules if redaction_rules else None,
                fields_to_redact=fields_to_redact,
            )
            
            if redacted_rules:
                applied.append(f"redaction:{','.join(redacted_rules)}")
        
        # 2. Check domain allowlist
        if obligations.get("domain_allowlist"):
            allowed_domains = obligations["domain_allowlist"]
            urls = self.extract_urls(processed_data)
            
            for url in urls:
                is_allowed, denied_domain = self.check_domain_allowlist(url, allowed_domains)
                if not is_allowed:
                    violations.append(f"domain_not_allowed:{denied_domain}")
        
        # 3. Check tool allowlist
        if obligations.get("tool_allowlist"):
            allowed_tools = obligations["tool_allowlist"]
            tools = self.extract_tools(processed_data)
            
            for tool in tools:
                if not self.check_tool_allowlist(tool, allowed_tools):
                    violations.append(f"tool_not_allowed:{tool}")
        
        return processed_data, violations, applied
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        # Remove protocol
        url = url.replace("http://", "").replace("https://", "")
        
        # Get domain part (before first /)
        parts = url.split("/")
        domain = parts[0]
        
        # Remove port
        domain = domain.split(":")[0]
        
        return domain


# Global obligations engine
obligations_engine = ObligationsEngine()
