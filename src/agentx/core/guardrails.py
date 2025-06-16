"""
Guardrails Engine - Comprehensive Safety and Compliance System

This module implements multi-layered safety mechanisms including input validation,
output filtering, rate limiting, content safety, and policy compliance checks.
"""

import re
import time
import hashlib
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from ..utils.logger import get_logger
from ..utils.id import generate_short_id
from .config import GuardrailPolicy, GuardrailType
from .message import GuardrailCheck, GuardrailPart
from .event import GuardrailViolationEvent
from ..event import publish_event

logger = get_logger(__name__)


@dataclass
class GuardrailContext:
    """Context information for guardrail checks."""
    agent_name: str
    task_id: Optional[str] = None
    step_id: Optional[str] = None
    content_type: str = "text"  # "text", "tool_call", "tool_result"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RateLimitState:
    """Rate limiting state tracking."""
    count: int = 0
    window_start: datetime = field(default_factory=datetime.now)
    last_request: datetime = field(default_factory=datetime.now)


class GuardrailRule(ABC):
    """Abstract base class for guardrail rules."""
    
    def __init__(self, name: str, severity: str = "medium", action: str = "warn"):
        self.name = name
        self.severity = severity  # "low", "medium", "high", "critical"
        self.action = action  # "block", "warn", "log"
    
    @abstractmethod
    async def check(self, content: str, context: GuardrailContext) -> GuardrailCheck:
        """Check content against this rule."""
        pass


class InputValidationRule(GuardrailRule):
    """Input validation rule for sanitizing user inputs."""
    
    def __init__(self, name: str, patterns: List[str], **kwargs):
        super().__init__(name, **kwargs)
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    async def check(self, content: str, context: GuardrailContext) -> GuardrailCheck:
        """Check input against validation patterns."""
        check_id = generate_short_id()
        
        for pattern in self.patterns:
            if pattern.search(content):
                return GuardrailCheck(
                    check_id=check_id,
                    check_type="input_validation",
                    status="failed",
                    message=f"Input validation failed: content matches prohibited pattern",
                    policy_violated=self.name,
                    severity=self.severity
                )
        
        return GuardrailCheck(
            check_id=check_id,
            check_type="input_validation",
            status="passed",
            message="Input validation passed"
        )


class ContentFilterRule(GuardrailRule):
    """Content filtering rule for blocking inappropriate content."""
    
    def __init__(self, name: str, keywords: List[str], **kwargs):
        super().__init__(name, **kwargs)
        self.keywords = [keyword.lower() for keyword in keywords]
    
    async def check(self, content: str, context: GuardrailContext) -> GuardrailCheck:
        """Check content for inappropriate keywords."""
        check_id = generate_short_id()
        content_lower = content.lower()
        
        for keyword in self.keywords:
            if keyword in content_lower:
                return GuardrailCheck(
                    check_id=check_id,
                    check_type="content_filter",
                    status="failed",
                    message=f"Content filter triggered: inappropriate content detected",
                    policy_violated=self.name,
                    severity=self.severity
                )
        
        return GuardrailCheck(
            check_id=check_id,
            check_type="content_filter",
            status="passed",
            message="Content filter passed"
        )


class RateLimitRule(GuardrailRule):
    """Rate limiting rule for preventing abuse."""
    
    def __init__(self, name: str, max_requests: int, window_seconds: int, **kwargs):
        super().__init__(name, **kwargs)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.state: Dict[str, RateLimitState] = {}
    
    async def check(self, content: str, context: GuardrailContext) -> GuardrailCheck:
        """Check rate limits for the agent."""
        check_id = generate_short_id()
        agent_key = context.agent_name
        now = datetime.now()
        
        # Get or create state for this agent
        if agent_key not in self.state:
            self.state[agent_key] = RateLimitState()
        
        state = self.state[agent_key]
        
        # Check if we need to reset the window
        if (now - state.window_start).total_seconds() >= self.window_seconds:
            state.count = 0
            state.window_start = now
        
        # Increment count
        state.count += 1
        state.last_request = now
        
        # Check if rate limit exceeded
        if state.count > self.max_requests:
            return GuardrailCheck(
                check_id=check_id,
                check_type="rate_limit",
                status="failed",
                message=f"Rate limit exceeded: {state.count}/{self.max_requests} requests in {self.window_seconds}s",
                policy_violated=self.name,
                severity=self.severity
            )
        
        return GuardrailCheck(
            check_id=check_id,
            check_type="rate_limit",
            status="passed",
            message=f"Rate limit check passed: {state.count}/{self.max_requests} requests"
        )


