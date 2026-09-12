# MAJE – Deployment auf dem IONOS-Server (`/opt/MAJE`)

## 1. Voraussetzungen
- Ubuntu/Debian mit **Docker** + **Docker Compose v2** (`docker compose version`)
- Port **8000** (bzw. 80/443 bei HTTPS-Proxy) erreichbar
- Optional: Domain, die per DNS auf den Server zeigt (für HTTPS)

## 2. Installation (Kurzfassung)
```bash
sudo mkdir -p /opt/MAJE && cd /opt/MAJE          # Repo hierhin kopieren/klonen
sudo bash deploy/install.sh                      # legt Ordner, .env, config an und startet
nano /opt/MAJE/config/api_keys.py                # Gemini-/Groq-Keys eintragen
docker compose restart maje-backend
curl -s http://127.0.0.1:8000/health             # {"status":"ok",...}
```

## 3. Speicherorte auf `/opt/MAJE`
| Pfad | Inhalt |
|---|---|
| `/opt/MAJE/data` | MAJE-Workspace (bind → `/maje` im Container): `soul/`, `memory/`, `files/`, `scripts/`, `skills/`, `workspace/`, `soul/maje.db` (SQLite) |
| `/opt/MAJE/config` | `api_keys.py` (bind → `/app/config`) |
| `/opt/MAJE/redis` | Redis AOF-Daten |
| `/opt/MAJE/caddy` | TLS-Zertifikate (nur mit Profil `proxy`) |

> Alle Daten liegen damit **außerhalb** von `/var/lib/docker` direkt in `/opt/MAJE`.
> Falls `/opt` auf einer eigenen großen Partition liegt, ist das gewünscht.

## 4. App verbinden
1. In der App unter **Settings**:
   - **Server URL**: `http://<server-ip>:8000` (oder `https://deine-domain`)
   - **JWT Token**: erzeugen mit `curl -s http://127.0.0.1:8000/settings/token`
     (der Endpoint ist **nur von localhost** erreichbar – per SSH auf dem Server ausführen).
2. **Verbindung testen & speichern**.

## 5. Von überall erreichbar – drei Optionen
| Option | Sicherheit | Aufwand | Hinweis |
|---|---|---|---|
| **Tailscale** | sehr hoch | gering | Kein offener Port. Server-URL = Tailscale-IP/MagicDNS (`http://100.x.y.z:8000`). Geräte brauchen Tailscale. |
| **Cloudflare Tunnel** | hoch | mittel | Kein offener Port, HTTPS, optional Cloudflare Access. Ideal für „von jedem Handy“. |
| **Caddy (Profil `proxy`)** | mittel | gering | Offene Ports 80/443, automatisches HTTPS: `docker compose --profile proxy up -d`, `DOMAIN` in `.env`. |

**Netlify-PWA (optional, ohne Installation):**
```bash
cd app
npm install
npx expo export --platform web      # erzeugt ./dist
# ./dist zu Netlify deployen (oder Netlify CLI). Danach ALLOW_ORIGINS auf die Netlify-Domain setzen.
```
Die PWA verbindet sich mit derselben Server-URL. Sprachsteuerung nutzt im Browser die
kostenlose Web-Speech-API; auf Android/iOS funktioniert „Zum Startbildschirm hinzufügen“.

## 6. Sicherheit (wichtig)
- **JWT_SECRET** in `.env` muss ein langer Zufallswert sein (macht `install.sh` automatisch).
- Der Backend-Container hat Zugriff auf `/var/run/docker.sock` (nötig für die Code-Sandbox).
  Das ist mächtig – exponiere MAJE daher nicht ungeschützt ins Internet (Tailscale/Tunnel + Token).
- Sandbox-Container laufen gehärtet: non-root, `cap_drop: ALL`, `no-new-privileges`,
  Read-only-Rootfs, `pids_limit`, Netzwerk standardmäßig aus.
