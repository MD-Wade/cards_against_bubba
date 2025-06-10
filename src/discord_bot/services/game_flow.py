import asyncio
import random
from discord import Interaction, ApplicationContext
from cards_engine.player import Player
from cards_engine.game_phases import Phase
from discord_bot.services.state_manager import get_lobby
from discord_bot.views.judge_button_view import JudgeButtonView
from discord_bot.views.play_button_view import PlayButtonView
from discord_bot.views.play_view import PlayView
from discord_bot.views.judge_view import JudgeView
from discord_bot.views.draft_view import DraftView

async def reveal_submissions(channel, game, on_judge_button, delay=3.0):
    """Reveal all submissions anonymously to the main channel, one at a time."""
    submissions = list(game.state.submissions.items())
    prompt = game.state.current_prompt

    random.shuffle(submissions)
    game.state.submissions_shuffled = submissions

    await channel.send("✅ All responses are in! Revealing submissions anonymously...")
    await asyncio.sleep(delay)

    for idx, (player_id, cards) in enumerate(submissions):
        responses = [c.text for c in cards]
        formatted = prompt.format_prompt(responses)
        await channel.send(f"**#{idx+1}:** {formatted}")
        await asyncio.sleep(delay)

    judge = game.state.current_judge
    async def on_judge_pick(game, player_id):
        await game.judge(player_id)
    view_judge_button = JudgeButtonView(
        game, 
        on_judge_button=lambda interaction, game: handle_judge(interaction, game, on_judge_pick=on_judge_pick)
    )
    await channel.send(
        f"All submissions revealed! <@{judge.id}>, please select the best response using by clicking the button below.",
        view=view_judge_button
    )

async def announce_round_start(channel, game, on_play_button):
    judge_current = getattr(game.state, "current_judge", None)
    judge_mention = f"<@{judge_current.id}>" if judge_current else "Unknown"
    prompt_card = getattr(game.state, "current_prompt", None)
    prompt_text = prompt_card.text if prompt_card else "No prompt selected."
    prompt_picks = prompt_card.pick if prompt_card else 1

    if game.state.phase == Phase.DRAFT_PICKING:
        await channel.send(
            "🏀 **Draft mode** is enabled. "
            "Please type **/draft** to begin selecting your cards!"
        )
    else:
        view_play_button = PlayButtonView(game, on_play_button=on_play_button)
        prompt_picks_plurality = "blanks" if prompt_picks > 1 else "blank"
        message_content = (
            f"_ _\nThe Judge is currently **{judge_mention}**.\n"
            f"Your prompt is: **{prompt_text}**\n"
            f"(There should be **{prompt_picks}** {prompt_picks_plurality}. If there is not, the Judge may `/skip`.)\n"
        )
        await channel.send(
            content=message_content,
            view=view_play_button
        )

async def handle_play(ctx_or_interaction, game, bot, *, as_button=False):
    channel_id, user_id = get_channel_and_user_id(ctx_or_interaction)

    if not game:
        return await respond(ctx_or_interaction, "There's no game, pal.", ephemeral=True)
    if not game.state:
        return await respond(ctx_or_interaction, "The game is not ready yet.", ephemeral=True)
    if game.state.phase != Phase.SUBMISSIONS:
        return await respond(ctx_or_interaction, "You can only submit cards during submissions, obviously.", ephemeral=True)

    player = game.state.player_by_id(user_id)
    if not player:
        return await respond(ctx_or_interaction, "You are NOT in this game!", ephemeral=True)

    if game.state.current_judge.id == player.id:
        return await respond(ctx_or_interaction, "You are the judge this round!", ephemeral=True)

    view = PlayView(channel_id, user_id, bot)
    msg = "Select a response to play for this prompt." if view.pick_count == 1 else "Select a response to play for the first blank of this prompt."
    await respond(ctx_or_interaction, msg, view=view, ephemeral=True)

async def handle_judge(ctx_or_interaction, game, *, on_judge_pick):
    channel_id, user_id = get_channel_and_user_id(ctx_or_interaction)

    if not game:
        return await respond(ctx_or_interaction, "There's no game, pal.", ephemeral=True)
    if not game.state:
        return await respond(ctx_or_interaction, "The game is not ready yet.", ephemeral=True)
    
    if game.state.phase != Phase.JUDGING:
        return await respond(ctx_or_interaction, "You can only judge during the judging phase, bro.", ephemeral=True)

    player = game.state.player_by_id(user_id)
    if not player or player.id != game.state.current_judge.id:
        return await respond(ctx_or_interaction, "You are NOT the judge this round!", ephemeral=True)

    view = JudgeView(game, judge_id=game.state.current_judge.id, on_judge_pick=on_judge_pick)
    await respond(ctx_or_interaction, "Select the best response from the submissions:", view=view, ephemeral=True)

