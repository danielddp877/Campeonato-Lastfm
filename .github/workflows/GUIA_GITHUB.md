# Publicar la web con GitHub (sin instalar nada)

1. Crea cuenta en github.com (gratis).
2. Arriba a la derecha: "+" → "New repository". Nombre: campeonato-lastfm. Marca **Public** (Pages gratis lo exige). Create repository.
3. En el repositorio nuevo: "uploading an existing file". Descomprime el zip y arrastra TODO el contenido
   (incluida la carpeta .github; si no te deja, mira el paso 3b). Commit changes.
   3b. Si falta .github/workflows/sync.yml: "Add file" → "Create new file", escribe como nombre
       .github/workflows/sync.yml (las barras crean carpetas), pega el contenido del archivo del zip y Commit.
4. Settings → Secrets and variables → Actions → "New repository secret".
   Nombre: LASTFM_API_KEY   Valor: tu API key (solo la key, nunca el shared secret).
5. Settings → Pages → Source: **GitHub Actions**.
6. Pestaña Actions → "actualizar-y-publicar" → "Run workflow". Tarda 1-2 minutos.
   Al acabar, la dirección sale en Settings → Pages (https://TU-USUARIO.github.io/campeonato-lastfm/).
7. Desde entonces se actualiza solo cada día. Para forzarlo: el mismo botón Run workflow.
