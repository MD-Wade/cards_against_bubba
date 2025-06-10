import discord
from discord.ext import commands
import asyncio
from discord_bot.services.state_manager import get_game, remove_game
from discord_bot.services.game_manager  import create_lobby
from discord_bot.services.game_flow     import handle_play, handle_judge, handle_draft, handle_stop, handle_skip, handle_join
from discord_bot.views.setup_view       import SetupView
from discord_bot.views.join_view        import JoinView
from discord_bot.views.draft_view       import DraftView
from discord_bot.views.play_view        import PlayView
from discord_bot.views.judge_view       import JudgeView
from cards_engine.game_phases           import Phase
from cards_engine.player                import Player
from cards_engine.game                  import Game
from discord_bot.views.judge_button_view import JudgeButtonView

guild_ids_master = [1075249749357252680, 1167164629844234270, 972953179710963762]

class GameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
            name="start", 
            description="Create and configure a new game of Cards Against Bubba",
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
            host_id=str(ctx.author.id),
            host_name=ctx.author.display_name
        )

        player_host = Player(id=str(ctx.author.id), name=ctx.author.display_name)
        lobby.players.append(player_host)

        async def on_join_button(interaction: discord.Interaction):
            """Handle the join button click."""
            await handle_join(interaction)

        view_join = JoinView(lobby, on_join_button=on_join_button)
        join_message = await ctx.channel.send(
            f"👋 {ctx.author.display_name} started a new game of Cards Against Bubba! Join with `/join` or by clicking the button!",
            view=view_join,
        )
        await asyncio.sleep(1)
        lobby.join_message_id = join_message.id

        view_setup = SetupView(ctx.channel_id, bot=self.bot)
        await ctx.respond(
            content="CONFIGURATION: Please configure which packs and regions to enable, as well as other game settings.",
            view=view_setup,
            ephemeral=True
        )

    @commands.slash_command(
            name="join",
            description="Join the current game of Cards Against Bubba",
            )
    async def join(self, ctx: discord.ApplicationContext):
        """Join the current game."""
        await handle_join(ctx)

    @commands.slash_command(
            name="draft", 
            description="Pick from your current draft pack",
            )
    async def draft(self, ctx: discord.ApplicationContext):
        await handle_draft(ctx, game=get_game(ctx.channel_id))

    @commands.slash_command(
            name="stop",
            description="STOP! STOP!!!!!!",
            )
    async def stop(self, ctx: discord.ApplicationContext):
        await handle_stop(ctx, get_game, remove_game)

    @commands.slash_command(
        name="play",
        description="Select cards to play as a response to the current prompt",
    )
    async def play(self, ctx: discord.ApplicationContext):
        await handle_play(ctx, get_game(ctx.channel_id), bot=self.bot)

    @commands.slash_command(
        name="judge",
        description="Select the best response as the judge",
    )
    async def judge(self, ctx: discord.ApplicationContext):
        async def on_judge_pick(game, player_id):
            await self.on_judge_pick(ctx.channel_id, player_id)
        await handle_judge(ctx, game=get_game(ctx.channel_id), on_judge_pick=on_judge_pick)

    @commands.slash_command(
        name="skip",
        description="Discards the current prompt and moves to the next one.",
    )
    async def skip(self, ctx: discord.ApplicationContext):
        await handle_skip(ctx, bot=self.bot, game=get_game(ctx.channel_id))

    async def on_judge_pick(self, channel_id: int, player_id: str):
        game = get_game(channel_id)
        await game.judge(player_id)

    async def on_button_view_judge(self, interaction: discord.Interaction, game: Game):
        """Create a view for the judge button."""
        if str(interaction.user.id) != str(game.state.current_judge.id):
            await interaction.response.send_message("Only the judge can judge this round!", ephemeral=True)
            return
        # Build the actual judge view
        view = JudgeView(game, judge_id=game.state.current_judge.id, on_judge_pick=self.on_judge_pick)
        await interaction.response.send_message(
            "Select the best response:",
            view=view,
            ephemeral=True
        )

def setup(bot):
    bot.add_cog(GameCog(bot))
