"""Self-consistency on Persuasion + Faux-pas tasks.

For each sample in those 2 tasks (40 total), run the per-task best skill
n=5 times at temperature=0.4, majority-vote.

Best skills (from matrix_summary.json):
  Persuasion Story Task         -> cs2_S11_BeliefEmotion (oracle 0.70)
  Faux-pas Recognition Test     -> cs1_skill10           (oracle 0.80)

Cost: 40 samples × 5 votes = 200 LLM calls.
"""
from __future__ import annotations
import argparse, json, os, random, re, sys, time, importlib.util
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
_ext_repo = os.environ.get("SYMBOLICTOM_REPRO_PATH", str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, _ext_repo)

from benchmark_adapters import load_tombench  # type: ignore  # noqa: E402
from tom_harness import LLMClient  # noqa: E402

TARGET_TASKS = {"Persuasion Story Task", "Faux-pas Recognition Test"}
MAIN_8 = {
    "Unexpected Outcome Test", "Scalar Implicature Test", "Persuasion Story Task",
    "False Belief Task", "Ambiguous Story Task", "Hinting Task Test",
    "Strange Story Task", "Faux-pas Recognition Test",
}


def stratified(samples, per_task=20, seed=42):
    rng = random.Random(seed)
    buckets = defaultdict(list)
    for s in samples:
        if s["metadata"].get("task", "") in MAIN_8:
            buckets[s["metadata"]["task"]].append(s)
    out = []
    for t in sorted(buckets):
        b = buckets[t]; rng.shuffle(b); out.extend(b[:per_task])
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


def load_set1_skill(name: str) -> str:
    _skill_root = Path(os.environ.get("SKILL_PACK_ROOT",
                       str(Path(__file__).resolve().parent.parent / "tom_harness/plugins/external_skill_pack/data")))
    return (_skill_root / "skill_set1" / name / "SKILL.md").read_text(encoding="utf-8")


def load_set2_skill(key: str) -> str:
    _skill_root = Path(os.environ.get("SKILL_PACK_ROOT",
                       str(Path(__file__).resolve().parent.parent / "tom_harness/plugins/external_skill_pack/data")))
    skills_path = str(_skill_root / "skill_set2" / "skills.py")
    spec = importlib.util.spec_from_file_location("set2_skills_module", skills_path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)  # type: ignore
    return mod.SKILLS[key]


def vote_one(llm: LLMClient, s: dict, skill_body: str, n: int) -> dict:
    user = build_user(s, skill_body)
    votes = []
    elapsed = 0.0
    for _ in range(n):
        t0 = time.time()
        try:
            text = llm.chat(SYSTEM_RAW, user, max_tokens=1024)
            v = parse_letter(text)
            if v: votes.append(v)
        except Exception:  # noqa: BLE001
            pass
        elapsed += time.time() - t0
    winner = Counter(votes).most_common(1)[0][0] if votes else ""
    return {"id": s["id"], "task": s["metadata"]["task"], "gold": s["answer"],
            "votes": votes, "pred": winner, "ok": winner == s["answer"],
            "elapsed": elapsed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per_task", type=int, default=20)
    ap.add_argument("--n", type=int, default=5, help="self-consistency samples per question")
    ap.add_argument("--temperature", type=float, default=0.4)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out_dir", default="results_selfconsistency")
    args = ap.parse_args()

    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.environ.get("TOM_API_KEY")
    model = os.environ.get("TOM_MODEL", "qwen-plus")
    if not api_key: raise SystemExit("ERROR: set TOM_API_KEY")
    llm = LLMClient(api_base=api_base, api_key=api_key, model=model,
                    temperature=args.temperature, max_tokens=1024,
                    timeout=180.0, max_retries=3)

    skills = {
        "Persuasion Story Task": ("cs2_S11_BeliefEmotion", load_set2_skill("S11_BeliefEmotion")),
        "Faux-pas Recognition Test": ("cs1_skill10", load_set1_skill("skill10")),
    }

    samples = load_tombench()
    pool = stratified(samples, args.per_task)
    target = [s for s in pool if s["metadata"]["task"] in TARGET_TASKS]
    print(f"target samples: {len(target)} (Persuasion+Faux-pas)")

    out_dir = Path(args.out_dir); out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"sc_n{args.n}_t{args.temperature}.jsonl"
    done = set()
    if out_path.exists():
        for ln in open(out_path, encoding="utf-8"):
            try: done.add(json.loads(ln)["id"])
            except Exception: pass
    pending = [s for s in target if s["id"] not in done]
    print(f"resume: done={len(done)} pending={len(pending)}")

    results = []
    if out_path.exists():
        for ln in open(out_path, encoding="utf-8"):
            try: results.append(json.loads(ln))
            except Exception: pass

    f = open(out_path, "a", encoding="utf-8")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {}
        for s in pending:
            sid, body = skills[s["metadata"]["task"]]
            futs[ex.submit(vote_one, llm, s, body, args.n)] = (s, sid)
        for fut in as_completed(futs):
            r = fut.result(); f.write(json.dumps(r, ensure_ascii=False)+"\n"); f.flush()
            results.append(r)
    f.close()
    print(f"done in {time.time()-t0:.1f}s")

    # Per-task acc
    per_task = defaultdict(lambda: {"correct": 0, "total": 0})
    for r in results:
        per_task[r["task"]]["total"] += 1
        if r["ok"]: per_task[r["task"]]["correct"] += 1
    for t, c in per_task.items():
        c["accuracy"] = round(c["correct"]/c["total"], 4) if c["total"] else 0.0

    # Compare to oracle single-shot
    oracle_persuasion = 0.70  # cs2_S11_BeliefEmotion @ temp=0
    oracle_fauxpas    = 0.80  # cs1_skill10           @ temp=0

    print(f"\n{'='*70}\nSELF-CONSISTENCY n={args.n} t={args.temperature}\n{'='*70}")
    for t in sorted(per_task):
        c = per_task[t]
        baseline = oracle_persuasion if t == "Persuasion Story Task" else oracle_fauxpas
        delta = c["accuracy"] - baseline
        print(f"  {t:<32} {c['correct']:>2}/{c['total']:<2} = {c['accuracy']:.2f}  "
              f"(oracle@temp0: {baseline:.2f}, Δ={delta:+.2f})")

    summary = {"per_task_sc": dict(per_task), "n": args.n, "temperature": args.temperature,
               "oracle_baseline": {"Persuasion Story Task": oracle_persuasion,
                                   "Faux-pas Recognition Test": oracle_fauxpas}}
    (out_dir / "selfcons_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
