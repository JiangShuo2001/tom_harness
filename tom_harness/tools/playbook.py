"""MemoryPlaybook — static playbook loader.

Loads pre-built playbook files (ACE-framework strategy collections) from
a directory and provides their content for prompt context injection.

Unlike MemoryStore (which stores and retrieves task-plan pairs dynamically),
the playbook is loaded once and injected in full into the planner/executor
context as fixed guidance. The two will be unified in a future iteration.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_PLAYBOOK_DIR = str(Path(__file__).resolve().parent.parent.parent / "memory_playbook")


@dataclass
class MemoryPlaybook:
    """Load and serve static memory playbook content."""

    playbook_dir: str = _DEFAULT_PLAYBOOK_DIR
    _content: str = field(default="", init=False, repr=False)
    _ready: bool = field(default=False, init=False, repr=False)

    def load(self) -> None:
        """Load all .txt/.md files from the playbook directory."""
        path = Path(self.playbook_dir)
        if not path.exists():
            logger.warning("[MemoryPlaybook] directory %s does not exist", path)
            return
        parts: list[str] = []
        for f in sorted(path.iterdir()):
            if f.suffix in (".txt", ".md") and f.is_file():
                text = f.read_text(encoding="utf-8").strip()
                if text:
                    parts.append(text)
                    logger.info("[MemoryPlaybook] Loaded %s (%d chars)", f.name, len(text))
        if parts:
            self._content = "\n\n".join(parts)
            self._ready = True
            logger.info("[MemoryPlaybook] Ready — %d files, %d total chars",
                        len(parts), len(self._content))
        else:
            logger.info("[MemoryPlaybook] No playbook files found in %s", path)

    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def content(self) -> str:
        return self._content

    def size(self) -> int:
        return len(self._content)
