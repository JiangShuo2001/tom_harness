from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("The skills_v5 generator requires the `openai` package.") from exc

ROOT = Path(__file__).resolve().parent
PROMPTS = ROOT / "prompts"
BLUEPRINT_PATH = ROOT / "skill_blueprint.json"
FRAMEWORK_TEXT_PATH = ROOT / "social_mind_skill_framework_en.md"
DEFAULT_OUT = ROOT / "generated"
FROZEN_OUT = ROOT / "frozen"
DEFAULT_MODEL = os.environ.get("SKILL_V5_MODEL", "gpt-5.5")
DEFAULT_RUN_TIMEOUT = int(os.environ.get("SKILL_V5_RUN_TIMEOUT", os.environ.get("SKILL_V5_TIMEOUT", "240")))
DEFAULT_MAX_RETRIES = int(os.environ.get("SKILL_V5_MAX_RETRIES", "1"))
DEFAULT_TEMPERATURE = float(os.environ.get("SKILL_V5_TEMPERATURE", "0"))
DEFAULT_RUN_MAX_TOKENS = int(os.environ.get("SKILL_V5_RUN_MAX_TOKENS", os.environ.get("SKILL_V5_MAX_TOKENS", "16384")))
AUDIT_CHUNK_SIZE = int(os.environ.get("SKILL_V5_AUDIT_CHUNK_SIZE", "16"))
SUPPORTED_PATCH_PATHS = {
    "use_when",
    "do_not_use_when",
    "trigger_checklist",
    "workflow",
    "boundary_exit_rule",
    "references.hard_boundary",
    "references.shortcut_to_avoid",
    "references.common_failure_modes",
    "references.boundary_stress_test",
    "references.generalization_note",
}
SUPPORTED_PATCH_OPS = {"append", "extend", "set", "merge", "remove"}


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def load_json(path: Path) -> Any:
    return json.loads(load_text(path))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def fill_template(template: str, **replacements: str) -> str:
    out = template
    for key, value in replacements.items():
        out = out.replace(f"{{{{{key}}}}}", value)
    return out


def compact_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def chunked(items: list[Any], size: int) -> list[list[Any]]:
    size = max(1, size)
    return [items[i:i + size] for i in range(0, len(items), size)]


def _env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return default


def normalize_unit_id(value: str) -> str:
    token = str(value or "").strip().lower().replace("_", "-").replace(" ", "")
    m = re.fullmatch(r"(micro|macro)-?(\d{1,3})", token)
    if not m:
        return ""
    return f"{m.group(1)}-{int(m.group(2)):02d}"


def unit_kind(unit_id: str) -> str:
    unit_id = normalize_unit_id(unit_id)
    if unit_id.startswith("micro-"):
        return "micro"
    if unit_id.startswith("macro-"):
        return "macro"
    return ""


def unit_number(unit_id: str) -> int:
    token = normalize_unit_id(unit_id)
    m = re.fullmatch(r"(micro|macro)-(\d{2})", token)
    if not m:
        return 10_000
    return int(m.group(2)) if m.group(1) == "micro" else 1_000 + int(m.group(2))


def sort_units(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(units, key=lambda item: unit_number(item.get("id", "")))


def all_units(registry: dict[str, Any]) -> list[dict[str, Any]]:
    return sort_units(list(registry.get("micro_units", [])) + list(registry.get("macro_units", [])))


def registry_lookup(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {normalize_unit_id(item.get("id", "")): item for item in all_units(registry)}


def strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def extract_json(text: str) -> Any:
    cleaned = strip_code_fences(text)
    candidates = [cleaned]
    for opener, closer in (("{", "}"), ("[", "]")):
        first = cleaned.find(opener)
        last = cleaned.rfind(closer)
        if first != -1 and last != -1 and last > first:
            candidates.append(cleaned[first:last + 1])
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError(f"Could not parse JSON from model response:\n{text}")


class LLMClient:
    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str,
        timeout: int = DEFAULT_RUN_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        temperature: float = DEFAULT_TEMPERATURE,
        reasoning_effort: str = "",
        default_max_tokens: int = DEFAULT_RUN_MAX_TOKENS,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.temperature = temperature
        self.reasoning_effort = reasoning_effort.strip()
        self.default_max_tokens = default_max_tokens
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat(self, system: str, user: str, max_tokens: int | None = None) -> str:
        max_tokens = self.default_max_tokens if max_tokens is None else max_tokens
        last_err: str | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=self.temperature,
                    max_completion_tokens=max_tokens,
                    reasoning_effort=self.reasoning_effort or None,
                )
                return self._extract_chat_content(response)
            except Exception as exc:  # pragma: no cover
                last_err = f"{type(exc).__name__}: {exc}"
            if attempt < self.max_retries:
                time.sleep(min(2 ** (attempt - 1), 8))
        raise RuntimeError(f"LLM request failed after retries: {last_err}")

    @staticmethod
    def _extract_chat_content(data: Any) -> str:
        choices = getattr(data, "choices", None) or []
        if not choices:
            raise ValueError(f"LLM response had no choices: {data}")
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None) if message is not None else None
        if content is None and isinstance(message, dict):
            content = message.get("content")
        if not content:
            raise ValueError(f"LLM response had empty content: {data}")
        if isinstance(content, list):
            parts = []
            for item in content:
                text = getattr(item, "text", None) if not isinstance(item, dict) else item.get("text")
                if text:
                    parts.append(str(text))
            content = "\n".join(parts)
        return str(content).strip()


