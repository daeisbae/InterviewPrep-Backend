from __future__ import annotations

from typing import Optional

import google.generativeai as genai

from interview_prep_backend.config import get_settings


async def generate_coaching_line(prompt: str, *, tone: str = "supportive") -> str:
    settings = get_settings()
    if not settings.enable_external_apis or not settings.gemini_api_key:
        return _fallback_response(prompt, tone)

    # Configure Gemini
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

    try:
        # Build system instruction
        system_instruction = (
            f"You are an empathetic interview coach. "
            f"Provide one concise, actionable tip based on the user's question. "
            f"Maintain a {tone} tone."
        )
        
        # Combine system instruction with user prompt
        full_prompt = f"{system_instruction}\n\nUser question: {prompt}"
        
        # Generate response
        response = await model.generate_content_async(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=120,
                temperature=0.6,
            ),
        )

        completion = response.text
        if not completion:
            return _fallback_response(prompt, tone)
        return completion.strip()
    except Exception as e:
        # Log error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Gemini API error: {e}")
        return _fallback_response(prompt, tone)


def _fallback_response(prompt: str, tone: str) -> str:
    return (
        "Take a breath, answer with structured points, and keep your energy steady."
        " Focus on one clear outcome in your next sentence."
    )
