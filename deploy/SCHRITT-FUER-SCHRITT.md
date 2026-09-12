# MAJE – Schritt für Schritt: IONOS-Server + Netlify

> Alle Befehle mit `#` sind Kommentare. `<...>` = durch deinen Wert ersetzen.

---

## TEIL A – Backend auf den IONOS-Server (/opt/MAJE)

### A0. Was du brauchst
- IONOS-Server (Ubuntu 22.04/24.04) mit **root** oder sudo-Zugang per SSH
- Deine Server-IP (z. B. `123.45.67.89`)
- Auf dem Server: Docker (installieren wir in A2)

### A1. Per SSH einloggen
```bash
ssh root@<server-ip>
```

### A2. Docker + Compose installieren (falls nicht vorhanden)
```bash
docker --version || curl -fsSL https://get.docker.com | sh
```

### A3. Projekt auf den Server bringen
Der Git-Remote liegt aktuell nur in deinem Heimnetz (`192.168.178.92`),
darum **eine** dieser Varianten:

**Variante A – Zip + scp (von deinem Windows-PC, PowerShell):**
```powershell
cd C:\Users\david\Desktop\Code\Python\MAJE
# node_modules NICHT mitpacken (groß):
tar --exclude=node_modules --exclude=app/node_modules --exclude=.git -czf maje.tgz .
scp maje.tgz root@<server-ip>:/tmp/
```
Dann auf dem Server:
```bash
mkdir -p /opt/MAJE && tar -xzf /tmp/maje.tgz -C /opt/MAJE
```

**Variante B – GitHub:** Repo zu GitHub pushen, auf dem Server:
```bash
git clone https://github.com/<dein-user>/MAJE.git /opt/MAJE
```

**Variante C – git bundle (bleibt privat):**
```powershell
cd C:\Users\david\Desktop\Code\Python\MAJE
git bundle create maje.bundle --all
scp maje.bundle root@<server-ip>:/opt/MAJE/
```
```bash
cd /opt/MAJE && git clone maje.bundle repo && mv repo/* repo/.[!.]* . 2>/dev/null; rm -rf repo
```

### A4. Setup ausführen
```bash
cd /opt/MAJE
sudo bash deploy/install.sh
```
Das erstellt: `/opt/MAJE/data` (Workspace/Soul/SQLite), `/opt/MAJE/redis`,
`/opt/MAJE/data/keys/` (Keys, wird beim ersten Eintragen erstellt), `.env` mit **zufälligem JWT_SECRET**,
und startet Backend + Redis + Docker-Socket-Proxy.

### A5. API-Keys eintragen
**Am einfachsten in der App** (Settings → API-KEYS) – siehe Teil B.
Alternativ direkt auf dem Server:
```bash
nano /opt/MAJE/data/keys/keys.json   # Keys eintragen (gemini, groq, tavily)
docker compose restart maje-backend
```
**Pflicht:** mindestens einen LLM-Key (Gemini **oder** Groq – beide kostenlos).
Für Sprache (Whisper) wird ein **Groq-Key** empfohlen.

### A6. Testen
```bash
curl -s http://127.0.0.1:8000/health          # {"status":"ok",...}
curl -s http://127.0.0.1:8000/settings/token  # JWT-Token (nur localhost!)
```
Den Token kopieren – den brauchst du in der App.

### A7. Von außen erreichbar machen
- **Für die native App (http)** reicht Port 8000:
  IONOS/Firewall (ufw): `ufw allow 8000/tcp`
- **Für die Netlify-PWA ist HTTPS Pflicht** (sonst blockt der Browser „mixed content“).
  Einfachste Variante: Caddy mit Domain:
  ```bash
  nano /opt/MAJE/.env          # DOMAIN=maje.deinedomain.de setzen
  docker compose --profile proxy up -d
  ```
  (DNS der Domain muss auf die Server-IP zeigen, Ports 80/443 offen.)

---

## TEIL B – Die App aufs Handy

### B1. Sofort testen (kein Build nötig)
```bash
cd /opt/MAJE/app   # oder lokal auf dem PC
npm install
npx expo start
```
QR-Code mit **Expo Go** scannen (Android/iOS).
In der App: **Settings** → Server-URL (`http://<server-ip>:8000`) + JWT-Token → „Verbindung testen“.

### B2. Echte Android-APK bauen (optional)
```bash
npm install -g eas-cli
eas login
eas build -p android --profile preview   # erzeugt eine installierbare APK
```
Für iOS brauchst du einen Apple-Developer-Account (TestFlight) – ohne geht nur Expo Go.

> Tipp: Für „überall ohne Installation“ ist die **PWA (Teil C)** einfacher als eine APK.

---

## TEIL C – Web-App (PWA) auf Netlify

