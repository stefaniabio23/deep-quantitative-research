"""Small markdown emitters used by the signal-card renderer."""

from __future__ import annotations

from typing import Iterable


def kv_table(rows: Iterable[tuple[str, str]]) -> str:
    lines = ["| Field | Value |", "| --- | --- |"]
    for k, v in rows:
        lines.append(f"| {k} | {v} |")
    return "\n".join(lines)


def section(title: str, body: str) -> str:
    body = (body or "").strip()
    return f"## {title}\n\n{body}\n"


def bullets(items: Iterable[str]) -> str:
    out = [f"- {x}" for x in items if x]
    return "\n".join(out)
