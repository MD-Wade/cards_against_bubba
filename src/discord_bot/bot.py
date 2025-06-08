from discord.ext import commands
from discord_bot.config import TOKEN, intents
from discord_bot.services.game_manager import set_bot

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    user_id = bot.user.id if bot.user else "Unknown"
    print(f"Bot is ready. User ID: {user_id}")

if __name__ == "__main__":
    for cog in ["discord_bot.cogs.game_cog"]:
        bot.load_extension(cog)
    set_bot(bot)
    bot.run(TOKEN)