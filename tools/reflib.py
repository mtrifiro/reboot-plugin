"""Shared model of the skills' reference files, read from their frontmatter.

One parser for every tool, so the generated indices, the budget and the
lint all agree on what a reference says about itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

FRONT_DOORS = ("mcp-ui", "web-app", "backend-only")
# Build order. API before the project shell: the shell's main.py and
# .rbtrc depend on the API module (reboot-air-141 §4).
BUILD_STEPS = ("api", "shell", "servicer", "auth", "frontend", "tests")
STEPS = BUILD_STEPS + ("run", "deploy", "any")
IMPACT_ORDER = ("CRITICAL", "HIGH", "MEDIUM", "LOW-MEDIUM", "LOW")


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    out: dict = {}
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if value.startswith('"'):
            # Quoted string: take up to the closing unescaped quote.
            m2 = re.match(r'"((?:[^"\\]|\\.)*)"', value)
            value = m2.group(1).replace('\\"', '"') if m2 else value.strip('"')
            out[key] = value
            continue
        value = re.sub(r"\s+#.*$", "", value)
        if value.startswith("[") and value.endswith("]"):
            out[key] = [v.strip() for v in value[1:-1].split(",") if v.strip()]
        elif value in ("true", "false"):
            out[key] = value == "true"
        else:
            out[key] = value
    return out


@dataclass
class Ref:
    path: Path
    fm: dict = field(repr=False)

    @property
    def rel(self) -> str:
        """Path under skills/, e.g. python/references/rpc-refs.md."""
        return str(self.path.relative_to(SKILLS))

    @property
    def skill(self) -> str:
        return self.path.parent.parent.name

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def concept(self) -> str:
        return self.path.stem.split("-", 1)[0]

    @property
    def step(self) -> str:
        return self.fm.get("step", "")

    @property
    def applies(self) -> list[str]:
        value = self.fm.get("applies", [])
        return value if isinstance(value, list) else [value]

    @property
    def always(self) -> bool:
        return self.fm.get("always") is True

    @property
    def via(self) -> str:
        return self.fm.get("via", "") or ""

    @property
    def summary(self) -> str:
        return self.fm.get("summary", "")

    @property
    def title(self) -> str:
        return self.fm.get("title", self.path.stem)

    @property
    def impact_rank(self) -> int:
        impact = str(self.fm.get("impact", "")).upper()
        return IMPACT_ORDER.index(impact) if impact in IMPACT_ORDER else len(IMPACT_ORDER)

    def when(self, front_door: str) -> str:
        """The condition for this front door; "" means unconditional."""
        override = f"when-{front_door}"
        if override in self.fm:
            return self.fm[override]
        return self.fm.get("when", "") or ""

    def words(self) -> int:
        return len(self.path.read_text(encoding="utf-8").split())


def load_refs() -> list[Ref]:
    paths = sorted(SKILLS.glob("*/references/*.md"))
    return [Ref(p, parse_frontmatter(p.read_text(encoding="utf-8")))
            for p in paths if not p.name.startswith("_")]


def concepts() -> list[tuple[str, str]]:
    """(prefix, heading) pairs from python/references/_sections.md, in order."""
    text = (SKILLS / "python" / "references" / "_sections.md").read_text(encoding="utf-8")
    return [(m.group(2), m.group(1))
            for m in re.finditer(r"^## \d+\. (.+?) \(([a-z-]+)\)\s*$", text, re.M)]


def reading_list(refs: list[Ref], front_door: str, step: str) -> list[Ref]:
    """References a build of `front_door` reads at `step`, in reading order.

    Unconditional files first, then by impact, then by name. Files
    marked `always` have their own list; files reached `via` a router
    are listed by the router, not here.
    """
    chosen = [r for r in refs
              if r.step == step and front_door in r.applies
              and not r.always and not r.via]
    return sorted(chosen, key=lambda r: (bool(r.when(front_door)), r.impact_rank, r.name))


def always_list(refs: list[Ref], front_door: str) -> list[Ref]:
    return sorted((r for r in refs if r.always and front_door in r.applies),
                  key=lambda r: (r.impact_rank, r.name))


def pinned_reboot_version() -> str:
    m = re.search(r'REBOOT_VERSION="([^"]+)"', (ROOT / "bin" / "rbt").read_text())
    return m.group(1) if m else ""
