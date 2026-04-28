"""External skill pack adapter layer.

Goal: integrate skill packs authored by other contributors **without
modifying their source files**. Each pack is wrapped by a SkillPackAdapter
that knows how to (1) load its skills into our SkillLib, (2) route a case
to one of those skills, and (3) report its own provenance.

This module is the only piece the harness exposes for cross-team plugins.
The harness core (scheduler / planner / executor / schemas / hooks) is
untouched.
"""

from .adapter import SkillPackAdapter, SkillPackInfo, RoutingResult

__all__ = ["SkillPackAdapter", "SkillPackInfo", "RoutingResult"]
