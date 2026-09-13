#!/usr/bin/env bash
# =============================================================================
#  MAJE – HTTPS ohne offene Ports und OHNE Apache anzufassen
#  (Tailscale Funnel:  https://<name>.<tailnet>.ts.net  ->  localhost:8000)
#
#  Ausführen:  sudo bash deploy/setup-funnel.sh
# =============================================================================
set -euo pipefail

echo "==> 1/3 Tailscale installieren (falls nicht vorhanden)"
if ! command -v tailscale >/dev/null 2>&1; then
  curl -fsSL https://tailscale.com/install.sh | sh
fi

echo
echo "==> 2/3 Bei Tailscale anmelden"
echo "    Es erscheint gleich ein Link – den im Browser öffnen und einloggen."
tailscale up

echo
echo "==> 3/3 HTTPS-Funnel für das MAJE-Backend (Port 8000) aktivieren"
tailscale funnel --bg 8000

echo
echo "================= DEINE HTTPS-ADRESSE ================="
tailscale funnel status || true
echo "======================================================"
echo
echo "So geht's weiter:"
echo "  * Adresse jederzeit erneut anzeigen:  bash deploy/show-url.sh"
echo "  1. Adresse oben kopieren (Form: https://<name>.<tailnet>.ts.net)"
echo "  2. In der MAJE-Web-App (Netlify) im Einrichtungs-Assistenten"
echo "     als 'SERVER-URL' eintragen  ->  Verbinden."
echo "  3. Optional: beim Web-Build vorbelegen, dann muss man sie nie tippen:"
echo "         EXPO_PUBLIC_DEFAULT_SERVER=<adresse> npm run build:web"
echo
echo "Hinweis: Apache bleibt unangetastet. Port 8000 muss NICHT öffentlich sein."
