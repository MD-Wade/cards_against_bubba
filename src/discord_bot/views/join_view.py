from discord import ui, ButtonStyle, Interaction
from cards_engine.player import Player

class JoinView(ui.View):
    def __init__(self, lobby):
        super().__init__(timeout=None)
        self.lobby = lobby
        self.join_button.label = f"Join Game ({len(self.lobby.players)})"

    @ui.button(label="Join Game", style=ButtonStyle.primary, custom_id="join_game")
    async def join_button(self, button, inter: Interaction):
        user = inter.user
        p = Player(id=str(user.id), name=user.nick or user.name)
        if any(pl.id == p.id for pl in self.lobby.players):
            return await inter.response.send_message("You’ve already joined!", ephemeral=True)

        self.lobby.players.append(p)
        button.label = f"Join Game ({len(self.lobby.players)})"
        await inter.response.edit_message(view=self)
