# Discord-бот для перевода по флагу

Поставьте под любым сообщением реакцию-флаг (🇬🇧 🇺🇸 🇷🇺 🇺🇦 🇩🇪 🇫🇷 🇪🇸 🇯🇵 🇨🇳 …), и бот ответит на это сообщение переводом через DeepL.

- Перевод можно сделать на любой из ~30 языков DeepL. Исходный язык определяется автоматически.
- Если флаг ставит второй человек, бот не публикует перевод повторно и не тратит лимит DeepL.
- Если сообщение уже написано на выбранном языке, бот ничего не делает.
- Бот может работать только в выбранных каналах (`ALLOWED_CHANNEL_IDS`).
- Переводы можно автоматически удалять через заданное время (`TRANSLATION_DELETE_AFTER`).
- Упоминания в переводе никого не пингуют.

Полный список флагов есть в `languages.py`. Новый флаг добавляется одной строкой в `_COUNTRY_TO_LANG`.

## 1. Создайте бота в Discord

1. Откройте https://discord.com/developers/applications, нажмите **New Application** и введите имя.
2. На вкладке **Bot** нажмите **Reset Token** и скопируйте токен. Это значение `DISCORD_TOKEN`.
3. Там же включите **Message Content Intent**. Без него бот не сможет прочитать текст сообщения.
4. На вкладке **OAuth2 → URL Generator** отметьте scope `bot` и права:
   `View Channels`, `Send Messages`, `Embed Links`, `Read Message History`.
   Откройте получившуюся ссылку и добавьте бота на свой сервер.
5. Чтобы получить ID канала: в Discord включите *Настройки → Расширенные → Режим разработчика*, затем нажмите правой кнопкой на канал и выберите **Копировать ID канала**.

## 2. Получите ключ DeepL

Зарегистрируйтесь на https://www.deepl.com/pro-api (есть бесплатный тариф **DeepL API Free**: 500 000 символов в месяц) и скопируйте ключ на странице https://www.deepl.com/your-account/keys.
Ключ бесплатного тарифа оканчивается на `:fx`. Бот сам выберет нужный адрес API.

## 3. Запуск на сервере (Docker)

Скопируйте папку проекта на сервер и перейдите в неё.

```bash
cp .env.example .env
```

```bash
nano .env
```

В `.env` заполните `DISCORD_TOKEN`, `DEEPL_API_KEY` и, если нужно, `ALLOWED_CHANNEL_IDS`.

```bash
docker compose up -d --build
```

Просмотр логов:

```bash
docker compose logs -f
```

Благодаря `restart: unless-stopped` бот сам перезапускается после сбоев и перезагрузки сервера. После изменений в коде повторите `docker compose up -d --build`.

### Запуск без Docker

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
```

```bash
python bot.py
```

## Настройки (.env)

| Переменная | Описание |
|---|---|
| `DISCORD_TOKEN` | токен бота (обязательно) |
| `DEEPL_API_KEY` | ключ DeepL (обязательно) |
| `ALLOWED_CHANNEL_IDS` | ID каналов через запятую. Пусто = все каналы, где у бота есть доступ |
| `TRANSLATION_DELETE_AFTER` | через сколько секунд удалять перевод, `0` = не удалять |

## Тесты

```bash
pip install pytest && python -m pytest -q tests
```
