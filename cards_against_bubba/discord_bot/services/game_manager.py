# discord_bot/services/game_manager.py
from typing import Dict
from cards_against_bubba.cards_engine.game import Game

# channel_id → Game
_games: Dict[int, Game] = {}

def create_game(channel_id: int, player_ids: list[str], hand_size: int, draft_mode: bool) -> Game:
    game = Game(player_ids, BLACK_CARDS, WHITE_CARDS, hand_size=hand_size, draft_mode=draft_mode)
    _games[channel_id] = game
    return game

def get_game(channel_id: int) -> Game | None:
    return _games.get(channel_id)

def remove_game(channel_id: int) -> None:
    _games.pop(channel_id, None)
