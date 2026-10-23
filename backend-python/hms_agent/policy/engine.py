"""Deterministic policy engine.

This is the only component permitted to decide whether an action may proceed.
Three properties matter more than anything else here, and each has a test:

1. **Fail closed.** A tool with no declared policy is denied.
2. **Inputs are structural, not textual.** The decision is a function of
   (role, tool) and declared rules only. Nothing the model wrote, and nothing in
   the tool arguments, can change a decision — so prompt injection in a free-text
   field cannot escalate privilege.
3. **Blocked means the handler never runs.** Enforcement happens before dispatch,
   not inside the handler.
"""
from __future__ import annotations

from typing import Any, Mapping

from .decisions import Decision, PolicyDecision, Principal, ToolTier
from .registry import TOOL_POLICIES, ToolPolicy


class PolicyViolation(RuntimeError):
    """Raised when a caller attempts to execute a blocked action."""

    def __init__(self, decision: PolicyDecision):
        self.decision = decision
        super().__init__(f"{decision.decision.value}: {decision.tool} for role '{decision.role}' ({decision.reason})")


class PolicyEngine:
    """Evaluates tool requests against the declared registry."""

    def __init__(self, policies: Mapping[str, ToolPolicy] | None = None):
        self._policies = dict(TOOL_POLICIES if policies is None else policies)

    # -- introspection ----------------------------------------------------
    def known_tools(self) -> frozenset[str]:
        return frozenset(self._policies)

    def tools_for_role(self, role: str) -> frozenset[str]:
        """Tools this role may reach at all, in any decision mode.

        Used to build the model's tool menu, so the agent is never shown a
        capability it could not use. Narrowing the menu is a usability and token
        optimisation; it is not the security control. The gate is still checked.
        """
        out = set()
        for name, p in self._policies.items():
            if role in p.allowed_roles or role in p.approval_roles or role in p.confirm_roles:
                out.add(name)
        return frozenset(out)

    # -- the gate ---------------------------------------------------------
    def check(
        self,
        principal: Principal,
        tool: str,
        arguments: Mapping[str, Any] | None = None,
    ) -> PolicyDecision:
        """Return a decision for this (principal, tool) pair.

        ``arguments`` is accepted so that future argument-scoped rules have a
        home, and so callers cannot form the habit of omitting it. It is
        deliberately **not** consulted for the role decision.
        """
        policy = self._policies.get(tool)

        if policy is None:
            return PolicyDecision(
                decision=Decision.DENY,
                tool=tool,
                role=principal.role,
                rule_id="unknown_tool",
                reason="tool has no declared policy; denied by default",
            )

        role = principal.role

        if role in policy.approval_roles:
            return PolicyDecision(
                decision=Decision.REQUIRE_HUMAN_APPROVAL,
                tool=tool,
                role=role,
                rule_id="approval_required",
                reason=policy.reason or f"{tool} requires human approval for role '{role}'",
                tier=policy.tier,
            )

        if role in policy.confirm_roles:
            return PolicyDecision(
                decision=Decision.REQUIRE_CONFIRMATION,
                tool=tool,
                role=role,
                rule_id="confirmation_required",
                reason=policy.reason or f"{tool} requires explicit confirmation for role '{role}'",
                tier=policy.tier,
            )

        if role in policy.allowed_roles:
            return PolicyDecision(
                decision=Decision.ALLOW,
                tool=tool,
                role=role,
                rule_id="role_permitted",
                reason=f"role '{role}' is permitted to call {tool}",
                tier=policy.tier,
            )

        return PolicyDecision(
            decision=Decision.DENY,
            tool=tool,
            role=role,
            rule_id="role_not_permitted",
            reason=policy.reason or f"role '{role}' may not call {tool}",
            tier=policy.tier,
        )

    def enforce(
        self,
        principal: Principal,
        tool: str,
        arguments: Mapping[str, Any] | None = None,
    ) -> PolicyDecision:
        """Like :meth:`check`, but raises when the action may not proceed."""
        decision = self.check(principal, tool, arguments)
        if decision.blocked:
            raise PolicyViolation(decision)
        return decision