def build_client(args: argparse.Namespace) -> LLMClient:
    base_url = args.base_url or _env("SKILL_V5_BASE_URL", "OPENAI_BASE_URL", "BASE_URL", default="https://api.openai.com/v1")
    api_key = args.api_key or _env("SKILL_V5_API_KEY", "OPENAI_API_KEY", "API_KEY")
    if not api_key:
        raise EnvironmentError("Missing API key. Set SKILL_V5_API_KEY or OPENAI_API_KEY.")
    return LLMClient(
        model=args.model,
        base_url=base_url,
        api_key=api_key,
        timeout=args.timeout,
        max_retries=args.max_retries,
        temperature=args.temperature,
        reasoning_effort=args.reasoning_effort,
        default_max_tokens=args.max_tokens,
    )


def prompt_text(name: str, **replacements: str) -> str:
    return fill_template(load_text(PROMPTS / name), **replacements)


def load_blueprint() -> dict[str, Any]:
    return load_json(BLUEPRINT_PATH)


def load_framework_text() -> str:
    return load_text(FRAMEWORK_TEXT_PATH)


def make_run_dir(out: str | None) -> Path:
    if out:
        return Path(out).resolve()
    return (DEFAULT_OUT / time.strftime("run_%Y%m%d_%H%M%S")).resolve()


def registry_summary(registry: dict[str, Any]) -> dict[str, Any]:
    micro = sort_units(registry.get("micro_units", []))
    macro = sort_units(registry.get("macro_units", []))
    return {
        "library_name": registry.get("library_name", "skills_v5"),
        "micro_count": len(micro),
        "macro_count": len(macro),
        "micro_ids": [item.get("id") for item in micro],
        "macro_ids": [item.get("id") for item in macro],
        "families": {
            "micro": sorted({str(item.get("family", "")) for item in micro if item.get("family")}),
            "macro": sorted({str(item.get("family", "")) for item in macro if item.get("family")}),
        },
    }


def sibling_context(registry: dict[str, Any], unit_id: str) -> dict[str, Any]:
    unit_id = normalize_unit_id(unit_id)
    units = all_units(registry)
    ids = [normalize_unit_id(item.get("id", "")) for item in units]
    idx = ids.index(unit_id)
    neighbors = []
    for offset in (-2, -1, 1, 2):
        pos = idx + offset
        if 0 <= pos < len(units):
            neighbors.append(units[pos])
    return {"target": registry_lookup(registry).get(unit_id, {}), "neighbors": neighbors}


def validate_registry(registry: dict[str, Any], blueprint: dict[str, Any]) -> None:
    expected_micro = int(blueprint.get("target_counts", {}).get("micro", 56))
    expected_macro = int(blueprint.get("target_counts", {}).get("macro", 20))
    micro = sort_units(registry.get("micro_units", []))
    macro = sort_units(registry.get("macro_units", []))
    if len(micro) != expected_micro or len(macro) != expected_macro:
        raise ValueError(f"Registry count mismatch: micro={len(micro)} macro={len(macro)}")
    expected_ids = {f"micro-{i:02d}" for i in range(1, expected_micro + 1)} | {f"macro-{i:02d}" for i in range(1, expected_macro + 1)}
    actual_ids = {normalize_unit_id(item.get("id", "")) for item in micro + macro}
    if actual_ids != expected_ids:
        missing = sorted(expected_ids - actual_ids)
        extra = sorted(actual_ids - expected_ids)
        raise ValueError(f"Registry ids mismatch. missing={missing[:8]} extra={extra[:8]}")
    valid_micro_ids = {f"micro-{i:02d}" for i in range(1, expected_micro + 1)}
    for item in macro:
        unit_id = normalize_unit_id(item.get("id", ""))
        micro_ids = item.get("expandable_micro_ids", [])
        if not isinstance(micro_ids, list):
            raise ValueError(f"{unit_id} expandable_micro_ids must be a list")
        invalid = [x for x in micro_ids if normalize_unit_id(str(x)) not in valid_micro_ids]
        if invalid:
            raise ValueError(f"{unit_id} has invalid expandable_micro_ids: {invalid[:8]}")


