from discord import ui, SelectOption, ButtonStyle
from cards_against_bubba.cards_engine.game_phases import Phase
from services.game_manager import remove_game

# your expansions + regions lists
ALL_EXPANSIONS = ["Base", "NSFW", "Holiday", "Party"]
ALL_REGIONS    = ["us", "uk", "ca", "au", "intl"]

class SettingsView(ui.View):
    def __init__(self, game, ctx):
        super().__init__(timeout=None)
        self.game = game
        self.ctx  = ctx

    @ui.select(
        placeholder="Select expansions…",
        min_values=1, max_values=len(ALL_EXPANSIONS),
        options=[SelectOption(label=e) for e in ALL_EXPANSIONS],
        row=0
    )
    async def pack_select(self, select: ui.Select, inter):
        self.game.state.expansions = select.values
        await self._maybe_enable_launch()
        await inter.response.edit_message(view=self)

    @ui.select(
        placeholder="Select regions…",
        min_values=1, max_values=len(ALL_REGIONS),
        options=[SelectOption(label=r.upper(), value=r) for r in ALL_REGIONS],
        row=1
    )
    async def region_select(self, select: ui.Select, inter):
        self.game.state.regions = { r: (r in select.values) for r in ALL_REGIONS }
        await self._maybe_enable_launch()
        await inter.response.edit_message(view=self)

    @ui.button(label="▶️ Launch Game", style=ButtonStyle.success, row=2)
    async def launch_button(self, button: ui.Button, inter):
        await inter.response.edit_message(content="✅ Game launched!", view=None)
        self.game.start()
        channel = inter.channel
        prompt = self.game.state.current_prompt.text
        await channel.send(f"🏁 **Game started!**\n**Black card:** {prompt}")
        for pid in self.game.state.players:
            user = await self.ctx.bot.fetch_user(pid)
            hand = "\n".join(f"{i}: {c.text}"
                              for i, c in enumerate(self.game.state.player_by_id(pid).hand))
            await user.send(f"Your hand:\n{hand}")

    @ui.button(label="❌ Cancel", style=ButtonStyle.danger, row=2)
    async def cancel_button(self, button: ui.Button, inter):
        remove_game(self.ctx.channel_id)
        await inter.response.edit_message(content="🚫 Game cancelled.", view=None)

    async def _maybe_enable_launch(self):
        packs_ok   = bool(self.game.state.expansions)
        regions_ok = any(self.game.state.regions.values())
        self.launch_button.disabled = not (packs_ok and regions_ok)
