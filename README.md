# Ticketgram
A simple yet powerful support bot that allows you to receive and respond to user feedback.

## Gallery
|User-side|Support-side|
|-|-|
|![](/screenshots/user_side.png)|![](/screenshots/support_side.png)|

See more at [Screenshots](screenshots/SCREENSHOTS.md)

# Features
- Message-based (question-answer)
- Anonymous (pseudonym system)
- Configurable
- Dockerized
- Internationalization support
- Access control & usage limitting
- Monitoring support (Prometheus)

# Uses
- `Python 3.11`
- `python-telegram-bot` Telegram Bot HTTP API wrapper (that you can't refuse)
- `peewee` as an ORM
- `babel` for localization
- `prometheus-client` for instrumentation & serving the `/metrics` endpoint
- `SQLite` as a database

# Commands
Client-side:
- `/start` Welcome message
- `/ticket` Create a new ticket

Support-side:
- `/open` View open tickets
- `/ban` Ban the user
- `/unban` Unban the user
- `/pseudonym` Set pseudonym

# Usage
## Prerequisites
1. Bot account
   1. Start the [@BotFather](https://t.me/BotFather)
   2. Type the `/newbot` command
   3. Follow the instructions to get your own bot and `TELEGRAM_TOKEN`
2. Supergroup
   1. Create a regular private group
   2. Upgrade it to a supergroup (for example, by changing the visibility of `chat history for new members`) [1]
3. `chat_id` of the supergroup
   1. Invite the bot to the supergroup
   2. You will see that the bot automatically leaves from unauthorized groups.
   3. Notice the log line `... | INFO | callbacks::leave_chat (...) | Chat is not authorized: 'chat_id'`, where `chat_id` is supergroup id
   > ℹ️ Optionally, use a bot or a custom telegram client of your choice that gives you `chat_id` of the group, for example [@getidsbot](https://t.me/getidsbot)

[1] - Learn more about supergroup triggers here: https://stackoverflow.com/a/62291433

# Installation
>⚠️ Requires Python 3.11 or above

First of all, clone the repository using the `git clone` command and `cd` into the `ticketgram` directory.

## Using Poetry (recommended)
```bash
poetry install
poetry shell
```

## Using pip
```bash
pip install -r requirements.txt
```

# Launch
```bash
# dont forget about environment variables
# Powershell syntax
$env:KEY="VALUE"
# Bash syntax
export KEY=VALUE

...

python src/bot.py
```

# Deploy using Docker
You can pull the latest image from Docker Hub:
```bash
docker pull mikurei/ticketgram:latest
```
Head to the [build section](#build) if you want to build the image by yourself.

## Build
```bash
cd ticketgram
docker build -t ticketgram .
```

## Deploy
Replace `YOUR_TOKEN` with a valid Telegram bot token and `GROUP_CHAT_ID` with the chat id of the group where the bot will operate.

```
docker run -d \
   -e TELEGRAM_TOKEN="YOUR_TOKEN" \
   -e AUTHORIZED_GROUP_ID="GROUP_CHAT_ID" \
   -e DB_URI="/app/db/sqlite.db" \
   --mount "type=volume,src=ticketgram_db,target=/app/db/" \
   ticketgram
```
> ℹ️ You can specify other environment variables here using `-e KEY="VALUE"` syntax to configure runtime of the bot.

# Configuration
Bot is configured using the `Environment Variables`.

List of available env vars
|Name|Description|
|-|-|
|TELEGRAM_TOKEN|**Required** bot token to access the HTTP Bot API|
|AUTHORIZED_GROUP_ID|**Required** group in which the bot operates|
|BOT_LANGUAGE|*Optional* Language of the bot's messages. Defaults to `"en"`|
|DB_URI|*Optional* SQLite connection URI. Defaults to `"sqlite.db"`|
|USER_OPEN_TICKETS_MAX|*Optional* Maximum amount of open tickets per user. Defaults to `"3"`|
|BOT_TIME_ACTIVE|*Optional* Support opening hours which are displayed in the welcome message. Defaults to `"09:00-17:00"`|
|BOT_TIME_ZONE|*Optional* Timezone of the support. Defaults to `"+0"`|
|BOT_ACTIVE_DAYS|*Optional* Working days of the support. Defaults to `"monday tuesday wednesday thursday friday saturday sunday"`|
|PROMETHEUS_ENABLED|*Optional* Enables the Prometheus metrics exporter. Defaults to `False`|
|PROMETHEUS_PORT|*Optional* Port on which the bot serves the `/metrics` endpoint. Defaults to `8000`|

To change the welcome and support reply messages, review the `templates.py` module.

# Monitoring the bot
Ticketgram provides an optional feature that allows you to export metrics to **Prometheus**. To enable it, set the `PROMETHEUS_ENABLED` to `1` and provide a port using `PROMETHEUS_PORT`.

You will need a configured [Prometheus](https://prometheus.io/) server for pulling metrics from the bot. You can use the awesome [Grafana](https://grafana.com/) for visualizaiton.

Currently, ticketgram provides two metrics:
- `ticketgram_callbacks_total{func_name}`
- `ticketgram_callbacks_duration_seconds{func_name}`

To check if the exporter works, open `http://HOST:PROMETHEUS_PORT` in your browser, for example http://localhost:8000

# Localization
Project uses [GNU gettext](https://docs.python.org/3/library/gettext.html) and [Babel](https://babel.pocoo.org/en/latest/index.html) utilities for internationalization.
```
locales/                | Message catalog
|  LANGUAGE_CODE/       | Concrete translation
|  |  LC_MESSAGES/      |
|  |  |  base.mo        | Compiled translation file
|  |  |  base.po        | Translation file
|  base.pot             | Template translation file
```

## Adding a new language
1. Create a new language directory under the `locales/`, for example `ja_JP/`
2. Create `LC_MESSAGES/` in new language directory
3. Copy the `base.pot` from `locales/` folder into `LC_MESSAGES` and rename it to `base.po`
4. Translate the strings to desired language
   - `msgid` key is original string
   - `msgstr` key is translated string
5. Compile the `base.po` to `base.mo` either using `pybabel compile` or `msgfmt` (Linux/WSL only)

___
*I'd appreciate it if you'd leave a **star ⭐** and **fork the repo**. Thanks!*

*Created by [mikurei](https://github.com/mikurei) 2023*