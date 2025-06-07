from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict
from card import Card
from player import Player
from game_phases import Phase

@dataclass
class GameState:
    players: List[Player]
    hand_size: int = 7
    draft_queues: Dict[str, List[Card]] = field(default_factory=dict)
    black_deck: List[Card] = field(default_factory=list)
    white_deck: List[Card] = field(default_factory=list)
    current_prompt: Optional[Card] = None
    judge_index: int = 0
    phase: Phase = Phase.WAITING

    def phase_check(self, expected_phase: Phase):
        if self.phase != expected_phase:
            raise ValueError(f"Invalid phase: expected {expected_phase}, got {self.phase}")

    def reset(self):
        self.current_prompt = None
        self.judge_index = 0
        self.phase = Phase.WAITING
        for player in self.players:
            player.hand.clear()
            player.score = 0
            player.submission = None
        self.black_deck.clear()
        self.white_deck.clear()
