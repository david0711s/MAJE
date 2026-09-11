# MAJE – Persönlicher, selbstlernender AI-Agent (v3)

MAJE ist ein persönlicher, hochgradig autonomer und selbstlernender AI-Agent, bestehend aus einem performanten **Python FastAPI Backend** (optimiert für 4GB RAM IONOS Cloud-Server) und einer modernen **React Native / Expo App** (iOS & Android) im edlen **Linear / Raycast / Arc Browser Dark-Theme**.

---

## 🌟 Hauptfunktionen

1. **ReAct-Agenten-Loop (Reasoning → Action → Observation)**:
   - Ausführung komplexer mehrschrittiger Aufgaben mit Gedankenprotokoll, Tool-Nutzung und dynamischer Selbstkorrektur.
   - Live-Streaming jedes Einzelschritts über WebSockets direkt in die Mobile App.
2. **Drei Betriebsmodi**:
   - 💬 **Chat-Modus**: Schneller, direkter Dialog ohne Tool-Overhead.
   - ⚡ **Agenten-Modus**: Autonome Ausführung mit Code-Sandbox, Webrecherche, Terminal und Dateiverwaltung.
   - 🤖 **Autonomie-Modus**: Kontinuierliche Hintergrundschleife auf dem IONOS-Server für selbstständiges Lernen, Netzwerk-Audits und Systemoptimierung mit einstellbarem Budget-Limit.
3. **Skalierbares Multi-Provider API-Key Management (`config/api_keys.py`)**:
   - Beliebig viele API-Keys pro Provider hinzufügen (OpenAI, Anthropic, Google Gemini, DeepSeek, Groq, Mistral, Ollama, Tavily etc.).
   - Automatisches Failover bei Rate-Limits (429) oder Ausfällen.
4. **Isolierte Docker-Sandbox**:
   - Sichere Ausführung von generiertem Python/Bash-Code in einem ressourcenbegrenzten Container (Standard: 512MB RAM, 1 CPU Core).
5. **Persistentes Langzeitgedächtnis & Soul**:
   - Vektorielles & relationales Gedächtnis zur Speicherung persönlicher Fakten.
   - Editierbare "Soul" (Persönlichkeit, Werte, Verhaltensweisen und System-Prompt).
6. **"Für MAJE" Dynamisches Dashboard**:
   - MAJE kann über das Tool `add_ui_button` / `add_ui_widget` selbstständig eigene Buttons und Widgets im Interface erstellen!
7. **Echtzeit-Kosten- & Token-Tracker**:
   - Berechnet sekundengenau die Kosten in Euro (€) basierend auf den verbrauchten Prompt- und Completion-Tokens mit konfigurierbarem Tageslimit.

---

## 📁 Projektstruktur

