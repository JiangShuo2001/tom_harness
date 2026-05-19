"""Harness Optimizer — non-invasive offline optimizer for tom_harness.

This package is *standalone* and *non-invasive*: it does not import, modify,
or otherwise touch the original ``tom_harness`` runtime. It produces YAML
``policy_bundle`` artefacts that the runtime can optionally load in the
future to override its routing, gating, prompt-composition, RAG, memory
and validator behaviour.

See ``optimizer/README.md`` for a full overview.
"""

from .interfaces import (
    RouteDecision,
    ModuleGateDecision,
    ModuleOutput,
    OptimizerTarget,
)
from .policy_bundle import PolicyBundle
from .experience_store import ExperienceStore
from .config import OptimizerConfig

__all__ = [
    "RouteDecision",
    "ModuleGateDecision",
    "ModuleOutput",
    "OptimizerTarget",
    "PolicyBundle",
    "ExperienceStore",
    "OptimizerConfig",
]

__version__ = "0.1.0"
