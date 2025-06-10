import discord
import random
from discord.ui import View, Select, Button
from cards_engine.game_phases import Phase
from discord_bot.services.state_manager import get_game

class PlayView(View):
    def __init__(self, channel_id, player_id, bot, picks=None, pick_index=0):
        super().__init__(timeout=60)
        self.channel_id = channel_id
        self.player_id = str(player_id)
        self.bot = bot
        self.picks = picks or []
        self.pick_index = pick_index

        game = get_game(channel_id)
        if not game:
            raise RuntimeError("No game found!")

        self.game = game
        self.state = game.state
        self.player = self.state.player_by_id(player_id)
        self.judge = self.state.current_judge

        if not self.player:
            raise RuntimeError("Player not found!")

        if self.judge.id == self.player_id:
            self.add_item(Button(label="You are the judge!", style=discord.ButtonStyle.secondary, disabled=True))
            self.is_submit_enabled = False
        else:
            self.is_submit_enabled = True
            self.pick_count = self.state.current_prompt.pick if self.state.current_prompt else 1
            remaining_hand = [(i, c) for i, c in enumerate(self.player.hand) if i not in self.picks]
            options = [discord.SelectOption(label=c.text[:80], value=str(i)) for i, c in remaining_hand]
            suffix = ["first", "second", "third", "fourth", "fifth"]
            which = suffix[self.pick_index] if self.pick_index < len(suffix) else f"#{self.pick_index + 1}"
            placeholder = (
                "Select a response for the blank."
                if self.pick_count == 1 else
                f"Select a response for the {which} blank."
            )
            sel = Select(placeholder=placeholder, options=options, min_values=1, max_values=1)
            sel.callback = self.on_pick
            self.add_item(sel)

    async def on_pick(self, interaction: discord.Interaction):
        if not self.is_submit_enabled:
            if not interaction.response.is_done():
                await interaction.response.send_message("You are the judge this round.", ephemeral=True)
            else:
                await interaction.followup.send("You are the judge this round.", ephemeral=True)
            return

        picked_idx = int(interaction.data["values"][0])
        picks = self.picks + [picked_idx]
        pick_index = self.pick_index + 1
        pick_count = self.state.current_prompt.pick if self.state.current_prompt else 1

        if pick_index < pick_count:
            suffix = ["first", "second", "third", "fourth", "fifth"]
            which = suffix[pick_index] if pick_index < len(suffix) else f"#{pick_index + 1}"
            prompt = (
                "Select a response to play for this prompt."
                if pick_count == 1 else
                f"Select a response to play for the {which} blank of this prompt."
            )
            # EDIT THE SAME MESSAGE INSTEAD OF SENDING A NEW ONE
            if not interaction.response.is_done():
                await interaction.response.edit_message(
                    content=prompt,
                    view=PlayView(self.channel_id, self.player_id, self.bot, picks=picks, pick_index=pick_index)
                )
            else:
                await interaction.followup.send(
                    content=prompt,
                    view=PlayView(self.channel_id, self.player_id, self.bot, picks=picks, pick_index=pick_index),
                    ephemeral=True
                )
            return

        edit_message = "Your responses have been submitted!"
        if random.randint(0, 100) < 2:
            edit_message = "Your responses have been submitted! Bubba is pleased..."
        await interaction.response.edit_message(
            content=edit_message,
            view=None
        )
        await self.game.submit(self.player_id, picks)
        