"""
MAJE – Voice Routes
Speech-to-Text via the Groq Whisper API (free tier) – no extra cost for the user.
Text-to-Speech happens on-device in the app (expo-speech), so it is free too.
"""
from __future__ import annotations

import os
from typing import Optional

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from loguru import logger

router = APIRouter()

GROQ_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
OPENAI_STT_URL = "https://api.openai.com/v1/audio/transcriptions"


def _groq_keys() -> list[str]:
    keys: list[str] = []
    try:
        from config.api_keys import API_PROVIDERS
        for p in API_PROVIDERS:
            if p.get("provider_id") == "groq":
                keys += [k for k in p.get("keys", []) if k and not str(k).startswith("DEIN_")]
    except Exception:
        pass
    env_key = os.getenv("GROQ_API_KEY")
    if env_key and env_key not in keys:
        keys.append(env_key)
    return keys


def _stt_provider() -> tuple[Optional[str], Optional[str]]:
    """Return (provider, api_key) for the best available STT provider."""
    groq = _groq_keys()
    if groq:
        return "groq", groq[0]
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        return "openai", openai_key
    return None, None


@router.get("/status")
async def voice_status():
    provider, _ = _stt_provider()
    return {"stt_available": provider is not None, "provider": provider, "tts": "on-device"}


@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
):
    """Transcribe an uploaded audio clip to text (Groq Whisper, free tier)."""
    provider, api_key = _stt_provider()
    if not provider:
        raise HTTPException(
            503,
            "No transcription provider configured. Add a Groq API key (free) in config/api_keys.py.",
        )

    data = await audio.read()
    if not data:
        raise HTTPException(400, "Empty audio file.")
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(413, "Audio file too large (max 25 MB).")

    if provider == "groq":
        url, model = GROQ_STT_URL, os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo")
    else:
        url, model = OPENAI_STT_URL, "whisper-1"

    filename = audio.filename or "audio.m4a"
    files = {"file": (filename, data, audio.content_type or "audio/m4a")}
    form = {"model": model, "response_format": "json"}
    if language:
        form["language"] = language

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                data=form,
            )
        if resp.status_code != 200:
            logger.warning(f"STT ({provider}) failed: {resp.status_code} {resp.text[:300]}")
            raise HTTPException(502, f"Transcription failed ({provider}): {resp.text[:200]}")
        text = resp.json().get("text", "").strip()
        return {"text": text, "provider": provider, "model": model}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"STT error: {e}")
        raise HTTPException(502, f"Transcription error: {e}")
