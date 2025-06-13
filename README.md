# Cards Against Bubba

**Cards Against Bubba** is a Discord implementation of a "Cards Against Humanity" style game.  It consists of a card game engine and a Discord bot with slash commands for running games in your server.

## Features

- A game engine that manages hands, scoring and phases such as `WAITING`, `DRAFT_PICKING`, `SUBMISSIONS`, `JUDGING` and `FINISHED`【F:src/cards_engine/game_phases.py†L1-L8】.
- Card data is loaded from `data/*.json*` files, with support for both plain JSON and zstd compressed files【F:src/cards_engine/card_repository.py†L19-L24】.
- The engine shuffles decks, deals hands and draws prompts when starting a game【F:src/cards_engine/game_engine.py†L8-L27】.
- A Discord bot exposes commands like `/start`, `/join`, `/draft`, `/play`, `/judge`, `/skip` and `/stop` for playing entirely via Discord【F:src/discord_bot/cogs/game_cog.py†L23-L107】.

## Requirements

- Python 3.10+
- The packages listed in [`requirements.txt`](requirements.txt).
- A Discord bot token stored in the environment variable `CAB_BOT_TOKEN`【F:src/discord_bot/config.py†L1-L5】.
- A directory named `data/` containing the card JSON or `.json.zst` files.

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Place your card data files inside `data/` at the project root. See `CardRepository` for the expected format.

## Running the Bot

Start the bot after setting the token:

```bash
export CAB_BOT_TOKEN=your_token_here
python -m discord_bot.bot
```

On startup you should see "Bot is ready" in the console【F:src/discord_bot/bot.py†L5-L10】.

## Running Tests

Unit tests for the engine are located in `src/tests`. Run them with:

```bash
pytest
```

The tests exercise full rounds and edge cases of the engine【F:src/tests/test_game.py†L1-L19】【F:src/tests/test_game.py†L259-L261】.

## Repository Layout

```
src/
    cards_engine/   # Core game logic
    discord_bot/    # Discord bot implementation
    tests/          # Pytest suite
assets/             # Static assets
```

## License

No explicit license file is provided. Assume all rights reserved.

