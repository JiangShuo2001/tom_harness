from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from collections import Counter
from functools import lru_cache
from pathlib import Path

from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent.parent
SKILLS_ROOT = REPO_ROOT / 'skills'
RESULTS_ROOT = ROOT / 'results'
DEFAULT_TIMEOUT = float(os.getenv('OPENROUTER_TIMEOUT_SECONDS', '180'))
DEFAULT_MAX_RETRIES = int(os.getenv('OPENROUTER_MAX_RETRIES', '3'))
DEFAULT_WRONG_SKILL_MAP = {
    'skill3': 'skill5',
    'skill8': 'skill9',
    'skill14': 'skill15',
}
DEFAULT_ROUTE_AND_SOLVE_PACK = ROOT / 'gpt54mini_positive_routing_pack.json'
LEGACY_SKILL_CHOICES = ['skill3', 'skill8', 'skill14']
ALL_SKILLS = [f'skill{i}' for i in range(1, 16)]


def _build_client(timeout: float) -> OpenAI:
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise EnvironmentError('Set OPENROUTER_API_KEY before running validation.')
    return OpenAI(base_url='https://openrouter.ai/api/v1', api_key=api_key, timeout=timeout)


def load_text(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def load_json(path: Path) -> dict:
    return json.loads(load_text(path))


def call_model_api(
    model: str,
    messages: list[dict],
    temperature: float = 0.0,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    reasoning_enabled: bool = True,
) -> str:
    client = _build_client(timeout=timeout)
    extra_body = {'reasoning': {'enabled': True}} if reasoning_enabled else None

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                extra_body=extra_body,
            )
            if response is None:
                raise ValueError('Model API returned None response object.')
            choices = getattr(response, 'choices', None)
            if not choices:
                raise ValueError(f'Model API returned no choices. Raw response object: {response}')
            first_choice = choices[0]
            message = getattr(first_choice, 'message', None)
            if message is None:
                raise ValueError(f'Model API returned a choice without message. First choice: {first_choice}')
            content = getattr(message, 'content', None)
            if content is None:
                raise ValueError(f'Model returned empty content. First choice message: {message}')
            return content
        except (APITimeoutError, APIConnectionError, RateLimitError, ValueError) as exc:
            last_error = exc
            if attempt == max_retries:
                break
            sleep_seconds = min(2 ** (attempt - 1), 8)
            print(
                f'[warn] API call failed on attempt {attempt}/{max_retries}: {exc.__class__.__name__}: {exc}. Retrying in {sleep_seconds}s...',
                file=sys.stderr,
            )
            time.sleep(sleep_seconds)

    assert last_error is not None
    raise last_error


def find_skill_doc(skill_name: str) -> Path:
    skill_doc = SKILLS_ROOT / skill_name / 'SKILL.md'
    if not skill_doc.exists():
        raise FileNotFoundError(f'SKILL.md not found: {skill_doc}')
    return skill_doc


def find_skill_reference(skill_name: str) -> Path:
    ref_path = SKILLS_ROOT / skill_name / 'references' / 'examples.md'
    if not ref_path.exists():
        raise FileNotFoundError(f'Reference file not found: {ref_path}')
    return ref_path


def find_validation_pack(skill_name: str) -> Path:
    pack = ROOT / skill_name / 'validation_items.json'
    if not pack.exists():
        raise FileNotFoundError(f'Validation pack not found: {pack}')
    return pack


def find_route_and_solve_pack(pack_arg: str | None) -> Path:
    candidates = []
    if pack_arg:
        path = Path(pack_arg)
        candidates.extend([path, ROOT / path, REPO_ROOT / path])
    else:
        candidates.append(DEFAULT_ROUTE_AND_SOLVE_PACK)

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    searched = ', '.join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f'Route-and-solve pack not found. Searched: {searched}')


