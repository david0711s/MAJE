"""
================================================================================
  MAJE – API KEY CONFIGURATION
================================================================================

  Trage hier alle API-Keys ein. Die Reihenfolge in API_PROVIDERS bestimmt die
  Fallback-Reihenfolge (Index 0 = höchste Priorität).

  Um einen NEUEN Provider hinzuzufügen:
    1. Neuen Konfig-Block unten nach dem vorhandenen Muster anlegen
    2. Key in der "keys"-Liste eintragen
    3. Block ans Ende von API_PROVIDERS anfügen
    4. Fertig – das Backend erkennt ihn automatisch

  Felder pro Provider-Eintrag:
    name                        – Anzeigename (App-Badges und Logs)
    provider_id                 – eindeutiger Bezeichner (snake_case, nie ändern nach Einsatz)
    keys                        – Liste von API-Keys; bei mehreren Keys Round-Robin-Rotation
    model                       – Standard-Modellname für diesen Provider
    base_url                    – API-Endpoint (None = Library-Default)
    rpm_limit                   – Requests per Minute (0 = kein Limit bekannt)
    rpd_limit                   – Requests per Day  (0 = kein Limit bekannt)
    cost_per_1k_input_tokens    – Kosten in USD pro 1.000 Input-Token
    cost_per_1k_output_tokens   – Kosten in USD pro 1.000 Output-Token
    is_free_tier                – True = kostenloses Kontingent
    enabled                     – False = Provider komplett übersprungen (Killswitch)
    tags                        – Tags zur Filterung, z.B. "fast", "cheap", "smart"

================================================================================
"""

from __future__ import annotations
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
#  STUFE 1 – PRIMÄR: Google Gemini
#  Gratis-Tier: ~1.500 Req/Tag (Gemini 2.5 Flash)
# ─────────────────────────────────────────────────────────────────────────────
GEMINI_CONFIG: dict[str, Any] = {
    "name":         "Google Gemini",
    "provider_id":  "gemini",
    "keys": [
        "DEIN_GEMINI_API_KEY_HIER",          # Key 1  ← hier eintragen
        # "ZWEITER_GEMINI_KEY",              # Key 2  (auskommentiert lassen bis vorhanden)
        # "DRITTER_GEMINI_KEY",              # Key 3
    ],
    "model":                      "gemini-2.5-flash",
    "base_url":                   None,      # None = Standard-Google-Endpoint
    "rpm_limit":                  15,
    "rpd_limit":                  1500,
    "cost_per_1k_input_tokens":   0.0,
    "cost_per_1k_output_tokens":  0.0,
    "is_free_tier":               True,
    "enabled":                    True,
    "tags":                       ["primary", "smart", "free"],
}

# ─────────────────────────────────────────────────────────────────────────────
#  STUFE 2 – FALLBACK 1: Groq (ultra-schnell, sehr großzügiges Gratis-Tier)
#  Gratis-Tier: ~14.400 Req/Tag (Llama 3.3 70B)
# ─────────────────────────────────────────────────────────────────────────────
GROQ_CONFIG: dict[str, Any] = {
    "name":         "Groq",
    "provider_id":  "groq",
    "keys": [
        "DEIN_GROQ_API_KEY_HIER",            # Key 1  ← hier eintragen
        # "ZWEITER_GROQ_KEY",                # Key 2
    ],
    "model":                      "llama-3.3-70b-versatile",
    "base_url":                   "https://api.groq.com/openai/v1",
    "rpm_limit":                  30,
    "rpd_limit":                  14400,
    "cost_per_1k_input_tokens":   0.0,
    "cost_per_1k_output_tokens":  0.0,
    "is_free_tier":               True,
    "enabled":                    True,
    "tags":                       ["fallback1", "fast", "free"],
}

