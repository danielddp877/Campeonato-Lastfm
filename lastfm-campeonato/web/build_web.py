#!/usr/bin/env python3
"""Mete web/datos.json dentro de template.html y genera web/index.html (se abre con doble clic)."""
import json
t = open("web/template.html", encoding="utf-8").read()
d = open("web/datos.json", encoding="utf-8").read()
body = t.replace("/*__DATA__*/null", d)
open("web/pagina.html", "w", encoding="utf-8").write(body)   # fragmento para publicar
open("web/index.html", "w", encoding="utf-8").write(
    '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    + body.replace("<title>", "<title>", 1) + "</body></html>")
print("web/index.html listo")
