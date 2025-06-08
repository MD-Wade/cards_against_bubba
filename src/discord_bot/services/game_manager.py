import random
import asyncio
from typing                         import Dict
from cards_engine.game              import Game
from cards_engine.card_repository   import CardRepository
from .lobby                         import Lobby
from cards_engine.game_phases       import Phase
from cards_engine.player            import Player
from .game_flow                     import reveal_submissions, announce_round_start
from discord_bot.views.play_button_view import PlayButtonView
from discord_bot.views.judge_button_view import JudgeButtonView

_repo = CardRepository()
_lobbies: Dict[int, Lobby] = {}   # channel_id → Lobby
_games:   Dict[int, Game]  = {}   # channel_id → running Game
_bot = None

def set_bot(bot) -> None:
    """Sets the global bot instance."""
    global _bot
    _bot = bot

def get_repository() -> CardRepository:
    """Returns the global card repository."""
    return _repo

def create_lobby(channel_id: int, host_id: int, host_name: str) -> Lobby:
    host_player = Player(id=str(host_id), name=host_name)
    lobby = Lobby(host=host_player)
    _lobbies[channel_id] = lobby
    return lobby

def get_lobby(channel_id: int) -> Lobby | None:
    return _lobbies.get(channel_id)

def remove_lobby(channel_id: int) -> None:
    _lobbies.pop(channel_id, None)

async def start_game(channel_id: int) -> Game:
    lobby = _lobbies.pop(channel_id)
    random.shuffle(lobby.players)
    real = Game(
        players    = lobby.players,
        config     = lobby.config,
        repository = _repo,
        channel_id = channel_id
    )
    print(f"start_game: new Game id={id(real)}")
    real.add_phase_listener(on_phase_change)
    await real.start()
    _games[channel_id] = real
    return real


async def on_phase_change(game: Game, old_phase: Phase, new_phase: Phase):
    print(f"[GameManager] Phase changed  ({old_phase} -> {new_phase}) for game {game.channel_id}")
    game_channel = _bot.get_channel(game.channel_id)
    if new_phase == Phase.JUDGING:
        await reveal_submissions(game_channel, game)
        await game_channel.send(
            "🔍 All responses are in! The judge is now reviewing the submissions. "
            "Please wait for the judge to select the best response."
        )
        return

    elif new_phase == Phase.SUBMISSIONS:
        winner_id = getattr(game.state, "last_round_selected_id", None)
        winner_cards = getattr(game.state, "last_round_selected_cards", [])
        if winner_id:
            winner = game.state.player_by_id(winner_id)
            winner_name = winner.name if winner else f"<@{winner_id}>"
            winner_score = winner.score if winner else "?"
            cards_str = "\n".join(f"> **{c.text}**" for c in winner_cards)
            await game_channel.send(
                f"🏆 **{winner_name}** was selected as the winner!\n"
                f"Winning card(s):\n{cards_str}\n"
                f"**{winner_name}** now has **{winner_score}** point{'s' if winner_score != 1 else ''}!"
            )
        
        await announce_round_start(game_channel, game)
        

    await asyncio.sleep(2)

def get_game(channel_id: int) -> Game | None:
    game = _games.get(channel_id)
    print(f"get_game: Game id={id(game) if game else None}")
    return game

def remove_game(channel_id: int) -> None:
    _games.pop(channel_id, None)
