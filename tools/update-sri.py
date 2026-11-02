#!/usr/bin/env python3
"""Recalcule les empreintes SRI (sha384) utilisées par js/boot.js et pour vendor/sql-asm.js.
A lancer après toute modification d'un fichier JS : python3 tools/update-sri.py"""
import base64, hashlib, pathlib, re
root = pathlib.Path(__file__).resolve().parent.parent
sri = lambda p: "sha384-" + base64.b64encode(hashlib.sha384((root / p).read_bytes()).digest()).decode()
app = (root / "js/app.js").read_text(encoding="utf-8")
app = re.sub(r's\.integrity = "(?:__SRI_ASM__|sha384-[^"]*)"', 's.integrity = "' + sri("vendor/sql-asm.js") + '"', app)
(root / "js/app.js").write_text(app, encoding="utf-8")
boot = (root / "js/boot.js").read_text(encoding="utf-8")
boot = re.sub(r'\["([^"]+)", "[^"]*"\]', lambda m: '["%s", "%s"]' % (m.group(1), sri(m.group(1))), boot)
(root / "js/boot.js").write_text(boot, encoding="utf-8")
print("SRI mis à jour")
