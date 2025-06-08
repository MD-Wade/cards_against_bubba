import random
from typing import List
from .game_state    import GameState
from .player        import Player
from .card          import Card
from .game_phases   import Phase

class GameEngine:
    def start_game(self, state: GameState) -> Phase:
        """Standard deal & first prompt."""
        random.shuffle(state.black_deck)
        random.shuffle(state.white_deck)

        total_needed = len(state.players) * state.hand_size
        if len(state.white_deck) < total_needed:
            raise ValueError(
                f"Not enough white cards for classic deal: need {total_needed}, got {len(state.white_deck)}"
            )

        state.submissions.clear()
        for p in state.players:
            p.hand = [state.white_deck.pop() for _ in range(state.hand_size)]
            p.score = 0

        self.draw_prompt(state)
        return Phase.SUBMISSIONS


    def draw_prompt(self, state: GameState) -> None:
        state.submissions.clear()
        state.current_prompt = state.black_deck.pop()

    def submit_cards(self, state: GameState, player_id: str, cards: List[Card]) -> bool:
        state.phase_check(Phase.SUBMISSIONS)

        # find the player
        player = next(p for p in state.players if p.id == player_id)
        # judge guard
        if state.players[state.judge_index] is player:
            raise RuntimeError("Judge cannot submit cards.")

        # pick-count guard
        expected = state.current_prompt.pick
        if len(cards) != expected:
            raise ValueError(f"Expected {expected} cards, got {len(cards)}.")

        # remove from hand
        for c in cards:
            player.hand.remove(c)

        # record submission
        state.submissions[player_id] = cards

        all_in = self._all_non_judges_submitted(state)
        if all_in:
            print(f"[DEBUG] Player {player_id} submitted {len(cards)} cards.")
        else:
            print(f"[DEBUG] Player {player_id} has submitted {len(cards)} cards, waiting for others...")
        return all_in
            

    def judge_pick(self, state: GameState, winner_id: str) -> Phase:
        state.last_round_selected_id = winner_id
        state.last_round_selected_cards = state.submissions.get(winner_id, [])
        state.phase_check(Phase.JUDGING)
        winner = self.find_player(state, winner_id)
        winner.score += 1

        self._replenish_hands(state)
        state.judge_index = (state.judge_index + 1) % len(state.players)
        self.draw_prompt(state)
        return Phase.SUBMISSIONS
    
    def draft_deal(self, state: GameState, pack_size: int) -> Phase:
        """Deal each player a pack of `pack_size` from white_deck, init kept‐piles, and enter draft."""
        random.shuffle(state.white_deck)
        total_needed = len(state.players) * pack_size
        if len(state.white_deck) < total_needed:
            raise ValueError(
                f"Not enough white cards for draft: need {total_needed}, got {len(state.white_deck)}"
            )

        # zero out any old draft data
        state.draft_queues     = {}
        state.draft_kept       = {}
        state.draft_round_picks = 0   # counter for picks this round

        for p in state.players:
            state.draft_queues[p.id] = [state.white_deck.pop() for _ in range(pack_size)]
            state.draft_kept[p.id]   = []

        return Phase.DRAFT_PICKING

    def draft_pick(self, state: GameState, player_id: str, pick_index: int):
        """Player picks one card from their queue.  Once *all* players have picked this round,
           rotate the *remainders* to the next seat in one batch."""
        state.phase_check(Phase.DRAFT_PICKING)

        # 1) Remove chosen card & stash in kept‐pile
        queue = state.draft_queues[player_id]
        picked = queue.pop(pick_index)
        state.draft_kept[player_id].append(picked)

        # 2) Count this pick
        state.draft_round_picks += 1

        # 3) If every player has now picked once, **rotate** the leftover queues:
        if state.draft_round_picks >= len(state.players):
            old_qs = state.draft_queues
            new_qs = {}
            n      = len(state.players)
            for i, p in enumerate(state.players):
                # p gets the leftovers from the previous player
                prev = state.players[(i - 1) % n]
                new_qs[p.id] = old_qs[prev.id]
            state.draft_queues = new_qs
            state.draft_round_picks = 0

        # 4) Have we now kept `hand_size` each?  If so, finish draft:
        if all(len(state.draft_kept[p.id]) >= state.hand_size for p in state.players):
            # move each kept‐pile into that player’s hand
            for p in state.players:
                p.hand.extend(state.draft_kept[p.id])
            self.draw_prompt(state)
            return Phase.SUBMISSIONS
        return Phase.DRAFT_PICKING

    # ─── Helpers ────────────────────────────────────────────────

    def find_player(self, state: GameState, player_id: str) -> Player:
        return next(p for p in state.players if p.id == player_id)

    def _all_non_judges_submitted(self, state: GameState) -> bool:
        judge = state.players[state.judge_index]
        for p in state.players:
            name = p.name if p.name else p.id
            if p is judge:
                print(f"[DEBUG] Player {name} is the judge.")
                continue
            if p.id not in state.submissions:
                print(f"[DEBUG] Player {name} has not submitted.")
                return False
        print("[DEBUG] All non-judges have submitted.")
        return True

    def _is_judge(self, state: GameState, player: Player) -> bool:
        return state.players[state.judge_index] is player

    def _replenish_hands(self, state: GameState) -> None:
        for p in state.players:
            while len(p.hand) < state.hand_size:
                p.hand.append(state.white_deck.pop())