# ─────────────────────────────────────────────────────────────────────────────
#  STUFE 3 – FALLBACK 2: DeepSeek (kostenpflichtig, nur nach Gratis-Erschöpfung)
#  enabled=False → pausiert statt Geld auszugeben; in Settings per Schalter steuerbar
# ─────────────────────────────────────────────────────────────────────────────
DEEPSEEK_CONFIG: dict[str, Any] = {
    "name":         "DeepSeek",
    "provider_id":  "deepseek",
    "keys": [
        "DEIN_DEEPSEEK_API_KEY_HIER",        # Key 1  ← hier eintragen
        # "ZWEITER_DEEPSEEK_KEY",            # Key 2
    ],
    "model":                      "deepseek-chat",   # "auto" → Backend wählt Flash/Pro
    "base_url":                   "https://api.deepseek.com/v1",
    "rpm_limit":                  60,
    "rpd_limit":                  0,         # kein bekanntes Tageslimit
    "cost_per_1k_input_tokens":   0.00027,   # USD (Stand: DeepSeek V3 / 2025)
    "cost_per_1k_output_tokens":  0.001,
    "is_free_tier":               False,
    "enabled":                    True,      # False = kein einziger cent wird ausgegeben
    "tags":                       ["fallback2", "paid", "smart"],
}

# ─────────────────────────────────────────────────────────────────────────────
#  STUFE 4 – OPTIONAL: OpenAI (deaktiviert, nach Bedarf aktivieren)
# ─────────────────────────────────────────────────────────────────────────────
OPENAI_CONFIG: dict[str, Any] = {
    "name":         "OpenAI",
    "provider_id":  "openai",
    "keys": [
        # "DEIN_OPENAI_API_KEY_HIER",        # Key 1
    ],
    "model":                      "gpt-4o-mini",
    "base_url":                   None,
    "rpm_limit":                  500,
    "rpd_limit":                  0,
    "cost_per_1k_input_tokens":   0.00015,
    "cost_per_1k_output_tokens":  0.0006,
    "is_free_tier":               False,
    "enabled":                    False,     # ← auf True setzen um zu aktivieren
    "tags":                       ["optional", "paid"],
}

# ─────────────────────────────────────────────────────────────────────────────
#  STUFE 5 – OPTIONAL: Anthropic Claude (deaktiviert)
# ─────────────────────────────────────────────────────────────────────────────
ANTHROPIC_CONFIG: dict[str, Any] = {
    "name":         "Anthropic Claude",
    "provider_id":  "anthropic",
    "keys": [
        # "DEIN_ANTHROPIC_API_KEY_HIER",     # Key 1
    ],
    "model":                      "claude-3-5-haiku-20241022",
    "base_url":                   None,
    "rpm_limit":                  50,
    "rpd_limit":                  0,
    "cost_per_1k_input_tokens":   0.0008,
    "cost_per_1k_output_tokens":  0.004,
    "is_free_tier":               False,
    "enabled":                    False,
    "tags":                       ["optional", "paid", "smart"],
}

# ─────────────────────────────────────────────────────────────────────────────
#  STUFE 6 – OPTIONAL: Mistral AI (deaktiviert)
# ─────────────────────────────────────────────────────────────────────────────
MISTRAL_CONFIG: dict[str, Any] = {
    "name":         "Mistral AI",
    "provider_id":  "mistral",
    "keys": [
        # "DEIN_MISTRAL_API_KEY_HIER",       # Key 1
    ],
    "model":                      "mistral-small-latest",
    "base_url":                   "https://api.mistral.ai/v1",
    "rpm_limit":                  5,
    "rpd_limit":                  0,
    "cost_per_1k_input_tokens":   0.0002,
    "cost_per_1k_output_tokens":  0.0006,
    "is_free_tier":               False,
    "enabled":                    False,
    "tags":                       ["optional", "paid"],
}

# ─────────────────────────────────────────────────────────────────────────────
#  STUFE 7 – OPTIONAL: Together AI (deaktiviert, viele Open-Source-Modelle)
# ─────────────────────────────────────────────────────────────────────────────
TOGETHER_CONFIG: dict[str, Any] = {
    "name":         "Together AI",
    "provider_id":  "together",
    "keys": [
        # "DEIN_TOGETHER_API_KEY_HIER",      # Key 1
    ],
    "model":                      "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "base_url":                   "https://api.together.xyz/v1",
    "rpm_limit":                  60,
    "rpd_limit":                  0,
    "cost_per_1k_input_tokens":   0.00088,
    "cost_per_1k_output_tokens":  0.00088,
    "is_free_tier":               False,
    "enabled":                    False,
    "tags":                       ["optional", "paid", "open-source"],
}