def extract_option_map(item: dict) -> dict[str, str]:
    options = item.get('options') or {}
    if isinstance(options, dict):
        return {str(key).strip().upper(): str(value).strip() for key, value in options.items()}

    labels = item.get('labels') or []
    return {
        str(labels[index]).strip().upper(): str(value).strip()
        for index, value in enumerate(options)
        if index < len(labels)
    }


def format_options(options: dict[str, str]) -> str:
    return '\n'.join(f'{key}. {value}' for key, value in sorted(options.items()))


def build_legacy_messages(skill_name: str, run_type: str, item: dict, skill_name_for_prompt: str | None = None) -> list[dict]:
    active_skill_name = skill_name_for_prompt or skill_name
    skill_doc = load_text(find_skill_doc(active_skill_name))
    skill_ref = load_text(find_skill_reference(active_skill_name))
    system_text = (
        'You are evaluating a reasoning skill on a multiple-choice Tombench-style item. '
        'Return one strictly valid JSON object only. Do not use markdown fences. '
        'The response must start with { and end with }. Select exactly one option label.'
    )

    if run_type == 'baseline':
        mode_text = 'Answer directly without explicitly applying any skill document.'
    elif run_type == 'with_skill':
        mode_text = f'Use the target skill `{active_skill_name}` and reference material explicitly.'
    elif run_type == 'wrong_skill':
        mode_text = f'Deliberately use the supplied skill `{active_skill_name}` even if it may be the wrong tool.'
    else:
        raise ValueError(f'Unsupported run_type: {run_type}')

    item_block = {
        'item_id': item['id'],
        'split': item['split'],
        'task_name': item['task_name'],
        'ability': item['ability'],
    }
    options = item.get('options') or {}
    schema = {
        'selected_option_label': 'single option label such as A, B, C, or D',
        'selected_option_text': 'exact option text for the selected label',
        'reasoning_summary': 'short string',
        'should_trigger_skill': 'yes|no|boundary',
        'did_trigger_skill_correctly': 'yes|no',
        'decision_variable_identified': 'yes|no',
        'shortcut_avoided': 'yes|no',
        'boundary_respected': 'yes|no',
        'notes': 'short string',
    }

    parts = [mode_text]
    if run_type != 'baseline':
        parts.extend(['Skill document:', skill_doc, 'Reference document:', skill_ref])
    parts.extend([
        'Validation metadata:',
        json.dumps(item_block, ensure_ascii=False, indent=2),
        'Scene:\n' + item['scene'],
        'Question:\n' + item['question'],
        'Options:',
        format_options(options),
        'Return JSON using exactly this schema:',
        json.dumps(schema, ensure_ascii=False, indent=2),
        'Important output rules:',
        '1. Choose exactly one option from the provided options.',
        '2. Put the option label into selected_option_label.',
        '3. Put the exact option text into selected_option_text.',
        '4. Return exactly one JSON object.',
        '5. Do not wrap the JSON in ```json or any markdown fences.',
        '6. Do not add any explanation before or after the JSON.',
        '7. The response must begin with { and end with }.',
    ])
    return [
        {'role': 'system', 'content': system_text},
        {'role': 'user', 'content': '\n\n'.join(parts)},
    ]


