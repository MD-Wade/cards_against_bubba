import random
import asyncio
from typing                             import Dict, List, Tuple
from cards_engine.game                  import Game
from cards_engine.card_repository       import CardRepository
from cards_engine.game_phases           import Phase
from cards_engine.player                import Player
from discord_bot.services.lobby         import Lobby
from discord_bot.services.state_manager import set_game, set_lobby, get_lobby, remove_lobby, remove_game
from discord_bot.services.game_flow     import reveal_submissions, announce_round_start, handle_play, handle_judge, handle_draft

_repo = CardRepository()
_lobbies: Dict[int, Lobby] = {}   # channel_id → Lobby
_games:   Dict[int, Game]  = {}   # channel_id → running Game
_bot = None

def set_bot(bot) -> None:
    """Sets the global bot instance."""
    global _bot
    _bot = bot

def create_lobby(channel_id: int, host_id: int, host_name: str) -> Lobby:
    host_player = Player(id=str(host_id), name=host_name)
    lobby = Lobby(host=host_player)
    set_lobby(channel_id, lobby)
    return lobby

async def start_game(channel_id: int) -> Game:
    lobby = get_lobby(channel_id)
    random.shuffle(lobby.players)
    real = Game(
        players    = lobby.players,
        config     = lobby.config,
        repository = _repo,
        host_id    = lobby.host.id,
        channel_id = channel_id
    )
    remove_lobby(channel_id)
    real.add_phase_listener(on_phase_change)
    set_game(channel_id, real)
    await real.start()
    return real


async def on_phase_change(game: Game, old_phase: Phase, new_phase: Phase):
    print(f"[GameManager] Phase changed  ({old_phase} -> {new_phase}) for game {game.channel_id}")
    game_channel = _bot.get_channel(game.channel_id)
    if new_phase == Phase.JUDGING:
        async def on_judge_button(interaction, game):
            return await handle_judge(interaction, game, on_judge_pick=on_judge_button)

        await reveal_submissions(game_channel, game, on_judge_button=on_judge_button)
        return

    elif new_phase == Phase.SUBMISSIONS:
        await announce_round_winner(game, game_channel)
        def on_play_button(interaction, game):
            return handle_play(interaction, game, bot=_bot, as_button=True)
        await announce_round_start(game_channel, game, on_play_button=on_play_button)

    elif new_phase == Phase.FINISHED:
        await announce_round_winner(game, game_channel)
        await announce_game_winner(game, game_channel)

async def announce_round_winner(game: Game, channel):
    """Sends the “wins the round” message based on game.state."""
    winner_id    = game.state.last_round_selected_id
    winner_cards = game.state.last_round_selected_cards
    if not winner_id:
        return

    player     = game.state.player_by_id(winner_id)
    name       = player.name if player else f"<@{winner_id}>"
    score      = player.score if player else "?"
    cards_list = "\n".join(f"> **{c.text}**" for c in winner_cards)
    score_plurality = "point" if score == 1 else "points"
    cards_plurality = "card" if len(winner_cards) == 1 else "cards"

    await channel.send(
        f"🏆 **{name}** wins the round, and now has **{score}** {score_plurality}!\n"
        f"Winning {cards_plurality}:\n{cards_list}\n"
    )
    await asyncio.sleep(2)


async def announce_game_winner(game: Game, channel):
    """Sends the final-game 'wins the game' message with full leaderboard."""
    champ_id = game.state.last_round_selected_id
    champ = game.state.player_by_id(champ_id)
    champ_name = champ.name if champ else f"<@{champ_id}>"
    champ_score = champ.score if champ else 0
    points_label = "point" if champ_score == 1 else "points"

    # Header
    await channel.send(
        f"_ _\n🎉 **{champ_name}** has reached {champ_score} {points_label} and wins the game! 🏆"
    )

    # Build and send leaderboard lines
    board = _generate_leaderboard(game.state.players)
    lines = []
    for label, entries in board:
        for name, pts in entries:
            pts_label = "point" if pts == 1 else "points"
            lines.append(f"{label} {name} - {pts} {pts_label}")
    await channel.send("\n".join(lines))

    # Cleanup
    remove_game(game.channel_id)

def _generate_leaderboard(players: List[Player]) -> List[Tuple[str, List[Tuple[str, int]]]]:
    # sort descending by score
    sorted_ps = sorted(players, key=lambda p: p.score, reverse=True)

    # competition‐style ranking
    leaderboard: List[Tuple[int, Player]] = []
    prev_score = None
    prev_rank  = 0
    count      = 0
    for p in sorted_ps:
        count += 1
        if p.score != prev_score:
            rank = count
            prev_score, prev_rank = p.score, rank
        else:
            rank = prev_rank
        leaderboard.append((rank, p))

    # group players by rank
    ranks: Dict[int, List[Player]] = {}
    for rank, p in leaderboard:
        ranks.setdefault(rank, []).append(p)

    # build the final [(label, [(name,score),…]), …]
    result: List[Tuple[str, List[Tuple[str, int]]]] = []
    for rank in sorted(ranks):
        players_at_rank = ranks[rank]
        if rank == 1:
            label = "🥇"
        elif rank == 2:
            label = "🥈"
        elif rank == 3:
            label = "🥉"
        else:
            label = f"{_ordinal(rank)}: "

        entries: List[Tuple[str, int]] = [(p.name, p.score) for p in players_at_rank]
        result.append((label, entries))

    return result

def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"