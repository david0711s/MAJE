# MAJE – Persönlicher, selbstlernender AI-Agent (v3)

MAJE ist ein persönlicher, autonomer und selbstlernender AI-Agent:
ein **Python FastAPI Backend** (optimiert für kleine Server) + eine **React Native / Expo App**
(iOS, Android **und Web/PWA**) im Linear/Raycast-Dark-Theme.

---

## 🌟 Hauptfunktionen

1. **ReAct-Agenten-Loop** (Reasoning → Action → Observation) mit Live-Streaming über WebSockets.
2. **Drei Modi**: 💬 Chat, ⚡ Agent, 🤖 Autonomie (Hintergrund-Lernen mit Budget-Limit).
3. **Multi-Provider-Fallback** (`config/api_keys.py`): Gemini → Groq → DeepSeek → … mit Key-Rotation,
   automatischem Failover bei 429/Fehlern und Kosten-Tracking in Euro.
4. **Gehärtete Docker-Sandbox**: eigener Wegwerf-Container pro Ausführung, non-root, `cap_drop: ALL`,
   `no-new-privileges`, Read-only-Rootfs, `pids_limit`, Netzwerk standardmäßig aus,
   RAM/CPU/Timeout-Limits (zur Laufzeit über die App einstellbar).
5. **Dateien**: Datei-Upload aus der App (`/files/upload`), In-App-Vorschau (`/files/view`),
   Download/Teilen, Agent-Tools `read_file` / `write_file`.
6. **Sprache (kostenlos)**: 🎤 Aufnahme → Transkription über **Groq Whisper (Free-Tier)**;
   🔊 Vorlesen der Antworten per **On-Device-TTS** (`expo-speech`). In der PWA zusätzlich
   Web-Speech-API (Browser).
7. **Memory & Soul**: strukturierte Persönlichkeit (soul.json + soul.md) und Langzeitgedächtnis.
8. **„Für MAJE" Dashboard**: MAJE erstellt selbst Buttons/Widgets (`create_ui_element`).
9. **Echtzeit-Kosten-Tracker** mit Tageslimit (Chat/Agent/Autonomie).
10. **Auth**: JWT-Pflicht auf allen HTTP-Routen, WebSocket nur mit gültigem Token,
    Access-Whitelist (Nummern/Passcodes), Pentest-Ziel-Whitelist als Hard-Gate.

---

## 📁 Projektstruktur (Auszug)

```
MAJE/
├── config/api_keys.py           # Provider + Keys + Kosten
├── backend/
│   ├── main.py                  # FastAPI Entrypoint (Routen, CORS, Startup)
│   ├── api/routes/              # chat, tasks, files, soul, ui, settings, costs, autonomy, voice
│   ├── core/                    # agent_loop, llm_client, cost_tracker, task_state
│   ├── sandbox/                 # docker_manager (gehärtet), sandbox_config (Limits)
│   ├── tools/                   # code_exec, files, web_search, memory, ui, pentesting
│   └── tests/                   # pytest (Whitelist + CostTracker)
├── app/                         # Expo App (iOS/Android/Web)
├── deploy/                      # install.sh, Caddyfile, Deployment-Doku (/opt/MAJE)
├── docker-compose.yml
└── .env.example
```

---

## 🚀 Schnellstart (Entwicklung)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# App
cd ../app
npm install
npx expo start          # Expo Go: QR-Code scannen (Voice/Upload sind in Expo Go enthalten)
```

In der App unter **Settings**: Server-URL eintragen, JWT-Token einfügen, „Verbindung testen".
Token erzeugen: `curl -s http://127.0.0.1:8000/settings/token` (nur von localhost erlaubt).

---

## 🖥️ Deployment auf dem IONOS-Server (`/opt/MAJE`)

**📋 Schritt-für-Schritt-Anleitung (Server + Netlify): [deploy/SCHRITT-FUER-SCHRITT.md](deploy/SCHRITT-FUER-SCHRITT.md)**
Details & Hintergründe: **[deploy/README.md](deploy/README.md)**. Kurz:

```bash
sudo mkdir -p /opt/MAJE && cd /opt/MAJE      # Repo hierhin kopieren
sudo bash deploy/install.sh                  # Ordner, .env (Zufalls-JWT), config, Start
nano /opt/MAJE/config/api_keys.py            # Keys eintragen
```

- Daten liegen unter **`/opt/MAJE/data`** (Workspace, Soul, SQLite) und **`/opt/MAJE/redis`**.
- Optional HTTPS per Caddy: `docker compose --profile proxy up -d` (Domain in `.env`).
- Von überall: **Tailscale** (empfohlen, kein offener Port), **Cloudflare Tunnel** oder Caddy+Domain.

---

## 📱 Web/PWA (z. B. Netlify) – ohne Installation

```bash
cd app
npm install
npx expo export --platform web     # erzeugt ./dist  → zu Netlify deployen
```
Die PWA verbindet sich mit derselben Server-URL und lässt sich per
„Zum Startbildschirm hinzufügen" installieren. Setze dann `ALLOW_ORIGINS` in der `.env`
auf die Netlify-Domain.

---

## 🔑 API-Keys (zentral & skalierbar)

Alle Keys liegen an **einer** Stelle (beliebig viele pro Anbieter):
im Container `/maje/keys/keys.json` (= auf dem Server `/opt/MAJE/data/keys/keys.json`),
lokal in der Entwicklung `config/keys.json`. Drei Wege, sie zu setzen – ohne sie
jemals mit Dritten zu teilen:

1. **App:** Settings → **API-KEYS** → Key eintragen (sofort aktiv, nur maskiert angezeigt).
2. **Datei:** Keys-Datei direkt bearbeiten (Vorlage `config/keys.example.json`, `chmod 600`).
3. **`.env`:** `GEMINI_API_KEY`, `GROQ_API_KEY`, `TAVILY_API_KEY`, …

Reihenfolge in `config/api_keys.py` bestimmt den Fallback (Gemini → Groq → DeepSeek → …).
Für kostenlose Nutzung: Gemini (Free) + Groq (Free, auch Whisper-Sprache).
Die Datei ist **gitignored** und kann optional verschlüsselt werden (`MAJE_KEYS_KEY`) –
Details unter [deploy/README.md](deploy/README.md#8-api-keys-verwalten-ohne-sie-weiterzugeben).

---

## 🛡️ Sicherheit

- Sandbox: isolierte, gehärtete Container; Pentest-Tools nur gegen whitelistete Ziele.
- Auth: JWT für alle Routen, WebSocket nur mit Token; `/settings/token` nur von localhost.
- **Docker-Socket-Proxy**: Das Backend hat **keinen** direkten Root-Socket-Zugriff mehr;
  Sandbox-Container werden über einen eingeschränkten Proxy erzeugt (kein `exec`, keine
  Netzwerk-/Volume-/Swarm-Änderungen erlaubt).
- **Wichtig**: Exponiere MAJE trotzdem nicht ungeschützt ins Internet
  (Tunnel/Tailscale + Token verwenden) und setze ein langes `JWT_SECRET`.

---

## 🧪 Tests

```bash
cd backend
python -m pytest tests -q
```
