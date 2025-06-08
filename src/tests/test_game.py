import pytest
from cards_engine.game            import Game
from cards_engine.game_config     import GameConfig
from cards_engine.card_repository import CardRepository
from cards_engine.player          import Player
from cards_engine.game_phases     import Phase

@pytest.fixture
def repo():
    return CardRepository()

@pytest.fixture
def players():
    return [Player(id=str(i), name=f"Bot{i}") for i in range(1, 5)]

@pytest.mark.asyncio
async def test_full_round(repo, players):
    """Standard full round (no draft), one judge, three submitters, judge picks."""
    cfg = GameConfig(
        expansions=repo.available_expansions(),
        regions={r: True for r in repo.available_regions()},
        draft_mode=False,
        hand_size=5
    )
    game = Game(players, cfg, repo)
    await game.start()
    assert game.state.phase == Phase.SUBMISSIONS
    assert game.state.current_prompt is not None

    judge_id = game.state.players[game.state.judge_index].id
    pick_n = game.state.current_prompt.pick
    for p in game.state.players:
        if p.id != judge_id:
            await game.submit(p.id, list(range(pick_n)))

    assert game.state.phase == Phase.JUDGING
    subs = list(game.state.submissions.items())
    winner_id, _ = subs[0]
    await game.judge(winner_id)

    winner = next(p for p in game.state.players if p.id == winner_id)
    assert winner.score == 1
    assert game.state.current_prompt is not None

@pytest.mark.asyncio
async def test_draft_flow(repo, players):
    """Full draft, players pick one card per round, hands fill up, queues empty."""
    pack_size = 4
    cfg = GameConfig(
        expansions=repo.available_expansions(),
        regions={r: True for r in repo.available_regions()},
        draft_mode=True,
        hand_size=pack_size
    )
    game = Game(players, cfg, repo)
    await game.start()
    assert game.state.phase == Phase.DRAFT_PICKING
    for p in game.state.players:
        q = game.state.draft_queues[p.id]
        assert len(q) == pack_size
        assert p.hand == []
    # Simulate pass-and-pick
    for _ in range(pack_size):
        for p in game.state.players:
            await game.draft_pick(p.id, 0)
    assert game.state.phase == Phase.SUBMISSIONS
    for p in game.state.players:
        assert len(p.hand) == pack_size
    for q in game.state.draft_queues.values():
        assert q == []

# -------------------------
# EDGE CASES & ERROR TESTS
# -------------------------

@pytest.mark.asyncio
async def test_judge_cannot_submit(repo, players):
    """Judge should not be allowed to submit cards."""
    cfg = GameConfig(
        expansions=repo.available_expansions(),
        regions={r: True for r in repo.available_regions()},
        draft_mode=False,
        hand_size=3
    )
    game = Game(players, cfg, repo)
    await game.start()
    judge = game.state.players[game.state.judge_index]
    with pytest.raises(RuntimeError):
        await game.submit(judge.id, [0])

@pytest.mark.asyncio
async def test_wrong_number_of_cards(repo, players):
    """Player tries to submit wrong number of cards for prompt."""
    cfg = GameConfig(
        expansions=repo.available_expansions(),
        regions={r: True for r in repo.available_regions()},
        draft_mode=False,
        hand_size=3
    )
    game = Game(players, cfg, repo)
    await game.start()
    judge_id = game.state.players[game.state.judge_index].id
    non_judge = next(p for p in game.state.players if p.id != judge_id)
    wrong_count = [0] * (game.state.current_prompt.pick + 1)
    with pytest.raises(ValueError):
        await game.submit(non_judge.id, wrong_count)

@pytest.mark.asyncio
async def test_submit_wrong_phase(repo, players):
    """Player tries to submit in wrong phase (not SUBMISSIONS)."""
    cfg = GameConfig(
        expansions=repo.available_expansions(),
        regions={r: True for r in repo.available_regions()},
        draft_mode=False,
        hand_size=3
    )
    game = Game(players, cfg, repo)
    await game.start()
    game.state.phase = Phase.JUDGING
    judge_id = game.state.players[game.state.judge_index].id
    non_judge = next(p for p in game.state.players if p.id != judge_id)
    with pytest.raises(ValueError):
        await game.submit(non_judge.id, [0])

@pytest.mark.asyncio
async def test_judge_pick_wrong_phase(repo, players):
    """Judge tries to pick winner in non-JUDGING phase."""
    cfg = GameConfig(
        expansions=repo.available_expansions(),
        regions={r: True for r in repo.available_regions()},
        draft_mode=False,
        hand_size=3
    )
    game = Game(players, cfg, repo)
    await game.start()
    # skip to submissions, but don't submit all cards
    with pytest.raises(ValueError):
        await game.judge(players[0].id)

