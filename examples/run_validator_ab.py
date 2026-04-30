"""A/B test: validator stack ON vs OFF on 3 target tasks.

Tasks (1360 samples total):
  - Scalar Implicature Test (200) — ScalarProceduralValidator fires
  - Faux-pas Recognition Test (560) — CrossSkillValidator fires
  - False Belief Task (600) — CrossSkillValidator + FBStateBackedValidator fire

Reports: per-task acc with vs without validators, validator firing rate,
substitute rate. Confirms (or refutes) the +1.5-2pp prediction made in
WEEKLY_REPORT_HARNESS_2026-04-29 §四.
"""

from __future__ import annotations

import argparse, json, logging, os, sys, time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, "/home/coder/survey_1/symbolictom_repro")

from benchmark_adapters import load_tombench  # type: ignore  # noqa: E402

from tom_harness import LLMClient  # noqa: E402
from tom_harness.runtime import HarnessRuntime, build_default_runtime  # noqa: E402
from tom_harness.routing import OraclePicksRouter  # noqa: E402
from tom_harness.tools.skills import SkillLib  # noqa: E402
from tom_harness.plugins.external_skill_pack.set1_adapter import Set1Adapter  # noqa: E402
from tom_harness.plugins.external_skill_pack.set2_adapter import Set2Adapter  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("ab"); logger.setLevel(logging.INFO)


TARGET_TASKS = {
    # Scalar dropped: ScalarProceduralValidator disabled (1.5% fire, net -1pp)
    # FB and Faux-pas: only CrossSkillValidator (conservative unanimous rule)
    "Faux-pas Recognition Test",
    "False Belief Task",
}


def build_runtime(api_base, api_key, model, validator_on: bool) -> HarnessRuntime:
    llm = LLMClient(api_base=api_base, api_key=api_key, model=model,
                    temperature=0.0, max_tokens=1024, timeout=180.0, max_retries=3)
    sl = SkillLib()
    Set1Adapter(pack_root=Path("/workspace/symbolictom_report/skill_set1")).load_into(sl)
    Set2Adapter(pack_root=Path("/workspace/symbolictom_report/skill_set2/skill_v2"),
                routing_mode="signature").load_into(sl)
    return build_default_runtime(
        llm=llm, skill_lib=sl, router=OraclePicksRouter(),
        enable_scalar_validator=validator_on,
        enable_cross_skill_validator=validator_on,
        enable_fb_state_validator=validator_on,
    )


def run_one(runtime: HarnessRuntime, s: dict) -> dict:
    t0 = time.time()
    r = runtime.answer_one(
        question=s["question"], story=s["story"], options=s["options"],
        task_type=s["metadata"]["task"],
    )
    return {"id": s["id"], "task": s["metadata"]["task"], "gold": s["answer"],
            "skill_id": r.skill_id, "pred": r.answer, "ok": r.answer == s["answer"],
            "n_llm_calls": r.n_llm_calls, "validator_events": r.validator_events,
            "elapsed": time.time() - t0}


def run_config(name: str, runtime: HarnessRuntime, samples: list,
               out_path: Path, workers: int) -> list[dict]:
    done = set()
    if out_path.exists():
        for ln in open(out_path, encoding="utf-8"):
            try: done.add(json.loads(ln)["id"])
            except Exception: pass
    pending = [s for s in samples if s["id"] not in done]
    logger.info(f"[{name}] resume done={len(done)} pending={len(pending)}")
    if pending:
        f = open(out_path, "a", encoding="utf-8")
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(run_one, runtime, s): s for s in pending}
            n_done = 0
            for fut in as_completed(futs):
                r = fut.result()
                f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
                n_done += 1
                if n_done % 200 == 0:
                    logger.info(f"  [{name}] {n_done}/{len(pending)} ({time.time()-t0:.1f}s)")
        f.close()
        logger.info(f"[{name}] done in {time.time()-t0:.1f}s")
    rows = []
    for ln in open(out_path, encoding="utf-8"):
        try: rows.append(json.loads(ln))
        except Exception: pass
    return rows


