# game_config.py
from dataclasses import dataclass, field
from typing import List, Dict

hand_size_min = 3
hand_size_max = 14
max_players_min = 3
max_players_max = 12
blank_count_min = 1
blank_count_max = 3
score_limit_min = 1
score_limit_max = 20

@dataclass(frozen=True)
class GameConfig:
    expansions: List[str]               = field(default_factory=list)
    regions:    Dict[str,bool]          = field(default_factory=lambda: {
        "us": True, "uk": True, "ca": True, "au": True, "intl": True
    })
    draft_mode: bool                    = False
    hand_size: int                      = 6
    score_limit: int                    = 6
    min_blanks: int                     = 1
    max_blanks: int                     = 3
    max_players: int                    = 10