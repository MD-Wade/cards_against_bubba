from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Tuple
from .card import Card
from .player import Player
from .game_phases import Phase

@dataclass
class GameState:
    players:                List[Player]
    score_limit:            int
    hand_size:              int = 7
    draft_queues:           Dict[str, List[Card]] = field(default_factory=dict)
    draft_kept:             Dict[str, List[Card]] = field(default_factory=dict)
    draft_pass_index:       int = 0
    draft_direction:        int = +1
    draft_round_picks:      int = 0
    black_deck:             List[Card] = field(default_factory=list)
    white_deck:             List[Card] = field(default_factory=list)
    current_prompt:         Optional[Card] = None
    judge_index:            int = 0
    phase:                  Phase = Phase.WAITING
    last_round_selected_id: Optional[str] = None
    last_round_selected_cards: List[Card] = field(default_factory=list)
    submissions:            Dict[str, List[Card]] = field(default_factory=dict)
    submissions_shuffled:   List[Tuple[str, List[Card]]] = field(default_factory=list)

    @property
    def current_judge(self) -> Player:
        return self.players[self.judge_index]

    def phase_check(self, expected_phase: Phase):
        if self.phase != expected_phase:
            raise ValueError(f"Invalid phase: expected {expected_phase}, got {self.phase}")
        
    def player_by_id(self, player_id: str) -> Optional[Player]:
        for player in self.players:
            if str(player.id) == str(player_id):
                return player
        return None

    def reset(self):
        self.current_prompt = None
        self.judge_index = 0
        self.phase = Phase.WAITING
        for player in self.players:
            player.hand.clear()
            player.score = 0
        self.black_deck.clear()
        self.white_deck.clear()
        self.submissions.clear()
        self.submissions_shuffled.clear()