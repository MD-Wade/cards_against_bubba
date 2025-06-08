# src/cards_engine/game.py

import inspect
from typing    import Callable, List, Union, Awaitable
from .game_state    import GameState
from .game_phases   import Phase
from .card_repository import CardRepository
from .game_config   import GameConfig
from .player        import Player
from .game_engine   import GameEngine

PhaseListener = Union[
    Callable[['Game', Phase, Phase], None],
    Callable[['Game', Phase, Phase], Awaitable[None]]
]

class Game:
    def __init__(self,
                 players:    List[Player],
                 config:     GameConfig,
                 repository: CardRepository,
                 channel_id: int = None) -> None:
        self.players = players
        self.config = config
        self.repo   = repository
        self.channel_id = channel_id
        self.engine = GameEngine()
        self._phase_listeners: List[PhaseListener] = []
        self.state = None

    def add_phase_listener(self, fn: PhaseListener) -> None:
        self._phase_listeners.append(fn)

    async def _set_phase(self, new_phase: Phase) -> None:
        print(f"Game._set_phase: {new_phase}, id(self)={id(self)}")
        old = self.state.phase
        if old is new_phase:
            return
        self.state.phase = new_phase
        for fn in self._phase_listeners:
            print(f"Calling phase listener {fn} for Game id={id(self)}")
            result = fn(self, old, new_phase)
            if inspect.isawaitable(result):
                await result

    async def start(self) -> None:
        black = self.repo.filter(
            card_type   = "prompt",
            regions     = self.config.regions,
            expansions  = self.config.expansions)
        black = [c for c in black if self.config.min_blanks <= c.pick <= self.config.max_blanks]

        white = self.repo.filter(
            card_type   = "response",
            regions     = self.config.regions,
            expansions  = self.config.expansions)

        self.state = GameState(
            players= self.players,
            hand_size= self.config.hand_size,
            black_deck= black,
            white_deck= white
        )

        if self.config.draft_mode:
            next_phase = self.engine.draft_deal(self.state, self.state.hand_size)
        else:
            next_phase = self.engine.start_game(self.state)
        await self._set_phase(next_phase)

    async def submit(self, player_id: str, card_indices: List[int]) -> None:
        if not self.state:
            raise RuntimeError("Game not started yet.")
        
        player = self.state.player_by_id(player_id)
        cards  = [player.hand[i] for i in card_indices]
        all_in = self.engine.submit_cards(self.state, player_id, cards)
        if all_in:
            await self._set_phase(Phase.JUDGING)

    async def judge(self, winner_id: str) -> None:
        print("Game.judge")
        if not self.state:
            raise RuntimeError("Game not started yet.")

        next_phase = self.engine.judge_pick(self.state, winner_id)
        await self._set_phase(next_phase)

    async def draft_pick(self, player_id: str, pick_index: int) -> None:
        if not self.state:
            raise RuntimeError("Game not started")
        if self.state.phase is not Phase.DRAFT_PICKING:
            raise RuntimeError(f"Not in draft phase: {self.state.phase}")
        next_phase = self.engine.draft_pick(self.state, player_id, pick_index)
        await self._set_phase(next_phase)