@pytest.mark.asyncio
async def test_draft_pick_wrong_phase(repo, players):
    """Player tries to draft pick in the wrong phase."""
    cfg = GameConfig(
        expansions=repo.available_expansions(),
        regions={r: True for r in repo.available_regions()},
        draft_mode=False,
        hand_size=3
    )
    game = Game(players, cfg, repo)
    await game.start()
    # Not in draft phase
    with pytest.raises(RuntimeError):
        await game.draft_pick(players[0].id, 0)

@pytest.mark.asyncio
async def test_game_state_reset(repo, players):
    """GameState.reset() brings state to waiting and clears hands, scores, etc."""
    cfg = GameConfig(
        expansions=repo.available_expansions(),
        regions={r: True for r in repo.available_regions()},
        draft_mode=False,
        hand_size=3
    )
    game = Game(players, cfg, repo)
    await game.start()
    # Play one round
    judge_id = game.state.players[game.state.judge_index].id
    pick_n = game.state.current_prompt.pick
    for p in game.state.players:
        if p.id != judge_id:
            await game.submit(p.id, list(range(pick_n)))
    await game.judge([p for p in game.state.players if p.id != judge_id][0].id)
    # Now reset
    game.state.reset()
    assert game.state.phase == Phase.WAITING
    assert all(p.hand == [] for p in game.state.players)
    assert all(p.score == 0 for p in game.state.players)
    assert all(p.id not in game.state.submissions for p in game.state.players)
    assert game.state.current_prompt is None

# -------------------------------
# CARD REPOSITORY EDGE TESTS
# -------------------------------

def test_repo_filtering(repo):
    """Test expansion and region filtering returns expected cards."""
    expansions = repo.available_expansions()
    regions = repo.available_regions()
    cards = repo.filter(expansions=[expansions[0]])
    assert all(card.expansion == expansions[0] for card in cards)
    if regions:
        cards_region = repo.filter(regions={regions[0]: True})
        assert all(card.regions[regions[0]] for card in cards_region)

def test_format_prompt_blanks(repo):
    """Check that format_prompt replaces blanks and appends responses."""
    card = next((c for c in repo.load() if c.card_type == "prompt" and c.has_blanks), None)
    if not card:
        pytest.skip("No prompt with blanks in test set")
    result = card.format_prompt(["foo", "bar"])
    assert "**foo**" in result

def test_format_prompt_no_blanks(repo):
    """Check that format_prompt appends response if no blanks."""
    card = next((c for c in repo.load() if c.card_type == "prompt" and not c.has_blanks), None)
    if not card:
        pytest.skip("No prompt without blanks in test set")
    result = card.format_prompt(["hello"])
    assert "**hello**" in result

# ---------------------
# OPTIONAL: FUZZ TESTS
# ---------------------

import random

@pytest.mark.asyncio
@pytest.mark.parametrize("draft_mode", [False, True])
async def test_randomized_games(repo, draft_mode):
    """Simulate multiple random short games to shake out state bugs."""
    for _ in range(5):  # Five short games
        num_players = random.randint(3, 6)
        players = [Player(id=str(i), name=f"Bot{i}") for i in range(num_players)]
        expansions = random.sample(repo.available_expansions(), k=1)
        regions = {r: True for r in repo.available_regions()}
        hand_size = random.randint(3, 7)

        white_cards = repo.filter(
            card_type="response",
            regions=regions,
            expansions=expansions
        )
        if draft_mode and len(white_cards) < len(players) * hand_size:
            continue  # Not enough for a fair draft, skip this combo
        if not draft_mode and len(white_cards) < len(players) * hand_size:
            continue  # Not enough for classic deal, skip


        cfg = GameConfig(
            expansions=expansions,
            regions=regions,
            draft_mode=draft_mode,
            hand_size=hand_size
        )
        game = Game(players, cfg, repo)
        await game.start()
        # Play a single round if not in draft phase
        if game.state.phase == Phase.DRAFT_PICKING:
            for _ in range(cfg.hand_size):
                for p in game.state.players:
                    await game.draft_pick(p.id, 0)
        if game.state.phase == Phase.SUBMISSIONS:
            judge_id = game.state.players[game.state.judge_index].id
            pick_n = game.state.current_prompt.pick
            for p in game.state.players:
                if p.id != judge_id:
                    await game.submit(p.id, list(range(pick_n)))
            assert game.state.phase == Phase.JUDGING

if __name__ == "__main__":
    pytest.main(["-v", __file__])