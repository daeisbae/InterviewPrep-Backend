from __future__ import annotations

from typing import Optional

import httpx

from app.config import get_settings

_DEEPSEEK_URL = "https://api.deepseek.com/text/generation"


async def generate_coaching_line(prompt: str, *, tone: str = "supportive") -> str:
    settings = get_settings()
    if not settings.enable_external_apis or not settings.deepseek_api_key:
        return _fallback_response(prompt, tone)

    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.deepseek_model,
        "prompt": (
            "You are an empathetic interview coach. Provide one concise, actionable tip based on the prompt."
            f" Maintain a {tone} tone.\nPrompt: {prompt}"
        ),
        "max_tokens": 120,
        "temperature": 0.6,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(_DEEPSEEK_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    completion = data.get("choices", [{}])[0].get("text")
    if not completion:
        return _fallback_response(prompt, tone)
    return completion.strip()


def _fallback_response(prompt: str, tone: str) -> str:
    return (
        "Take a breath, answer with structured points, and keep your energy steady."
        " Focus on one clear outcome in your next sentence."
    )
