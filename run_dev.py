"""
MAJE – Quickstart Runner (für lokale Entwicklung & unterwegs)

Startet das MAJE-Backend mit einem einzigen Befehl:
    python run_dev.py

- Kein Redis nötig (In-Memory Fallback aktiviert sich automatisch)
- Kein Docker nötig (Code-Ausführung optional)
- Daten werden lokal im Ordner ./data gespeichert
- Authentifizierung standardmäßig deaktiviert (sofort testbar)
"""
import os
import socket
import sys
from pathlib import Path

# UTF-8 Encoding auf Windows-Konsolen sicherstellen
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Sicherstellen, dass das Projektverzeichnis im PYTHONPATH ist
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

# .env laden falls vorhanden
from dotenv import load_dotenv
env_file = ROOT_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    # Falls noch keine .env existiert, legen wir eine an, damit Keys eingetragen werden können
    example_file = ROOT_DIR / ".env.example"
    if example_file.exists():
        import shutil
        shutil.copy(example_file, env_file)
        print("📄 Neue .env-Datei aus .env.example erstellt.")
    load_dotenv(env_file)

# Standardwerte für bequemen Start ohne Server-Setup
os.environ.setdefault("AUTH_REQUIRED", "false")
os.environ.setdefault("ALLOW_ORIGINS", "*")

def get_local_ip() -> str:
    """Ermittelt die lokale Netzwerk-IP für Smartphone/Expo-Verbindung."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # Verbindet nicht wirklich, ermittelt nur das Standard-Interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def main():
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    local_ip = get_local_ip()

    print("=" * 65)
    print("           🌟 MAJE Backend – Sofortstart 🌟")
    print("=" * 65)
    print(f" 💻 Lokal im Browser:     http://localhost:{port}")
    print(f" 📖 Swagger API-Doku:     http://localhost:{port}/docs")
    print(f" 📱 Für Smartphone/Expo:  http://{local_ip}:{port}")
    print("=" * 65)
    print(" 💡 Hinweis: Redis & Docker sind optional.")
    print("    Wenn nicht vorhanden, läuft alles automatisch In-Memory!")
    print("=" * 65)
    print()

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=True,
        app_dir=str(ROOT_DIR),
    )

if __name__ == "__main__":
    main()
