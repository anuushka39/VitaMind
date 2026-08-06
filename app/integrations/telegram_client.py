"""Thin async wrapper around the Telegram Bot API."""

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

TELEGRAM_BASE_URL = "https://api.telegram.org/bot{token}"


class TelegramClient:
    def __init__(self):
        self.base_url = TELEGRAM_BASE_URL.format(token=settings.TELEGRAM_BOT_TOKEN)

    async def send_message(self, chat_id: str, text: str) -> None:
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                # Logged, not raised — a failed outbound send (e.g. user
                # blocked the bot) shouldn't crash the background task or
                # take down a scheduled job for every other user.
                logger.error("Telegram sendMessage failed: %s", response.text)

    async def download_file(self, file_id: str) -> bytes:
        """
        Telegram requires two calls: getFile (to resolve file_id -> path),
        then a direct download from the file path.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            meta_resp = await client.get(f"{self.base_url}/getFile", params={"file_id": file_id})
            meta_resp.raise_for_status()
            file_path = meta_resp.json()["result"]["file_path"]

            download_url = (
                f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file_path}"
            )
            file_resp = await client.get(download_url)
            file_resp.raise_for_status()
            return file_resp.content


telegram_client = TelegramClient()
