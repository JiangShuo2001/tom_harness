"""Case-level cross-model analysis on the per-model experiment outputs.

Loads:   data/results/per_model/{ToMBench,CogToM}__{gpt-5_4-mini,glm-5}.json
Joins on global_idx, then computes:
  • Asymmetric outcomes: gpt-only-fixed vs glm-only-fixed buckets
  • Both-still-wrong buckets (hardest residual)
  • Reasoning-style heuristics: response length, "Step"/"LAYER"/"PATTERN" markers,
    answer-letter location, repeat-skill-step usage.
  • For 4–6 high-impact buckets, dump representative case pairs
    (story / question / options / two model responses).

Output: data/results/per_model/CASE_ANALYSIS.md and case_analysis_raw.json
"""
import json
import os
import re
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RES = os.path.join(DATA, "results", "per_model")
DATASETS = ["ToMBench", "CogToM"]
MODELS = ["gpt-5.4-mini", "glm-5"]

STEP_MARKERS = re.compile(r"\b(STEP\s*\d|LAYER\s*\d|Step\s*\d|Layer\s*\d|"
                           r"PATTERN\s*[A-D]|Pattern\s*[A-D]|"
                           r"CHECK\s*\d|SPECIAL\s*CASE|GUARDRAIL)\b")


def load_split(ds, model):
    p = os.path.join(RES, f"{ds}__{model.replace('.','_')}.json")
    with open(p) as f:
        return json.load(f)


def load_source(ds):
    out = {}
    with open(os.path.join(DATA, f"{ds}.jsonl")) as f:
        for line in f:
            r = json.loads(line)
            out[r["global_idx"]] = r
    return out


