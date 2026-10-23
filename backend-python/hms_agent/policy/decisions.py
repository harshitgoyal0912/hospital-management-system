"""Value types for policy decisions.

These are deliberately plain and immutable. A decision is data produced by
deterministic code; it is never produced by, or influenced by, model output.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class ToolTier(str, Enum):
    """Risk tier of a tool, independent of who is calling it."""

    READ = "READ"          # returns data, changes nothing
    WRITE = "WRITE"        # creates or modifies a record
    CLINICAL = "CLINICAL"  # decision support; advisory output a clinician may act on
    EXECUTE = "EXECUTE"    # irreversible, clinically or operationally consequential


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_CONFIRMATION = "REQUIRE_CONFIRMATION"
    REQUIRE_HUMAN_APPROVAL = "REQUIRE_HUMAN_APPROVAL"


#: Decisions that permit the handler to run in this same call.
TERMINAL_ALLOW = frozenset({Decision.ALLOW})


@dataclass(frozen=True)
class Principal:
    """The authenticated caller.

    Constructed only from a server-verified token. It is never built from tool
    arguments, model output, or a client-supplied field, because a role the
    caller can assert is not an authorization signal.
    """

    user_id: str
    role: str
    session_id: str | None = None

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("Principal.user_id must not be empty")
        if not self.role:
            raise ValueError("Principal.role must not be empty")


@dataclass(frozen=True)
class ApprovalGrant:
    """Evidence that a human approved one specific action.

    Bound to the tool *and* a hash of its arguments. Approving "discharge bed
    B1" therefore cannot be replayed to discharge B2 — the hash will not match
    and the boundary refuses.

    A grant can satisfy REQUIRE_HUMAN_APPROVAL or REQUIRE_CONFIRMATION. It can
    never turn a DENY into an ALLOW: no amount of approval grants a role a
    capability its policy does not include.
    """

    tool: str
    approver_id: str
    approver_role: str
    arguments_hash: str

    def matches(self, tool: str, arguments_hash: str) -> bool:
        return self.tool == tool and self.arguments_hash == arguments_hash

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "approver_id": self.approver_id,
            "approver_role": self.approver_role,
            "arguments_hash": self.arguments_hash,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "ApprovalGrant | None":
        if not data:
            return None
        try:
            return cls(
                tool=data["tool"],
                approver_id=data["approver_id"],
                approver_role=data["approver_role"],
                arguments_hash=data["arguments_hash"],
            )
        except (KeyError, TypeError):
            return None


@dataclass(frozen=True)
class PolicyDecision:
    decision: Decision
    tool: str
    role: str
    rule_id: str
    reason: str
    tier: ToolTier | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def allowed(self) -> bool:
        return self.decision in TERMINAL_ALLOW

    @property
    def blocked(self) -> bool:
        """True when the handler must not run as a result of this call."""
        return self.decision is not Decision.ALLOW

    def to_audit(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "tool": self.tool,
            "role": self.role,
            "rule_id": self.rule_id,
            "reason": self.reason,
            "tier": self.tier.value if self.tier else None,
        }
