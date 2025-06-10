from cards_engine.card_repository import CardRepository
from cards_engine.game import Game

_repo = CardRepository()
_games = {}
_lobbies = {}

def get_repository():
    return _repo

def get_game(channel_id):
    return _games.get(channel_id)

def set_game(channel_id, game):
    _games[channel_id] = game

def remove_game(channel_id):
    _games.pop(channel_id, None)

def get_lobby(channel_id):
    return _lobbies.get(channel_id)

def set_lobby(channel_id, lobby):
    _lobbies[channel_id] = lobby

def remove_lobby(channel_id):
    _lobbies.pop(channel_id, None)
