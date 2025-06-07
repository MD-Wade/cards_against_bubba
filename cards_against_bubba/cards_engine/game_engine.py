import random
from typing import List
from game_state import GameState
from card import Card
from player import Player
from game_phases import Phase

def start_game(state: GameState):
    random.shuffle(state.black_deck)
    random.shuffle(state.white_deck)
    for p in state.players:
        p.hand = [state.white_deck.pop() for _ in range(state.hand_size)]
        p.score = 0
        p.submission = None

    state.phase = Phase.SUBMISSIONS
    draw_prompt(state)

def draw_prompt(state: GameState):
    state.current_prompt = state.black_deck.pop()
    for p in state.players:
        p.submission = None

def submit_cards(state: GameState, player_id: str, cards: List[Card]):
    # 1) Phase guard
    state.phase_check(Phase.SUBMISSIONS)

    player = find_player(state, player_id)

    # 2) Don’t let the judge submit
    if _is_judge(state, player):
        raise RuntimeError("Judge cannot submit cards.")

    # 3) Pick‐count guard
    expected = state.current_prompt.pick
    if len(cards) != expected:
        raise ValueError(f"Expected {expected} cards, got {len(cards)}.")

    # 4) Remove submitted cards from hand
    for c in cards:
        player.hand.remove(c)
    player.submission = cards

    # 5) Advance phase if everyone else has submitted
    if _all_non_judges_submitted(state):
        state.phase = Phase.JUDGING

def judge_pick(state: GameState, winner_id: str):
    state.phase_check(Phase.JUDGING)
    winner = find_player(state, winner_id)
    winner.score += 1

    _replenish_hands(state)
    state.judge_index = (state.judge_index + 1) % len(state.players)
    state.phase = Phase.SUBMISSIONS
    draw_prompt(state)

def find_player(state: GameState, player_id: str) -> Player:
    return next(p for p in state.players if p.id == player_id)

def _all_non_judges_submitted(state: GameState) -> bool:
    judge = state.players[state.judge_index]
    return all(
        p.submission is not None
        for p in state.players
        if p is not judge
    )

def _is_judge(state: GameState, player: Player) -> bool:
    return state.players[state.judge_index] is player

def _replenish_hands(state: GameState):
    for p in state.players:
        while len(p.hand) < state.hand_size:
            p.hand.append(state.white_deck.pop())