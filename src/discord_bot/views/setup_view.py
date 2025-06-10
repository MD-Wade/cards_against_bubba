# src/discord_bot/views/setup_view.py

from dataclasses import replace
from discord import Interaction, ButtonStyle, SelectOption
from discord.ui import View, Button, Select
from cards_engine.game_config import (
        GameConfig,
        hand_size_min, hand_size_max,
        max_players_min, max_players_max,
        blank_count_min, blank_count_max,
        score_limit_min, score_limit_max
    )
from discord_bot.services.game_manager  import start_game
from discord_bot.services.state_manager import get_lobby, remove_lobby, get_repository

MAX_PAGE = 2

class SetupView(View):
    def __init__(self, channel_id: int, bot, page: int = 1):
        super().__init__(timeout=300)
        self.channel_id = channel_id
        self.bot        = bot
        self.page       = page

        lobby = get_lobby(channel_id)
        if lobby is None:
            raise RuntimeError("No lobby for this channel")
        if lobby.config is None:
            lobby.config = GameConfig()
        self.lobby = lobby

        repository   = get_repository()
        expansions   = repository.available_expansions()
        regions      = repository.available_regions()
        sizes        = list(range(hand_size_min, hand_size_max + 1))
        max_players_opts = list(range(max_players_min, max_players_max + 1))

        # Defaults
        if not self.lobby.config.expansions:
            self.lobby.config = replace(self.lobby.config, expansions=expansions.copy())

        # ========== SELECT COMPONENTS ==========
        self.sel_packs = Select(
            placeholder="Select Expansions",
            options=[SelectOption(label=e, value=e, default=(e in self.lobby.config.expansions))
                     for e in expansions],
            min_values=1, max_values=len(expansions), row=0
        )
        self.sel_packs.callback = self.on_select_packs

        self.sel_regions = Select(
            placeholder="Select Regions",
            options=[SelectOption(label=r.upper(), value=r, default=self.lobby.config.regions.get(r, False))
                     for r in regions],
            min_values=1, max_values=len(regions), row=1
        )
        self.sel_regions.callback = self.on_select_regions

        self.sel_size = Select(
            placeholder="Hand Size",
            options=[SelectOption(label=f"Hand Size: {n}", value=str(n), default=(n == self.lobby.config.hand_size)) for n in sizes],
            min_values=1, max_values=1, row=0
        )
        self.sel_size.callback = self.on_select_size

        # --- Clearer Labels for Blanks Selectors ---
        blank_opts_min = [
            SelectOption(
                label=f"Min. Blanks Per Prompt: {n}",
                value=str(n),
                default=(n == self.lobby.config.min_blanks)
            )
            for n in range(blank_count_min, blank_count_max + 1)
        ]
        self.sel_min_blanks = Select(
            placeholder="Minimum Blanks Per Prompt",
            options=blank_opts_min,
            min_values=1, max_values=1,
            row=1
        )
        self.sel_min_blanks.callback = self.on_select_min_blanks

        blank_opts_max = [
            SelectOption(
                label=f"Max. Blanks Per Prompt: {n}",
                value=str(n),
                default=(n == self.lobby.config.max_blanks)
            )
            for n in range(blank_count_min, blank_count_max + 1)
        ]
        self.sel_max_blanks = Select(
            placeholder="Maximum Blanks Per Prompt",
            options=blank_opts_max,
            min_values=1, max_values=1,
            row=2
        )
        self.sel_max_blanks.callback = self.on_select_max_blanks

        self.sel_score_limit = Select(
            placeholder="Score Limit",
            options=[SelectOption(label=f"Score Limit: {n}", value=str(n), default=(n == self.lobby.config.score_limit))
                     for n in range(score_limit_min, score_limit_max + 1)],
            min_values=1, max_values=1, row=3
        )
        self.sel_score_limit.callback = self.on_select_score_limit

        self.sel_max_players = Select(
            placeholder="Max Players",
            options=[SelectOption(label=f"Max Players: {n}", value=str(n), default=(n == self.lobby.config.max_players)) for n in max_players_opts],
            min_values=1, max_values=1, row=2
        )
        self.sel_max_players.callback = self.on_select_max_players

        # ========== PAGE CONTENT ==========
        if self.page == 1:
            self.add_item(self.sel_packs)    # row=0
            self.add_item(self.sel_regions)  # row=1
            self.add_item(self.sel_max_players)  # row=2
        elif self.page == 2:
            self.add_item(self.sel_size)         # row=0
            self.add_item(self.sel_min_blanks)   # row=1
            self.add_item(self.sel_max_blanks)   # row=2
            self.add_item(self.sel_score_limit)   # row=3

        # ========== NAVIGATION/CONTROL BUTTONS (ROW 4) ==========

        draft_mode_active = self.lobby.config.draft_mode
        draft_emoji = "🏀" if draft_mode_active else "🎲"
        draft_style = ButtonStyle.success if draft_mode_active else ButtonStyle.secondary

        # Disable nav arrows at ends
        left_disabled = self.page == 1
        right_disabled = self.page == MAX_PAGE

        #self.add_item(Button(
        #    emoji=draft_emoji, style=draft_style, row=4,
        #    custom_id="toggle_draft"
        #))
        self.add_item(Button(
            emoji="◀️", style=ButtonStyle.primary, row=4,
            custom_id="page_left", disabled=left_disabled
        ))
        self.add_item(Button(
            emoji="▶️", style=ButtonStyle.primary, row=4,
            custom_id="page_right", disabled=right_disabled
        ))
        self.add_item(Button(
            emoji="✅", style=ButtonStyle.success, row=4,
            custom_id="begin_game"
        ))
        self.add_item(Button(
            emoji="❌", style=ButtonStyle.danger, row=4,
            custom_id="cancel_setup"
        ))

    # ========== SELECT CALLBACKS ==========

    async def on_select_packs(self, interaction: Interaction):
        new_cfg = replace(self.lobby.config, expansions=interaction.data["values"])
        self.lobby.config = new_cfg
        for opt in self.sel_packs.options:
            opt.default = opt.value in new_cfg.expansions
        await interaction.response.edit_message(view=SetupView(self.channel_id, self.bot, self.page))

    async def on_select_regions(self, interaction: Interaction):
        vals = interaction.data["values"]
        new_regions = {r: (r in vals) for r in self.lobby.config.regions}
        new_cfg = replace(self.lobby.config, regions=new_regions)
        self.lobby.config = new_cfg
        for opt in self.sel_regions.options:
            opt.default = opt.value in vals
        await interaction.response.edit_message(view=SetupView(self.channel_id, self.bot, self.page))

    async def on_select_size(self, interaction: Interaction):
        size = int(interaction.data["values"][0])
        new_cfg = replace(self.lobby.config, hand_size=size)
        self.lobby.config = new_cfg
        for opt in self.sel_size.options:
            opt.default = (opt.value == str(size))
        await interaction.response.edit_message(view=SetupView(self.channel_id, self.bot, self.page))

    async def on_select_min_blanks(self, interaction: Interaction):
        min_val = int(interaction.data["values"][0])
        max_val = getattr(self.lobby.config, "max_blanks", 3)
        if min_val > max_val:
            min_val = max_val
        new_cfg = replace(self.lobby.config, min_blanks=min_val)
        self.lobby.config = new_cfg
        for opt in self.sel_min_blanks.options:
            opt.default = (int(opt.value) == min_val)
        await interaction.response.edit_message(view=SetupView(self.channel_id, self.bot, self.page))

    async def on_select_max_blanks(self, interaction: Interaction):
        max_val = int(interaction.data["values"][0])
        min_val = getattr(self.lobby.config, "min_blanks", 1)
        if max_val < min_val:
            max_val = min_val
        new_cfg = replace(self.lobby.config, max_blanks=max_val)
        self.lobby.config = new_cfg
        for opt in self.sel_max_blanks.options:
            opt.default = (int(opt.value) == max_val)
        await interaction.response.edit_message(view=SetupView(self.channel_id, self.bot, self.page))

    async def on_select_max_players(self, interaction: Interaction):
        max_players = int(interaction.data["values"][0])
        self.lobby.config = replace(self.lobby.config, max_players=max_players)
        await interaction.response.edit_message(view=SetupView(self.channel_id, self.bot, self.page))

    async def on_select_score_limit(self, interaction: Interaction):
        score_limit = int(interaction.data["values"][0])
        self.lobby.config = replace(self.lobby.config, score_limit=score_limit)
        for opt in self.sel_score_limit.options:
            opt.default = (int(opt.value) == score_limit)
        await interaction.response.edit_message(view=SetupView(self.channel_id, self.bot, self.page))

    # ========== BUTTON HANDLERS ==========

    async def interaction_check(self, interaction: Interaction):
        # This is needed so all custom_id buttons work with one method
        if interaction.data.get("custom_id") == "toggle_draft":
            await self.on_toggle_draft(interaction)
        elif interaction.data.get("custom_id") == "page_left":
            await self.on_page_left(interaction)
        elif interaction.data.get("custom_id") == "page_right":
            await self.on_page_right(interaction)
        elif interaction.data.get("custom_id") == "begin_game":
            await self.on_begin(interaction)
        elif interaction.data.get("custom_id") == "cancel_setup":
            await self.on_cancel(interaction)
        else:
            return True
        return False  # prevents default handling

    async def on_toggle_draft(self, interaction: Interaction):
        new_cfg = replace(self.lobby.config, draft_mode=not self.lobby.config.draft_mode)
        self.lobby.config = new_cfg
        await interaction.response.edit_message(view=SetupView(self.channel_id, self.bot, self.page))

    async def on_page_left(self, interaction: Interaction):
        prev_page = max(1, self.page - 1)
        await interaction.response.edit_message(view=SetupView(self.channel_id, self.bot, prev_page))

    async def on_page_right(self, interaction: Interaction):
        next_page = min(self.page + 1, MAX_PAGE)
        await interaction.response.edit_message(view=SetupView(self.channel_id, self.bot, next_page))

    async def on_begin(self, interaction: Interaction):
        enough = len(self.lobby.players) >= 3 or self.lobby.host.id == "171721577979838465"
        packs  = bool(self.lobby.config.expansions)
        regs   = any(self.lobby.config.regions.values())
        size   = isinstance(self.lobby.config.hand_size, int)
        if not (enough and packs and regs and size):
            await interaction.response.send_message("❌ Cannot start: check settings.", ephemeral=True)
            return

        game = await start_game(self.channel_id)
        await interaction.response.edit_message(content="Bubba's Challenge BEGINS ...", view=None)
        channel = self.bot.get_channel(self.channel_id)
        
        lobby = get_lobby(self.channel_id)
        if lobby and getattr(lobby, "join_message_id", None):
            try:
                msg = await channel.fetch_message(lobby.join_message_id)
                await msg.delete()
            except Exception as e:
                print(f"Failed to delete join message: {e}")

        judge_current = getattr(game.state, "current_judge", None)
        judge_current_name = judge_current.name if judge_current else "Unknown"
        prompt_card = getattr(game.state, "current_prompt", None)
        prompt_text = prompt_card.text if prompt_card else "No prompt selected."

    async def on_cancel(self, interaction: Interaction):
        remove_lobby(self.channel_id)
        await interaction.response.edit_message(content="🚫 Setup cancelled.", view=None)