import asyncio
import os
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from aiohttp import web

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DISCORD_TOKEN", "test")
os.environ.setdefault("DEEPL_API_KEY", "test:fx")

import discord

import bot
from deepl_client import (
    DeepLClient,
    QuotaExceeded,
    Translation,
    default_base_url,
)
from languages import base_lang, lang_for_emoji


def test_flags():
    assert lang_for_emoji("🇷🇺") == "RU"
    assert lang_for_emoji("🇬🇧") == "EN-GB"
    assert lang_for_emoji("🇺🇸") == "EN-US"
    assert lang_for_emoji("🇺🇦") == "UK"
    assert lang_for_emoji("👍") is None
    assert base_lang("ZH-HANS") == "ZH"


def test_base_url():
    assert default_base_url("abc:fx") == "https://api-free.deepl.com"
    assert default_base_url("abc") == "https://api.deepl.com"


async def _run_fake_deepl(status=200):
    seen = {}

    async def handler(request):
        seen["auth"] = request.headers.get("Authorization")
        seen["body"] = await request.json()
        if status != 200:
            return web.Response(status=status)
        return web.json_response({"translations": [{"detected_source_language": "RU", "text": "Hello"}]})

    app = web.Application()
    app.router.add_post("/v2/translate", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    return runner, f"http://127.0.0.1:{port}", seen


def test_deepl_client():
    async def go():
        runner, url, seen = await _run_fake_deepl()
        client = DeepLClient("key123", base_url=url)
        try:
            res = await client.translate("Привет", "EN-US")
        finally:
            await client.close()
            await runner.cleanup()
        assert res == Translation(text="Hello", source_lang="RU")
        assert seen["auth"] == "DeepL-Auth-Key key123"
        assert seen["body"] == {"text": ["Привет"], "target_lang": "EN-US"}

    asyncio.run(go())


def test_deepl_quota():
    async def go():
        runner, url, _ = await _run_fake_deepl(status=456)
        client = DeepLClient("k", base_url=url)
        try:
            await client.translate("x", "EN-US")
        except QuotaExceeded:
            return
        finally:
            await client.close()
            await runner.cleanup()
        raise AssertionError("expected QuotaExceeded")

    asyncio.run(go())


def _make_bot_with_mocks(translation):
    b = bot.TranslateBot.__new__(bot.TranslateBot)  # без подключения к Discord
    from collections import OrderedDict
    b._done, b._in_progress = OrderedDict(), set()
    b.deepl = MagicMock()
    b.deepl.translate = AsyncMock(return_value=translation)
    b._connection = MagicMock()
    b._connection.user = SimpleNamespace(id=999)

    message = MagicMock()
    message.clean_content = "Привет всем"
    message.author.display_name = "Вася"
    message.author.display_avatar.url = "https://cdn.example/a.png"
    message.reply = AsyncMock(return_value=SimpleNamespace(id=555))

    channel = MagicMock(spec=discord.TextChannel)
    channel.fetch_message = AsyncMock(return_value=message)
    typing_cm = MagicMock()
    typing_cm.__aenter__ = AsyncMock(return_value=None)
    typing_cm.__aexit__ = AsyncMock(return_value=False)
    channel.typing.return_value = typing_cm
    channel.send = AsyncMock()
    b.get_channel = MagicMock(return_value=channel)
    return b, channel, message


def _payload(emoji="🇬🇧", user_id=1):
    return SimpleNamespace(user_id=user_id, member=None, channel_id=10, message_id=20, emoji=emoji)


def test_reaction_translates_once():
    b, _, message = _make_bot_with_mocks(Translation("Hello everyone", "RU"))

    async def go():
        await b.on_raw_reaction_add(_payload())
        await b.on_raw_reaction_add(_payload(user_id=2))  # второй человек ставит тот же флаг

    asyncio.run(go())
    b.deepl.translate.assert_awaited_once_with("Привет всем", "EN-GB")
    assert message.reply.await_count == 1
    embed = message.reply.call_args.kwargs["embed"]
    assert embed.description == "Hello everyone"
    assert "русский → английский (UK)" in embed.footer.text


def test_ignores_non_flag_own_and_same_language():
    b, _, message = _make_bot_with_mocks(Translation("Привет всем", "RU"))

    async def go():
        await b.on_raw_reaction_add(_payload(emoji="👍"))
        await b.on_raw_reaction_add(_payload(user_id=999))  # реакция самого бота
        await b.on_raw_reaction_add(_payload(emoji="🇷🇺"))  # уже на русском

    asyncio.run(go())
    assert b.deepl.translate.await_count == 1
    message.reply.assert_not_awaited()


def test_allowed_channels(monkeypatch):
    b, _, _ = _make_bot_with_mocks(Translation("Hi", "RU"))
    monkeypatch.setattr(bot, "ALLOWED_CHANNEL_IDS", {777})
    asyncio.run(b.on_raw_reaction_add(_payload()))
    b.deepl.translate.assert_not_awaited()
