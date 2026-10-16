#!/usr/bin/env python3
"""Exporta campeonato.db a web/datos.json para la web."""
import json, os, re, sqlite3, unicodedata
from collections import defaultdict
from datetime import datetime, timezone

con = sqlite3.connect(os.environ.get("DB_PATH", "campeonato.db"))
SHORT = {"La Maravillosa Orquesta del Alcohol": "La M.O.D.A."}
clave = lambda s: re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()) or s

# nombre canónico por artista: la variante con más escuchas (a igualdad, la que lleva tilde)
vari = defaultdict(lambda: defaultdict(int))
for a, n in con.execute("SELECT artista, SUM(escuchas) FROM escuchas_mes GROUP BY artista"): vari[clave(a)][a] += n
for a, n in con.execute("SELECT artista, SUM(escuchas) FROM base_anio GROUP BY artista"): vari[clave(a)][a] += n
canon = {k: max(v, key=lambda x: (not x.isascii(), v[x])) for k, v in vari.items()}   # prefiere la variante con tilde, como Last.fm
nm = lambda a: SHORT.get(canon[clave(a)], canon[clave(a)])

meses = {}
for mes, art, esc, pos, pts, emp in con.execute(
        "SELECT mes, artista, escuchas, pos, puntos, empate FROM v_gp ORDER BY mes, pos"):
    meses.setdefault(mes, []).append([nm(art), esc, pos, pts, int(emp)])
abierto = [m for m, c in con.execute("SELECT mes, cerrado FROM meses") if not c]

# escuchas totales por artista y año: meses cerrados (base) + meses posteriores completos
base_hasta = con.execute("SELECT valor FROM meta WHERE clave='base_hasta'").fetchone()[0]
per = defaultdict(lambda: defaultdict(int)); nombre = {}
for y, a, n in con.execute("SELECT anio, artista, escuchas FROM base_anio"): per[clave(a)][y] += n; nombre[clave(a)] = nm(a)
for mes, a, n in con.execute("SELECT mes, artista, escuchas FROM escuchas_mes WHERE mes > ?", (base_hasta,)):
    per[clave(a)][mes[:4]] += n; nombre.setdefault(clave(a), nm(a))
tot_anio = defaultdict(int)
for y, t in con.execute("SELECT anio, total FROM base_total"): tot_anio[y] += t
for mes, t, s in con.execute("SELECT m.mes, m.total, (SELECT SUM(escuchas) FROM escuchas_mes e WHERE e.mes=m.mes) FROM meses m WHERE m.mes > ?", (base_hasta,)):
    tot_anio[mes[:4]] += t if t is not None else (s or 0)
artistas = sorted(([nombre[k], sum(v.values()), dict(v)] for k, v in per.items()), key=lambda x: -x[1])[:80]
out = {"meses": meses, "abierto": abierto,
       "escuchas": {"totalAnio": dict(tot_anio), "total": sum(tot_anio.values()), "artistas": artistas},
       "actualizado": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
json.dump(out, open("web/datos.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(len(meses), "meses,", len(artistas), "artistas con escuchas")