- Pentest-Tools (nmap/gobuster/sqlmap) sind **whitelist-gated** und laufen nur gegen
  eingetragene Ziele (Settings → Security).

## 7. Betrieb
```bash
docker compose logs -f maje-backend          # Logs
docker compose ps                            # Status
docker compose down && docker compose up -d --build   # Update
```

---

## 8. API-Keys verwalten (ohne sie weiterzugeben)

Es gibt **drei** Wege – alle landen zentral in der Keys-Datei
`/opt/MAJE/data/keys/keys.json` (im Container `/maje/keys/keys.json`, persistent & schreibbar):

**A) In der App (empfohlen, kein SSH nötig):**
Settings → **API-KEYS** → pro Anbieter Key eintragen. Wird sofort (ohne Neustart)
übernommen. Anzeige nur maskiert. Keys verlassen nie deinen Server – der Agent
sieht nur maskierte Werte und kann sie nicht auslesen.

**B) Datei direkt (SSH/Editor):**
```bash
nano /opt/MAJE/data/keys/keys.json
```
Format (Vorlage im Repo: `config/keys.example.json`):
```json
{
  "gemini": ["AIzaSy...", "AIzaSy..."],
  "groq":   ["gsk_..."],
  "tavily": ["tvly-..."]
}
```
Die Datei wird automatisch mit `chmod 600` (Eigentümer UID 1000) angelegt.

**C) `.env`** (je EIN Key pro Variable): `GEMINI_API_KEY`, `GROQ_API_KEY`, `TAVILY_API_KEY`, …

### Verschlüsselung der Keys-Datei
- Aktivieren: `GET /settings/keys/newkey` → Wert als `MAJE_KEYS_KEY` in `.env` → Container neu starten
  → in der App „Verschlüsselung aktivieren". Danach ist `keys.json` ein Fernet-Blob.
- **Ehrliche Einschätzung:** Verschlüsselung *at rest* schützt nur, wenn jemand die Datei,
  aber **nicht** die `.env`/den Server hat. Auf einem Einzelserver bringt sie begrenzten
  Zusatznutzen. Der größte Schutz ist: Datei `chmod 600`, **nicht** ins Git, und Keys nie
  mit Dritten (auch nicht mit der KI) teilen. Genau das ist hier umgesetzt.
- Ohne `MAJE_KEYS_KEY` funktioniert alles normal (Klartext) – Verschlüsselung ist optional.

---

## 9. Sandbox-Sicherheit (Docker-Socket-Proxy)
Das Backend hat **keinen** direkten Root-Zugriff auf `/var/run/docker.sock` mehr.
Stattdessen läuft ein eingeschränkter Proxy (`maje-docker-proxy`), der nur
Container anlegen/starten/stoppen/killen und Images pullen darf – aber **kein**
`exec`, keine Netzwerke/Volumes/Swarm-Änderungen.

Falls die Sandbox wider Erwarten nicht funktioniert, in der `.env`/Compose testweise
den direkten Socket verwenden (weniger sicher):
```yaml
# beim maje-backend-Service
environment:
  - DOCKER_HOST=unix:///var/run/docker.sock
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

---

## 10. App oder Website? (kurz)
- Es ist **eine** Codebasis (Expo/React Native). Daraus entsteht **beides**:
  - **Native App** → Android **APK** (bzw. iOS-Build). Installation/Aktualisierung nötig.
  - **Web/PWA** → statische Dateien (`npx expo export --platform web`) → zu **Netlify** hochladen.
    Auf dem Handy „Zum Startbildschirm hinzufügen" = fühlt sich wie eine App an, Updates sofort.
- **Am einfachsten:** die **PWA auf Netlify** (nichts installieren, jedes Handy). Sie verbindet
  sich mit derselben Backend-URL. APK nur nötig, wenn du echte Push/Native-Features brauchst.
- Alle App-Module (Datei-Upload, Mikrofon, Vorlesen) sind in Expo Go enthalten; in der
  PWA greift für Sprache automatisch die Web-Speech-API des Browsers.

