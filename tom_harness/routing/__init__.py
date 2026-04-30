"""Routing layer: Router ABC + concrete routers.

A Router decides "which skill to apply to this sample" without making
LLM calls (LLM-based routing was empirically worse than rule-based; see
WEEKLY_REPORT_HARNESS_2026-04-29). Routers are pure functions of
(question, story, options, task_type).
"""

from .base import Router, RouteDecision
from .oracle_picks import ORACLE_PICKS, OraclePicksRouter

__all__ = ["Router", "RouteDecision", "ORACLE_PICKS", "OraclePicksRouter"]
