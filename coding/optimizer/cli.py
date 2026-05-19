"""Minimal CLI for the Harness Optimizer.

Run with::

    python -m optimizer.cli inspect
    python -m optimizer.cli route-gate-demo --policy <yaml> --input <jsonl>
    python -m optimizer.cli prompt-demo      --policy <yaml> --input <json>
    python -m optimizer.cli init-run         --name test_run
    python -m optimizer.cli validate-policy  --policy <yaml>

The CLI must work from the repo root *or* from inside ``coding/`` —
both ``python -m optimizer.cli ...`` (when ``coding/`` is on the path)
and ``python -m coding.optimizer.cli ...`` (from the project root)
should behave identically. ``__main__.py`` handles invocation as
``python coding/optimizer/cli.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Allow ``python coding/optimizer/cli.py`` and ``python -m optimizer.cli``
# alike — both resolve to the same package after this bootstrap.
if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    here = Path(__file__).resolve()
    sys.path.insert(0, str(here.parent.parent))
    __package__ = "optimizer"

from .config import OptimizerConfig, has_pyyaml, load_yaml
from .experience_store import ExperienceStore
from .interfaces import RouteDecision
from .policy_bundle import PolicyBundle
from .targets.prompt_compose_target import PromptComposePolicy
from .targets.route_gate_target import RouteGatePolicyEngine


def _print(msg: str = "") -> None:
    sys.stdout.write(msg + "\n")


# ──────────────────────────────────────────────────────────────────────
#  Subcommands
# ──────────────────────────────────────────────────────────────────────

def cmd_inspect(_: argparse.Namespace) -> int:
    cfg = OptimizerConfig()
    _print("Harness Optimizer — inspect")
    _print(f"  package_root        : {cfg.package_root}")
    _print(f"  policies_dir        : {cfg.policies_dir}")
    _print(f"  examples_dir        : {cfg.examples_dir}")
    _print(f"  runs_dir (default)  : {cfg.runs_dir.resolve()}")
    _print(f"  PyYAML available    : {has_pyyaml()}")
    _print()
    _print("Available policy files:")
    if cfg.policies_dir and cfg.policies_dir.exists():
        for p in sorted(cfg.policies_dir.iterdir()):
            _print(f"  - {p.name}")
    _print()
    _print("Available example inputs:")
    if cfg.examples_dir and cfg.examples_dir.exists():
        for p in sorted(cfg.examples_dir.iterdir()):
            _print(f"  - {p.name}")
    return 0


def cmd_route_gate_demo(args: argparse.Namespace) -> int:
    engine = RouteGatePolicyEngine.from_yaml(args.policy)
    issues = engine.validate()
    if issues:
        _print("Policy issues:")
        for i in issues:
            _print(f"  - {i}")
        return 2

    n_total = 0
    n_skill_on = n_rag_on = n_mem_on = 0
    with open(args.input, "r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                _print(f"  [line {line_no}] skip: {e}")
                continue
            n_total += 1
            decision = engine.decide(
                rec.get("route_decision") or {},
                task_text=rec.get("task_text", ""),
            )
            if decision.use_skill:
                n_skill_on += 1
            if decision.use_rag:
                n_rag_on += 1
            if decision.use_memory:
                n_mem_on += 1
            _print(f"── {rec.get('sample_id', f'line{line_no}')} ──")
            _print(
                f"  scene  : {(rec.get('route_decision') or {}).get('scene_tag')}"
            )
            _print(
                f"  skill  : {(rec.get('route_decision') or {}).get('skill_id')} "
                f"@ conf={(rec.get('route_decision') or {}).get('confidence')}"
            )
            _print(f"  → use_skill   : {decision.use_skill}")
            _print(f"  → use_rag     : {decision.use_rag}")
            _print(f"  → use_memory  : {decision.use_memory}")
            _print(f"  → validators  : {decision.selected_validators}")
            _print(f"  rationale     : {decision.rationale}")
            _print()
    _print("── summary ──")
    _print(f"  total samples : {n_total}")
    _print(f"  skill on      : {n_skill_on}")
    _print(f"  rag on        : {n_rag_on}")
    _print(f"  memory on     : {n_mem_on}")
    return 0


def cmd_prompt_demo(args: argparse.Namespace) -> int:
    engine = PromptComposePolicy.from_yaml(args.policy)
    issues = engine.validate()
    if issues:
        _print("Policy issues:")
        for i in issues:
            _print(f"  - {i}")
        return 2

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = engine.render(
        task=payload.get("task") or {},
        route_decision=payload.get("route_decision") or {},
        module_outputs=payload.get("module_outputs") or [],
    )

    _print("── system_prompt ──")
    _print(result["system_prompt"])
    _print()
    _print("── user_prompt ──")
    _print(result["user_prompt"])
    _print()
    _print("── debug ──")
    _print(json.dumps(result["debug"], indent=2, ensure_ascii=False))

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(_render_markdown(result), encoding="utf-8")
        _print(f"\nWrote markdown report → {out_path}")
    return 0


def cmd_init_run(args: argparse.Namespace) -> int:
    cfg = OptimizerConfig(runs_dir=Path(args.runs_dir or "optimizer_runs"))
    store = ExperienceStore(cfg.runs_dir)
    run_dir = store.create_run(args.name)
    # Seed each run with the default candidate policy so the run is
    # reproducible without external state.
    bundle = PolicyBundle.from_yaml(cfg.default_policy_bundle_path())
    store.save_candidate_policy(run_dir, bundle.as_dict())
    _print(f"Created run at: {run_dir}")
    _print(f"  candidate_policy.yaml seeded from {cfg.default_policy_bundle_path()}")
    return 0


def cmd_validate_policy(args: argparse.Namespace) -> int:
    bundle = PolicyBundle.from_yaml(args.policy)
    issues = bundle.validate()
    # Run per-target validators too, for the slots that are present.
    if bundle.route_gate_policy:
        issues.extend(
            f"route_gate_policy: {i}"
            for i in RouteGatePolicyEngine.from_policy(
                bundle.route_gate_policy
            ).validate()
        )
    if bundle.prompt_compose_policy:
        issues.extend(
            f"prompt_compose_policy: {i}"
            for i in PromptComposePolicy.from_policy(
                bundle.prompt_compose_policy
            ).validate()
        )
    if not issues:
        _print(f"OK — {args.policy} passes structural validation.")
        return 0
    _print(f"Issues found in {args.policy}:")
    for i in issues:
        _print(f"  - {i}")
    return 1


# ──────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────

def _render_markdown(result: dict) -> str:
    lines = ["# Prompt Compose Demo", "", "## System prompt", "", "```",
             result["system_prompt"], "```", "", "## User prompt", "",
             "```", result["user_prompt"], "```", "", "## Debug", "",
             "```json", json.dumps(result["debug"], indent=2, ensure_ascii=False),
             "```", ""]
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────
#  Argument parser
# ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="optimizer",
        description="Harness Optimizer — non-invasive offline optimizer for tom_harness.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sp_inspect = sub.add_parser("inspect", help="Show package layout and config.")
    sp_inspect.set_defaults(func=cmd_inspect)

    sp_rg = sub.add_parser(
        "route-gate-demo", help="Apply route-gate policy to JSONL of samples."
    )
    sp_rg.add_argument("--policy", required=True)
    sp_rg.add_argument("--input", required=True)
    sp_rg.set_defaults(func=cmd_route_gate_demo)

    sp_pc = sub.add_parser(
        "prompt-demo", help="Apply prompt-compose policy to a JSON sample."
    )
    sp_pc.add_argument("--policy", required=True)
    sp_pc.add_argument("--input", required=True)
    sp_pc.add_argument("--output", help="Optional markdown report path.")
    sp_pc.set_defaults(func=cmd_prompt_demo)

    sp_init = sub.add_parser("init-run", help="Create a new optimizer run dir.")
    sp_init.add_argument("--name", default=None)
    sp_init.add_argument("--runs-dir", default=None)
    sp_init.set_defaults(func=cmd_init_run)

    sp_val = sub.add_parser(
        "validate-policy", help="Structural-validate a policy bundle YAML."
    )
    sp_val.add_argument("--policy", required=True)
    sp_val.set_defaults(func=cmd_validate_policy)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
