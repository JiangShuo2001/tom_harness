"""Test alternative skill picks on full ToMBench (target tasks only).

Given that current oracle_skill picks gave +1.66pp overall but Faux-pas
REGRESSED -2.1pp on full benchmark, test alternative picks for the
weak/regressed tasks. Only run each candidate on its target-task subset.

Candidates:
  Faux-pas (560 samples, raw 73.9%, current pick 71.8%):
    - cs2_S1_FauxPas        (topical match, 160=0.70)
    - cs1_skill11           (160=0.80, tied with current)
    - cs1_skill2            (160=0.80, tied with current)
  Persuasion (100 samples, raw 61.0%, current pick 69.0%):
    - cs2_S12_CommitmentPrio (160=0.70, tied with current)
  Scalar (200 samples, raw 47.0%, current pick 55.0%):
    - cs2_S2_Scalar          (topical, 160=0.50)
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
logger = logging.getLogger("alt"); logger.setLevel(logging.INFO)


# (skill_id, task_name, kind)
CANDIDATES = [
    ("cs2_S1_FauxPas",       "Faux-pas Recognition Test", "cs2"),
    ("cs1_skill11",          "Faux-pas Recognition Test", "cs1"),
    ("cs1_skill2",           "Faux-pas Recognition Test", "cs1"),
    ("cs2_S12_CommitmentPrio","Persuasion Story Task",    "cs2"),
    ("cs2_S2_Scalar",        "Scalar Implicature Test",   "cs2"),
]


def load_skills() -> dict[str, str]:
    out: dict[str, str] = {}
    base1 = Path("/workspace/symbolictom_report/skill_set1")
    cs1_ids = [(sid, sid.replace("cs1_", "")) for sid, _, k in CANDIDATES if k == "cs1"]
    for sid, n in cs1_ids:
        out[sid] = (base1 / n / "SKILL.md").read_text(encoding="utf-8")
    cs2_ids = [(sid, sid.replace("cs2_", "")) for sid, _, k in CANDIDATES if k == "cs2"]
    if cs2_ids:
        spec = importlib.util.spec_from_file_location("set2_skills_module",
            "/workspace/symbolictom_report/skill_set2/skill_v2/skills.py")
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)  # type: ignore
        for sid, key in cs2_ids:
            out[sid] = mod.SKILLS[key]
    return out


SYSTEM_RAW = (
    "You are a reading comprehension assistant. Read the story and answer "
    'the multiple-choice question. Reply with ONLY a JSON object: '
    '{"answer": "A" | "B" | "C" | "D"}'
)


def build_user(s, skill_body):
    opts = "\n".join(f"{k}. {v}" for k, v in s["options"].items() if v)
    return (
        f"## Reasoning Skill (apply before answering)\n{skill_body}\n\n"
        f"## Story\n{s['story']}\n\n"
        f"## Question\n{s['question']}\n\n"
        f"## Options\n{opts}\n\n"
        '## Answer\nAfter applying the skill above, reply with ONLY a JSON object: {"answer": "A"|"B"|"C"|"D"}'
    )


_LETTER = re.compile(r'"answer"\s*:\s*"([A-D])"')


def parse_letter(text: str) -> str:
    text = re.sub(r"<think>[\s\S]*?</think>", "", text or "").strip()
    try:
        d = json.loads(text); a = str(d.get("answer", "")).strip().upper()
        if a in {"A","B","C","D"}: return a
    except Exception: pass
    m = _LETTER.search(text)
    return m.group(1).upper() if m else ""


def run_one(llm: LLMClient, s: dict, skill_id: str, skill_body: str) -> dict:
    user = build_user(s, skill_body)
    t0 = time.time()
    try:
        text = llm.chat(SYSTEM_RAW, user, max_tokens=1024)
    except Exception as e:  # noqa: BLE001
        return {"id": s["id"], "task": s["metadata"]["task"], "gold": s["answer"],
                "skill_id": skill_id, "pred": "", "ok": False,
                "err": str(e)[:200], "elapsed": time.time()-t0}
    pred = parse_letter(text)
    return {"id": s["id"], "task": s["metadata"]["task"], "gold": s["answer"],
            "skill_id": skill_id, "pred": pred, "ok": pred == s["answer"],
            "elapsed": time.time()-t0}


def run_candidate(llm: LLMClient, samples: list, skill_id: str, skill_body: str,
                  out_path: Path, workers: int) -> None:
    done = set()
    if out_path.exists():
        for ln in open(out_path, encoding="utf-8"):
            try: done.add(json.loads(ln)["id"])
            except Exception: pass
    pending = [s for s in samples if s["id"] not in done]
    if not pending: return
    f = open(out_path, "a", encoding="utf-8")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(run_one, llm, s, skill_id, skill_body): s for s in pending}
        n_done = 0
        for fut in as_completed(futs):
            r = fut.result()
            f.write(json.dumps(r, ensure_ascii=False)+"\n"); f.flush()
            n_done += 1
    f.close()
    logger.info(f"  {skill_id} on {len(pending)} samples done in {time.time()-t0:.1f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out_dir", default="results_alt_picks")
    args = ap.parse_args()

    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.environ.get("TOM_API_KEY")
    model = os.environ.get("TOM_MODEL", "qwen-plus")
    if not api_key: raise SystemExit("ERROR: set TOM_API_KEY")
    llm = LLMClient(api_base=api_base, api_key=api_key, model=model,
                    temperature=0.0, max_tokens=1024, timeout=180.0, max_retries=3)

    skills = load_skills()
    samples_all = load_tombench()
    samples_by_task = defaultdict(list)
    for s in samples_all:
        samples_by_task[s["metadata"].get("task", "")].append(s)

    out_dir = Path(args.out_dir); out_dir.mkdir(exist_ok=True)
    for skill_id, task_name, _ in CANDIDATES:
        target = samples_by_task[task_name]
        out_path = out_dir / f"alt_{skill_id}__{task_name.replace(' ','_')}.jsonl"
        logger.info(f"\n--- {skill_id} on {task_name} ({len(target)} samples) ---")
        run_candidate(llm, target, skill_id, skills[skill_id], out_path, args.workers)

    # Load raw and current oracle for comparison
    raw_rows = [json.loads(ln) for ln in open("results_full_oracle/full_raw_results.jsonl", encoding="utf-8") if ln.strip()]
    cur_rows = [json.loads(ln) for ln in open("results_full_oracle/full_oracle_skill_results.jsonl", encoding="utf-8") if ln.strip()]
    raw_acc_per_task = defaultdict(lambda: {"correct": 0, "total": 0})
    cur_acc_per_task = defaultdict(lambda: {"correct": 0, "total": 0})
    for r in raw_rows:
        raw_acc_per_task[r["task"]]["total"] += 1
        if r["ok"]: raw_acc_per_task[r["task"]]["correct"] += 1
    for r in cur_rows:
        cur_acc_per_task[r["task"]]["total"] += 1
        if r["ok"]: cur_acc_per_task[r["task"]]["correct"] += 1

    # Compute candidate accs
    print(f"\n{'='*80}\nALT PICKS — full ToMBench, qwen-plus, temp=0\n{'='*80}")
    print(f"{'task':<32} {'pick':<28} {'acc':<8} {'vs raw':<10} {'vs current':<10}")
    print(f"{'-'*88}")
    cand_results = {}
    for skill_id, task_name, _ in CANDIDATES:
        out_path = out_dir / f"alt_{skill_id}__{task_name.replace(' ','_')}.jsonl"
        rows = [json.loads(ln) for ln in open(out_path, encoding="utf-8") if ln.strip()]
        n_correct = sum(1 for r in rows if r["ok"])
        n_total = len(rows)
        acc = n_correct / n_total if n_total else 0.0
        raw = raw_acc_per_task[task_name]
        raw_acc = raw["correct"] / raw["total"] if raw["total"] else 0.0
        cur = cur_acc_per_task[task_name]
        cur_acc = cur["correct"] / cur["total"] if cur["total"] else 0.0
        cand_results[(skill_id, task_name)] = (acc, n_correct, n_total)
        print(f"{task_name:<32} {skill_id:<28} {acc:.3f}    "
              f"({acc-raw_acc:+.3f})    ({acc-cur_acc:+.3f})")

    # Build best new oracle: for each task, pick whichever (current vs candidates) gave highest acc
    print(f"\n{'='*80}\nNEW BEST PICKS\n{'='*80}")
    new_picks_acc = {}
    for task in raw_acc_per_task:
        cur = cur_acc_per_task[task]
        cur_acc = cur["correct"] / cur["total"] if cur["total"] else 0.0
        raw = raw_acc_per_task[task]
        raw_acc = raw["correct"] / raw["total"] if raw["total"] else 0.0
        candidates_for_task = [(sid, *cand_results[(sid, task)])
                               for (sid, t), _ in cand_results.items() if t == task]
        # also include raw and current
        options = [("raw", raw["correct"], raw["total"]), ("current_pick", cur["correct"], cur["total"])]
        for sid, c, t in [(sid, c, n) for (sid, t_), (acc_, c, n) in cand_results.items() if t_ == task for sid in [sid]]:
            options.append((sid, c, t))
        # dedup by name
        seen = set(); options_dedup = []
        for o in options:
            if o[0] not in seen: seen.add(o[0]); options_dedup.append(o)
        best = max(options_dedup, key=lambda o: o[1]/o[2] if o[2] else 0)
        new_picks_acc[task] = best
        best_acc = best[1]/best[2]
        print(f"  {task:<32} pick={best[0]:<28} {best[1]}/{best[2]} = {best_acc:.3f}  "
              f"(raw {raw_acc:.3f}, cur {cur_acc:.3f})")

    # Sum
    total_correct = sum(b[1] for b in new_picks_acc.values())
    total_total = sum(b[2] for b in new_picks_acc.values())
    total_correct_raw = sum(c["correct"] for c in raw_acc_per_task.values())
    total_total_raw = sum(c["total"] for c in raw_acc_per_task.values())
    total_correct_cur = sum(c["correct"] for c in cur_acc_per_task.values())
    new_acc = total_correct / total_total
    raw_acc = total_correct_raw / total_total_raw
    cur_acc = total_correct_cur / total_total_raw

    print(f"\nOVERALL:")
    print(f"  raw                  : {total_correct_raw}/{total_total_raw} = {raw_acc:.4f}")
    print(f"  current oracle pick  : {total_correct_cur}/{total_total_raw} = {cur_acc:.4f}")
    print(f"  new best pick (alt)  : {total_correct}/{total_total} = {new_acc:.4f}")
    print(f"  new vs raw:          {(new_acc-raw_acc)*100:+.2f} pp")
    print(f"  new vs current:      {(new_acc-cur_acc)*100:+.2f} pp")


if __name__ == "__main__":
    main()
