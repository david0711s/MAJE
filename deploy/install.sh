#!/usr/bin/env bash
# =============================================================================
#  MAJE – Setup-Skript für den IONOS-Server (Ziel: /opt/MAJE)
#  Ausführen:  sudo bash deploy/install.sh
# =============================================================================
set -euo pipefail

APP_DIR="/opt/MAJE"

echo "==> MAJE Setup in ${APP_DIR}"

command -v docker >/dev/null 2>&1 || { echo "Fehler: Docker ist nicht installiert."; exit 1; }

# 1) Verzeichnisse anlegen (Daten liegen NICHT in /var/lib/docker, sondern in /opt/MAJE)
mkdir -p "${APP_DIR}"/{data,redis,caddy/data,caddy/config,config,web}
mkdir -p "${APP_DIR}"/data/{scripts,tools,skills,files,workspace,soul/memory,keys}

# Platzhalter, falls die Web-Oberfläche noch nicht gebaut wurde
if [ ! -f "${APP_DIR}/web/index.html" ]; then
  cat > "${APP_DIR}/web/index.html" <<'EOF'
<!doctype html><meta charset="utf-8"><title>MAJE</title>
<body style="background:#0C0C0F;color:#F0F0FF;font-family:sans-serif;padding:40px">
<h2>MAJE läuft ✅</h2>
<p>Die Web-Oberfläche ist noch nicht hochgeladen.<br>
Auf dem PC: <code>cd app &amp;&amp; npm run build:web</code> und den Inhalt von
<code>app/dist</code> nach <code>/opt/MAJE/web</code> kopieren.</p>
<p>Backend-Status: <a style="color:#7C6EFA" href="/health">/health</a></p>
</body>
EOF
fi

# 2) Ownership – der Backend-Container läuft als UID 1000 (User "maje")
chown -R 1000:1000 "${APP_DIR}/data" "${APP_DIR}/redis"

# 3) .env erzeugen (mit zufälligem JWT_SECRET und korrekter Docker-GID)
if [ ! -f "${APP_DIR}/.env" ]; then
  cp "${APP_DIR}/.env.example" "${APP_DIR}/.env"
  SECRET="$(openssl rand -hex 32)"
  sed -i "s|^JWT_SECRET=.*|JWT_SECRET=${SECRET}|" "${APP_DIR}/.env"
  echo "==> .env erstellt (JWT_SECRET zufällig generiert)"
fi

# 4) config/api_keys.py + config/keys.json aus Vorlagen
if [ ! -f "${APP_DIR}/config/api_keys.py" ]; then
  cp "${APP_DIR}/config/api_keys.example.py" "${APP_DIR}/config/api_keys.py"
  echo "==> config/api_keys.py angelegt (Keys besser in der App oder keys.json pflegen)."
fi
if [ ! -f "${APP_DIR}/data/keys/keys.json" ]; then
  echo "==> Keys-Datei wird beim ersten Eintragen automatisch erstellt: ${APP_DIR}/data/keys/keys.json"
  echo "    Am einfachsten: in der App unter Settings -> API-KEYS eintragen."
fi

# 5) Backend + Redis starten
cd "${APP_DIR}"
docker compose up -d --build

echo "==> Fertig."
echo "    Health-Check:  curl -s http://127.0.0.1:8000/health"
echo -n "    JWT-Token:     "
docker compose exec -T maje-backend python -c "from api.middleware.auth import create_token; print(create_token())" 2>/dev/null \
  || echo "(später erneut: docker compose exec -T maje-backend python -c \"from api.middleware.auth import create_token; print(create_token())\")"