> **Wichtig:** Eine Netlify-Seite läuft immer über **HTTPS**. Der Browser verbietet
> dann Verbindungen zu `http://…`. Deshalb muss dein Backend **HTTPS** haben
> (siehe A7 – Caddy/Cloudflare Tunnel). Die native App (Teil B) darf dagegen http.

### C1. Lokal vorbereiten
```bash
cd C:\Users\david\Desktop\Code\Python\MAJE\app
npm install
npx expo export --platform web      # erzeugt den Ordner  app/dist
```

### C2. Auf Netlify hochladen – drei Wege

**Weg 1 – Drag & Drop (am einfachsten, kein Git nötig):**
1. https://app.netlify.com → einloggen → **Add new site → Deploy manually**
2. Den Ordner **`app\dist`** mit der Maus auf die Drop-Zone ziehen. Fertig.
   Du bekommst eine URL wie `https://maje-xyz.netlify.app`.

**Weg 2 – Netlify CLI:**
```bash
npm install -g netlify-cli
netlify login
cd C:\Users\david\Desktop\Code\Python\MAJE\app
netlify deploy --dir=dist --prod
```

**Weg 3 – Git (Auto-Deploy bei jedem Push):**
1. Repo zu GitHub pushen.
2. Netlify → **Add new site → Import an existing project** → Repo wählen.
3. **Base directory: `app`** (nutzt automatisch `app/netlify.toml`:
   Build `npx expo export --platform web`, Publish `dist`).

### C3. CORS am Backend freischalten
Auf dem Server die Netlify-Domain in die `.env` eintragen:
```bash
nano /opt/MAJE/.env
# ALLOW_ORIGINS=https://maje-xyz.netlify.app
docker compose up -d            # Backend neu starten
```
(Mehrere Domains mit Komma trennen.)

**Bequemer** – alle Netlify-Subdomains automatisch erlauben (kein Suchen der genauen URL):
```bash
# in der .env:
ALLOW_ORIGINS=*
ALLOW_ORIGIN_REGEX=https://([a-z0-9-]+\.)*netlify\.app
```
```bash
docker compose up -d
```

### C4. In der PWA verbinden
Netlify-Seite auf dem Handy öffnen → **Settings** → **Server URL**:
`https://maje.deinedomain.de` (die HTTPS-Adresse aus A7) + **JWT-Token** → „Verbindung testen“.
Danach **Settings → API-KEYS** → Keys eintragen (sofort aktiv).

### C5. Als App installieren (Startbildschirm)
- **Android (Chrome):** Menü ⋮ → „App installieren“ / „Zum Startbildschirm hinzufügen“.
- **iPhone (Safari):** Teilen-Symbol → „Zum Home-Bildschirm“.
Danach startet MAJE wie eine normale App – Updates erscheinen automatisch.

---

## Kurz-Checkliste (Reihenfolge)

1. `ssh root@<server-ip>` → Docker installieren
2. Projekt nach `/opt/MAJE` (scp/GitHub/bundle)
3. `sudo bash deploy/install.sh`
4. HTTPS aufsetzen: `DOMAIN` in `.env` + `docker compose --profile proxy up -d`
5. Keys eintragen (App → API-KEYS oder `/opt/MAJE/data/keys/keys.json`)
6. `curl http://127.0.0.1:8000/settings/token` → Token notieren
7. App: `npm install` → `npx expo export --platform web`
8. `app\dist` zu Netlify hochladen
9. `ALLOW_ORIGINS=https://<netlify-domain>` in `.env` + `docker compose up -d`
10. PWA öffnen → Server-URL (https) + Token → API-KEYS ausfüllen → „Zum Startbildschirm“

---

## Fehlersuche

| Problem | Ursache / Lösung |
|---|---|
| PWA: „Verbindung fehlgeschlagen“ | Backend muss **https** sein (mixed content). A7 prüfen. |
| CORS-Fehler in der Browser-Konsole | `ALLOW_ORIGINS` auf die Netlify-Domain setzen, Backend neu starten. |
| App offline / 401 | Token fehlt/falsch. `curl http://127.0.0.1:8000/settings/token` (nur auf dem Server!). |
| Live-Updates (WebSocket) kommen nicht | `wss://` nötig → HTTPS-Proxy (Caddy/Cloudflare) verwenden. |
| Sandbox: „Docker not available“ | `docker compose ps` prüfen (maje-docker-proxy läuft?). Notfalls Fallback in deploy/README §9. |
| `npm install` Fehler | `node_modules` löschen und erneut `npm install`; Node ≥ 20 verwenden. |
| Port 8000 von außen nicht erreichbar | Firewall: `ufw allow 8000/tcp` (bzw. IONOS-Firewall-Regel). |
| Keys werden nicht übernommen | In der App „API-KEYS“ speichern oder `/opt/MAJE/data/keys/keys.json` prüfen; Logs: `docker compose logs -f maje-backend`. |

