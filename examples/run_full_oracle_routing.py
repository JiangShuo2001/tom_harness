"""Honest full-ToMBench run: oracle task_type routing → per-task best skill.

Decision rules (chosen ONCE before this run):
  - Pick skill iff it strictly beat raw on the 160-sample matrix sweep
  - Tie → raw (small-sample tie is noise, not signal)
  - temp=0, single shot per sample, no self-consistency tricks

Configs (run side-by-side for fair comparison):
  raw           : no skill, just CoT
  oracle_skill  : oracle task_type → per-task pick from PICKS table

Both run on identical 2470-sample full ToMBench main-8 pool.
"""
from __future__ import annotations
import argparse, json, logging, os, re, sys, time, importlib.util
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, "/home/coder/survey_1/symbolictom_repro")

from benchmark_adapters import load_tombench  # type: ignore  # noqa: E402
from tom_harness import LLMClient  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("full"); logger.setLevel(logging.INFO)


MAIN_8 = {
    "Unexpected Outcome Test", "Scalar Implicature Test", "Persuasion Story Task",
    "False Belief Task", "Ambiguous Story Task", "Hinting Task Test",
    "Strange Story Task", "Faux-pas Recognition Test",
}


# Per-task picks: (skill_id, kind) — 'cs1' / 'cs2' / None for raw
# Chosen via "skill strictly beat raw on 160-sample matrix" rule.
PICKS: dict[str, tuple[str | None, str | None]] = {
    "Ambiguous Story Task":         (None, None),                       # tie -> raw
    "False Belief Task":            ("cs1_skill12", "cs1"),             # 0.95 vs raw 0.90
    "Faux-pas Recognition Test":    ("cs1_skill10", "cs1"),             # 0.80 vs raw 0.65
    "Hinting Task Test":            ("cs1_skill8",  "cs1"),             # 1.00 vs raw 0.95
    "Persuasion Story Task":        ("cs2_S11_BeliefEmotion", "cs2"),   # 0.70 vs raw 0.65
    "Scalar Implicature Test":      ("cs1_skill10", "cs1"),             # 0.60 vs raw 0.40
    "Strange Story Task":           ("cs1_skill15", "cs1"),             # 0.95 vs raw 0.85
    "Unexpected Outcome Test":      (None, None),                       # tie -> raw
}


def load_skills() -> dict[str, str]:
    out: dict[str, str] = {}
    base1 = Path("/workspace/symbolictom_report/skill_set1")
    for sid, kind in [(p[0], p[1]) for p in PICKS.values() if p[0] and p[1] == "cs1"]:
        n = sid.replace("cs1_", "")
        out[sid] = (base1 / n / "SKILL.md").read_text(encoding="utf-8")
    cs2_keys = [(p[0], p[0].replace("cs2_", "")) for p in PICKS.values() if p[0] and p[1] == "cs2"]
    if cs2_keys:
        skills_path = "/workspace/symbolictom_report/skill_set2/skill_v2/skills.py"
        spec = importlib.util.spec_from_file_location("set2_skills_module", skills_path)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)  # type: ignore
        for full_id, key in cs2_keys:
            out[full_id] = mod.SKILLS[key]
    return out


SYSTEM_RAW = (
    "You are a reading comprehension assistant. Read the story and answer "
    'the multiple-choice question. Reply with ONLY a JSON object: '
    '{"answer": "A" | "B" | "C" | "D"}'
)


def build_user(s, skill_body=None):
    opts = "\n".join(f"{k}. {v}" for k, v in s["options"].items() if v)
    if skill_body:
        return (
            f"## Reasoning Skill (apply before answering)\n{skill_body}\n\n"
            f"## Story\n{s['story']}\n\n"
            f"## Question\n{s['question']}\n\n"
            f"## Options\n{opts}\n\n"
            '## Answer\nAfter applying the skill above, reply with ONLY a JSON object: {"answer": "A"|"B"|"C"|"D"}'
        )
    return f"Story: {s['story']}\n\nQuestion: {s['question']}\n\nOptions:\n{opts}"


_LETTER = re.compile(r'"answer"\s*:\s*"([A-D])"')


def parse_letter(text: str) -> str:
    text = re.sub(r"<think>[\s\S]*?</think>", "", text or "").strip()
    try:
        d = json.loads(text); a = str(d.get("answer", "")).strip().upper()
        if a in {"A","B","C","D"}: return a
    except Exception: pass
    m = _LETTER.search(text)
    return m.group(1).upper() if m else ""


