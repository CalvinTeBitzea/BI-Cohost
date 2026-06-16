"""
Tiny markdown helpers shared by the skill and template registries.

SKILL.md and TEMPLATE.md are authored as human-readable markdown with YAML-ish
frontmatter, GitHub-style tables, and `##` sections. These helpers parse just
enough of that to drive the registries — no full markdown dependency.
"""
import re

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split leading `--- ... ---` frontmatter from the body.

    Returns (frontmatter_dict, body). Frontmatter is parsed as simple
    `key: value` lines (no nested YAML). If absent, returns ({}, text).
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm: dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        fm[key.strip()] = val.strip()
    return fm, text[m.end():]


def extract_section(text: str, heading_substr: str) -> str:
    """Return the body of the first `##`/`###` section whose title contains
    `heading_substr` (case-insensitive), up to the next heading of level <= 2.
    Empty string if not found.
    """
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^#{1,6}\s", line) and heading_substr.lower() in line.lower():
            start = i + 1
            break
    if start is None:
        return ""
    out = []
    for line in lines[start:]:
        if re.match(r"^#{1,2}\s", line):  # next top-level/section heading ends it
            break
        out.append(line)
    return "\n".join(out)


def parse_table(chunk: str) -> list[dict]:
    """Parse the first GitHub-style markdown table found in `chunk`.

    Returns a list of row dicts keyed by header cell text. Cells are stripped.
    The `|---|` separator row is skipped. Returns [] if no table is present.
    """
    rows = [ln for ln in chunk.splitlines() if ln.strip().startswith("|")]
    if len(rows) < 2:
        return []

    def cells(line: str) -> list[str]:
        parts = line.strip().split("|")
        # drop the empty strings produced by leading/trailing pipes
        return [p.strip() for p in parts[1:-1]] if len(parts) >= 2 else []

    header = cells(rows[0])
    out = []
    for line in rows[2:]:  # skip header + separator
        c = cells(line)
        if not c or set("".join(c)) <= set("-: "):
            continue
        out.append({header[i]: (c[i] if i < len(c) else "") for i in range(len(header))})
    return out
