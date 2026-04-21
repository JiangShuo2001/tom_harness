"""ToM-specific plugin pack.

A single entry point `install(harness_components)` wires up everything:
  - failure-type → skill mappings (recovery handler)
  - memory metadata enrichment (indexing structure)
  - output validators (knowledge-gate consistency, etc.)
  - plan-template skills (drop-ins under plan_templates/)

None of this modifies the core. If you disable this plugin, the harness
still runs — just with generic behavior.
"""

from .install import install

__all__ = ["install"]