def summarize(rows: list[dict]) -> dict:
    per_task = defaultdict(lambda: {"correct": 0, "total": 0,
                                    "validator_fires": 0, "validator_substitutes": 0,
                                    "validator_per_kind": defaultdict(lambda: {"fires": 0, "subst": 0})})
    for r in rows:
        c = per_task[r["task"]]
        c["total"] += 1
        if r["ok"]: c["correct"] += 1
        for ev in r.get("validator_events", []):
            if not ev.get("valid", True):
                c["validator_fires"] += 1
                k = ev.get("validator", "?")
                c["validator_per_kind"][k]["fires"] += 1
                if ev.get("had_suggestion"):
                    c["validator_substitutes"] += 1
                    c["validator_per_kind"][k]["subst"] += 1
    for c in per_task.values():
        c["accuracy"] = round(c["correct"] / c["total"], 4) if c["total"] else 0.0
        c["validator_per_kind"] = dict(c["validator_per_kind"])
    return dict(per_task)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out_dir", default="results_validator_ab")
    args = ap.parse_args()

    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.environ.get("TOM_API_KEY")
    model = os.environ.get("TOM_MODEL", "qwen-plus")
    if not api_key: raise SystemExit("ERROR: set TOM_API_KEY")

    samples = [s for s in load_tombench() if s["metadata"].get("task") in TARGET_TASKS]
    logger.info(f"target pool: {len(samples)} samples (Scalar+Faux-pas+FB)")
    out_dir = Path(args.out_dir); out_dir.mkdir(exist_ok=True)

    # ── A: validators OFF ─────────────────────────────────────────────────
    runtime_off = build_runtime(api_base, api_key, model, validator_on=False)
    rows_off = run_config("OFF", runtime_off, samples, out_dir / "ab_off.jsonl", args.workers)
    summ_off = summarize(rows_off)

    # ── B: validators ON ──────────────────────────────────────────────────
    runtime_on = build_runtime(api_base, api_key, model, validator_on=True)
    rows_on = run_config("ON", runtime_on, samples, out_dir / "ab_on.jsonl", args.workers)
    summ_on = summarize(rows_on)

    # ── Report ────────────────────────────────────────────────────────────
    print(f"\n{'='*88}\nVALIDATOR A/B — {model}, full Scalar+Faux-pas+FB ({len(samples)} samples)\n{'='*88}")
    print(f"{'task':<32} {'OFF acc':<10} {'ON acc':<10} {'Δ':<8} {'fires':<10} {'substitutes':<10}")
    total_off_correct = 0; total_off_total = 0
    total_on_correct = 0; total_on_total = 0
    for t in sorted(TARGET_TASKS):
        a = summ_off.get(t, {"accuracy": 0, "correct": 0, "total": 0})
        b = summ_on.get(t, {"accuracy": 0, "correct": 0, "total": 0,
                            "validator_fires": 0, "validator_substitutes": 0})
        delta = b["accuracy"] - a["accuracy"]
        total_off_correct += a["correct"]; total_off_total += a["total"]
        total_on_correct += b["correct"]; total_on_total += b["total"]
        print(f"  {t:<30} {a['accuracy']:.3f}     {b['accuracy']:.3f}     "
              f"{delta:+.4f}  {b.get('validator_fires',0):<8}  {b.get('validator_substitutes',0):<8}")
        per_kind = b.get("validator_per_kind", {})
        for k, kc in per_kind.items():
            print(f"    {k:<32}  fires={kc['fires']:<5}  subst={kc['subst']}")
    print(f"  {'-'*86}")
    if total_off_total > 0:
        oa = total_off_correct / total_off_total
        ob = total_on_correct / total_on_total
        print(f"  {'OVERALL (3 tasks)':<30} {oa:.3f}     {ob:.3f}     {ob-oa:+.4f}")

    # save summary
    summary = {"validator_OFF": summ_off, "validator_ON": summ_on,
               "model": model, "n_samples": len(samples)}
    (out_dir / "ab_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=lambda o: dict(o) if hasattr(o, 'items') else str(o)),
        encoding="utf-8")


if __name__ == "__main__":
    main()
