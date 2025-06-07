from typing import Callable, List
from game_state import GameState
from game_phases import Phase
import game_engine

PhaseListener = Callable[[str, str], None]  # (old_phase, new_phase)

class Game:
    def __init__(self, players, card_repository, hand_size=10):
        self.state = GameState(
            players=players,
            hand_size=hand_size,
            black_deck=black_cards.copy(),
            white_deck=white_cards.copy(),
        )
        self._phase_listeners: List[PhaseListener] = []

    def add_phase_listener(self, fn: PhaseListener):
        """Register a callback(old_phase, new_phase)."""
        self._phase_listeners.append(fn)

    def _set_phase(self, new_phase: str):
        old = self.state.phase
        if old == new_phase:
            return
        self.state.phase = Phase(new_phase)
        for fn in self._phase_listeners:
            fn(old, new_phase)

    def start(self):
        game_engine.start_game(self.state)
        self._set_phase(self.state.phase)

    def submit(self, player_id, card_indices):
        player = game_engine.find_player(self.state, player_id)
        cards = [player.hand[i] for i in card_indices]
        game_engine.submit_cards(self.state, player_id, cards)
        self._set_phase(self.state.phase)

    def judge(self, winner_id):
        game_engine.judge_pick(self.state, winner_id)
        self._set_phase(self.state.phase)
