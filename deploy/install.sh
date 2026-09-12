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
mkdir -p "${APP_DIR}"/{data,redis,caddy/data,caddy/config,config}
mkdir -p "${APP_DIR}"/data/{scripts,tools,skills,files,workspace,soul/memory}

# 2) Ownership – der Backend-Container läuft als UID 1000 (User "maje")
chown -R 1000:1000 "${APP_DIR}/data" "${APP_DIR}/redis"

# 3) .env erzeugen (mit zufälligem JWT_SECRET und korrekter Docker-GID)
if [ ! -f "${APP_DIR}/.env" ]; then
  cp "${APP_DIR}/.env.example" "${APP_DIR}/.env"
  SECRET="$(openssl rand -hex 32)"
  DG="$(getent group docker | cut -d: -f3 || echo 999)"
  sed -i "s|^JWT_SECRET=.*|JWT_SECRET=${SECRET}|" "${APP_DIR}/.env"
  sed -i "s|^DOCKER_GID=.*|DOCKER_GID=${DG}|" "${APP_DIR}/.env"
  echo "==> .env erstellt (JWT_SECRET zufällig, DOCKER_GID=${DG})"
fi

# 4) config/api_keys.py aus Vorlage, falls noch nicht vorhanden
if [ ! -f "${APP_DIR}/config/api_keys.py" ]; then
  cp "${APP_DIR}/config/api_keys.example.py" "${APP_DIR}/config/api_keys.py"
  echo "==> config/api_keys.py angelegt – bitte Gemini/Groq-Keys eintragen!"
fi

# 5) Backend + Redis starten
cd "${APP_DIR}"
docker compose up -d --build

echo "==> Fertig."
echo "    Health-Check:  curl -s http://127.0.0.1:8000/health"
echo "    JWT-Token:     curl -s http://127.0.0.1:8000/settings/token"
