"""
Thin async wrapper around the Gemini API (Vision + Text).

Deliberately a plain httpx call to the REST endpoint rather than the full
google-generativeai SDK — one less heavy dependency, and it makes the actual
request/response shape visible and explainable rather than hidden behind
SDK abstractions. If Gemini is ever swapped for another provider, this is
the only file that changes.
"""

import base64
import json
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# Asks Gemini to reason like a nutrition expert, not just estimate macros —
# this is what replaced the old local healthy_score heuristic (which scored
# deep-fried pakora as "healthy" purely because of a protein bonus). The
# classification now comes from the model weighing the same signals a
# nutritionist actually would: fiber, whole food vs. refined/processed
# ingredients, cooking method, added sugar, sodium, and overall balance —
# not calories/protein/fat in isolation.
MEAL_ANALYSIS_PROMPT = """You are an expert nutritionist analyzing a meal photo.

First, identify the food and estimate its calories, protein, carbohydrates,
and fat.

Then classify the overall healthfulness of the meal the way a nutritionist
would — reasoning about the whole picture, not just calories and macros.
Weigh things like: fiber content, presence of vegetables or fruit, whether
it relies on refined flour or heavily processed ingredients, the cooking
method (deep-fried vs. grilled/steamed/roasted), added sugar, sodium level,
and overall nutritional balance. A high-protein food can still be
unhealthy overall (e.g. deep-fried and low in fiber), and a lower-protein
food can still be healthy (e.g. fiber-rich vegetables and whole grains) —
classify on the full picture, not any single factor.

Classify into exactly one of: "healthy", "moderate", "unhealthy".

Respond with ONLY a JSON object, no markdown, no extra text, in exactly
this shape:

{"detected_food": "string", "calories": number, "protein_g": number,
 "carbs_g": number, "fat_g": number,
 "health_status": "healthy" | "moderate" | "unhealthy",
 "reason": "one concise sentence explaining the classification"}
"""


class GeminiClient:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL

    async def analyze_meal_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
        """
        Sends the meal photo + the nutrition-expert prompt to Gemini Vision
        and parses the JSON it returns. Raises ValueError if the model's
        response can't be parsed — callers decide how to handle that
        (retry, fallback, surface an error to the user).
        """
        url = f"{GEMINI_BASE_URL}/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": MEAL_ANALYSIS_PROMPT},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64.b64encode(image_bytes).decode(),
                            }
                        },
                    ]
                }
            ]
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return self._parse_json_response(text)

    async def generate_text(self, prompt: str) -> str:
        """Used for dynamic messages: morning greetings, and the composed
        conversational meal-logged reply."""
        url = f"{GEMINI_BASE_URL}/{self.model}:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    @staticmethod
    def _parse_json_response(text: str) -> dict:
        # Gemini sometimes wraps JSON in ```json ... ``` even when asked not
        # to — strip that before parsing rather than trusting raw output.
        cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Gemini response as JSON: %s", text)
            raise ValueError("Gemini returned an unparsable response") from exc


gemini_client = GeminiClient()