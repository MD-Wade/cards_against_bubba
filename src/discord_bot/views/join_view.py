from discord import ui, ButtonStyle, Interaction
from cards_engine.player import Player

class JoinView(ui.View):
    def __init__(self, lobby, on_join_button=None):
        super().__init__(timeout=None)
        self.lobby = lobby
        self.on_join_button = on_join_button
        self.join_button.label = f"Join Game ({len(self.lobby.players)})"

    @ui.button(label="Join Game", style=ButtonStyle.primary, custom_id="join_game")
    async def join_button(self, button, inter: Interaction):
        button.label = f"Join Game ({len(self.lobby.players)})"
        await inter.response.edit_message(view=self)
        await self.on_join_button(inter)

