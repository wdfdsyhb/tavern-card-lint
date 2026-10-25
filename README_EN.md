# tavern-card-lint

[![CI](https://github.com/wdfdsyhb/tavern-card-lint/actions/workflows/tests.yml/badge.svg)](https://github.com/wdfdsyhb/tavern-card-lint/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)

> Feed it a character card PNG, get an error/warning list — broken openings and dead lorebook entries caught before you ship.

## What it checks

| Level | Check |
|---|---|
| error | name / description / first_mes empty (the card can't open a scene) |
| error | `alternate_greetings` not a list, `character_book` not an object |
| warning | personality / scenario / mes_example empty (recommended to fill) |
| warning | Lorebook entry with no keys (**can never trigger**, the most common source of dead entries) |
| warning | Lorebook entry with empty content |

Supports V2/V3 cards (PNG-embedded `chara` / `ccv3` tEXt chunks).

## Usage

```bash
python tavern_card_lint.py character.png
python tavern_card_lint.py *.png --json report.json   # batch + export
python tavern_card_lint.py pack/*.png -q              # only the problematic ones
```

Output:

```
[warning] character_book: entry 3 ('hidden lore') has no keys - it can never trigger
(character.png: 0 errors, 1 warnings)
```

Exit code 1 when an error is found, so it fits a pre-release check pipeline.

## How it works

A PNG is a chunk structure with CRCs; a `tEXt` chunk stores `keyword\0text` pairs. SillyTavern base64-encodes the whole card into the `chara` keyword. This tool hand-writes the chunk traversal (~30 lines) and doesn't depend on Pillow — which is also why it can catch cards with corrupted chunk structures.

## Notes

- Structure and completeness checks only; it doesn't judge your card-writing skills
- Zero dependencies, standard library only

## License

MIT

> 🇨🇳 中文文档: [README.md](README.md)
