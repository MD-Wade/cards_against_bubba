import asyncio
import random
from discord_bot.views.judge_button_view import JudgeButtonView
from cards_engine.game_phases import Phase
from discord_bot.views.play_button_view import PlayButtonView

async def reveal_submissions(channel, game, on_judge_button, delay=3.0):
    """Reveal all submissions anonymously to the main channel, one at a time."""
    submissions = list(game.state.submissions.items())
    prompt = game.state.current_prompt

    # Shuffle for fairness
    random.shuffle(submissions)

    await channel.send("✅ All responses are in! Revealing submissions anonymously...")
    await asyncio.sleep(delay)

    for idx, (player_id, cards) in enumerate(submissions):
        responses = [c.text for c in cards]
        formatted = prompt.format_prompt(responses)
        await channel.send(f"**#{idx+1}:** {formatted}")
        await asyncio.sleep(delay)

    judge = game.state.current_judge
    view_judge_button = JudgeButtonView(game, on_judge_button)
    await channel.send(
        f"All submissions revealed! <@{judge.id}>, please select the best response using `/judge` command!\n",
        view=view_judge_button
    )

async def announce_round_start(channel, game):
    judge_current = getattr(game.state, "current_judge", None)
    judge_current_name = judge_current.name if judge_current else "Unknown"
    prompt_card = getattr(game.state, "current_prompt", None)
    prompt_text = prompt_card.text if prompt_card else "No prompt selected."

    if game.state.phase == Phase.DRAFT_PICKING:
        await channel.send(
            "🏀 **Draft mode** is enabled. "
            "Please type **/draft** to begin selecting your cards!"
        )
    else:
        view_play_button = PlayButtonView(game, bot=game.bot)
        await channel.send(
            f"\n\nThe judge is currently **{judge_current_name}**.\n"
            f"Your prompt is:\n**{prompt_text}**",
            view=view_play_button
        )

