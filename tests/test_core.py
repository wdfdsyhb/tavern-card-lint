import base64
import json
import struct
import zlib

import pytest

import tavern_card_lint as tcl


def png_bytes(text_chunks):
    data = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    for ctype, cdata in [(b"IHDR", ihdr)] + list(text_chunks) + [(b"IEND", b"")]:
        data += struct.pack(">I", len(cdata)) + ctype + cdata
        data += struct.pack(">I", zlib.crc32(ctype + cdata) & 0xFFFFFFFF)
    return data


def make_card_dict(**over):
    card = {"name": "Alice", "description": "A bot", "first_mes": "hi",
            "personality": "", "scenario": "", "mes_example": ""}
    card.update(over)
    return card


def make_card(**over):
    return base64.b64encode(json.dumps(make_card_dict(**over)).encode()).decode()


def card_png(**over):
    return png_bytes([(b"tEXt", b"chara\x00" + make_card(**over).encode())])


def card_png_raw(card):
    encoded = base64.b64encode(json.dumps(card).encode()).decode()
    return png_bytes([(b"tEXt", b"chara\x00" + encoded.encode())])


def test_extract_chara_from_text_chunk():
    card = tcl.read_card_bytes(card_png())
    assert card["name"] == "Alice"


def test_lint_complete_card_no_errors():
    issues = tcl.lint(tcl.read_card_bytes(card_png()))
    assert not [i for i in issues if i["level"] == "error"]


def test_lint_missing_first_mes():
    issues = tcl.lint(tcl.read_card_bytes(card_png(first_mes="")))
    assert any(i["field"] == "first_mes" and i["level"] == "error" for i in issues)


def test_lint_missing_name():
    issues = tcl.lint(tcl.read_card_bytes(card_png(name="")))
    assert any(i["field"] == "name" for i in issues)


def test_lint_worldbook_entry_missing_keys():
    card = make_card_dict(character_book={"entries": [{"content": "x", "comment": "no keys"}]})
    issues = tcl.lint(tcl.read_card_bytes(card_png_raw(card)))
    wb = [i for i in issues if i["field"] == "character_book"]
    assert wb and all(i["level"] == "warning" for i in wb)


def test_not_a_png_raises():
    with pytest.raises(tcl.CardFormatError):
        tcl.read_card_bytes(b"this is definitely not a png file.........")


def test_png_without_chara_raises():
    with pytest.raises(tcl.CardFormatError):
        tcl.read_card_bytes(png_bytes([(b"tEXt", b"other\x00hello")]))