async def handle_draft(ctx_or_interaction, game):
    channel_id, user_id = get_channel_and_user_id(ctx_or_interaction)

    if not game or game.state.phase != Phase.DRAFT_PICKING:
        return await respond(ctx_or_interaction, "No draft in progress.", ephemeral=True)

    view = DraftView(channel_id, user_id)
    await respond(ctx_or_interaction, "Your draft pack, pick one card:", view=view, ephemeral=True)

async def handle_stop(ctx_or_interaction, game_manager_get_game, game_manager_remove_game):
    """Handler for stopping a game. Expects ctx or interaction, plus injected get/remove game funcs."""
    channel_id, user_id = get_channel_and_user_id(ctx_or_interaction)

    game = game_manager_get_game(channel_id)
    if not game:
        return await respond(ctx_or_interaction, "❌ No game is currently running in this channel.", ephemeral=True)

    # Host is usually first in players or lobby.host, tweak as needed!
    host_id = game.host_id
    if str(user_id) != str(host_id):
        return await respond(ctx_or_interaction, "❌ WHO do you think YOU are? The host?", ephemeral=True)

    game_manager_remove_game(channel_id)
    await respond(ctx_or_interaction, "Ending the game now ...", ephemeral=True)
    try:
        await ctx_or_interaction.channel.send("🛑 **Game ended by the host!**")
    except Exception:
        pass

async def handle_skip(ctx_or_interaction, bot, game):
    """Handler for skipping the current prompt."""
    channel_id, user_id = get_channel_and_user_id(ctx_or_interaction)

    if not game:
        return await respond(ctx_or_interaction, "What game are you even trying to skip?", ephemeral=True)
    if not game.state or game.state.phase != Phase.SUBMISSIONS:
        return await respond(ctx_or_interaction, "You can only skip prompts during the submission phase.", ephemeral=True)

    player = game.state.player_by_id(user_id)
    if not player:
        return await respond(ctx_or_interaction, "You are NOT in this game!", ephemeral=True)
    if player.id != game.state.current_judge.id:
        return await respond(ctx_or_interaction, "You are NOT the judge this round!", ephemeral=True)

    game.engine.draw_prompt(game.state)
    await respond(ctx_or_interaction, "Prompt skipped!", ephemeral=True)
    await asyncio.sleep(0.5)
    await ctx_or_interaction.channel.send(
        f"⏭️ The Judge, **{player.name}**, has skipped the current prompt. A new one has been drawn!"
    )
    await asyncio.sleep(0.5)
    def on_play_button(interaction, game):
        return handle_play(interaction, game, bot=bot, as_button=True)
    await announce_round_start(
        ctx_or_interaction.channel, game,
        on_play_button=on_play_button
    )

async def handle_join(ctx_or_interaction):
    channel_id, user_id = get_channel_and_user_id(ctx_or_interaction)
    
    # Check if there's an active lobby
    lobby = get_lobby(channel_id)
    if not lobby:
        return await respond(ctx_or_interaction, "What game are you even joining?", ephemeral=True)
    
    # Check if the user is already in the lobby
    if any(player.id == str(user_id) for player in lobby.players):
        return await respond(ctx_or_interaction, "You are already in the game!", ephemeral=True)
    
    if len(lobby.players) >= lobby.config.max_players:
        return await respond(ctx_or_interaction, "The lobby is full! You can't join.", ephemeral=True)

    # Add the player
    player_name = (ctx_or_interaction.author.display_name 
                   if isinstance(ctx_or_interaction, ApplicationContext) 
                   else ctx_or_interaction.user.display_name)
    new_player = Player(id=str(user_id), name=player_name)
    lobby.players.append(new_player)
    
    player_count = len(lobby.players)
    players_plurality = "players" if player_count != 1 else "player"
    await respond(ctx_or_interaction, f"✅ {player_name} has joined the game! (Now {player_count} {players_plurality}).", ephemeral=False)



# Helper: handle both ctx.respond() and interaction.response.send_message()
async def respond(ctx_or_interaction, *args, **kwargs):
    try:
        # Slash command context
        await ctx_or_interaction.respond(*args, **kwargs)
    except AttributeError:
        # Component interaction
        if not ctx_or_interaction.response.is_done():
            await ctx_or_interaction.response.send_message(*args, **kwargs)
        else:
            await ctx_or_interaction.followup.send(*args, **kwargs)

def get_channel_and_user_id(ctx_or_interaction):
    if isinstance(ctx_or_interaction, ApplicationContext):
        return ctx_or_interaction.channel_id, str(ctx_or_interaction.author.id)
    elif isinstance(ctx_or_interaction, Interaction):
        return ctx_or_interaction.channel.id, str(ctx_or_interaction.user.id)
    else:
        raise ValueError("Unknown context type")