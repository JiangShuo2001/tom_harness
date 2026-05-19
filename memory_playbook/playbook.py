"""Playbook parsing and filtering.

Bullet line format:
    [slug-00001] helpful=N harmful=M buckets={fb:5/7,fp:1/3} :: content

- helpful / harmful: aggregate counters across all subtask buckets.
- buckets: per-subtask helpful/total counts. Optional; legacy lines without
  `buckets={...}` store the aggregate under an implicit GLOBAL_BUCKET.
"""
import json
import re

GLOBAL_BUCKET = "_global"


def _parse_buckets(bucket_str):
    buckets = {}
    if not bucket_str:
        return buckets
    for part in bucket_str.split(','):
        part = part.strip()
        if not part:
            continue
        m = re.match(r'([^:\s]+)\s*:\s*(\d+)\s*/\s*(\d+)', part)
        if m:
            buckets[m.group(1)] = {'h': int(m.group(2)), 'n': int(m.group(3))}
    return buckets


def _format_buckets(buckets):
    if not buckets:
        return ''
    parts = []
    for name in sorted(buckets.keys()):
        b = buckets[name]
        h = int(b.get('h', 0))
        n = int(b.get('n', 0))
        if n == 0 and h == 0:
            continue
        parts.append(f"{name}:{h}/{n}")
    return ','.join(parts)


def _aggregate_counts(buckets):
    h = sum(b.get('h', 0) for b in buckets.values())
    n = sum(b.get('n', 0) for b in buckets.values())
    return h, max(0, n - h)


def parse_playbook_line(line):
    """Parse a single playbook line. Returns dict or None."""
    pattern = (
        r'\[([^\]]+)\]\s*'
        r'helpful=(\d+)\s*harmful=(\d+)'
        r'(?:\s*buckets=\{([^}]*)\})?'
        r'\s*::\s*(.*)'
    )
    match = re.match(pattern, line.strip())
    if not match:
        return None

    bullet_id = match.group(1)
    helpful = int(match.group(2))
    harmful = int(match.group(3))
    bucket_str = match.group(4) or ''
    content = match.group(5)

    buckets = _parse_buckets(bucket_str)
    if not buckets:
        if helpful or harmful:
            buckets[GLOBAL_BUCKET] = {'h': helpful, 'n': helpful + harmful}

    return {
        'id': bullet_id,
        'helpful': helpful,
        'harmful': harmful,
        'buckets': buckets,
        'content': content,
        'raw_line': line,
    }


def format_playbook_line(bullet_id, helpful, harmful, content, buckets=None):
    if buckets:
        agg_h, agg_harm = _aggregate_counts(buckets)
        helpful, harmful = agg_h, agg_harm
        bucket_str = _format_buckets(buckets)
        if bucket_str:
            return (
                f"[{bullet_id}] helpful={helpful} harmful={harmful} "
                f"buckets={{{bucket_str}}} :: {content}"
            )
    return f"[{bullet_id}] helpful={helpful} harmful={harmful} :: {content}"


def extract_json_from_text(text, json_key=None):
    """Extract a JSON object from an LLM response. Returns dict or None."""
    try:
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        json_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue

        def find_json_objects(text):
            objs = []
            i = 0
            while i < len(text):
                if text[i] == '{':
                    depth = 1
                    start = i
                    i += 1
                    while i < len(text) and depth > 0:
                        if text[i] == '{':
                            depth += 1
                        elif text[i] == '}':
                            depth -= 1
                        elif text[i] == '"':
                            i += 1
                            while i < len(text) and text[i] != '"':
                                if text[i] == '\\':
                                    i += 1
                                i += 1
                        i += 1
                    if depth == 0:
                        objs.append(text[start:i])
                else:
                    i += 1
            return objs

        for json_str in find_json_objects(text):
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue
    except Exception as e:
        print(f"Failed to extract JSON: {e}")

    return None


def filter_playbook_to_bullets(playbook_text, bullet_ids):
    """Return a playbook text containing only the bullets in `bullet_ids`,
    preserving section headers that still have at least one surviving bullet.

    Unlike the ACE source, this returns an empty string when `bullet_ids` is
    empty — the memory module's contract is "no fallback to full playbook".
    """
    if not bullet_ids:
        return ""

    keep = set(bullet_ids)
    lines = playbook_text.strip().split('\n')

    sections = []
    current_header = None
    current_body = []
    for line in lines:
        if line.strip().startswith('##'):
            sections.append((current_header, current_body))
            current_header = line
            current_body = []
        else:
            current_body.append(line)
    sections.append((current_header, current_body))

    out = []
    for header, body in sections:
        kept_body = []
        for line in body:
            parsed = parse_playbook_line(line)
            if parsed:
                if parsed['id'] in keep:
                    kept_body.append(line)
            else:
                kept_body.append(line)
        if any(parse_playbook_line(l) for l in kept_body):
            if header is not None:
                out.append(header)
            out.extend(kept_body)

    if not out:
        return ""
    return '\n'.join(out)


def extract_known_subtasks(playbook_text):
    """Walk every parsed bullet, collect bucket keys other than GLOBAL_BUCKET."""
    subtasks = set()
    for line in playbook_text.split('\n'):
        parsed = parse_playbook_line(line)
        if parsed:
            for key in parsed['buckets']:
                if key != GLOBAL_BUCKET:
                    subtasks.add(key)
    return sorted(subtasks)