def extract_markdown_section(markdown: str, heading: str) -> str:
    match = re.search(rf'^## {re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)', markdown, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return ''
    return match.group(1).strip()


@lru_cache(maxsize=1)
def build_route_and_solve_registry() -> tuple[str, str]:
    routing_guide = load_text(SKILLS_ROOT / 'ROUTING.md')
    capsules = []
    for skill_name in ALL_SKILLS:
        skill_doc = load_text(find_skill_doc(skill_name))
        skill_ref = load_text(find_skill_reference(skill_name))
        decision_variable = extract_markdown_section(skill_ref, 'Decision Variable')
        use_when = extract_markdown_section(skill_doc, 'Use When')
        do_not_use_when = extract_markdown_section(skill_doc, 'Do Not Use When')
        workflow = extract_markdown_section(skill_doc, 'Workflow')
        boundary = extract_markdown_section(skill_ref, 'Hard Boundary')
        capsules.append(
            '\n'.join(
                [
                    f'### {skill_name}',
                    'Decision Variable:',
                    decision_variable,
                    'Use When:',
                    use_when,
                    'Do Not Use When:',
                    do_not_use_when,
                    'Workflow:',
                    workflow,
                    'Hard Boundary:',
                    boundary,
                ]
            ).strip()
        )
    return routing_guide, '\n\n'.join(capsules)


def build_route_and_solve_messages(item: dict) -> list[dict]:
    routing_guide, skill_registry = build_route_and_solve_registry()
    system_text = (
        'You are evaluating a one-call route-and-solve workflow for mindreading multiple-choice items. '
        'Choose the single best skill from skill1 to skill15, then answer the multiple-choice question using that skill in the same response. '
        'Return one strictly valid JSON object only. Do not use markdown fences. '
        'The response must start with { and end with }.'
    )
    item_block = {
        'item_id': item.get('item_id', item.get('id', '')),
        'source_dataset': item.get('source_dataset', item.get('dataset', '')),
        'task_type': item.get('task_type', ''),
        'ability': item.get('ability', ''),
    }
    options = extract_option_map(item)
    schema = {
        'predicted_skill': 'one of skill1 to skill15',
        'selected_option_label': 'single option label such as A, B, C, or D',
        'selected_option_text': 'exact option text for the selected label',
        'decision_variable': 'short string naming the variable that determines the answer',
        'routing_reasoning_summary': 'short string',
        'answer_reasoning_summary': 'short string',
        'closest_alternative_skill': 'one of skill1 to skill15 or empty string',
        'notes': 'short string',
    }
    parts = [
        'Routing guide:',
        routing_guide,
        'Compact skill registry:',
        skill_registry,
        'Item metadata:',
        json.dumps(item_block, ensure_ascii=False, indent=2),
        'Scene:\n' + item['scene'],
        'Question:\n' + item['question'],
        'Options:',
        format_options(options),
        'Return JSON using exactly this schema:',
        json.dumps(schema, ensure_ascii=False, indent=2),
        'Important output rules:',
        '1. predicted_skill must be exactly one of skill1, skill2, ..., skill15.',
        '2. Choose exactly one option from the provided options.',
        '3. Put the option label into selected_option_label.',
        '4. Put the exact option text into selected_option_text.',
        '5. Return exactly one JSON object.',
        '6. Do not wrap the JSON in ```json or any markdown fences.',
        '7. Do not add any explanation before or after the JSON.',
        '8. The response must begin with { and end with }.',
    ]
    return [
        {'role': 'system', 'content': system_text},
        {'role': 'user', 'content': '\n\n'.join(parts)},
    ]


def _strip_code_fences(raw_text: str) -> str:
    text = raw_text.strip()
    if not text.startswith('```'):
        return text

    lines = text.splitlines()
    if lines and lines[0].strip().startswith('```'):
        lines = lines[1:]
    if lines and lines[-1].strip() == '```':
        lines = lines[:-1]
    return '\n'.join(lines).strip()


def parse_model_json(raw_text: str) -> dict:
    candidates = []
    text = raw_text.strip()
    if text:
        candidates.append(text)

    stripped = _strip_code_fences(text)
    if stripped and stripped not in candidates:
        candidates.append(stripped)

    for candidate in list(candidates):
        first_brace = candidate.find('{')
        last_brace = candidate.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            extracted = candidate[first_brace:last_brace + 1].strip()
            if extracted and extracted not in candidates:
                candidates.append(extracted)
        elif first_brace == -1 and last_brace != -1:
            prefix_repaired = ('{' + candidate[:last_brace + 1].strip())
            if prefix_repaired not in candidates:
                candidates.append(prefix_repaired)

    seen = set()
    errors = []
    for candidate in candidates:
        normalized = candidate.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        try:
            parsed = json.loads(normalized)
        except json.JSONDecodeError as exc:
            errors.append(f'{exc}: {normalized[:200]}')
            continue
        if not isinstance(parsed, dict):
            raise ValueError(f'Model response JSON must be an object, got {type(parsed).__name__}.\nRaw response:\n{raw_text}')
        return parsed

    error_block = '\n'.join(errors[:3]) if errors else 'No parse candidates generated.'
    raise ValueError(
        'Model response is not valid JSON after normalization attempts.\n'
        f'Parse attempts:\n{error_block}\n'
        f'Raw response:\n{raw_text}'
    )


def _normalize_answer_text(text: str) -> str:
    normalized = text.strip().lower()
    normalized = re.sub(r'^[\s"\']+|[\s"\'.,!?;:]+$', '', normalized)
    normalized = re.sub(r'\b(a|an|the)\b', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized.strip()


def resolve_selected_option(parsed: dict, item: dict) -> tuple[str, str]:
    option_map = extract_option_map(item)

    label_raw = str(parsed.get('selected_option_label', '')).strip().upper()
    text_raw = str(parsed.get('selected_option_text', '')).strip()

    if label_raw in option_map:
        return label_raw, option_map[label_raw]

    if text_raw:
        text_norm = _normalize_answer_text(text_raw)
        for key, value in option_map.items():
            if _normalize_answer_text(value) == text_norm:
                return key, value

    return '', text_raw


def resolve_skill_name(value: object) -> str:
    text = str(value or '').strip().lower()
    if text in ALL_SKILLS:
        return text
    match = re.search(r'\b(skill(?:1[0-5]|[1-9]))\b', text)
    if match:
        return match.group(1)
    return ''


def resolve_wrong_skill_name(skill_name: str, wrong_skill_name: str | None) -> str:
    candidate = wrong_skill_name or DEFAULT_WRONG_SKILL_MAP.get(skill_name)
    if not candidate:
        raise ValueError(f'No wrong-skill mapping configured for {skill_name}. Please pass --wrong-skill-name.')
    if candidate == skill_name:
        raise ValueError(f'wrong_skill_name must differ from target skill: {skill_name}')
    find_skill_doc(candidate)
    find_skill_reference(candidate)
    return candidate


def evaluate_answer(item: dict, run_type: str, parsed: dict) -> dict:
    selected_option_label, selected_option_text = resolve_selected_option(parsed=parsed, item=item)
    gold_label = str(item.get('correct_answer', '')).strip().upper()
    option_map = extract_option_map(item)
    gold_text = option_map.get(gold_label, '')
    is_correct = bool(selected_option_label) and selected_option_label == gold_label
    return {
        'item_id': item['id'],
        'split': item['split'],
        'run_type': run_type,
        'question': item['question'],
        'gold_option_label': gold_label,
        'gold_option_text': gold_text,
        'selected_option_label': selected_option_label,
        'selected_option_text': selected_option_text,
        'option_correct': 'yes' if is_correct else 'no',
        'should_trigger_skill': parsed.get('should_trigger_skill', ''),
        'did_trigger_skill_correctly': parsed.get('did_trigger_skill_correctly', ''),
        'decision_variable_identified': parsed.get('decision_variable_identified', ''),
        'shortcut_avoided': parsed.get('shortcut_avoided', ''),
        'boundary_respected': parsed.get('boundary_respected', ''),
        'reasoning_summary': parsed.get('reasoning_summary', ''),
        'notes': parsed.get('notes', ''),
    }


def evaluate_route_and_solve(item: dict, parsed: dict) -> dict:
    option_map = extract_option_map(item)
    predicted_skill = resolve_skill_name(parsed.get('predicted_skill', ''))
    closest_alternative_skill = resolve_skill_name(parsed.get('closest_alternative_skill', ''))
    selected_option_label, selected_option_text = resolve_selected_option(parsed=parsed, item=item)
    gold_skill = str(item.get('skill', '')).strip().lower()
    gold_label = str(item.get('correct_answer', '')).strip().upper()
    gold_text = option_map.get(gold_label, '')
    routing_correct = bool(predicted_skill) and predicted_skill == gold_skill
    answer_correct = bool(selected_option_label) and selected_option_label == gold_label
    both_correct = routing_correct and answer_correct
    return {
        'item_id': item.get('item_id', item.get('id', '')),
        'source_dataset': item.get('source_dataset', item.get('dataset', '')),
        'task_type': item.get('task_type', ''),
        'ability': item.get('ability', ''),
        'gold_skill': gold_skill,
        'predicted_skill': predicted_skill,
        'routing_correct': 'yes' if routing_correct else 'no',
        'closest_alternative_skill': closest_alternative_skill,
        'question': item['question'],
        'gold_option_label': gold_label,
        'gold_option_text': gold_text,
        'selected_option_label': selected_option_label,
        'selected_option_text': selected_option_text,
        'answer_correct': 'yes' if answer_correct else 'no',
        'both_correct': 'yes' if both_correct else 'no',
        'decision_variable': parsed.get('decision_variable', ''),
        'routing_reasoning_summary': parsed.get('routing_reasoning_summary', ''),
        'answer_reasoning_summary': parsed.get('answer_reasoning_summary', ''),
        'notes': parsed.get('notes', ''),
        'gpt_5_4_mini_predicted': item.get('gpt_5_4_mini_predicted', ''),
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def summarize_legacy(rows: list[dict]) -> dict:
    summary = {}
    by_run = {}
    for row in rows:
        by_run.setdefault(row['run_type'], []).append(row)
    for run_type, items in by_run.items():
        total = len(items)
        correct = sum(1 for item in items if item['option_correct'] == 'yes')
        summary[run_type] = {
            'total': total,
            'correct': correct,
            'accuracy': (correct / total) if total else 0.0,
        }
    return summary


def _accuracy_from_flags(rows: list[dict], field_name: str) -> float:
    total = len(rows)
    if not total:
        return 0.0
    correct = sum(1 for row in rows if row[field_name] == 'yes')
    return correct / total


def summarize_route_and_solve(rows: list[dict]) -> dict:
    total = len(rows)
    routing_correct = sum(1 for row in rows if row['routing_correct'] == 'yes')
    answer_correct = sum(1 for row in rows if row['answer_correct'] == 'yes')
    both_correct = sum(1 for row in rows if row['both_correct'] == 'yes')

    routed_right_rows = [row for row in rows if row['routing_correct'] == 'yes']
    routed_wrong_rows = [row for row in rows if row['routing_correct'] == 'no']

    outcome_buckets = {
        'route_correct_answer_correct': sum(1 for row in rows if row['routing_correct'] == 'yes' and row['answer_correct'] == 'yes'),
        'route_correct_answer_wrong': sum(1 for row in rows if row['routing_correct'] == 'yes' and row['answer_correct'] == 'no'),
        'route_wrong_answer_correct': sum(1 for row in rows if row['routing_correct'] == 'no' and row['answer_correct'] == 'yes'),
        'route_wrong_answer_wrong': sum(1 for row in rows if row['routing_correct'] == 'no' and row['answer_correct'] == 'no'),
    }

    per_skill = {}
    for skill_name in ALL_SKILLS:
        skill_rows = [row for row in rows if row['gold_skill'] == skill_name]
        if not skill_rows:
            continue
        per_skill[skill_name] = {
            'total': len(skill_rows),
            'routing_correct': sum(1 for row in skill_rows if row['routing_correct'] == 'yes'),
            'routing_accuracy': _accuracy_from_flags(skill_rows, 'routing_correct'),
            'answer_correct': sum(1 for row in skill_rows if row['answer_correct'] == 'yes'),
            'answer_accuracy': _accuracy_from_flags(skill_rows, 'answer_correct'),
            'both_correct': sum(1 for row in skill_rows if row['both_correct'] == 'yes'),
            'both_accuracy': _accuracy_from_flags(skill_rows, 'both_correct'),
            'route_correct_answer_correct': sum(1 for row in skill_rows if row['routing_correct'] == 'yes' and row['answer_correct'] == 'yes'),
            'route_correct_answer_wrong': sum(1 for row in skill_rows if row['routing_correct'] == 'yes' and row['answer_correct'] == 'no'),
            'route_wrong_answer_correct': sum(1 for row in skill_rows if row['routing_correct'] == 'no' and row['answer_correct'] == 'yes'),
            'route_wrong_answer_wrong': sum(1 for row in skill_rows if row['routing_correct'] == 'no' and row['answer_correct'] == 'no'),
        }

    confusion_counter = Counter(
        (row['gold_skill'], row['predicted_skill'] or 'unparsed')
        for row in rows
        if row['routing_correct'] == 'no'
    )
    routing_confusions = [
        {
            'gold_skill': gold_skill,
            'predicted_skill': predicted_skill,
            'count': count,
        }
        for (gold_skill, predicted_skill), count in sorted(
            confusion_counter.items(),
            key=lambda item: (-item[1], item[0][0], item[0][1]),
        )
    ]

    predicted_distribution = Counter(row['predicted_skill'] or 'unparsed' for row in rows)

    return {
        'overall': {
            'total': total,
            'routing_correct': routing_correct,
            'routing_accuracy': (routing_correct / total) if total else 0.0,
            'answer_correct': answer_correct,
            'answer_accuracy': (answer_correct / total) if total else 0.0,
            'both_correct': both_correct,
            'both_accuracy': (both_correct / total) if total else 0.0,
            'answer_accuracy_given_routing_correct': _accuracy_from_flags(routed_right_rows, 'answer_correct'),
            'answer_accuracy_given_routing_wrong': _accuracy_from_flags(routed_wrong_rows, 'answer_correct'),
            'route_correct_answer_correct': outcome_buckets['route_correct_answer_correct'],
            'route_correct_answer_wrong': outcome_buckets['route_correct_answer_wrong'],
            'route_wrong_answer_correct': outcome_buckets['route_wrong_answer_correct'],
            'route_wrong_answer_wrong': outcome_buckets['route_wrong_answer_wrong'],
        },
        'per_skill': per_skill,
        'predicted_skill_distribution': dict(sorted(predicted_distribution.items())),
        'routing_confusions': routing_confusions,
    }


def run_skill_validation(
    skill_name: str,
    model: str,
    run_types: list[str],
    temperature: float,
    timeout: float,
    max_retries: int,
    reasoning_enabled: bool,
    limit: int | None,
    wrong_skill_name: str | None,
) -> dict:
    pack = load_json(find_validation_pack(skill_name))
    items = pack['items'][:limit] if limit else pack['items']
    all_rows = []
    resolved_wrong_skill = resolve_wrong_skill_name(skill_name, wrong_skill_name) if 'wrong_skill' in run_types else None
    raw_payload = {'mode': 'legacy', 'skill': skill_name, 'model': model, 'wrong_skill_name': resolved_wrong_skill, 'runs': []}
    for run_type in run_types:
        for item in items:
            active_skill_name = resolved_wrong_skill if run_type == 'wrong_skill' else skill_name
            messages = build_legacy_messages(skill_name, run_type, item, skill_name_for_prompt=active_skill_name)
            raw_text = call_model_api(
                model=model,
                messages=messages,
                temperature=temperature,
                timeout=timeout,
                max_retries=max_retries,
                reasoning_enabled=reasoning_enabled,
            )
            parsed = parse_model_json(raw_text)
            row = evaluate_answer(item=item, run_type=run_type, parsed=parsed)
            all_rows.append(row)
            raw_payload['runs'].append({
                'run_type': run_type,
                'prompt_skill_name': active_skill_name,
                'item_id': item.get('id', item.get('item_id', '')),
                'raw_response': raw_text,
                'parsed_response': parsed,
            })

    output_dir = RESULTS_ROOT / skill_name / model.replace('/', '_')
    write_json(output_dir / 'raw_results.json', raw_payload)
    write_json(output_dir / 'summary.json', summarize_legacy(all_rows))
    write_csv(output_dir / 'scored_rows.csv', all_rows)
    return {'mode': 'legacy', 'skill': skill_name, 'model': model, 'output_dir': str(output_dir)}


def run_route_and_solve_validation(
    pack_path: Path,
    model: str,
    temperature: float,
    timeout: float,
    max_retries: int,
    reasoning_enabled: bool,
    limit: int | None,
) -> dict:
    pack = load_json(pack_path)
    items = pack['items'][:limit] if limit else pack['items']
    pack_name = pack.get('pack_name', pack_path.stem)
    all_rows = []
    raw_payload = {
        'mode': 'route_and_solve',
        'pack_name': pack_name,
        'model': model,
        'runs': [],
    }

    for item in items:
        messages = build_route_and_solve_messages(item)
        raw_text = call_model_api(
            model=model,
            messages=messages,
            temperature=temperature,
            timeout=timeout,
            max_retries=max_retries,
            reasoning_enabled=reasoning_enabled,
        )
        parsed = parse_model_json(raw_text)
        row = evaluate_route_and_solve(item=item, parsed=parsed)
        all_rows.append(row)
        raw_payload['runs'].append({
            'item_id': item.get('item_id', item.get('id', '')),
            'raw_response': raw_text,
            'parsed_response': parsed,
        })

    output_dir = RESULTS_ROOT / pack_name / model.replace('/', '_') / 'route_and_solve'
    write_json(output_dir / 'raw_results.json', raw_payload)
    write_json(output_dir / 'summary.json', summarize_route_and_solve(all_rows))
    write_csv(output_dir / 'scored_rows.csv', all_rows)
    return {
        'mode': 'route_and_solve',
        'pack_name': pack_name,
        'model': model,
        'output_dir': str(output_dir),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run legacy skill validation or one-call route-and-solve validation.')
    parser.add_argument('--mode', default='legacy', choices=['legacy', 'route_and_solve'])
    parser.add_argument('--skill', default=None, help='Legacy mode only. Supported: skill3, skill8, skill14.')
    parser.add_argument('--pack', default=None, help='Route-and-solve mode only. Defaults to gpt54mini_positive_routing_pack.json.')
    parser.add_argument('--model', required=True)
    parser.add_argument('--run-types', nargs='+', default=['baseline', 'with_skill'], choices=['baseline', 'with_skill', 'wrong_skill'])
    parser.add_argument('--wrong-skill-name', default=None, help='Legacy mode only. Skill to inject for wrong_skill runs.')
    parser.add_argument('--temperature', type=float, default=0.0)
    parser.add_argument('--timeout', type=float, default=DEFAULT_TIMEOUT, help='Per-request timeout in seconds.')
    parser.add_argument('--max-retries', type=int, default=DEFAULT_MAX_RETRIES, help='Retry count for timeout, rate limit, and connection errors.')
    parser.add_argument('--disable-reasoning', action='store_true', help='Disable the OpenRouter reasoning extra_body for faster or cheaper runs.')
    parser.add_argument('--limit', type=int, default=None, help='Optional limit on how many validation items to run.')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.mode == 'legacy':
        if args.skill not in LEGACY_SKILL_CHOICES:
            raise ValueError(f'Legacy mode requires --skill to be one of: {", ".join(LEGACY_SKILL_CHOICES)}')
        result = run_skill_validation(
            args.skill,
            args.model,
            args.run_types,
            args.temperature,
            args.timeout,
            args.max_retries,
            not args.disable_reasoning,
            args.limit,
            args.wrong_skill_name,
        )
    else:
        pack_path = find_route_and_solve_pack(args.pack)
        result = run_route_and_solve_validation(
            pack_path=pack_path,
            model=args.model,
            temperature=args.temperature,
            timeout=args.timeout,
            max_retries=args.max_retries,
            reasoning_enabled=not args.disable_reasoning,
            limit=args.limit,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
