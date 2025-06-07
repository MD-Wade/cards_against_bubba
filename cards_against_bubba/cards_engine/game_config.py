# game_config.py
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass(frozen=True)
class GameConfig:
    expansions: List[str]              = field(default_factory=list)
    regions:    Dict[str,bool]         = field(default_factory=lambda: {
        "us": True, "uk": True, "ca": True, "au": True, "intl": True
    })
