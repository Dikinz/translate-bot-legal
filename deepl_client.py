"""Минимальный асинхронный клиент DeepL API."""

from dataclasses import dataclass

import aiohttp


class DeepLError(Exception):
    pass


class QuotaExceeded(DeepLError):
    pass


@dataclass
class Translation:
    text: str
    source_lang: str  # например "RU"


def default_base_url(api_key: str) -> str:
    # Ключи бесплатного тарифа заканчиваются на ":fx" и работают только с api-free
    if api_key.endswith(":fx"):
        return "https://api-free.deepl.com"
    return "https://api.deepl.com"


class DeepLClient:
    def __init__(self, api_key: str, base_url: str | None = None, timeout: float = 15):
        self._api_key = api_key
        self._base_url = (base_url or default_base_url(api_key)).rstrip("/")
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self._timeout,
                headers={"Authorization": f"DeepL-Auth-Key {self._api_key}"},
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def translate(self, text: str, target_lang: str) -> Translation:
        session = await self._get_session()
        payload = {"text": [text], "target_lang": target_lang}
        async with session.post(f"{self._base_url}/v2/translate", json=payload) as resp:
            if resp.status == 456:
                raise QuotaExceeded("Исчерпан лимит символов DeepL")
            if resp.status == 403:
                raise DeepLError("DeepL отклонил ключ (403). Проверьте DEEPL_API_KEY")
            if resp.status == 429:
                raise DeepLError("Слишком много запросов к DeepL, попробуйте позже")
            if resp.status != 200:
                body = await resp.text()
                raise DeepLError(f"DeepL вернул {resp.status}: {body[:200]}")
            data = await resp.json()
        item = data["translations"][0]
        return Translation(text=item["text"], source_lang=item["detected_source_language"].upper())