def _slugify(text: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", str(text or "").strip().lower())
    token = re.sub(r"-+", "-", token).strip("-")
    return token or "general"


def _micro_family(layer: str, heading: str) -> str:
    heading = str(heading or "").strip()
    if "Meta-Cognition" in heading:
        return "meta-control"
    if "Perception" in heading:
        return "perception-memory-knowledge"
    if "Belief" in heading:
        return "belief-models"
    if "Desire" in heading:
        return "goal-action"
    if "Emotion" in heading:
        return "emotion-appraisal"
    if "Language" in heading:
        return "language-pragmatics"
    if "Social Norms" in heading:
        return "norms-relationships"
    if "Quantity" in heading:
        return "quantity-probability"
    return f"{layer.lower()}-{_slugify(heading)}"


def _macro_family(title: str) -> str:
    title = str(title or "").lower()
    if "false-belief" in title:
        return "false-belief"
    if "second-order" in title or "common knowledge" in title:
        return "nested-mind"
    if "appearance-reality" in title or "knowledge boundary" in title:
        return "appearance-reality"
    if "social cue" in title or "nonverbal" in title:
        return "social-cues"
    if "emotion" in title:
        return "emotion"
    if "language" in title or "conversation" in title or "speech" in title:
        return "language"
    if "persuasion" in title or "audience" in title:
        return "persuasion"
    if "preference" in title or "decision" in title or "negotiation" in title or "compromise" in title:
        return "decision-conflict"
    if "trust" in title or "relationship" in title:
        return "relationships"
    if "power" in title:
        return "power"
    if "quantity" in title or "probability" in title:
        return "estimation"
    return _slugify(title)


def _parse_registry_entry_line(line: str, unit_id: str) -> dict[str, str]:
    pattern = rf"- `{re.escape(unit_id)}`\s+(?P<title>[^:]+):\s+(?P<desc>.*?)\s+Decision variable:\s+(?P<decision>.*?)\s+Boundary:\s+(?P<boundary>.*)$"
    match = re.match(pattern, line.strip())
    if not match:
        raise ValueError(f"Could not parse framework entry for {unit_id}")
    return {key: value.strip().rstrip(".") for key, value in match.groupdict().items()}


def _micro_use_when(description: str) -> str:
    text = str(description or "").strip().rstrip(".")
    if not text:
        return "you need to identify the unit's target variable"
    return f"you need to {text[0].lower() + text[1:]}"


def _boundary_to_exclusion(boundary: str) -> str:
    text = str(boundary or "").strip().rstrip(".")
    if not text:
        return "the task is narrower than this unit"
    lowered = text.lower()
    if lowered.startswith(("does not ", "do not ", "is not ", "are not ", "was not ", "were not ", "differs from ", "depends on ", "requires ", "concerns ", "focuses on ", "centers on ", "asks whether ")):
        return f"this unit {text}"
    return text


def _parse_framework_registry(blueprint: dict[str, Any], framework_text: str) -> dict[str, Any]:
    lines = framework_text.splitlines()
    micro_units: list[dict[str, Any]] = []
    macro_units: list[dict[str, Any]] = []
    current_layer = ""
    current_family = ""
    for raw in lines:
        line = raw.strip()
        micro_section = re.match(r"###\s+(L\d)\s+(.+?):\s+(\d+)\s+Micro Skills", line)
        if micro_section:
            current_layer = micro_section.group(1)
            current_family = _micro_family(current_layer, micro_section.group(2))
            continue
        micro_match = re.match(r"- `(micro-\d{2})`\s+", line)
        if micro_match:
            unit_id = micro_match.group(1)
            parsed = _parse_registry_entry_line(line, unit_id)
            micro_units.append({
                "id": unit_id,
                "level": "micro",
                "layer": current_layer,
                "family": current_family,
                "title": parsed["title"],
                "core_question": parsed["desc"],
                "decision_variable": parsed["decision"],
                "use_when": [
                    f"Use when { _micro_use_when(parsed['desc']) }.",
                    f"Use when the answer depends on {parsed['decision'].lower()}.",
                ],
                "do_not_use_when": [
                    f"Do not use when {_boundary_to_exclusion(parsed['boundary'])}.",
                ],
                "boundary_neighbors": [],
                "source_mix": ["benchmark", "psychology", "real-world"],
            })
            continue
    micro_ids = [item["id"] for item in micro_units]
    for idx, item in enumerate(micro_units):
        item["boundary_neighbors"] = [x for x in micro_ids[max(0, idx - 2):idx] + micro_ids[idx + 1:idx + 3]]
    macro_lines = [line.strip() for line in lines if line.strip().startswith("- `macro-")]
    for idx, line in enumerate(macro_lines):
        m = re.match(r"- `(macro-\d{2})`\s+(?P<title>.+)$", line)
        if not m:
            raise ValueError(f"Could not parse macro entry line: {line}")
        unit_id = m.group(1)
        title = m.group("title").strip()
        if idx * 4 + 1 >= len(lines):
            raise ValueError(f"Missing framework lines for {unit_id}")
        # Re-scan the original section to locate the descriptive lines immediately after the macro bullet.
        line_index = next((i for i, raw in enumerate(lines) if raw.strip() == line), -1)
        if line_index == -1:
            raise ValueError(f"Could not locate framework line for {unit_id}")
        scene_line = lines[line_index + 1].strip()
        expand_line = lines[line_index + 2].strip()
        boundary_line = lines[line_index + 3].strip()
        if not scene_line.startswith("Scene decision variable:"):
            raise ValueError(f"Missing scene decision variable for {unit_id}")
        if not expand_line.startswith("Expand with:"):
            raise ValueError(f"Missing expansion line for {unit_id}")
        if not boundary_line.startswith("Boundary:"):
            raise ValueError(f"Missing boundary line for {unit_id}")
        decision = scene_line.removeprefix("Scene decision variable:").strip().rstrip(".")
        boundary = boundary_line.removeprefix("Boundary:").strip().rstrip(".")
        expand_ids = re.findall(r"`(micro-\d{2})`", expand_line)
        macro_units.append({
            "id": unit_id,
            "level": "macro",
            "layer": "macro",
            "family": _macro_family(title),
            "title": title,
            "core_question": decision,
            "decision_variable": decision,
            "direct_route_rule": next((item["direct_route_rule"] for item in blueprint.get("macro_archetypes", []) if item.get("id") == unit_id), ""),
            "expandable_micro_ids": expand_ids,
            "boundary_neighbors": [],
            "source_mix": ["benchmark", "psychology", "real-world"],
            "use_when": [f"Use when the scene matches the {title.lower()} prototype."],
            "do_not_use_when": [f"Do not use when the scene is better explained by a narrower micro capability than {boundary.lower()}."],
        })
    macro_ids = [item["id"] for item in macro_units]
    for idx, item in enumerate(macro_units):
        item["boundary_neighbors"] = [x for x in macro_ids[max(0, idx - 2):idx] + macro_ids[idx + 1:idx + 3]]
    registry = {
        "library_name": blueprint.get("library_name", "skills_v5"),
        "micro_units": micro_units,
        "macro_units": macro_units,
        "coverage_map": {
            "benchmark": list(blueprint.get("benchmark_sources", [])),
            "real_world": list(blueprint.get("real_world_extensions", [])),
        },
        "generation_notes": [
            "Registry was generated locally from the English framework text.",
            "Plan stage is deterministic and does not call the LLM.",
        ],
    }
    validate_registry(registry, blueprint)
    return registry


def framework_anchor_for_unit(framework_text: str, unit_id: str) -> str:
    token = f"`{normalize_unit_id(unit_id)}`"
    lines = framework_text.splitlines()
    for idx, line in enumerate(lines):
        if token not in line:
            continue
        start = idx
        end = idx + 1
        while end < len(lines):
            current = lines[end]
            if current.startswith("- `micro-") or current.startswith("- `macro-") or current.startswith(("## ", "### ")) or current.startswith("---"):
                break
            end += 1
        return "\n".join(lines[start:end]).strip()
    return ""


def ensure_pack_defaults(pack: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    unit_id = normalize_unit_id(entry.get("id", ""))
    merged = dict(pack)
    merged["id"] = unit_id
    merged["level"] = unit_kind(unit_id)
    merged["layer"] = entry.get("layer", merged.get("layer", ""))
    merged["family"] = entry.get("family", merged.get("family", ""))
    merged["title"] = merged.get("title") or entry.get("title") or unit_id
    merged["core_question"] = entry.get("core_question", merged.get("core_question", ""))
    merged["decision_variable"] = merged.get("decision_variable") or entry.get("decision_variable", "")
    merged.setdefault("use_when", entry.get("use_when", []))
    merged.setdefault("do_not_use_when", entry.get("do_not_use_when", []))
    merged.setdefault("trigger_checklist", [])
    merged.setdefault("workflow", [])
    merged.setdefault("boundary_exit_rule", [])
    merged.setdefault("references", {})
    merged.setdefault("validation_seed", {})
    merged.setdefault("notes", [])
    if unit_kind(unit_id) == "macro":
        merged["direct_route_rule"] = entry.get("direct_route_rule", merged.get("direct_route_rule", ""))
        micro_ids = merged.get("expandable_micro_ids") or entry.get("expandable_micro_ids", [])
        merged["expandable_micro_ids"] = [normalize_unit_id(str(x)) for x in micro_ids if normalize_unit_id(str(x))]
    return merged


def generate_registry(blueprint: dict[str, Any], framework_text: str) -> dict[str, Any]:
    registry = _parse_framework_registry(blueprint, framework_text)
    registry["micro_units"] = sort_units(registry.get("micro_units", []))
    registry["macro_units"] = sort_units(registry.get("macro_units", []))
    return registry


def generate_unit_pack(
    client: LLMClient,
    blueprint: dict[str, Any],
    framework_text: str,
    registry: dict[str, Any],
    entry: dict[str, Any],
) -> dict[str, Any]:
    unit_id = normalize_unit_id(entry.get("id", ""))
    kind = unit_kind(unit_id)
    prompt_name = "01_micro.md" if kind == "micro" else "02_macro.md"
    system = "You expand one compact social-mind unit. Return valid JSON only."
    user = prompt_text(
        prompt_name,
        BLUEPRINT_JSON=compact_json(blueprint),
        FRAMEWORK_EXCERPT=framework_anchor_for_unit(framework_text, unit_id),
        UNIT_JSON=compact_json(entry),
        NEIGHBOR_JSON=compact_json(sibling_context(registry, unit_id)),
    )
    pack = extract_json(client.chat(system, user))
    return ensure_pack_defaults(pack, entry)


def render_list(items: Any) -> str:
    values = items if isinstance(items, list) else [items] if items else []
    if not values:
        return "- None specified."
    return "\n".join(f"- {str(item).strip()}" for item in values if str(item).strip())


def yaml_safe(value: Any) -> str:
    text = str(value or "").replace('"', "'").strip()
    return f'"{text}"'


def render_skill_md(pack: dict[str, Any]) -> str:
    refs = pack.get("references", {}) if isinstance(pack.get("references"), dict) else {}
    lines = [
        "---",
        f"name: {pack['id']}",
        f"level: {pack.get('level', '')}",
        f"layer: {pack.get('layer', '')}",
        f"family: {yaml_safe(pack.get('family', ''))}",
        f"description: {yaml_safe(pack.get('frontmatter_description') or pack.get('core_question') or pack.get('title'))}",
        "---",
        "",
        f"# {pack.get('title', pack['id'])}",
        "",
        "## Use When",
        render_list(pack.get("use_when")),
        "",
        "## Do Not Use When",
        render_list(pack.get("do_not_use_when")),
        "",
        "## Decision Variable",
        str(pack.get("decision_variable", "")).strip() or "None specified.",
    ]
    if pack.get("level") == "macro":
        lines.extend([
            "",
            "## Direct Route Rule",
            str(pack.get("direct_route_rule", "")).strip() or "None specified.",
            "",
            "## Expand With Micro Units",
            render_list(pack.get("expandable_micro_ids")),
        ])
    lines.extend([
        "",
        "## Trigger Checklist",
        render_list(pack.get("trigger_checklist")),
        "",
        "## Workflow",
        render_list(pack.get("workflow")),
    ])
    special = pack.get("special_case") if isinstance(pack.get("special_case"), dict) else {}
    if special:
        example = special.get("worked_example", {}) if isinstance(special.get("worked_example"), dict) else {}
        lines.extend([
            "",
            "## Special Case",
            f"**{special.get('title', 'Special case')}**: {special.get('rule', '')}",
        ])
        if example:
            lines.extend([
                "",
                f"Scene: {example.get('scene', '')}",
                f"Question: {example.get('question', '')}",
                f"Answer logic: {example.get('answer_logic', '')}",
            ])
    lines.extend([
        "",
        "## Boundary Exit Rule",
        render_list(pack.get("boundary_exit_rule")),
        "",
        "## References",
        "- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.",
    ])
    if refs.get("route_signal"):
        lines.extend(["", "## Quick Route Signal", str(refs.get("route_signal"))])
    return "\n".join(lines).rstrip() + "\n"


def render_examples_md(pack: dict[str, Any]) -> str:
    refs = pack.get("references", {}) if isinstance(pack.get("references"), dict) else {}
    lines = [
        f"# {pack['id']} Examples and Boundaries",
        "",
        "## Decision Variable",
        str(pack.get("decision_variable", "")).strip() or "None specified.",
        "",
        "## Route Signal",
        str(refs.get("route_signal", "")).strip() or "None specified.",
        "",
        "## Hard Boundary",
        render_list(refs.get("hard_boundary")),
        "",
        "## Shortcut To Avoid",
        render_list(refs.get("shortcut_to_avoid")),
        "",
        "## Common Failure Modes",
        render_list(refs.get("common_failure_modes")),
        "",
        "## Minimal Pair",
    ]
    pairs = refs.get("minimal_pair", [])
    if isinstance(pairs, list) and pairs:
        for item in pairs:
            if isinstance(item, dict):
                lines.append(f"- Case: {item.get('case', '')} | Why: {item.get('why_it_matches', '')}")
            else:
                lines.append(f"- {item}")
    else:
        lines.append("- None specified.")
    lines.extend([
        "",
        "## Boundary Stress Test",
        render_list(refs.get("boundary_stress_test")),
        "",
        "## Generalization Note",
        str(refs.get("generalization_note", "")).strip() or "None specified.",
    ])
    return "\n".join(lines).rstrip() + "\n"


def unit_dir(run_dir: Path, unit_id: str) -> Path:
    return run_dir / normalize_unit_id(unit_id)


def write_unit(run_dir: Path, pack: dict[str, Any]) -> None:
    target = unit_dir(run_dir, pack["id"])
    write_json(target / "unit_pack.json", pack)
    write_text(target / "SKILL.md", render_skill_md(pack))
    write_text(target / "references" / "examples.md", render_examples_md(pack))


def pack_audit_summary(run_dir: Path, registry: dict[str, Any]) -> dict[str, Any]:
    summaries: list[dict[str, Any]] = []
    l0_meta_control: list[dict[str, Any]] = []
    for entry in all_units(registry):
        unit_id = normalize_unit_id(entry.get("id", ""))
        pack_path = unit_dir(run_dir, unit_id) / "unit_pack.json"
        if not pack_path.exists():
            continue
        pack = load_json(pack_path)
        summary = {
            "id": unit_id,
            "level": pack.get("level"),
            "layer": pack.get("layer"),
            "family": pack.get("family"),
            "title": pack.get("title"),
            "decision_variable": pack.get("decision_variable"),
            "use_when": pack.get("use_when", [])[:3],
            "do_not_use_when": pack.get("do_not_use_when", [])[:3],
            "boundary_exit_rule": pack.get("boundary_exit_rule", [])[:3],
        }
        if pack.get("level") == "macro":
            summary["direct_route_rule"] = pack.get("direct_route_rule", "")
            summary["expandable_micro_ids"] = pack.get("expandable_micro_ids", [])
        summaries.append(summary)
        if pack.get("layer") == "L0":
            l0_meta_control.append(summary)
    return {"l0_meta_control_units": l0_meta_control, "generated_units": summaries}


def audit_run(
    client: LLMClient,
    blueprint: dict[str, Any],
    framework_text: str,
    run_dir: Path,
    scope: str = "full",
) -> dict[str, Any]:
    registry = load_json(run_dir / "skill_registry.json")
    pack_summary = pack_audit_summary(run_dir, registry)
    generated_units = pack_summary.get("generated_units", [])
    audit_chunks = chunked(generated_units, AUDIT_CHUNK_SIZE)
    chunk_reports: list[dict[str, Any]] = []
    system = "You audit a generated skill library for coverage, overlap, and bloat risks. Return valid JSON only."
    for idx, audit_chunk in enumerate(audit_chunks or [[]], start=1):
        user = prompt_text(
            "03_audit.md",
            BLUEPRINT_JSON=compact_json(blueprint),
            FRAMEWORK_TEXT=framework_text,
            REGISTRY_SUMMARY_JSON=compact_json(registry_summary(registry)),
            L0_META_CONTROL_JSON=compact_json(pack_summary.get("l0_meta_control_units", [])),
            UNIT_SUMMARY_JSON=compact_json(audit_chunk),
            AUDIT_SCOPE=scope,
            AUDIT_CHUNK_NOTE=f"chunk {idx} of {max(1, len(audit_chunks))}; valid JSON slice, not character-truncated",
        )
        chunk_reports.append(extract_json(client.chat(system, user)))
    if len(chunk_reports) == 1:
        report = chunk_reports[0]
    else:
        report = {
            "coverage_gaps": sorted({x for r in chunk_reports for x in r.get("coverage_gaps", [])}),
            "l0_meta_control_gaps": sorted({x for r in chunk_reports for x in r.get("l0_meta_control_gaps", [])}),
            "overlap_risks": [x for r in chunk_reports for x in r.get("overlap_risks", [])],
            "boundary_confusions": [x for r in chunk_reports for x in r.get("boundary_confusions", [])],
            "bloat_risks": [x for r in chunk_reports for x in r.get("bloat_risks", [])],
            "rewrite_targets": sorted(
                {normalize_unit_id(str(x)) for r in chunk_reports for x in r.get("rewrite_targets", []) if normalize_unit_id(str(x))},
                key=unit_number,
            ),
            "summary": "Merged audit report from valid JSON chunks.",
            "chunk_reports": chunk_reports,
        }
    report.setdefault("created_at", time.strftime("%Y-%m-%d %H:%M:%S"))
    report.setdefault("audit_scope", scope)
    report.setdefault("audited_unit_count", len(generated_units))
    write_json(run_dir / "audit_report.json", report)
    return report


def generate_validation_pack(client: LLMClient, pack: dict[str, Any]) -> dict[str, Any]:
    system = "You create compact validation cases for one unit. Return valid JSON only."
    user = prompt_text("04_validation.md", UNIT_PACK_JSON=compact_json(pack))
    data = extract_json(client.chat(system, user))
    data.setdefault("unit_id", pack["id"])
    validate_validation_pack(data, pack["id"])
    return data


def validate_validation_pack(data: dict[str, Any], unit_id: str) -> None:
    if normalize_unit_id(str(data.get("unit_id", unit_id))) != normalize_unit_id(unit_id):
        raise ValueError(f"Validation unit_id mismatch for {unit_id}")
    items = data.get("items", [])
    if not isinstance(items, list) or not (3 <= len(items) <= 5):
        raise ValueError(f"Validation pack for {unit_id} must contain 3 to 5 items")
    patterns = {str(item.get("pattern", "")).strip() for item in items if isinstance(item, dict)}
    if "positive" not in patterns or not ({"near_miss", "boundary"} & patterns):
        raise ValueError(f"Validation pack for {unit_id} needs positive and near_miss/boundary cases")
    for item in items:
        if not isinstance(item, dict):
            raise ValueError(f"Validation item for {unit_id} is not an object")
        labels = item.get("labels", [])
        answer = str(item.get("gold_answer", "")).strip()
        if answer not in labels:
            raise ValueError(f"Validation item {item.get('id')} gold_answer is not in labels")


def parse_traces(path: Path | None) -> list[dict[str, Any]]:
    if not path:
        return []
    if not path.exists():
        raise FileNotFoundError(path)
    traces: list[dict[str, Any]] = []
    if path.suffix.lower() == ".jsonl":
        for line in load_text(path).splitlines():
            line = line.strip()
            if line:
                traces.append(json.loads(line))
    else:
        data = load_json(path)
        if isinstance(data, list):
            traces.extend(data)
        elif isinstance(data, dict):
            traces.extend(data.get("items", []) if isinstance(data.get("items"), list) else [data])
    return traces


def trace_unit_id(trace: dict[str, Any]) -> str:
    for key in ("unit_id", "target_id", "routed_unit", "skill_id"):
        value = normalize_unit_id(str(trace.get(key, "")))
        if value:
            return value
    return ""


def group_traces(traces: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for trace in traces:
        unit_id = trace_unit_id(trace)
        if unit_id:
            grouped.setdefault(unit_id, []).append(trace)
    return grouped


def summarize_trace(trace: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "unit_id", "kind", "scene", "story", "question", "gold_answer", "model_answer",
        "predicted", "is_correct", "reasoning", "rationale", "error_type", "lesson",
    ]
    return {key: trace.get(key) for key in keys if key in trace}


def load_pack(run_dir: Path, unit_id: str) -> dict[str, Any]:
    return load_json(unit_dir(run_dir, unit_id) / "unit_pack.json")


def save_pack(run_dir: Path, pack: dict[str, Any]) -> None:
    write_unit(run_dir, pack)


def feedback_candidates(client: LLMClient, blueprint: dict[str, Any], run_dir: Path, traces_path: Path | None, max_patches: int) -> dict[str, Any]:
    registry = load_json(run_dir / "skill_registry.json")
    audit = load_json(run_dir / "audit_report.json") if (run_dir / "audit_report.json").exists() else {}
    grouped = group_traces(parse_traces(traces_path))
    target_ids = sorted(set(grouped) | {normalize_unit_id(x) for x in audit.get("rewrite_targets", []) if normalize_unit_id(x)}, key=unit_number)
    lookup = registry_lookup(registry)
    candidates: list[dict[str, Any]] = []
    for unit_id in target_ids:
        if unit_id not in lookup or not (unit_dir(run_dir, unit_id) / "unit_pack.json").exists():
            continue
        pack = load_pack(run_dir, unit_id)
        trace_slice = [summarize_trace(t) for t in grouped.get(unit_id, [])[:12]]
        prompt = prompt_text(
            "05_feedback.md",
            BLUEPRINT_JSON=compact_json(blueprint),
            UNIT_PACK_JSON=compact_json(pack),
            AUDIT_JSON=compact_json(audit),
            TRACE_JSON=compact_json(trace_slice),
            MAX_PATCHES=str(max_patches),
        )
        raw = client.chat("You propose selective, approval-gated skill patches. Return valid JSON only.", prompt)
        data = extract_json(raw)
        patch_list = data.get("patches", data if isinstance(data, list) else [])
        if isinstance(patch_list, list):
            for patch in patch_list[:max_patches]:
                if isinstance(patch, dict):
                    patch["target_id"] = normalize_unit_id(str(patch.get("target_id", unit_id))) or unit_id
                    patch.setdefault("patch_id", f"{patch['target_id']}-p{len(candidates) + 1}")
                    candidates.append(patch)
    payload = {
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_run": str(run_dir),
        "traces_path": str(traces_path) if traces_path else "",
        "approval_required": True,
        "patches": candidates,
    }
    write_json(run_dir / "feedback_candidates.json", payload)
    write_json(run_dir / "approval_template.json", {
        "approval_required": True,
        "approved_patch_ids": [],
        "rejected_patch_ids": [],
        "note": "Fill approved_patch_ids manually before running `apply`. No candidate is applied automatically.",
        "candidate_file": "feedback_candidates.json",
    })
    return payload


def descend(container: Any, dotted_path: str) -> tuple[Any, str]:
    parts = [part for part in dotted_path.split(".") if part]
    if not parts:
        raise ValueError("Patch path cannot be empty")
    cur = container
    for part in parts[:-1]:
        if isinstance(cur, dict):
            cur = cur.setdefault(part, {})
        else:
            raise TypeError(f"Cannot descend into non-dict path at {part}")
    return cur, parts[-1]


def apply_patch_op(pack: dict[str, Any], patch: dict[str, Any]) -> None:
    op = str(patch.get("op", "")).lower()
    path = str(patch.get("path", "")).strip()
    value = patch.get("value")
    if op not in SUPPORTED_PATCH_OPS:
        raise ValueError(f"Unsupported patch op: {op}")
    if path not in SUPPORTED_PATCH_PATHS:
        raise ValueError(f"Unsupported patch path: {path}")
    parent, leaf = descend(pack, path)
    if not isinstance(parent, dict):
        raise TypeError(f"Patch parent for {path} is not a dict")
    if op == "set":
        parent[leaf] = value
    elif op == "append":
        parent.setdefault(leaf, [])
        if not isinstance(parent[leaf], list):
            raise TypeError(f"Patch target {path} is not a list")
        parent[leaf].append(value)
    elif op == "extend":
        parent.setdefault(leaf, [])
        if not isinstance(parent[leaf], list) or not isinstance(value, list):
            raise TypeError(f"Patch target/value for {path} must be lists")
        parent[leaf].extend(value)
    elif op == "merge":
        parent.setdefault(leaf, {})
        if not isinstance(parent[leaf], dict) or not isinstance(value, dict):
            raise TypeError(f"Patch target/value for {path} must be dicts")
        parent[leaf].update(value)
    elif op == "remove":
        if isinstance(parent.get(leaf), list):
            parent[leaf] = [item for item in parent[leaf] if item != value]
        elif leaf in parent:
            parent.pop(leaf)


def apply_approved_feedback(run_dir: Path, approval_path: Path | None) -> dict[str, Any]:
    candidates = load_json(run_dir / "feedback_candidates.json")
    approval = load_json(approval_path or (run_dir / "approval_template.json"))
    approved = set(approval.get("approved_patch_ids", []))
    if not approved:
        return {"applied": [], "skipped": "No approved_patch_ids were provided."}
    patches = [p for p in candidates.get("patches", []) if p.get("patch_id") in approved]
    applied: list[dict[str, str]] = []
    for patch in patches:
        target_id = normalize_unit_id(str(patch.get("target_id", "")))
        if not target_id:
            continue
        pack = load_pack(run_dir, target_id)
        apply_patch_op(pack, patch)
        save_pack(run_dir, pack)
        applied.append({"patch_id": str(patch.get("patch_id")), "target_id": target_id})
    result = {"applied": applied, "applied_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    write_json(run_dir / "applied_feedback.json", result)
    return result


def freeze_snapshot(run_dir: Path, tag: str, approved: bool) -> Path:
    if not approved:
        raise PermissionError("Freeze requires explicit approval. Pass --approved-by-user after reviewing the run.")
    if not (run_dir / "manifest.json").exists():
        raise FileNotFoundError(f"Not a generated run directory: {run_dir}")
    safe_tag = re.sub(r"[^a-zA-Z0-9_.-]+", "-", tag.strip()) or time.strftime("v%Y%m%d_%H%M%S")
    target = FROZEN_OUT / safe_tag
    if target.exists():
        raise FileExistsError(f"Frozen target already exists: {target}")
    shutil.copytree(run_dir, target)
    write_json(target / "freeze_manifest.json", {
        "tag": safe_tag,
        "source_run": str(run_dir),
        "frozen_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "approved_by_user": True,
        "note": "Snapshot only. Skill content must already reflect any approved feedback before freezing.",
    })
    return target


def run_pipeline(args: argparse.Namespace) -> Path:
    blueprint = load_blueprint()
    framework_text = load_framework_text()
    client = build_client(args)
    run_dir = make_run_dir(args.out)
    run_dir.mkdir(parents=True, exist_ok=True)
    registry = generate_registry(blueprint, framework_text) if not args.registry else load_json(Path(args.registry))
    validate_registry(registry, blueprint)
    write_json(run_dir / "skill_registry.json", registry)
    packs: list[dict[str, Any]] = []
    selected = {normalize_unit_id(x) for x in args.only if normalize_unit_id(x)} if args.only else set()
    if selected and args.feedback and not args.audit_partial and not args.traces:
        raise ValueError("Partial --only runs with --feedback require --audit-partial or --traces.")
    for entry in all_units(registry):
        unit_id = normalize_unit_id(entry.get("id", ""))
        if selected and unit_id not in selected:
            continue
        pack = generate_unit_pack(client, blueprint, framework_text, registry, entry)
        write_unit(run_dir, pack)
        packs.append(pack)
        if args.validation:
            write_json(unit_dir(run_dir, unit_id) / "validation_items.json", generate_validation_pack(client, pack))
    audit: dict[str, Any] = {}
    audit_scope = "partial" if selected else "full"
    if not selected or args.audit_partial:
        audit = audit_run(client, blueprint, framework_text, run_dir, scope=audit_scope)
    manifest = {
        "library_name": "skills_v5",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model": args.model,
        "run_dir": str(run_dir),
        "registry_summary": registry_summary(registry),
        "generated_unit_count": len(packs),
        "generation_scope": audit_scope,
        "audit_enabled": bool(audit),
        "validation_enabled": bool(args.validation),
        "audit_summary": audit.get("summary", ""),
        "feedback_policy": "Feedback produces candidates only; apply and freeze require explicit user approval.",
    }
    write_json(run_dir / "manifest.json", manifest)
    if args.feedback:
        feedback_candidates(client, blueprint, run_dir, Path(args.traces) if args.traces else None, args.max_patches_per_unit)
    return run_dir


def plan_only(args: argparse.Namespace) -> Path:
    blueprint = load_blueprint()
    framework_text = load_framework_text()
    run_dir = make_run_dir(args.out)
    registry = generate_registry(blueprint, framework_text)
    write_json(run_dir / "skill_registry.json", registry)
    write_json(run_dir / "registry_summary.json", registry_summary(registry))
    return run_dir


def cmd_audit(args: argparse.Namespace) -> dict[str, Any]:
    return audit_run(build_client(args), load_blueprint(), load_framework_text(), Path(args.run).resolve(), scope="full")


def cmd_feedback(args: argparse.Namespace) -> dict[str, Any]:
    return feedback_candidates(
        build_client(args),
        load_blueprint(),
        Path(args.run).resolve(),
        Path(args.traces).resolve() if args.traces else None,
        args.max_patches_per_unit,
    )


def add_llm_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--base-url", default="")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--timeout", type=int, default=DEFAULT_RUN_TIMEOUT)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument("--reasoning-effort", default=os.environ.get("SKILL_V5_REASONING_EFFORT", ""))
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_RUN_MAX_TOKENS)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="skills_v5 framework-driven skill generator")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Generate registry, unit folders, audit, and optional candidates")
    add_llm_args(run)
    run.add_argument("--out", default="")
    run.add_argument("--registry", default="", help="Use an existing skill_registry.json instead of planning a new one")
    run.add_argument("--only", nargs="*", default=[], help="Generate selected unit ids only; registry still must be complete")
    run.add_argument("--audit-partial", action="store_true", help="Audit a partial --only run; full audit is skipped by default")
    run.add_argument("--validation", action="store_true", help="Generate validation_items.json for each generated unit")
    run.add_argument("--feedback", action="store_true", help="Generate feedback candidates only; does not apply them")
    run.add_argument("--traces", default="", help="JSON/JSONL traces with correct and wrong reasoning paths")
    run.add_argument("--max-patches-per-unit", type=int, default=3)

    plan = sub.add_parser("plan", help="Generate the shared micro/macro registry only")
    plan.add_argument("--out", default="")

    audit = sub.add_parser("audit", help="Audit an existing generated run")
    add_llm_args(audit)
    audit.add_argument("--run", required=True)

    feedback = sub.add_parser("feedback", help="Create selective feedback candidates from audit and traces")
    add_llm_args(feedback)
    feedback.add_argument("--run", required=True)
    feedback.add_argument("--traces", default="")
    feedback.add_argument("--max-patches-per-unit", type=int, default=3)

    apply_cmd = sub.add_parser("apply", help="Apply approved feedback patches only")
    apply_cmd.add_argument("--run", required=True)
    apply_cmd.add_argument("--approval", default="", help="Approval JSON; defaults to approval_template.json in run dir")

    freeze = sub.add_parser("freeze", help="Freeze an approved generated run snapshot")
    freeze.add_argument("--run", required=True)
    freeze.add_argument("--tag", required=True)
    freeze.add_argument("--approved-by-user", action="store_true", help="Required after manual review/approval")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "run":
            path = run_pipeline(args)
            print(f"generated: {path}")
        elif args.command == "plan":
            path = plan_only(args)
            print(f"planned: {path}")
        elif args.command == "audit":
            print(compact_json(cmd_audit(args)))
        elif args.command == "feedback":
            print(compact_json(cmd_feedback(args)))
        elif args.command == "apply":
            result = apply_approved_feedback(Path(args.run).resolve(), Path(args.approval).resolve() if args.approval else None)
            print(compact_json(result))
        elif args.command == "freeze":
            path = freeze_snapshot(Path(args.run).resolve(), args.tag, args.approved_by_user)
            print(f"frozen: {path}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

