from __future__ import annotations

from typing import Optional

from openai import AsyncOpenAI

from interview_prep_backend.config import get_settings


async def generate_coaching_line(prompt: str, *, tone: str = "supportive") -> str:
    settings = get_settings()
    if not settings.enable_external_apis or not settings.deepseek_api_key:
        return _fallback_response(prompt, tone)

    client = AsyncOpenAI(
        api_key=settings.deepseek_api_key,
        base_url="https://api.deepseek.com",
    )

    try:
        response = await client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an empathetic interview coach. Provide one concise, actionable tip based on the prompt."
                    f" Maintain a {tone} tone.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=120,
            temperature=0.6,
        )

        completion = response.choices[0].message.content
        if not completion:
            return _fallback_response(prompt, tone)
        return completion.strip()
    except Exception:
        return _fallback_response(prompt, tone)


def _fallback_response(prompt: str, tone: str) -> str:
    return (
        "Take a breath, answer with structured points, and keep your energy steady."
        " Focus on one clear outcome in your next sentence."
    )