def run_one(llm: LLMClient, s: dict, config: str, skills: dict[str, str]) -> dict:
    task = s["metadata"]["task"]
    if config == "raw":
        skill_id, skill_body = None, None
    elif config == "oracle_skill":
        sid, _ = PICKS.get(task, (None, None))
        skill_id, skill_body = sid, (skills.get(sid) if sid else None)
    else:
        raise ValueError(config)
    user = build_user(s, skill_body)
    t0 = time.time()
    try:
        text = llm.chat(SYSTEM_RAW, user, max_tokens=1024)
    except Exception as e:  # noqa: BLE001
        return {"id": s["id"], "task": task, "gold": s["answer"],
                "config": config, "skill_id": skill_id,
                "pred": "", "ok": False, "err": str(e)[:200],
                "elapsed": time.time()-t0}
    pred = parse_letter(text)
    return {"id": s["id"], "task": task, "gold": s["answer"],
            "config": config, "skill_id": skill_id,
            "pred": pred, "ok": pred == s["answer"], "elapsed": time.time()-t0}


def run_config(llm: LLMClient, samples: list, config: str, skills: dict,
               out_path: Path, workers: int) -> None:
    done = set()
    if out_path.exists():
        for ln in open(out_path, encoding="utf-8"):
            try: done.add(json.loads(ln)["id"])
            except Exception: pass
    pending = [s for s in samples if s["id"] not in done]
    logger.info(f"  config={config} resume done={len(done)} pending={len(pending)}")
    if not pending: return
    f = open(out_path, "a", encoding="utf-8")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(run_one, llm, s, config, skills): s for s in pending}
        n_done = 0
        for fut in as_completed(futs):
            r = fut.result()
            f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
            n_done += 1
            if n_done % 200 == 0:
                logger.info(f"    {config}: {n_done}/{len(pending)} ({time.time()-t0:.1f}s)")
    f.close()
    logger.info(f"  config={config} done in {time.time()-t0:.1f}s")


def summarize(rows: list[dict]) -> dict:
    per_task = defaultdict(lambda: {"correct": 0, "total": 0})
    for r in rows:
        per_task[r["task"]]["total"] += 1
        if r["ok"]: per_task[r["task"]]["correct"] += 1
    for t, c in per_task.items():
        c["accuracy"] = round(c["correct"]/c["total"], 4) if c["total"] else 0.0
    total = sum(c["total"] for c in per_task.values())
    correct = sum(c["correct"] for c in per_task.values())
    return {"per_task": dict(per_task),
            "overall": {"total": total, "correct": correct,
                        "accuracy": round(correct/total, 4) if total else 0.0}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out_dir", default="results_full_oracle")
    ap.add_argument("--configs", nargs="+", default=["raw", "oracle_skill"])
    args = ap.parse_args()

    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.environ.get("TOM_API_KEY")
    model = os.environ.get("TOM_MODEL", "qwen-plus")
    if not api_key: raise SystemExit("ERROR: set TOM_API_KEY")
    llm = LLMClient(api_base=api_base, api_key=api_key, model=model,
                    temperature=0.0, max_tokens=1024, timeout=180.0, max_retries=3)

    samples = [s for s in load_tombench() if s["metadata"].get("task") in MAIN_8]
    logger.info(f"pool: {len(samples)} samples (full ToMBench main-8)")

    skills = load_skills()
    logger.info(f"loaded {len(skills)} skills: {list(skills.keys())}")

    out_dir = Path(args.out_dir); out_dir.mkdir(exist_ok=True)
    summary = {}
    for config in args.configs:
        logger.info(f"\n========== config = {config} ==========")
        out_path = out_dir / f"full_{config}_results.jsonl"
        run_config(llm, samples, config, skills, out_path, args.workers)
        # load and summarize
        rows = []
        for ln in open(out_path, encoding="utf-8"):
            try: rows.append(json.loads(ln))
            except Exception: pass
        summary[config] = summarize(rows)
    (out_dir / "full_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    # Print
    print(f"\n{'='*80}\nFULL ToMBench main-8 — qwen-plus, temp=0, 1-shot per sample\n{'='*80}")
    tasks = sorted({t for cfg_s in summary.values() for t in cfg_s["per_task"]})
    header = f"{'task':<32}" + "".join(f"{c:<18}" for c in args.configs)
    print(header)
    for t in tasks:
        row = f"{t:<32}"
        for c in args.configs:
            cell = summary[c]["per_task"].get(t, {})
            row += f"{cell.get('correct',0):>3}/{cell.get('total',0):<4} ({cell.get('accuracy',0):.3f})  "
        print(row)
    print(f"{'-'*80}")
    row = f"{'OVERALL':<32}"
    for c in args.configs:
        ov = summary[c]["overall"]
        row += f"{ov['correct']:>3}/{ov['total']:<4} ({ov['accuracy']:.3f})  "
    print(row)
    if "raw" in summary and "oracle_skill" in summary:
        raw = summary["raw"]["overall"]["accuracy"]
        sk = summary["oracle_skill"]["overall"]["accuracy"]
        print(f"\nlift: {sk - raw:+.4f} ({(sk-raw)*100:+.2f} pp)")


if __name__ == "__main__":
    main()
