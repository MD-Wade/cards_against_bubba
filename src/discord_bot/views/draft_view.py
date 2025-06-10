# discord_bot/views/draft_view.py

from discord import ui, SelectOption, Interaction
from cards_engine.game_phases import Phase
from discord_bot.services.state_manager import get_game

class DraftView(ui.View):
    """A persistent ephemeral view that walks a single player through
    all of their draft‐packs, editing in place instead of requiring
    them to retype /draft each round.
    """

    def __init__(self, channel_id: int, player_id: str):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.player_id  = player_id
        # grab the running game
        game = get_game(channel_id)
        if game is None:
            raise RuntimeError("No game in this channel")
        self.game = game
        # draw the first pack
        self._draw_round()

    def _draw_round(self):
        """(Re)build the Select so it reflects the current queue for this player."""
        # clear out any previous components
        self.clear_items()

        queue = self.game.state.draft_queues[self.player_id]
        # build one Select with one option per card
        options = [
            SelectOption(label=card.text, value=str(idx))
            for idx, card in enumerate(queue)
        ]
        self.add_item(
            ui.Select(
                placeholder="Pick one card…",
                options=options,
                min_values=1,
                max_values=1,
                row=0,
                callback=self.on_pick
            )
        )

    async def on_pick(self, interaction: Interaction):
        """Handle the user’s pick, advance the engine, then either finish
        or redraw for the next pass."""
        pick_index = int(interaction.data["values"][0])
        # step the draft engine
        self.game.draft_pick(self.player_id, pick_index)

        # if draft is now over, tear down
        if self.game.state.phase != Phase.DRAFT_PICKING:
            await interaction.response.edit_message(
                content="✅ Draft complete! Check your hand to see what you kept.",
                view=None
            )
            return

        # otherwise re‐draw this same ephemeral message
        self._draw_round()
        await interaction.response.edit_message(
            content="Next pack — pick again:",
            view=self
        )