```
MAJE/
├── config/
│   ├── __init__.py
│   └── api_keys.py              # Zentrale, beliebig skalierbare API-Key Konfiguration
├── backend/
│   ├── Dockerfile               # Production Dockerfile
│   ├── requirements.txt         # FastAPI, Uvicorn, LangChain/Tools, Docker, Redis
│   ├── main.py                  # API Entrypoint mit CORS und Middleware
│   ├── api/
│   │   ├── middleware/          # JWT-Auth & Zugriffs-Whitelist
│   │   └── routes/              # Chat, Tasks, Files, Soul, UI, Settings, Costs, Autonomy
│   ├── core/
│   │   ├── agent_loop.py        # Asynchroner ReAct-Loop
│   │   ├── llm_client.py        # Multi-Provider Router mit Fallback-Kette
│   │   ├── cost_tracker.py      # Token- und Euro-Kostenrechnung
│   │   └── task_state.py        # Persistenter Task-State Manager
│   ├── sandbox/
│   │   ├── docker_manager.py    # Container-Sandbox für Code-Ausführung
│   │   └── sandbox_config.py    # RAM-, CPU- und Timeout-Limits
│   ├── storage/
│   │   ├── sqlite_db.py         # Lokale Persistenz (Tasks, Memories, Soul)
│   │   └── redis_client.py      # State & Pub/Sub für Live-Events
│   └── tools/
│       ├── code_executor.py     # Python/Bash Sandbox Tool
│       ├── web_search.py        # Tavily Live-Websuche
│       ├── file_manager.py      # /maje Verzeichnisverwaltung
│       ├── memory_tools.py      # Gedächtnis lesen & schreiben
│       ├── pentesting.py        # Netzwerk- & Security-Scanning Tools
│       └── ui_tools.py          # Dynamische UI-Generierung für die App
├── app/                         # React Native / Expo Mobile App
│   ├── App.tsx                  # Root Navigation & WebSocket Lifecycle
│   ├── src/
│   │   ├── api/                 # Axios HTTP Client & WebSocket Singleton
│   │   ├── store/               # Zustand Stores (Chat, Tasks, Settings)
│   │   ├── theme/               # Linear/Raycast Farbpalette & Typografie
│   │   ├── components/          # ChatBubble, ReasoningLog, FileTree, CostChart etc.
│   │   └── screens/             # Home, TaskDetail, Files, Soul, Memory, MAJE, Autonomy, Costs, Settings
├── docker-compose.yml           # Deployment für den IONOS-Server (Backend + Redis)
└── .env.example                 # Beispiel-Umgebungsvariablen
```

---

## 🔑 API Keys konfigurieren & skalieren

Alle API-Keys werden in der Datei `config/api_keys.py` gepflegt:

```python
API_KEYS = {
    "gemini": [
        "AIzaSy...",
        # Beliebig viele weitere Keys hinzufügen:
        # "AIzaSy...",
    ],
    "groq": [
        "gsk_...",
    ],
    "deepseek": [
        "sk-...",
    ],
    "openai": [
        "sk-...",
    ],
    "anthropic": [
        "sk-ant-...",
    ],
    "tavily": [
        "tvly-...",
    ],
    "ollama": [
        "http://localhost:11434",
    ]
}
```

Wenn ein Key sein Rate-Limit erreicht (HTTP 429), rotiert MAJE automatisch zum nächsten konfigurierten Key oder zum nächsten Modell in der Fallback-Kette.

---

## 🚀 Installation & Start

### 1. Backend lokal starten (Entwicklung)

```bash
# In virtueller Python-Umgebung:
cd backend
pip install -r requirements.txt

# Starten mit Uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Deployment auf dem IONOS Server (4GB RAM)

MAJE ist mit Docker Compose für Linux-Server vorkonfiguriert. Es isoliert das Backend und Redis mit definierten RAM-Limits (2.5GB Backend, 512MB Redis):

```bash
# Auf den IONOS Server kopieren und starten:
docker compose up -d --build

# Logs ansehen:
docker compose logs -f maje-backend
```

### 3. Mobile App (Expo) starten

```bash
cd app
npm install

# Startet den Expo-Dev-Server (QR-Code mit Handy scannen via Expo Go):
npx expo start
```

In der App unter **Settings**:
- Server URL eintragen (z.B. `http://deine-server-ip:8000`)
- Optionalen JWT Auth-Token eintragen
- Auf **Verbindung testen & speichern** tippen – fertig!

---

## 🛡️ Sicherheit & Whitelist

- **Sandbox**: Jeglicher Code läuft in isolierten Containern ohne Host-Netzwerk-Rechte.
- **Whitelist**: Im Backend und in den App-Einstellungen kann eine Whitelist aktiviert werden, sodass nur autorisierte Telefonnummern oder geheime Passcodes Zugriff auf den Agenten erhalten.
- **Not-Aus (Emergency Stop)**: Sowohl über die App als auch über den API-Endpunkt `DELETE /chat/stop/{task_id}` kann jede laufende Agenten-Schleife sofort abgebrochen werden.
