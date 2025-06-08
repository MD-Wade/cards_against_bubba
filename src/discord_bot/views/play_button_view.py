# play_button_view.py

import discord
from discord.ui import View
from discord_bot.views.play_view import PlayView

class PlayButtonView(View):
    def __init__(self, game, bot):
        super().__init__(timeout=None)
        self.game = game
        self.bot = bot

    @discord.ui.button(label="Select responses!", style=discord.ButtonStyle.primary)
    async def play_button(self, button, interaction):
        player = self.game.state.player_by_id(str(interaction.user.id))
        if not player:
            await interaction.response.send_message("You are not in this game!", ephemeral=True)
            return
        if self.game.state.current_judge.id == player.id:
            await interaction.response.send_message("You are the judge this round!", ephemeral=True)
            return
        view = PlayView(self.game.channel_id, str(interaction.user.id), self.bot)
        await interaction.response.send_message(
            "Select your responses:",
            view=view,
            ephemeral=True
        )
