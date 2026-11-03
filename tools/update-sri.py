#!/usr/bin/env python3
"""Recompute the Subresource Integrity hashes (sha384).

Updates:
  1. the hash of vendor/sql-asm.js inside js/main.js (asm.js fallback loader),
  2. then the hash of every script listed in js/boot.js.
js/main.js is updated first because its own hash depends on that change.

Run after any change to a JavaScript file:  python3 tools/update-sri.py
"""
import base64
import hashlib
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent


def sri(path: str) -> str:
    """Return the sha384 SRI string of a file relative to the project root."""
    digest = hashlib.sha384((ROOT / path).read_bytes()).digest()
    return "sha384-" + base64.b64encode(digest).decode()


def update_main() -> None:
    main = ROOT / "js/main.js"
    text = main.read_text(encoding="utf-8")
    text = re.sub(r's\.integrity = "sha384-[^"]*"', 's.integrity = "' + sri("vendor/sql-asm.js") + '"', text)
    main.write_text(text, encoding="utf-8")


def update_boot() -> None:
    boot = ROOT / "js/boot.js"
    text = boot.read_text(encoding="utf-8")
    text = re.sub(r'\["([^"]+)", "[^"]*"\]', lambda m: '["%s", "%s"]' % (m.group(1), sri(m.group(1))), text)
    boot.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    update_main()
    update_boot()
    print("SRI hashes updated")
