# Campeonato Last.fm

1. Instala Python 3.9+ y `pip install openpyxl tzdata`.
2. Copia `.env.example` a `.env` y pon tu API key (nunca el shared secret).
3. `python sync.py --desde 2023-07` → descarga el top mensual y crea `campeonato.db`.
4. `python validate.py Lastfm.xlsx` → compara con tu hoja Campeonato manual (muestra diferencias mes a mes).
5. `python report.py` → genera `informe.xlsx` (campeonato, clasificación anual, campeones, estadísticas, empates).

Los meses se congelan 2 días después de terminar; solo se vuelve a pedir el mes en curso (`--refresh` fuerza todo).
Los meses se cortan en hora de Madrid. Empates: gana quien llegó antes a ese número de escuchas.
Automático: sube el repo a GitHub (privado), añade el secret `LASTFM_API_KEY` y el workflow `sync.yml` actualiza la base cada día.
Consulta la base con cualquier visor SQLite (DB Browser, Metabase, Grafana) usando las vistas `v_*`.
