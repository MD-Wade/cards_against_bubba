from dataclasses import dataclass, field
from typing import List
from cards_engine.player import Player
from cards_engine.game_config import GameConfig

@dataclass
class Lobby:
    host:    Player
    players: List[Player] = field(default_factory=list)
    config:  GameConfig   = field(default_factory=GameConfig)
    join_message_id: int = 0