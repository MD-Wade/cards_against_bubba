import os
from discord import Intents

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
intents = Intents.default()