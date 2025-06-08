import discord
from discord.ext import commands
from discord import Option
from discord_bot.services.game_manager  import create_lobby, get_game
from discord_bot.views.setup_view       import SetupView
from discord_bot.views.join_view        import JoinView
from discord_bot.views.draft_view       import DraftView
from discord_bot.views.play_view        import PlayView
from discord_bot.views.judge_view       import JudgeView
from cards_engine.game_phases           import Phase
from cards_engine.player                import Player
from cards_engine.game                  import Game
from discord_bot.views.judge_button_view import JudgeButtonView

class GameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
            name="start", 
            description="Create and configure a new game of Cards Against Bubba",
            guild_ids=[1075249749357252680, 1167164629844234270]
            )
    async def start(self, ctx: discord.ApplicationContext):
        existing = get_game(ctx.channel_id)
        if existing:
            await ctx.respond(
                "❌ A game is already in progress in this channel.",
                ephemeral=True
            )
            return None

        lobby = create_lobby(
            channel_id=ctx.channel_id,
            host_id=ctx.author.id,
            host_name=ctx.author.display_name
        )

        player_host = Player(id=str(ctx.author.id), name=ctx.author.display_name)
        lobby.players.append(player_host)

        view_join = JoinView(lobby)
        join_message = await ctx.channel.send(
            f"👋 {ctx.author.display_name} started a new game of Cards Against Bubba! Join with `/join` or by clicking the button!",
            view=view_join,
        )
        lobby.join_message_id = join_message.id

        view_setup = SetupView(ctx.channel_id, bot=self.bot)
        await ctx.respond(
            "👋 Host panel: Select packs and regions, then set hand size and draft mode, and ▶️ Launch!",
            view=view_setup,
            ephemeral=True
        )

    @commands.slash_command(
            name="draft", 
            description="Pick from your current draft pack",
            guild_ids=[1075249749357252680, 1167164629844234270]
            )
    async def draft(self, ctx: discord.ApplicationContext):
        game = get_game(ctx.channel_id)
        if not game or game.state.phase is not Phase.DRAFT_PICKING:
            return await ctx.respond("No draft in progress.", ephemeral=True)

        # send (or re‐use) one ephemeral message per player
        view = DraftView(ctx.channel_id, str(ctx.author.id))
        await ctx.respond(
            "Your draft pack, pick one card:",
            view=view,
            ephemeral=True
        )

    @commands.slash_command(
        name="play",
        description="Select cards to play as a response to the current prompt",
        guild_ids=[1075249749357252680, 1167164629844234270]
    )
    async def play(self, ctx: discord.ApplicationContext):
        game = get_game(ctx.channel_id)
        if not game or game.state.phase != Phase.SUBMISSIONS:
            return await ctx.respond("No active round to play cards.", ephemeral=True)

        player = game.state.player_by_id(str(ctx.author.id))
        if not player:
            return await ctx.respond("You are NOT in this game!", ephemeral=True)
        view = PlayView(ctx.channel_id, str(ctx.author.id), self.bot)
        if view.pick_count == 1:
            msg = "Select a response to play for this prompt."
        else:
            msg = "Select a response to play for the first blank of this prompt."
        await ctx.respond(
            msg,
            view=view,
            ephemeral=True
        )

    @commands.slash_command(
        name="judge",
        description="Select the best response as the judge",
        guild_ids=[1075249749357252680, 1167164629844234270]
    )
    async def judge(self, ctx: discord.ApplicationContext):
        game = get_game(ctx.channel_id)
        if not game or game.state.phase != Phase.JUDGING:
            return await ctx.respond("No active round to judge responses.", ephemeral=True)

        player = game.state.player_by_id(str(ctx.author.id))
        if not player or player.id != game.state.current_judge.id:
            return await ctx.respond("You are NOT the judge this round!", ephemeral=True)

        async def on_judge_pick(player_id: str):
            await self.on_judge_pick(ctx.channel_id, player_id)

        view = JudgeView(game, judge_id=game.state.current_judge.id, on_judge_pick=on_judge_pick)
        await ctx.respond(
            "Select the best response from the submissions.:",
            view=view,
            ephemeral=True
        )

    async def on_judge_pick(self, channel_id: int, player_id: str):
        print("GameCog.on_judge_pick")
        game = get_game(channel_id)
        await game.judge(player_id)

    async def on_button_view_judge(self, interaction: discord.Interaction, game: Game):
        """Create a view for the judge button."""
        if str(interaction.user.id) != str(game.state.current_judge.id):
            await interaction.response.send_message("Only the judge can judge this round!", ephemeral=True)
            return
        # Build the actual judge view
        view = JudgeView(game, judge_id=game.state.current_judge.id, on_judge_pick=...)  # etc.
        await interaction.response.send_message(
            "Select the best response:",
            view=view,
            ephemeral=True
        )

def setup(bot):
    bot.add_cog(GameCog(bot))
