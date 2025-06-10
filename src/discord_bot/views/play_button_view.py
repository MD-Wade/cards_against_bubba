import discord
from discord.ui import View

class PlayButtonView(View):
    def __init__(self, game, on_play_button):
        super().__init__(timeout=None)
        self.game = game
        self.on_play_button = on_play_button

    @discord.ui.button(label="Select responses!", style=discord.ButtonStyle.primary)
    async def play_button(self, button, interaction):
        await self.on_play_button(interaction, self.game)