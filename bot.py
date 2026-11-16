"""Discord-бот: переводит сообщение, когда под ним ставят реакцию-флаг (🇬🇧, 🇷🇺, 🇩🇪…)."""

import asyncio
import logging
import os
from collections import OrderedDict

import discord
from dotenv import load_dotenv

from deepl_client import DeepLClient, DeepLError, QuotaExceeded
from languages import LANGUAGE_NAMES, base_lang, lang_for_emoji

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("translate-bot")

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
DEEPL_API_KEY = os.environ["DEEPL_API_KEY"]
# Пусто = бот работает во всех каналах, где у него есть доступ
ALLOWED_CHANNEL_IDS = {int(x) for x in os.getenv("ALLOWED_CHANNEL_IDS", "").replace(" ", "").split(",") if x}
# Через сколько секунд удалять перевод (0 = не удалять)
DELETE_AFTER = int(os.getenv("TRANSLATION_DELETE_AFTER", "0")) or None

EMBED_LIMIT = 4096
CACHE_SIZE = 500


class TranslateBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True  # нужен, чтобы читать текст сообщений
        intents.reactions = True
        super().__init__(intents=intents, allowed_mentions=discord.AllowedMentions.none())
        self.deepl = DeepLClient(DEEPL_API_KEY)
        # (message_id, lang) -> id сообщения с переводом; защищает от дублей и экономит квоту DeepL
        self._done: OrderedDict[tuple[int, str], int] = OrderedDict()
        self._in_progress: set[tuple[int, str]] = set()

    async def on_ready(self) -> None:
        log.info("Вошёл как %s (id=%s)", self.user, self.user.id if self.user else "?")
        if ALLOWED_CHANNEL_IDS:
            log.info("Работаю только в каналах: %s", ", ".join(map(str, ALLOWED_CHANNEL_IDS)))

    async def close(self) -> None:
        await self.deepl.close()
        await super().close()

    def _remember(self, key: tuple[int, str], reply_id: int) -> None:
        self._done[key] = reply_id
        self._done.move_to_end(key)
        while len(self._done) > CACHE_SIZE:
            self._done.popitem(last=False)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.user_id == (self.user.id if self.user else None):
            return
        if payload.member is not None and payload.member.bot:
            return
        if ALLOWED_CHANNEL_IDS and payload.channel_id not in ALLOWED_CHANNEL_IDS:
            return

        target = lang_for_emoji(str(payload.emoji))
        if target is None:
            return

        key = (payload.message_id, target)
        if key in self._in_progress:
            return
        self._in_progress.add(key)
        try:
            await self._handle(payload, target, key)
        finally:
            self._in_progress.discard(key)

    async def _handle(self, payload: discord.RawReactionActionEvent, target: str, key: tuple[int, str]) -> None:
        channel = self.get_channel(payload.channel_id) or await self.fetch_channel(payload.channel_id)
        if not isinstance(channel, discord.abc.Messageable):
            return

        # Перевод уже есть и не удалён — повторно не публикуем
        if key in self._done:
            try:
                await channel.fetch_message(self._done[key])
                return
            except discord.NotFound:
                del self._done[key]

        try:
            message = await channel.fetch_message(payload.message_id)
        except (discord.NotFound, discord.Forbidden):
            return

        text = message.clean_content.strip()
        if not text:
            return

        try:
            async with channel.typing():
                result = await self.deepl.translate(text, target)
        except QuotaExceeded:
            await channel.send("⚠️ Лимит DeepL на этот месяц исчерпан.", delete_after=30)
            return
        except (DeepLError, asyncio.TimeoutError, OSError) as exc:
            log.warning("Ошибка перевода: %s", exc)
            await channel.send("⚠️ Не удалось перевести сообщение, попробуйте позже.", delete_after=15)
            return

        if result.source_lang == base_lang(target):
            return  # сообщение уже на этом языке

        translated = result.text
        if len(translated) > EMBED_LIMIT:
            translated = translated[: EMBED_LIMIT - 1] + "…"

        src_name = LANGUAGE_NAMES.get(result.source_lang, result.source_lang)
        dst_name = LANGUAGE_NAMES.get(target, target)
        embed = discord.Embed(description=translated, color=0x0F2B46)
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.set_footer(text=f"{payload.emoji} {src_name} → {dst_name} · DeepL")

        reply = await message.reply(embed=embed, mention_author=False, delete_after=DELETE_AFTER)
        self._remember(key, reply.id)


def main() -> None:
    TranslateBot().run(DISCORD_TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
