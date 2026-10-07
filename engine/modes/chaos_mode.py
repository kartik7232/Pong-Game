"""
===============================================================================
PONG GAME ENGINE - MODE 4: CHAOS MODE
===============================================================================
Architectural Role: Meta-mode cycling Wind, Portals, and Powerups every 60s
"""

import math
import random
from typing import List, Optional
import pygame

from engine.modes.base import GameMode
from engine.modes.wind_mode import WindMode
from engine.modes.portal_mode import PortalMode
from engine.modes.powerup_mode import PowerupMode
from engine.entities import Ball
from engine.config import (
    CHAOS_MODE_DURATION, CHAOS_BANNER_DURATION,
    SCREEN_WIDTH, SCREEN_HEIGHT, TOP_BOUND, BOTTOM_BOUND,
    COLOR_MENU_ACCENT, COLOR_MENU_SELECTED, COLOR_TEXT
)


class ChaosMode(GameMode):
    """
    Mode 4 - Chaos Mode
    - Reuses WindMode, PortalMode, and PowerupMode modules without duplicating logic.
    - Runs one mode for 60s, then switches cleanly to a different random mode (never repeating).
    - Cleans up state on each transition and displays a 2s animated transition banner.
    - Exposes countdown timer in the HUD.
    """
    def __init__(self, wind_mode: WindMode, portal_mode: PortalMode, powerup_mode: PowerupMode):
        super().__init__("Chaos Mode")
        self.submodes: List[GameMode] = [wind_mode, portal_mode, powerup_mode]
        self.current_submode: GameMode = wind_mode
        self.switch_timer: float = CHAOS_MODE_DURATION
        self.banner_timer: float = 0.0
        self.banner_anim_time: float = 0.0
        self.font_large: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None

    def init(self, game) -> None:
        super().init(game)
        for mode in self.submodes:
            mode.init(game)

    def reset(self) -> None:
        for mode in self.submodes:
            mode.disable()
            mode.reset()
        self.current_submode = random.choice(self.submodes)
        self.current_submode.enable()
        self.current_submode.reset()
        self.switch_timer = CHAOS_MODE_DURATION
        self.banner_timer = CHAOS_BANNER_DURATION
        self.banner_anim_time = 0.0

    def enable(self) -> None:
        super().enable()
        self.reset()

    def disable(self) -> None:
        super().disable()
        for mode in self.submodes:
            mode.disable()
            mode.reset()

    def update(self, dt: float) -> None:
        if not self.is_enabled:
            return

        self.switch_timer -= dt
        if self.banner_timer > 0.0:
            self.banner_timer -= dt
            self.banner_anim_time += dt

        # Check for 60s mode rotation
        if self.switch_timer <= 0.0:
            # 1. Cleanly disable previous submode
            self.current_submode.disable()
            self.current_submode.reset()

            # 2. Pick different random submode (never the same one twice in a row)
            remaining_candidates = [m for m in self.submodes if m != self.current_submode]
            self.current_submode = random.choice(remaining_candidates)

            # 3. Enable new submode
            self.current_submode.enable()
            self.current_submode.reset()

            # 4. Reset timers
            self.switch_timer = CHAOS_MODE_DURATION
            self.banner_timer = CHAOS_BANNER_DURATION
            self.banner_anim_time = 0.0

        # Update active submode
        self.current_submode.update(dt)

    def on_ball_update(self, ball: Ball, dt: float = 0.0) -> None:
        if not self.is_enabled:
            return
        self.current_submode.on_ball_update(ball, dt)

    def on_round_start(self) -> None:
        if not self.is_enabled:
            return
        self.current_submode.on_round_start()

    def on_round_end(self) -> None:
        if not self.is_enabled:
            return
        self.current_submode.on_round_end()

    def draw(self, renderer: pygame.Surface) -> None:
        if not self.is_enabled:
            return

        if self.font_large is None:
            self.font_large = pygame.font.SysFont("Consolas", 28, bold=True)
            self.font_small = pygame.font.SysFont("Consolas", 15, bold=True)

        # 1. Draw active submode visuals
        self.current_submode.draw(renderer)

        center_x = SCREEN_WIDTH // 2

        # 2. Draw Countdown HUD Indicator
        countdown_sec = max(0, int(self.switch_timer))
        hud_text = f"CHAOS: {self.current_submode.name.upper()} | SHIFT IN: {countdown_sec:02d}s"
        hud_surf = self.font_small.render(hud_text, True, COLOR_MENU_ACCENT)
        renderer.blit(hud_surf, (center_x - hud_surf.get_width() // 2, BOTTOM_BOUND - 48))

        # 3. Draw 2s Animated Transition Banner
        if self.banner_timer > 0.0:
            fade_ratio = min(1.0, self.banner_timer / 0.4)
            alpha = int(fade_ratio * 240)

            banner_w = 460
            banner_h = 60
            banner_rect = pygame.Rect(center_x - banner_w // 2, SCREEN_HEIGHT // 2 - 40, banner_w, banner_h)

            banner_surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
            banner_surf.fill((16, 20, 32, alpha))
            renderer.blit(banner_surf, banner_rect.topleft)

            pulse = 1.0 + math.sin(self.banner_anim_time * 12.0) * 0.05
            pygame.draw.rect(renderer, COLOR_MENU_ACCENT, banner_rect, width=2, border_radius=6)

            announcement = f"CHAOS: {self.current_submode.name.upper()}"
            text_surf = self.font_large.render(announcement, True, COLOR_MENU_SELECTED)
            text_surf.set_alpha(alpha)
            renderer.blit(text_surf, text_surf.get_rect(center=banner_rect.center))
