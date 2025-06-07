from discord.ext import commands
from config import TOKEN, intents

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")

if __name__ == "__main__":
    for cog in ["cogs.game_cog"]:
        bot.load_extension(cog)
    bot.run(TOKEN)