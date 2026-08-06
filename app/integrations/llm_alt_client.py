"""
Thin async wrapper around a second, minimal/free-quota LLM (Groq's hosted
Llama models), used ONLY by scripts/compare_llms.py for the latency/quality
comparison called for in the spec. Not wired into any user-facing flow —
Gemini remains the single production LLM for the actual product.

Groq's API is OpenAI-chat-completions-compatible, which keeps this client
small and structurally identical to a "swap the provider" exercise.
"""

import httpx

from app.core.config import settings

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class AltLLMClient:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL

    async def generate_text(self, prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(GROQ_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        return data["choices"][0]["message"]["content"].strip()


alt_llm_client = AltLLMClient()
