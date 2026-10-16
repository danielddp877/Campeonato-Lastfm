#!/usr/bin/env python3
"""Carga los datos descargados de Last.fm (hora de Madrid) en campeonato.db:
 datos_madrid.json  top 13 por mes      datos_14_20.json  puestos 14 a 20 (participación)
 datos_oct.json     mes en curso        datos_base.json   totales por artista y año"""
import json, sqlite3, os
con = sqlite3.connect(os.environ.get("DB_PATH", "campeonato.db"))
con.executescript(open("schema.sql", encoding="utf-8").read())
cargar = lambda f: json.load(open(f, encoding="utf-8"))
d, ex, b, oc = cargar("datos_madrid.json"), cargar("datos_14_20.json"), cargar("datos_base.json"), cargar("datos_oct.json")
for mes in d:
    d[mes] = d[mes] + ex.get(mes, [])
ult = max(d)
d[ult] = oc["rows"]                                       # el mes en curso, completo
totales = {ult: oc["total"]}
with con:
    for mes, arts in d.items():
        con.execute("DELETE FROM escuchas_mes WHERE mes=?", (mes,))
        con.executemany("INSERT INTO escuchas_mes VALUES (?,?,?,?)", [(mes, a, n, ts) for a, n, ts in arts])
        con.execute("INSERT OR REPLACE INTO meses VALUES (?,?,datetime('now'),?)", (mes, int(mes != ult), totales.get(mes)))
    con.execute("DELETE FROM base_anio"); con.execute("DELETE FROM base_total")
    for nombre, *por_anio in b["top"]:
        for y, n in zip(["2023", "2024", "2025", "2026"], por_anio):
            if n: con.execute("INSERT INTO base_anio VALUES (?,?,?)", (y, nombre, n))
    for y, t in b["yt"].items(): con.execute("INSERT INTO base_total VALUES (?,?)", (y, t))
    con.execute("INSERT OR REPLACE INTO meta VALUES ('base_hasta', ?)", (b["base_hasta"],))
print(len(d), "meses cargados")
