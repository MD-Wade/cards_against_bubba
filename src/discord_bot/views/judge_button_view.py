# judge_button_view.py

import discord
from discord.ui import View
from discord_bot.views.judge_view import JudgeView

class JudgeButtonView(View):
    def __init__(self, game, on_judge_button):
        super().__init__(timeout=None)
        self.game = game
        self.on_judge_button = on_judge_button

    @discord.ui.button(label="Judge!", style=discord.ButtonStyle.primary)
    async def judge_button(self, button, interaction):
        await self.on_judge_button(interaction, self.game)