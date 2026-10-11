#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tavern-card-lint - validate SillyTavern / TavernAI character cards before they break.

Reads the PNG 'chara'/'ccv3' tEXt chunk, parses the embedded card JSON,
and reports errors (missing name/first_mes, wrong types) and warnings
(world book entries that can never trigger, empty recommended fields).

Zero third-party dependencies.
"""

import argparse
import base64
import json
import re
import sys
from pathlib import Path

__version__ = "0.1.0"

PNG_SIG = b"\x89PNG\r\n\x1a\n"
CARD_KEYS = ("chara", "ccv3")
REQUIRED_FIELDS = ("name", "description", "first_mes")
RECOMMENDED_FIELDS = ("personality", "scenario", "mes_example")


class CardFormatError(Exception):
    pass


def read_card_bytes(data):
    """Extract the card JSON from PNG tEXt chunks (keyword: chara or ccv3)."""
    if not data.startswith(PNG_SIG):
        raise CardFormatError("not a PNG file")
    pos, texts = 8, {}
    while pos + 8 <= len(data):
        length = int.from_bytes(data[pos:pos + 4], "big")
        ctype = data[pos + 4:pos + 8]
        cdata = data[pos + 8:pos + 8 + length]
        if ctype == b"tEXt":
            keyword, _, value = cdata.partition(b"\x00")
            texts[keyword.decode("latin-1")] = value.decode("latin-1", "replace")
        if ctype == b"IEND":
            break
        pos += 12 + length
    for key in CARD_KEYS:
        if key in texts:
            try:
                return json.loads(base64.b64decode(texts[key]))
            except Exception:
                continue
    raise CardFormatError(f"no character data found (looked for tEXt chunks: {', '.join(CARD_KEYS)})")


def lint(card):
    """Return a list of issues: {'level': 'error'|'warning', 'field': str, 'message': str}."""
    issues = []
    for f in REQUIRED_FIELDS:
        if not str(card.get(f) or "").strip():
            issues.append({"level": "error", "field": f,
                           "message": f"empty or missing '{f}' - the card cannot start properly"})
    for f in RECOMMENDED_FIELDS:
        if not str(card.get(f) or "").strip():
            issues.append({"level": "warning", "field": f,
                           "message": f"empty '{f}' (optional but recommended)"})
    alt = card.get("alternate_greetings")
    if alt is not None and not isinstance(alt, list):
        issues.append({"level": "error", "field": "alternate_greetings",
                       "message": "'alternate_greetings' should be a list"})
    book = card.get("character_book")
    if isinstance(book, dict):
        entries = book.get("entries")
        if not isinstance(entries, list):
            issues.append({"level": "warning", "field": "character_book",
                           "message": "'entries' missing or not a list"})
        else:
            for i, e in enumerate(entries):
                if not isinstance(e, dict):
                    issues.append({"level": "warning", "field": "character_book",
                                   "message": f"entry {i} is not an object"})
                    continue
                if not e.get("keys") and not e.get("key"):
                    issues.append({"level": "warning", "field": "character_book",
                                   "message": f"entry {i} ('{e.get('comment', '?')}') has no keys - it can never trigger"})
                if not str(e.get("content") or "").strip():
                    issues.append({"level": "warning", "field": "character_book",
                                   "message": f"entry {i} has empty content"})
    elif book is not None:
        issues.append({"level": "error", "field": "character_book",
                       "message": "'character_book' should be an object"})
    return issues


def render(issues, source):
    if not issues:
        return f"[clean] {source}"
    lines = []
    for i in issues:
        lines.append(f"[{i['level']}] {i['field']}: {i['message']}")
    lines.append(f"({source}: {sum(1 for x in issues if x['level'] == 'error')} errors, "
                 f"{sum(1 for x in issues if x['level'] == 'warning')} warnings)")
    return "\n".join(lines)


EXAMPLES = """examples:
  python tavern_card_lint.py character.png
  python tavern_card_lint.py *.png --json report.json
"""


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="tavern-card-lint", description=__doc__.strip().splitlines()[0],
        epilog=EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cards", nargs="+", help="character card PNG file(s)")
    ap.add_argument("--json", dest="json_out", help="write JSON issues to file")
    ap.add_argument("-q", "--quiet", action="store_true", help="only print cards with issues")
    ap.add_argument("-V", "--version", action="version", version=f"tavern-card-lint {__version__}")
    args = ap.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    all_issues = []
    had_error = False
    for raw in args.cards:
        path = Path(raw).expanduser()
        try:
            card = read_card_bytes(path.read_bytes())
            issues = lint(card)
        except CardFormatError as e:
            issues = [{"level": "error", "field": "file", "message": str(e)}]
        all_issues.append({"file": str(path), "issues": issues})
        if issues:
            had_error = had_error or any(i["level"] == "error" for i in issues)
            print(render(issues, path), flush=True)
        elif not args.quiet:
            print(render([], path), flush=True)

    if args.json_out:
        Path(args.json_out).expanduser().write_text(
            json.dumps(all_issues, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if had_error else 0


if __name__ == "__main__":
    sys.exit(main())
