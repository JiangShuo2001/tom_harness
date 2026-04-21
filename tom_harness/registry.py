"""Tool Registry.

Maintains a map from (tool_type, tool_name) → concrete Tool implementation.
Handles schema validation, permission policy, and standardized dispatch.

Core responsibility: the planner emits abstract ToolCalls; the executor asks
the registry to resolve and invoke them. Concrete implementations are
opaque to the rest of the system.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .schemas import ToolCall, ToolType
from .tools.base import Tool, ToolResult


@dataclass
class ToolRegistry:
    """Two-dimensional registry keyed by (tool_type, tool_name)."""
    _tools: dict[tuple[ToolType, str], Tool] = field(default_factory=dict)
    _permissions: dict[tuple[ToolType, str], set[str]] = field(default_factory=dict)

    def register(
        self,
        tool: Tool,
        *,
        permissions: set[str] | None = None,
    ) -> None:
        key = (tool.tool_type, tool.tool_name)
        if key in self._tools:
            raise ValueError(f"Tool already registered: {key}")
        self._tools[key] = tool
        self._permissions[key] = permissions or set()

    def has(self, tool_type: ToolType, tool_name: str) -> bool:
        return (tool_type, tool_name) in self._tools

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def schema_summary(self) -> str:
        """Render a compact summary for Planner context injection."""
        if not self._tools:
            return "(no tools registered)"
        lines = []
        for (ttype, tname), tool in self._tools.items():
            lines.append(f"- [{ttype.value}] {tname}: {tool.description}")
        return "\n".join(lines)

    def dispatch(self, call: ToolCall, *, caller_scope: set[str] | None = None) -> ToolResult:
        """Resolve and invoke a tool call.

        Parameters
        ----------
        call : ToolCall
            The structured invocation request from a plan step.
        caller_scope : set[str] | None
            Permission tokens the caller possesses. Any permissions declared
            on the tool must be satisfied by this set.
        """
        key = (call.tool_type, call.tool_name)
        tool = self._tools.get(key)
        if tool is None:
            return ToolResult(
                success=False,
                error=f"Tool not registered: type={call.tool_type.value} name={call.tool_name}",
            )
        required = self._permissions.get(key, set())
        if required and not required.issubset(caller_scope or set()):
            missing = required - (caller_scope or set())
            return ToolResult(
                success=False,
                error=f"Permission denied: missing {missing}",
            )
        t0 = time.time()
        try:
            validated = tool.validate_params(call.tool_params)
            raw = tool.run(**validated)
            return ToolResult(
                success=True,
                raw_output=raw,
                structured_output=raw if isinstance(raw, dict) else {},
                duration_ms=int((time.time() - t0) * 1000),
            )
        except Exception as e:  # noqa: BLE001
            return ToolResult(
                success=False,
                error=f"{type(e).__name__}: {e}",
                duration_ms=int((time.time() - t0) * 1000),
            )
