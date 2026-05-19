"""Optimizer targets — one module per optimization surface.

Each target owns:
  * the policy schema for its slot in PolicyBundle
  * a policy engine that turns ``policy + sample`` into a decision
  * a default policy YAML under ``optimizer/policies/``
  * an example input JSON/JSONL under ``optimizer/examples/``
"""