# ═════════════════════════════════════════════════════════════════════════════
#  FALLBACK-KETTE – HIER REIHENFOLGE FESTLEGEN
#  Index 0 = zuerst probiert | höchster Index = letzter Ausweg
#  Das Backend überspringt automatisch:
#    • Provider mit enabled=False
#    • Provider ohne eingetragene Keys
#    • Provider deren Tageslimit (rpd_limit) bereits erreicht ist
#
#  Neuen Provider einfach ans Ende dieser Liste anfügen.
# ═════════════════════════════════════════════════════════════════════════════
API_PROVIDERS: list[dict[str, Any]] = [
    GEMINI_CONFIG,       # Stufe 1 – Primär       (kostenlos, 1.500/Tag)
    GROQ_CONFIG,         # Stufe 2 – Fallback 1   (kostenlos, 14.400/Tag)
    DEEPSEEK_CONFIG,     # Stufe 3 – Fallback 2   (kostenpflichtig)
    OPENAI_CONFIG,       # Stufe 4 – Optional     (deaktiviert)
    ANTHROPIC_CONFIG,    # Stufe 5 – Optional     (deaktiviert)
    MISTRAL_CONFIG,      # Stufe 6 – Optional     (deaktiviert)
    TOGETHER_CONFIG,     # Stufe 7 – Optional     (deaktiviert)
    # ← NEUEN PROVIDER HIER EINFÜGEN ↑
]


# ─────────────────────────────────────────────────────────────────────────────
#  EXTERNE DIENSTE (Suche, Scraping, sonstige Tools)
# ─────────────────────────────────────────────────────────────────────────────
EXTERNAL_SERVICES: dict[str, Any] = {
    # Serper – Google-Suche-API (für das search_web-Tool des Agents)
    "serper": {
        "name":    "Serper (Google Search)",
        "keys":    [
            # "DEIN_SERPER_API_KEY_HIER",
        ],
        "base_url": "https://google.serper.dev",
        "enabled":  False,
    },
    # Brave Search – datenschutzfreundliche Alternative zu Google-Suche
    "brave_search": {
        "name":    "Brave Search",
        "keys":    [
            # "DEIN_BRAVE_SEARCH_API_KEY_HIER",
        ],
        "base_url": "https://api.search.brave.com/res/v1",
        "enabled":  False,
    },
    # Firecrawl – Website-Scraping und Crawling
    "firecrawl": {
        "name":    "Firecrawl",
        "keys":    [
            # "DEIN_FIRECRAWL_API_KEY_HIER",
        ],
        "base_url": "https://api.firecrawl.dev/v1",
        "enabled":  False,
    },
    # Neue externe Dienste: einfach weiteres Dict nach gleichem Muster eintragen
}


# ─────────────────────────────────────────────────────────────────────────────
#  GLOBALE KOSTEN-EINSTELLUNGEN
# ─────────────────────────────────────────────────────────────────────────────
COST_SETTINGS: dict[str, Any] = {
    # Tägliches Gesamtlimit in EUR (0 = kein Limit – wird nicht empfohlen)
    "daily_limit_eur":              2.00,

    # Separates, niedrigeres Limit für den Autonomie-Modus
    "autonomy_mode_daily_limit_eur": 0.50,

    # EUR/USD-Wechselkurs für die Kostenanzeige
    "eur_usd_rate":                 1.08,

    # Warnschwelle: Push-Benachrichtigung wenn X % des Tageslimits erreicht
    "warning_threshold_pct":        80,
}


# ─────────────────────────────────────────────────────────────────────────────
#  INTERNE REQUEST-EINSTELLUNGEN (normalerweise nicht ändern nötig)
# ─────────────────────────────────────────────────────────────────────────────
INTERNAL: dict[str, Any] = {
    # Timeout pro API-Request in Sekunden
    "request_timeout_sec":      60,

    # Max. Retry-Versuche pro Provider bei Rate-Limit (HTTP 429)
    "max_retries_per_provider": 3,

    # Basis für exponentielles Backoff zwischen Retries (Sekunden)
    "retry_backoff_base_sec":   2,

    # Max. Output-Tokens pro Request (0 = Provider-Default)
    "max_tokens_per_request":   8192,
}
