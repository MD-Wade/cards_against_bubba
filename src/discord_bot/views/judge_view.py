import discord
from discord.ui import View, Select

class JudgeView(View):
    def __init__(self, game, judge_id, on_judge_pick):
        super().__init__(timeout=60)
        self.game = game
        self.judge_id = judge_id
        self.on_judge_pick = on_judge_pick

        # Convert submissions dict to a list for index mapping
        self.sub_list = list(self.game.state.submissions.items())  # [(player_id, [Card, Card, ...]), ...]
        
        # Build options with card texts, not objects or ids
        options = [
            discord.SelectOption(
                label=f"#{i+1}: {', '.join(card.text for card in cards)[:80]}",
                value=str(i)
            )
            for i, (player_id, cards) in enumerate(self.sub_list)
        ]

        self.select = Select(
            placeholder="Pick the best response",
            options=options,
            min_values=1,
            max_values=1
        )
        self.select.callback = self.on_pick
        self.add_item(self.select)

    async def on_pick(self, interaction: discord.Interaction):
        print("JudgeView.on_pick")
        if str(interaction.user.id) != str(self.judge_id):
            await interaction.response.send_message("Only the judge can select!", ephemeral=True)
            return

        picked_idx = int(interaction.data["values"][0])
        player_id, winner_cards = self.sub_list[picked_idx]
        await interaction.response.send_message(
            f"🏆 {interaction.user.mention} has selected <@{player_id}> as the winner with: "
            f"{', '.join(card.text for card in winner_cards)}",
            ephemeral=True
        )
        await self.on_judge_pick(player_id)
        self.stop()