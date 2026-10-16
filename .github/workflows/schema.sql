CREATE TABLE IF NOT EXISTS escuchas_mes (
  mes      TEXT NOT NULL,          -- 'YYYY-MM'
  artista  TEXT NOT NULL,
  escuchas INTEGER NOT NULL,
  llego_ts INTEGER,                -- timestamp (UTC) de su última escucha del mes = cuándo alcanzó ese número
  PRIMARY KEY (mes, artista)
);
CREATE TABLE IF NOT EXISTS meses (
  mes         TEXT PRIMARY KEY,
  cerrado     INTEGER NOT NULL DEFAULT 0,  -- 1 = congelado, ya no se vuelve a pedir
  actualizado TEXT,
  total       INTEGER                      -- escuchas totales del mes (todos los artistas)
);
CREATE TABLE IF NOT EXISTS base_anio (       -- escuchas por artista y año de los meses ya cerrados (hasta meta.base_hasta)
  anio TEXT NOT NULL, artista TEXT NOT NULL, escuchas INTEGER NOT NULL, PRIMARY KEY (anio, artista)
);
CREATE TABLE IF NOT EXISTS base_total (anio TEXT PRIMARY KEY, total INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS meta (clave TEXT PRIMARY KEY, valor TEXT);
CREATE TABLE IF NOT EXISTS puntos_f1 (
  pos INTEGER PRIMARY KEY, puntos INTEGER NOT NULL
);
INSERT OR REPLACE INTO puntos_f1 VALUES (1,25),(2,18),(3,15),(4,12),(5,10),(6,8),(7,6),(8,4),(9,2),(10,1);

-- Participar en un GP = quedar entre los 20 más escuchados del mes. Puntuar = quedar entre los 10 primeros.
DROP VIEW IF EXISTS v_gp;
CREATE VIEW v_gp AS
WITH r AS (
  SELECT mes, artista, escuchas,
         ROW_NUMBER() OVER (PARTITION BY mes ORDER BY escuchas DESC, COALESCE(llego_ts, 0), artista) AS pos,
         COUNT(*)     OVER (PARTITION BY mes, escuchas)                                              AS n_igual
  FROM escuchas_mes WHERE escuchas > 0
)
SELECT r.mes, substr(r.mes,1,4) AS anio, r.artista, r.escuchas, r.pos, COALESCE(p.puntos,0) AS puntos,
       (r.n_igual > 1) AS empate
FROM r LEFT JOIN puntos_f1 p ON p.pos = r.pos WHERE r.pos <= 20;

DROP VIEW IF EXISTS v_campeonato;
CREATE VIEW v_campeonato AS SELECT * FROM v_gp WHERE pos <= 10;

DROP VIEW IF EXISTS v_clasificacion_anual;
CREATE VIEW v_clasificacion_anual AS
SELECT anio, artista, SUM(puntos) AS puntos,
       SUM(pos=1) AS victorias, SUM(pos<=3) AS podios, COUNT(*) AS meses_puntuados,
       RANK() OVER (PARTITION BY anio ORDER BY SUM(puntos) DESC, SUM(pos=1) DESC, SUM(pos<=3) DESC) AS posicion
FROM v_campeonato GROUP BY anio, artista;

DROP VIEW IF EXISTS v_campeones;
CREATE VIEW v_campeones AS
SELECT anio, artista, puntos, victorias, podios FROM v_clasificacion_anual WHERE posicion = 1;

DROP VIEW IF EXISTS v_estadisticas;
CREATE VIEW v_estadisticas AS
SELECT c.artista,
       (SELECT COUNT(*) FROM v_gp g WHERE g.artista=c.artista) AS participaciones,
       SUM(c.pos=1)  AS victorias,
       SUM(c.pos<=3) AS podios,
       COUNT(*)      AS meses_puntuados,
       SUM(c.puntos) AS puntos_totales,
       ROUND(100.0*SUM(c.pos=1)/COUNT(*),1)  AS pct_victorias_sobre_puntuados,
       ROUND(100.0*SUM(c.pos=1)/NULLIF(SUM(c.pos<=3),0),1) AS pct_victorias_sobre_podios,
       (SELECT COUNT(*) FROM v_campeones v WHERE v.artista=c.artista) AS mundiales
FROM v_campeonato c GROUP BY c.artista;

DROP VIEW IF EXISTS v_empates;
-- empates a escuchas iguales, ya resueltos: gana quien llegó antes a ese número
CREATE VIEW v_empates AS SELECT mes, artista, escuchas, pos, datetime(llego_ts,'unixepoch') AS llego_utc FROM v_campeonato JOIN (SELECT mes AS m, artista AS a, llego_ts FROM escuchas_mes) ON m=mes AND a=artista WHERE empate=1 ORDER BY mes, pos;
