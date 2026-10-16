#!/usr/bin/env python3
"""Descarga tus scrobbles de Last.fm, los agrupa por mes en hora de Madrid y los guarda en SQLite.
Solo se piden los meses abiertos (el actual y, si hace falta, el anterior); los cerrados se congelan.
Uso:  python sync.py [--desde 2023-07] [--refresh]"""
import argparse, json, os, re, sqlite3, time, unicodedata, urllib.parse, urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

DB = os.environ.get("DB_PATH", "campeonato.db")
API = "https://ws.audioscrobbler.com/2.0/"
MAD = ZoneInfo("Europe/Madrid")

def load_env():
    if os.path.exists(".env"):
        for line in open(".env", encoding="utf-8"):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1); os.environ.setdefault(k, v)

def api(method, **p):
    p.update(method=method, api_key=os.environ["LASTFM_API_KEY"], format="json")
    url = API + "?" + urllib.parse.urlencode(p)
    for i in range(6):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                d = json.load(r)
            if "error" in d: raise RuntimeError(d.get("message"))
            return d
        except Exception:
            if i == 5: raise
            time.sleep(2 * (i + 1))

def clave(s):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()) or s

def inicio_mes(y, m): return datetime(y, m, 1, tzinfo=MAD)
def siguiente(y, m): return (y + 1, 1) if m == 12 else (y, m + 1)

def main():
    load_env()
    ap = argparse.ArgumentParser(); ap.add_argument("--desde", default="2023-07"); ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    user = os.environ["LASTFM_USER"]
    con = sqlite3.connect(DB)
    con.executescript(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql"), encoding="utf-8").read())
    ahora = datetime.now(MAD)
    y0, m0 = map(int, a.desde.split("-"))
    cerrados = set() if a.refresh else {r[0] for r in con.execute("SELECT mes FROM meses WHERE cerrado=1")}
    todos, (y, m) = [], (y0, m0)
    while (y, m) <= (ahora.year, ahora.month):
        todos.append((y, m)); y, m = siguiente(y, m)
    pend = [(y, m) for y, m in todos if f"{y}-{m:02d}" not in cerrados]
    if not pend: print("Nada que actualizar"); return
    desde = int(inicio_mes(*pend[0]).timestamp())
    agg = defaultdict(lambda: defaultdict(lambda: [0, 0, defaultdict(int)]))   # mes -> clave -> [n, ultima_ts, variantes]
    pag, total = 1, 1
    while pag <= total:
        rt = api("user.getrecenttracks", user=user, **{"from": desde, "limit": 200, "page": pag})["recenttracks"]
        total = int(rt["@attr"]["totalPages"])
        tr = rt.get("track", []); tr = [tr] if isinstance(tr, dict) else tr
        for t in tr:
            if "date" not in t: continue            # 'escuchando ahora'
            ts = int(t["date"]["uts"]); d = datetime.fromtimestamp(ts, MAD)
            nom = t["artist"]["#text"]
            e = agg[f"{d.year}-{d.month:02d}"][clave(nom)]; e[0] += 1; e[1] = max(e[1], ts); e[2][nom] += 1
        pag += 1; time.sleep(0.2)
    for y, m in pend:
        mes = f"{y}-{m:02d}"; ny, nm = siguiente(y, m)
        cerrar = int(ahora.timestamp()) > int(inicio_mes(ny, nm).timestamp()) + 2 * 86400
        with con:
            con.execute("DELETE FROM escuchas_mes WHERE mes=?", (mes,))
            filas = [(mes, max(v, key=lambda x: (v[x], not x.isascii())), n, ts) for _, (n, ts, v) in agg[mes].items()]
            con.executemany("INSERT INTO escuchas_mes VALUES (?,?,?,?)", filas)
            con.execute("INSERT OR REPLACE INTO meses VALUES (?,?,?,?)", (mes, cerrar, ahora.isoformat(timespec="seconds"), sum(f[2] for f in filas)))
        print(mes, len(agg[mes]), "artistas", "(cerrado)" if cerrar else "(abierto)")

if __name__ == "__main__":
    main()
