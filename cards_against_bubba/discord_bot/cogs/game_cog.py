# discord_bot/cogs/game_cog.py
import discord
from discord.ext import commands
from discord import Option
from services.game_manager import create_game, get_game
from game_phases import Phase

class GameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="startgame")
    async def startgame(
        self,
        ctx: discord.ApplicationContext,
        hand_size: Option(int, "Cards per player", required=False, default=7),
        draft_mode: Option(bool, "Use draft deal?", required=False, default=False),
    ):
        if get_game(ctx.channel_id):
            return await ctx.respond("A game is already running here!", ephemeral=True)

        # initially, no players; they’ll /join
        game = create_game(ctx.channel_id, [], hand_size, draft_mode)

        # announce phase changes
        def on_phase(old: Phase, new: Phase):
            self.bot.loop.create_task(ctx.channel.send(f"**Phase:** {new.value}"))
        game.add_phase_listener(on_phase)

        await ctx.respond("Game created! Players can now use `/join`.", ephemeral=False)

    @commands.slash_command(name="join")
    async def join(self, ctx: discord.ApplicationContext):
        game = get_game(ctx.channel_id)
        if not game:
            return await ctx.respond("No game running—use `/startgame` first.", ephemeral=True)
        if ctx.author.id in game.state.players:
            return await ctx.respond("You’ve already joined!", ephemeral=True)
        game.state.players.append(ctx.author.id)
        await ctx.respond(f"{ctx.author.display_name} joined! 🎉")

    @commands.slash_command(name="begin")
    async def begin(self, ctx: discord.ApplicationContext):
        game = get_game(ctx.channel_id)
        if not game:
            return await ctx.respond("No game running—use `/startgame` first.", ephemeral=True)
        if len(game.state.players) < 3:
            return await ctx.respond("At least 3 players needed.", ephemeral=True)

        game.start()
        prompt = game.state.current_prompt.text

        # DM each player their hand
        for pid in game.state.players:
            user = await self.bot.fetch_user(pid)
            hand = "\n".join(f"{i}: {c.text}" for i, c in enumerate(game.state.player_by_id(pid).hand))
            await user.send(f"Your hand:\n{hand}")

        await ctx.respond(f"**Black card:** {prompt}")

    @commands.slash_command(name="play")
    async def play(self, ctx: discord.ApplicationContext, choices: Option(str, "Comma-separated indices")):
        game = get_game(ctx.channel_id)
        if not game:
            return await ctx.respond("No game in progress.", ephemeral=True)

        try:
            idxs = [int(x.strip()) for x in choices.split(",")]
            game.submit(ctx.author.id, idxs)
            await ctx.respond("Cards submitted!", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"Error: {e}", ephemeral=True)
            return

        # if we just moved to JUDGING, DM the judge
        if game.state.phase == Phase.JUDGING:
            judge_id = game.state.players[game.state.judge_index]
            subs = list(game.state.submissions.items())
            formatted = "\n".join(
                f"{i}: {', '.join(c.text for c in cards)}"
                for i, (_, cards) in enumerate(subs)
            )
            judge = await self.bot.fetch_user(judge_id)
            await judge.send(f"Time to judge! Subs:\n{formatted}")
            await ctx.channel.send("All submissions in—judge has been DMed.")

    @commands.slash_command(name="judge")
    async def judge(self, ctx: discord.ApplicationContext, winner: Option(int, "Submission index")):
        game = get_game(ctx.channel_id)
        if not game:
            return await ctx.respond("No game in progress.", ephemeral=True)
        if game.state.phase is not Phase.JUDGING:
            return await ctx.respond("Not time to judge yet.", ephemeral=True)

        try:
            subs = list(game.state.submissions.items())
            winner_id, _ = subs[winner]
            game.judge(winner_id)
            await ctx.respond(f"🏆 { (await self.bot.fetch_user(winner_id)).display_name } wins!")
            await ctx.channel.send(f"Next prompt: **{game.state.current_prompt.text}**")
        except Exception as e:
            await ctx.respond(f"Error: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(GameCog(bot))