# ───────────────────── Reasoning-style heuristics ─────────────────────
def style_metrics(rows, src):
    chars = []
    step_counts = []
    n_followed = 0  # has at least one explicit STEP/LAYER/CHECK marker
    n_response_too_short = 0  # < 50 chars (often raw letter only)
    n_response_huge = 0  # > 4000 chars
    for r in rows:
        resp = r.get("answer_response") or ""
        L = len(resp)
        chars.append(L)
        markers = STEP_MARKERS.findall(resp)
        step_counts.append(len(markers))
        if len(markers) >= 2:
            n_followed += 1
        if L < 50:
            n_response_too_short += 1
        if L > 4000:
            n_response_huge += 1
    n = max(1, len(rows))
    return {
        "n":              len(rows),
        "mean_resp_len":  sum(chars) / n,
        "median_resp":    sorted(chars)[n // 2],
        "mean_steps":     sum(step_counts) / n,
        "pct_followed":   n_followed / n,
        "pct_too_short":  n_response_too_short / n,
        "pct_huge":       n_response_huge / n,
    }


# ───────────────────── Cross-model joining ─────────────────────
def join_cases(ds):
    """Returns {global_idx: {model: row}} restricted to cases where BOTH
    models were originally wrong on this case (intersection of per-model
    error sets), so the two-side comparison is well-defined."""
    splits = {m: {r["global_idx"]: r for r in load_split(ds, m)["rows"]}
              for m in MODELS}
    common = set(splits[MODELS[0]]) & set(splits[MODELS[1]])
    out = {}
    for gid in common:
        out[gid] = {m: splits[m][gid] for m in MODELS}
    return out, splits


def asym_buckets(joined):
    """Return three buckets keyed by global_idx:
        gpt_only_fixed   : gpt fixed, glm did not
        glm_only_fixed   : glm fixed, gpt did not
        both_unfixed     : both still wrong
        both_fixed       : both fixed
    """
    b = defaultdict(list)
    for gid, per in joined.items():
        gf = per["gpt-5.4-mini"]["fixed"]
        mf = per["glm-5"]["fixed"]
        if gf and not mf:
            b["gpt_only_fixed"].append(gid)
        elif mf and not gf:
            b["glm_only_fixed"].append(gid)
        elif gf and mf:
            b["both_fixed"].append(gid)
        else:
            b["both_unfixed"].append(gid)
    return b


# ───────────────────── Skill-conditioned slice ─────────────────────
def by_skill(rows):
    out = defaultdict(list)
    for r in rows:
        out[r["skill"]].append(r)
    return out


# ───────────────────── Markdown rendering ─────────────────────
def fmt_pct(num, den):
    return f"{num}/{den} ({num/max(1,den):.0%})"


def render_top_buckets(joined, src, top_k=5):
    """Identify the (task_type, asymmetry) buckets with most cases, dump
    sample reasoning for case studies."""
    asym = asym_buckets(joined)
    md = []
    md.append(f"\n### Asymmetric & shared outcomes  "
              f"(over {len(joined)} cases where both models were originally wrong)\n")
    md.append("| Outcome | Count | % |")
    md.append("|---|---:|---:|")
    for k in ("both_fixed", "gpt_only_fixed", "glm_only_fixed", "both_unfixed"):
        md.append(f"| {k} | {len(asym[k])} | {len(asym[k])/max(1,len(joined)):.1%} |")

    # Per task_type for the most informative bucket
    for bk in ("gpt_only_fixed", "glm_only_fixed", "both_unfixed"):
        per_tt = Counter(src[gid]["task_type"] for gid in asym[bk])
        md.append(f"\n#### `{bk}` — top task_types\n")
        md.append("| task_type | count |")
        md.append("|---|---:|")
        for tt, c in per_tt.most_common(top_k):
            md.append(f"| {tt} | {c} |")
    return md, asym


def render_case_study(gid, joined, src, max_len=900):
    item = src[gid]
    g = joined[gid]["gpt-5.4-mini"]
    m = joined[gid]["glm-5"]
    out = []
    out.append(f"#### `{gid}` — `{item['task_type']}` (gold = **{item['gold_answer']}**)\n")
    out.append(f"*Skill picked by router: `{g['skill']}` (same for both)*\n")
    out.append("**Story.** " + item["story"].replace("\n", " ") + "\n")
    out.append("**Question.** " + item["question"].replace("\n", " "))
    out.append("**Options.**")
    for l, o in zip(item["labels"], item["options"]):
        out.append(f"- **{l}.** {o}")
    out.append("")
    for label, m_row in (("gpt-5.4-mini", g), ("glm-5", m)):
        resp = (m_row.get("answer_response") or "").strip()
        if len(resp) > max_len:
            resp = resp[:max_len] + " …[truncated]"
        flag = "✓ FIXED" if m_row["fixed"] else "✗ wrong"
        out.append(f"**`{label}` answered = `{m_row['pred']}`  {flag}**\n")
        out.append("```\n" + resp + "\n```\n")
    out.append("---\n")
    return out


# ───────────────────── Main ─────────────────────
def main():
    full_md = ["# Case-level cross-model analysis\n",
               "Two answerer models on the same router (`gpt-5.4-mini`).",
               "Joined on `global_idx` per dataset.\n"]

    raw_dump = {}

    for ds in DATASETS:
        full_md.append(f"\n# Dataset: `{ds}`\n")
        joined, splits = join_cases(ds)
        src = load_source(ds)

        # Headline numbers per split
        for m in MODELS:
            rows = splits[m]
            n = len(rows); fx = sum(1 for r in rows.values() if r["fixed"])
            full_md.append(f"- `{m}`: {fx}/{n} fixed = **{fx/max(1,n):.1%}**")

        # Ensemble (either-fixed) on the joint set
        ens_n = len(joined)
        ens_fx = sum(
            1 for gid in joined
            if joined[gid]["gpt-5.4-mini"]["fixed"] or joined[gid]["glm-5"]["fixed"]
        )
        full_md.append(
            f"- Joint cases (both originally wrong): **{ens_n}**, "
            f"either-fixed = {ens_fx}/{ens_n} = **{ens_fx/max(1,ens_n):.1%}** "
            f"(ensemble upper bound)\n"
        )

        # Truncation diagnostic (key indicator after the max_tokens bump)
        full_md.append("\n## Truncation diagnostic (was the answer-format-guard respected?)\n")
        full_md.append("| Model | n | starts with `ANSWER:` | has `FINAL ANSWER:` | "
                       "pred=None | mean chars | >6000 chars |")
        full_md.append("|---|---:|---:|---:|---:|---:|---:|")
        for m in MODELS:
            rows = list(splits[m].values())
            n = len(rows)
            first_ok = sum(1 for r in rows
                           if (r.get("answer_response") or "").lstrip().lower().startswith("answer:"))
            final_ok = sum(1 for r in rows
                           if "final answer" in (r.get("answer_response") or "").lower())
            none_pred = sum(1 for r in rows if r["pred"] is None)
            mean_len = sum(len(r.get("answer_response") or "") for r in rows) / max(1, n)
            huge = sum(1 for r in rows if len(r.get("answer_response") or "") > 6000)
            full_md.append(
                f"| `{m}` | {n} | {first_ok}/{n} ({first_ok/max(1,n):.0%}) | "
                f"{final_ok}/{n} ({final_ok/max(1,n):.0%}) | "
                f"{none_pred}/{n} ({none_pred/max(1,n):.0%}) | "
                f"{mean_len:.0f} | {huge}/{n} ({huge/max(1,n):.0%}) |"
            )

        # Reasoning-style metrics
        full_md.append("\n## Reasoning-style heuristics (on the joint set)\n")
        full_md.append("| Model | Mean response chars | Median | Mean #step-markers | "
                       "% with ≥2 step markers | % too-short (<50) | % huge (>4000) |")
        full_md.append("|---|---:|---:|---:|---:|---:|---:|")
        for m in MODELS:
            sample = [splits[m][gid] for gid in joined]
            s = style_metrics(sample, src)
            full_md.append(
                f"| `{m}` | {s['mean_resp_len']:.0f} | {s['median_resp']} | "
                f"{s['mean_steps']:.2f} | {s['pct_followed']:.1%} | "
                f"{s['pct_too_short']:.1%} | {s['pct_huge']:.1%} |"
            )

        # Asymmetric buckets + top task types
        bucket_md, asym = render_top_buckets(joined, src)
        full_md.extend(bucket_md)
        raw_dump[ds] = {bk: list(asym[bk]) for bk in asym}

        # Skill-conditioned breakdown
        full_md.append("\n## Per-skill fix rate on the joint set\n")
        full_md.append("| Skill | n | gpt fix | gpt% | glm fix | glm% | gap (gpt-glm) |")
        full_md.append("|---|---:|---:|---:|---:|---:|---:|")
        skills = defaultdict(lambda: {"n": 0, "gpt": 0, "glm": 0})
        for gid in joined:
            sk = joined[gid]["gpt-5.4-mini"]["skill"]
            skills[sk]["n"] += 1
            skills[sk]["gpt"] += int(joined[gid]["gpt-5.4-mini"]["fixed"])
            skills[sk]["glm"] += int(joined[gid]["glm-5"]["fixed"])
        for sk, st in sorted(skills.items(), key=lambda x: -x[1]["n"]):
            n = st["n"]
            gp = st["gpt"] / n
            mp = st["glm"] / n
            full_md.append(f"| {sk} | {n} | {st['gpt']} | {gp:.0%} | "
                           f"{st['glm']} | {mp:.0%} | {gp-mp:+.0%} |")

        # ───────── Case studies ─────────
        full_md.append("\n## Case studies\n")

        # 1) gpt_only_fixed: pick top-2 task_types and 1 case each
        per_tt = Counter(src[gid]["task_type"] for gid in asym["gpt_only_fixed"])
        full_md.append("### A) gpt-5.4-mini fixed, glm-5 still wrong\n")
        for tt, _ in per_tt.most_common(3):
            example_gid = next(gid for gid in asym["gpt_only_fixed"]
                               if src[gid]["task_type"] == tt)
            full_md.extend(render_case_study(example_gid, joined, src))

        # 2) glm_only_fixed
        per_tt = Counter(src[gid]["task_type"] for gid in asym["glm_only_fixed"])
        full_md.append("### B) glm-5 fixed, gpt-5.4-mini still wrong\n")
        for tt, _ in per_tt.most_common(3):
            example_gid = next(gid for gid in asym["glm_only_fixed"]
                               if src[gid]["task_type"] == tt)
            full_md.extend(render_case_study(example_gid, joined, src))

        # 3) both_unfixed: pick top-3 task_types, 1 case each
        per_tt = Counter(src[gid]["task_type"] for gid in asym["both_unfixed"])
        full_md.append("### C) Both models still wrong (hardest residual)\n")
        for tt, _ in per_tt.most_common(3):
            example_gid = next(gid for gid in asym["both_unfixed"]
                               if src[gid]["task_type"] == tt)
            full_md.extend(render_case_study(example_gid, joined, src))

    out_md = os.path.join(RES, "CASE_ANALYSIS.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(full_md) + "\n")
    print("Saved", out_md)

    out_json = os.path.join(RES, "case_analysis_raw.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(raw_dump, f, ensure_ascii=False, indent=2)
    print("Saved", out_json)


if __name__ == "__main__":
    main()
