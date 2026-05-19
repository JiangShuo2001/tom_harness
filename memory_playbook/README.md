# memory — Portable recall from a trained ACE playbook

A self-contained package that wraps a trained playbook and a selector LLM to
retrieve relevant "bullets" (strategy entries) for a given question.

## Requirements

- Python 3.12+
- `openai` (the only external dependency)

## Quick start

```python
from memory import Memory, SelectorConfig

# Programmatic
memory = Memory(
    playbook_path="playbook/final_playbook.txt",
    selector=SelectorConfig(
        provider="deepseek",
        api_key="sk-...",
        model="deepseek-chat",
    ),
)

# Or from a TOML config file
memory = Memory.from_toml(
    playbook_path="playbook/final_playbook.txt",
    config_path="memory/config.example.toml",
)

# Recall relevant bullets
result = memory.recall("Where does Sally think the marble is?")

result.bullets             # list[Bullet] — may be empty
result.bullet_ids          # list[str]
result.predicted_subtask   # str
result.as_text()           # filtered playbook text ("" when no bullets)
bool(result)               # False when no bullets selected
```

## Configuration

The TOML file needs a `[selector]` table:

```toml
[selector]
provider      = "openai"          # openai | deepseek | together | sambanova | commonstack | qwen | custom
api_key       = "${OPENAI_API_KEY}"  # supports ${ENV_VAR} substitution
model         = "gpt-4o-mini"
# base_url    = "https://..."     # required only when provider = "custom"
max_tokens    = 1024
max_bullets   = 8
use_json_mode = false
```

## No-fallback contract

When the selector returns zero bullets (nothing relevant), `recall()` returns
an empty `RecallResult`. It does **not** fall back to the full playbook. The
caller decides what to do.

## Portability

Copy the entire `memory/` folder into another project. As long as `openai` is
installed, it will work with no other dependencies from this repo.
