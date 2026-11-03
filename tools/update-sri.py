#!/usr/bin/env python3
"""Recompute the integrity hashes.

Updates, in this order (each step depends on the previous one):
  1. the SRI hash (sha384) of vendor/sql-asm.js inside js/main.js,
  2. the SRI hash of every script listed in the inline loader of index.html,
  3. the sha256 hash of that inline loader in the Content-Security-Policy,
     so the browser runs the loader only if it is unchanged.

Run after any change to a JavaScript file or to the loader:
    python3 tools/update-sri.py
"""
import base64
import hashlib
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOADER = re.compile(r"(<!-- boot:start -->\n<script>)(.*?)(</script>\n<!-- boot:end -->)", re.S)


def b64(digest: bytes) -> str:
    return base64.b64encode(digest).decode()


def sri(path: str) -> str:
    """sha384 SRI string of a file relative to the project root."""
    return "sha384-" + b64(hashlib.sha384((ROOT / path).read_bytes()).digest())


def update_main() -> None:
    main = ROOT / "js/main.js"
    text = main.read_text(encoding="utf-8")
    text = re.sub(r's\.integrity = "sha384-[^"]*"', 's.integrity = "' + sri("vendor/sql-asm.js") + '"', text)
    main.write_text(text, encoding="utf-8")


def update_index() -> None:
    index = ROOT / "index.html"
    html = index.read_text(encoding="utf-8")
    match = LOADER.search(html)
    if not match:
        raise SystemExit("inline loader markers not found in index.html")
    loader = re.sub(r'\["([^"]+)", "[^"]*"\]', lambda m: '["%s", "%s"]' % (m.group(1), sri(m.group(1))), match.group(2))
    html = html[:match.start(2)] + loader + html[match.end(2):]
    csp_hash = "'sha256-" + b64(hashlib.sha256(loader.encode("utf-8")).digest()) + "'"
    html, n = re.subn(r"script-src 'self'(?: 'sha256-[^']*')?", "script-src 'self' " + csp_hash, html, count=1)
    if n != 1:
        raise SystemExit("script-src not found in the Content-Security-Policy")
    index.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    update_main()
    update_index()
    print("Integrity hashes updated")
