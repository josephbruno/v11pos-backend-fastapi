#!/usr/bin/env python3
"""Replace datetime.utcnow with utc_now_naive across the backend."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "app"
IMPORT_LINE = "from app.core.database import utc_now_naive\n"


def ensure_import(content: str) -> str:
    if "utc_now_naive" not in content:
        return content
    if "from app.core.database import" in content:
        if re.search(r"from app\.core\.database import[^\n]*utc_now_naive", content):
            return content

        def add_import(match: re.Match[str]) -> str:
            names = [n.strip() for n in match.group(1).split(",")]
            if "utc_now_naive" not in names:
                names.append("utc_now_naive")
            return "from app.core.database import " + ", ".join(names)

        return re.sub(
            r"from app\.core\.database import ([^\n]+)",
            add_import,
            content,
            count=1,
        )

    datetime_import = re.search(r"^from datetime import ([^\n]+)$", content, re.M)
    if datetime_import:
        return content.replace(
            datetime_import.group(0),
            datetime_import.group(0) + "\n" + IMPORT_LINE.rstrip(),
            1,
        )
    return IMPORT_LINE + content


def process_file(path: Path) -> bool:
    if path.name == "database.py" and path.parent.name == "core":
        return False

    original = path.read_text(encoding="utf-8")
    if "datetime.utcnow" not in original:
        return False

    updated = original.replace("datetime.utcnow()", "utc_now_naive()")
    updated = updated.replace("default=datetime.utcnow", "default=utc_now_naive")
    updated = updated.replace("onupdate=datetime.utcnow", "onupdate=utc_now_naive")
    updated = ensure_import(updated)

    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = 0
    for path in sorted(ROOT.rglob("*.py")):
        if process_file(path):
            changed += 1
            print(f"updated {path.relative_to(ROOT.parent)}")
    print(f"done: {changed} files")


if __name__ == "__main__":
    main()
