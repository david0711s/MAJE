#!/usr/bin/env bash
# =============================================================================
#  MAJE – Zeigt die HTTPS-Adresse (Tailscale Funnel) an
#  Ausführen:  bash deploy/show-url.sh
# =============================================================================
set -euo pipefail

if ! command -v tailscale >/dev/null 2>&1; then
  echo "Tailscale ist nicht installiert."
  echo "Zuerst ausführen:  sudo bash deploy/setup-funnel.sh"
  exit 1
fi

echo "== Funnel-Status =="
tailscale funnel status || true
echo

# DNS-Namen des Servers auslesen (ohne abschliessenden Punkt)
DNSNAME=""
if command -v python3 >/dev/null 2>&1; then
  DNSNAME="$(tailscale status --json 2>/dev/null \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('Self') or {}).get('DNSName','').rstrip('.'))" \
    2>/dev/null || true)"
fi
if [ -z "$DNSNAME" ]; then
  DNSNAME="$(tailscale status --json 2>/dev/null \
    | grep -o '"DNSName":"[^"]*"' | head -1 | sed 's/.*:"//; s/"$//; s/\.$//' || true)"
fi

echo "=================================================================="
if [ -n "$DNSNAME" ]; then
  echo " DEINE MAJE-ADRESSE:   https://${DNSNAME}"
else
  echo " Adresse: siehe 'Funnel-Status' oben"
  echo " Format:  https://<servername>.<dein-tailnet>.ts.net"
fi
echo "=================================================================="
echo
echo "Diese Adresse in der MAJE-Web-App (Netlify) als SERVER-URL eintragen."