class ContentSafetyRule(GuardrailRule):
    """Content safety rule using pattern matching and heuristics."""
    
    def __init__(self, name: str, safety_patterns: List[str], **kwargs):
        super().__init__(name, **kwargs)
        self.safety_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in safety_patterns]
    
    async def check(self, content: str, context: GuardrailContext) -> GuardrailCheck:
        """Check content for safety violations."""
        check_id = generate_short_id()
        
        for pattern in self.safety_patterns:
            if pattern.search(content):
                return GuardrailCheck(
                    check_id=check_id,
                    check_type="content_safety",
                    status="failed",
                    message="Content safety violation detected",
                    policy_violated=self.name,
                    severity=self.severity
                )
        
        return GuardrailCheck(
            check_id=check_id,
            check_type="content_safety",
            status="passed",
            message="Content safety check passed"
        )


class ComplianceRule(GuardrailRule):
    """Compliance rule for organizational and regulatory requirements."""
    
    def __init__(self, name: str, compliance_checks: List[Dict[str, Any]], **kwargs):
        super().__init__(name, **kwargs)
        self.compliance_checks = compliance_checks
    
    async def check(self, content: str, context: GuardrailContext) -> GuardrailCheck:
        """Check content for compliance violations."""
        check_id = generate_short_id()
        
        for check in self.compliance_checks:
            check_type = check.get("type", "pattern")
            
            if check_type == "pattern":
                pattern = re.compile(check["pattern"], re.IGNORECASE)
                if pattern.search(content):
                    return GuardrailCheck(
                        check_id=check_id,
                        check_type="compliance",
                        status="failed",
                        message=f"Compliance violation: {check.get('description', 'Policy violation')}",
                        policy_violated=self.name,
                        severity=self.severity
                    )
            
            elif check_type == "length":
                max_length = check.get("max_length", 10000)
                if len(content) > max_length:
                    return GuardrailCheck(
                        check_id=check_id,
                        check_type="compliance",
                        status="failed",
                        message=f"Content length exceeds limit: {len(content)} > {max_length}",
                        policy_violated=self.name,
                        severity=self.severity
                    )
        
        return GuardrailCheck(
            check_id=check_id,
            check_type="compliance",
            status="passed",
            message="Compliance check passed"
        )


