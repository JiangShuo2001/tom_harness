"""A/B: critic-feedback retry on Persuasion + Faux-pas (660 samples).

OFF: oracle pick + 1 LLM call (no validator)
ON:  oracle pick + LLMCriticValidator (1 LLM call + 1 critic call + maybe 1 retry)
"""
from __future__ import annotations

import argparse, json, logging, os, sys, time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, "/home/coder/survey_1/symbolictom_repro")

from benchmark_adapters import load_tombench  # type: ignore  # noqa: E402

from tom_harness import LLMClient, HarnessRuntime, OraclePicksRouter  # noqa: E402
from tom_harness.tools.skills import SkillLib  # noqa: E402
from tom_harness.validators import LLMCriticValidator  # noqa: E402
from tom_harness.plugins.external_skill_pack.set1_adapter import Set1Adapter  # noqa: E402
from tom_harness.plugins.external_skill_pack.set2_adapter import Set2Adapter  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("ab_critic"); logger.setLevel(logging.INFO)


TARGET_TASKS = {"Persuasion Story Task", "Faux-pas Recognition Test"}


def build_runtime(api_base, api_key, model, validator_on: bool) -> HarnessRuntime:
    llm = LLMClient(api_base=api_base, api_key=api_key, model=model,
                    temperature=0.0, max_tokens=1024, timeout=180.0, max_retries=3)
    sl = SkillLib()
    Set1Adapter(pack_root=Path("/workspace/symbolictom_report/skill_set1")).load_into(sl)
    Set2Adapter(pack_root=Path("/workspace/symbolictom_report/skill_set2/skill_v2"),
                routing_mode="signature").load_into(sl)
    validators = []
    if validator_on:
        validators.append(LLMCriticValidator(llm=llm, target_tasks=TARGET_TASKS))
    return HarnessRuntime(llm=llm, skill_lib=sl, router=OraclePicksRouter(),
                          validators=validators, max_retries=1)


def run_one(runtime, s):
    t0 = time.time()
    r = runtime.answer_one(question=s["question"], story=s["story"],
                            options=s["options"], task_type=s["metadata"]["task"])
    return {"id": s["id"], "task": s["metadata"]["task"], "gold": s["answer"],
            "skill_id": r.skill_id, "pred": r.answer, "ok": r.answer == s["answer"],
            "n_llm_calls": r.n_llm_calls, "validator_events": r.validator_events,
            "elapsed": time.time()-t0}


def run_config(name, runtime, samples, out_path, workers):
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
            n = 0
            for fut in as_completed(futs):
                f.write(json.dumps(fut.result(), ensure_ascii=False)+"\n"); f.flush()
                n += 1
                if n % 100 == 0:
                    logger.info(f"  [{name}] {n}/{len(pending)} ({time.time()-t0:.1f}s)")
        f.close()
        logger.info(f"[{name}] done in {time.time()-t0:.1f}s")
    rows = []
    for ln in open(out_path, encoding="utf-8"):
        try: rows.append(json.loads(ln))
        except Exception: pass
    return rows


def summarize(rows):
    per_task = defaultdict(lambda: {"correct":0,"total":0,"fires":0,"n_calls_total":0})
    for r in rows:
        c = per_task[r["task"]]
        c["total"] += 1
        c["n_calls_total"] += r.get("n_llm_calls", 1)
        if r["ok"]: c["correct"] += 1
        for ev in r.get("validator_events", []):
            if not ev.get("valid", True):
                c["fires"] += 1
    for c in per_task.values():
        c["accuracy"] = round(c["correct"]/c["total"], 4) if c["total"] else 0.0
        c["avg_calls"] = round(c["n_calls_total"]/c["total"], 2) if c["total"] else 0.0
    return dict(per_task)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out_dir", default="results_critic_ab")
    args = ap.parse_args()

    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.environ.get("TOM_API_KEY"); model = os.environ.get("TOM_MODEL", "qwen-plus")
    if not api_key: raise SystemExit("ERROR: TOM_API_KEY")

    samples = [s for s in load_tombench() if s["metadata"].get("task") in TARGET_TASKS]
    logger.info(f"target pool: {len(samples)} samples (Persuasion+Faux-pas)")
    out_dir = Path(args.out_dir); out_dir.mkdir(exist_ok=True)

    rt_off = build_runtime(api_base, api_key, model, validator_on=False)
    rows_off = run_config("OFF", rt_off, samples, out_dir/"off.jsonl", args.workers)
    summ_off = summarize(rows_off)

    rt_on = build_runtime(api_base, api_key, model, validator_on=True)
    rows_on = run_config("ON", rt_on, samples, out_dir/"on.jsonl", args.workers)
    summ_on = summarize(rows_on)

    print(f"\n{'='*86}\nCRITIC-FEEDBACK RETRY A/B — {model}, {len(samples)} samples\n{'='*86}")
    print(f"{'task':<32}{'OFF acc':<10}{'ON acc':<10}{'Δ':<10}{'fires':<8}{'avg_calls(ON)':<14}")
    tot_off=0; tot_on=0; tot_n=0
    for t in sorted(TARGET_TASKS):
        a = summ_off.get(t,{}); b = summ_on.get(t,{})
        d = b.get('accuracy',0) - a.get('accuracy',0)
        tot_off += a.get('correct',0); tot_on += b.get('correct',0); tot_n += a.get('total',0)
        print(f"  {t:<30} {a.get('accuracy',0):.3f}     {b.get('accuracy',0):.3f}     "
              f"{d:+.4f}  {b.get('fires',0):<6}  {b.get('avg_calls',0):.2f}")
    if tot_n:
        print(f"  {'-'*84}")
        print(f"  {'OVERALL':<30} {tot_off/tot_n:.3f}     {tot_on/tot_n:.3f}     "
              f"{(tot_on-tot_off)/tot_n:+.4f}")

    (out_dir / "summary.json").write_text(
        json.dumps({"OFF": summ_off, "ON": summ_on, "model": model, "n": len(samples)},
                   ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