class GuardrailEngine:
    """
    Comprehensive guardrails engine for safety and compliance.
    
    Implements multi-layered safety mechanisms including input validation,
    output filtering, rate limiting, content safety, and policy compliance.
    """
    
    def __init__(self):
        self.policies: Dict[str, List[GuardrailRule]] = {}
        self.global_rules: List[GuardrailRule] = []
        
        # Initialize default safety rules
        self._initialize_default_rules()
        
        logger.info("Guardrails engine initialized")
    
    def _initialize_default_rules(self):
        """Initialize default safety rules."""
        # Default input validation patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script injection
            r'javascript:',  # JavaScript URLs
            r'data:text/html',  # Data URLs
            r'eval\s*\(',  # Eval calls
            r'exec\s*\(',  # Exec calls
        ]
        
        # Default content safety patterns
        safety_patterns = [
            r'\b(password|secret|token|key)\s*[:=]\s*["\']?[\w\-]+["\']?',  # Credentials
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card numbers
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN patterns
        ]
        
        # Add default rules
        self.global_rules.extend([
            InputValidationRule("default_input_validation", dangerous_patterns, severity="high", action="block"),
            ContentSafetyRule("default_content_safety", safety_patterns, severity="high", action="warn"),
            RateLimitRule("default_rate_limit", max_requests=100, window_seconds=60, severity="medium", action="warn")
        ])
    
    def add_policy(self, policy: GuardrailPolicy):
        """Add a guardrail policy to the engine."""
        rules = []
        
        for rule_config in policy.rules:
            rule = self._create_rule_from_config(policy.name, rule_config, policy.severity, policy.action)
            if rule:
                rules.append(rule)
        
        self.policies[policy.name] = rules
        logger.info(f"Added guardrail policy '{policy.name}' with {len(rules)} rules")
    
    def _create_rule_from_config(self, policy_name: str, rule_config: Dict[str, Any], 
                                severity: str, action: str) -> Optional[GuardrailRule]:
        """Create a guardrail rule from configuration."""
        rule_type = rule_config.get("type", "")
        
        if rule_type == "input_validation":
            return InputValidationRule(
                name=f"{policy_name}_{rule_config.get('name', 'validation')}",
                patterns=rule_config.get("patterns", []),
                severity=severity,
                action=action
            )
        
        elif rule_type == "content_filter":
            return ContentFilterRule(
                name=f"{policy_name}_{rule_config.get('name', 'filter')}",
                keywords=rule_config.get("keywords", []),
                severity=severity,
                action=action
            )
        
        elif rule_type == "rate_limit":
            return RateLimitRule(
                name=f"{policy_name}_{rule_config.get('name', 'rate_limit')}",
                max_requests=rule_config.get("max_requests", 10),
                window_seconds=rule_config.get("window_seconds", 60),
                severity=severity,
                action=action
            )
        
        elif rule_type == "content_safety":
            return ContentSafetyRule(
                name=f"{policy_name}_{rule_config.get('name', 'safety')}",
                safety_patterns=rule_config.get("patterns", []),
                severity=severity,
                action=action
            )
        
        elif rule_type == "compliance":
            return ComplianceRule(
                name=f"{policy_name}_{rule_config.get('name', 'compliance')}",
                compliance_checks=rule_config.get("checks", []),
                severity=severity,
                action=action
            )
        
        else:
            logger.warning(f"Unknown guardrail rule type: {rule_type}")
            return None
    
    async def check_content(self, content: str, context: GuardrailContext, 
                          policy_names: Optional[List[str]] = None) -> GuardrailPart:
        """
        Check content against guardrail policies.
        
        Args:
            content: Content to check
            context: Context information
            policy_names: Specific policies to check (None for all applicable)
            
        Returns:
            GuardrailPart with check results
        """
        checks = []
        
        # Always run global rules
        for rule in self.global_rules:
            try:
                check = await rule.check(content, context)
                checks.append(check)
            except Exception as e:
                logger.error(f"Error running global rule {rule.name}: {e}")
                checks.append(GuardrailCheck(
                    check_id=generate_short_id(),
                    check_type="error",
                    status="failed",
                    message=f"Rule execution error: {str(e)}",
                    policy_violated=rule.name,
                    severity="high"
                ))
        
        # Run policy-specific rules
        policies_to_check = policy_names or list(self.policies.keys())
        
        for policy_name in policies_to_check:
            if policy_name in self.policies:
                for rule in self.policies[policy_name]:
                    try:
                        check = await rule.check(content, context)
                        checks.append(check)
                    except Exception as e:
                        logger.error(f"Error running policy rule {rule.name}: {e}")
                        checks.append(GuardrailCheck(
                            check_id=generate_short_id(),
                            check_type="error",
                            status="failed",
                            message=f"Rule execution error: {str(e)}",
                            policy_violated=rule.name,
                            severity="high"
                        ))
        
        # Determine overall status
        failed_checks = [c for c in checks if c.status == "failed"]
        warning_checks = [c for c in checks if c.status == "warning"]
        
        if failed_checks:
            overall_status = "failed"
        elif warning_checks:
            overall_status = "warning"
        else:
            overall_status = "passed"
        
        # Emit violation events for failed checks
        for check in failed_checks:
            await self._emit_violation_event(check, content, context)
        
        return GuardrailPart(
            checks=checks,
            overall_status=overall_status
        )
    
    async def _emit_violation_event(self, check: GuardrailCheck, content: str, context: GuardrailContext):
        """Emit a guardrail violation event."""
        try:
            # Create content sample (first 100 chars)
            content_sample = content[:100] + "..." if len(content) > 100 else content
            
            event = GuardrailViolationEvent(
                violation_id=check.check_id,
                check_type=check.check_type,
                severity=check.severity or "medium",
                policy_violated=check.policy_violated or "unknown",
                agent_name=context.agent_name,
                content_sample=content_sample,
                action_taken=self._get_action_for_check(check),
                timestamp=datetime.now()
            )
            
            await publish_event(event)
            
        except Exception as e:
            logger.error(f"Failed to emit guardrail violation event: {e}")
    
    def _get_action_for_check(self, check: GuardrailCheck) -> str:
        """Get the action taken for a failed check."""
        # This would normally be determined by the rule's action setting
        # For now, return a default based on severity
        if check.severity == "critical":
            return "blocked"
        elif check.severity == "high":
            return "warned"
        else:
            return "logged"
    
    def should_block_content(self, guardrail_part: GuardrailPart) -> bool:
        """Determine if content should be blocked based on guardrail results."""
        for check in guardrail_part.checks:
            if check.status == "failed" and check.severity in ["critical", "high"]:
                return True
        return False
    
    def get_policy_names(self) -> List[str]:
        """Get list of available policy names."""
        return list(self.policies.keys())
    
    def get_policy_stats(self) -> Dict[str, Any]:
        """Get statistics about guardrail policies and checks."""
        return {
            "total_policies": len(self.policies),
            "global_rules": len(self.global_rules),
            "policy_rules": {name: len(rules) for name, rules in self.policies.items()}
        }


# Global guardrail engine instance
_guardrail_engine: Optional[GuardrailEngine] = None


def get_guardrail_engine() -> GuardrailEngine:
    """Get the global guardrail engine instance."""
    global _guardrail_engine
    if _guardrail_engine is None:
        _guardrail_engine = GuardrailEngine()
    return _guardrail_engine


async def check_content_safety(content: str, agent_name: str, 
                             policy_names: Optional[List[str]] = None,
                             task_id: Optional[str] = None,
                             step_id: Optional[str] = None) -> GuardrailPart:
    """
    Convenience function to check content safety.
    
    Args:
        content: Content to check
        agent_name: Name of the agent
        policy_names: Specific policies to check
        task_id: Optional task ID
        step_id: Optional step ID
        
    Returns:
        GuardrailPart with check results
    """
    engine = get_guardrail_engine()
    context = GuardrailContext(
        agent_name=agent_name,
        task_id=task_id,
        step_id=step_id
    )
    
    return await engine.check_content(content, context, policy_names) 