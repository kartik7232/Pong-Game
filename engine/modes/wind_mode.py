"""
===============================================================================
PONG GAME ENGINE - MODE 1: WIND MODE
===============================================================================
Architectural Role: Periodic dynamic atmospheric force on ball kinematics
"""

import math
import random
from typing import List, Tuple, Optional
import pygame

from engine.modes.base import GameMode
from engine.entities import Ball
from engine.physics import Vector2D
from engine.config import (
    WIND_CYCLE_DURATION, WIND_ACTIVE_DURATION, WIND_WARNING_DURATION,
    WIND_FORCE, MAX_BALL_SPEED, SCREEN_WIDTH, SCREEN_HEIGHT,
    TOP_BOUND, BOTTOM_BOUND, LEFT_BOUND, RIGHT_BOUND,
    COLOR_MENU_SELECTED, COLOR_TEXT
)


class WindStreak:
    """Lightweight visual streak line for active wind representation."""
    def __init__(self, direction: str):
        self.reset(direction)

    def reset(self, direction: str):
        self.direction = direction
        self.length = random.uniform(25, 60)
        self.speed = random.uniform(500, 850)
        
        if direction == "RIGHT":
            self.x = random.uniform(LEFT_BOUND - 50, LEFT_BOUND)
            self.y = random.uniform(TOP_BOUND + 10, BOTTOM_BOUND - 10)
        elif direction == "LEFT":
            self.x = random.uniform(RIGHT_BOUND, RIGHT_BOUND + 50)
            self.y = random.uniform(TOP_BOUND + 10, BOTTOM_BOUND - 10)
        elif direction == "DOWN":
            self.x = random.uniform(LEFT_BOUND + 20, RIGHT_BOUND - 20)
            self.y = random.uniform(TOP_BOUND - 50, TOP_BOUND)
        elif direction == "UP":
            self.x = random.uniform(LEFT_BOUND + 20, RIGHT_BOUND - 20)
            self.y = random.uniform(BOTTOM_BOUND, BOTTOM_BOUND + 50)

    def update(self, dt: float) -> bool:
        if self.direction == "RIGHT":
            self.x += self.speed * dt
            return self.x < RIGHT_BOUND + 50
        elif self.direction == "LEFT":
            self.x -= self.speed * dt
            return self.x > LEFT_BOUND - 50
        elif self.direction == "DOWN":
            self.y += self.speed * dt
            return self.y < BOTTOM_BOUND + 50
        elif self.direction == "UP":
            self.y -= self.speed * dt
            return self.y > TOP_BOUND - 50
        return False

    def draw(self, surface: pygame.Surface):
        alpha = random.randint(120, 200)
        color = (130, 220, 255)
        if self.direction in ("LEFT", "RIGHT"):
            end_x = self.x + (self.length if self.direction == "RIGHT" else -self.length)
            end_y = self.y
        else:
            end_x = self.x
            end_y = self.y + (self.length if self.direction == "DOWN" else -self.length)
        pygame.draw.line(surface, color, (int(self.x), int(self.y)), (int(end_x), int(end_y)), 2)


class WindMode(GameMode):
    """
    Mode 1 - Wind Mode
    - 6s cycle: 3.5s calm, 0.5s warning, 2s active.
    - Timer runs continuously across point losses (no reset on round end).
    - Uniform random direction: UP, DOWN, LEFT, RIGHT.
    - Constant acceleration applied to ball, clamped to MAX_BALL_SPEED.
    - Visual streak particles + warning arrow + HUD badge.
    """
    DIRECTIONS = ["UP", "DOWN", "LEFT", "RIGHT"]
    DIR_VECTORS = {
        "UP": Vector2D(0.0, -1.0),
        "DOWN": Vector2D(0.0, 1.0),
        "LEFT": Vector2D(-1.0, 0.0),
        "RIGHT": Vector2D(1.0, 0.0)
    }

    def __init__(self):
        super().__init__("Wind Mode")
        self.timer: float = 0.0
        self.current_direction: str = "RIGHT"
        self.is_active: bool = False
        self.is_warning: bool = False
        self.streaks: List[WindStreak] = []
        self.font: Optional[pygame.font.Font] = None

    def reset(self) -> None:
        self.timer = 0.0
        self.is_active = False
        self.is_warning = False
        self.current_direction = random.choice(self.DIRECTIONS)
        self.streaks.clear()

    def update(self, dt: float) -> None:
        if not self.is_enabled:
            return

        calm_duration = WIND_CYCLE_DURATION - WIND_ACTIVE_DURATION  # 8.0s
        warning_start = calm_duration - WIND_WARNING_DURATION      # 7.5s

        self.timer += dt

        # State 1: Calm (before warning)
        if self.timer < warning_start:
            self.is_warning = False
            self.is_active = False

        # State 2: Warning (7.5s - 8.0s)
        elif self.timer < calm_duration:
            if not self.is_warning:
                self.is_warning = True
                self.current_direction = random.choice(self.DIRECTIONS)
            self.is_active = False

        # State 3: Active Wind (8.0s - 10.0s)
        elif self.timer < WIND_CYCLE_DURATION:
            self.is_warning = False
            self.is_active = True

            # Spawn wind streaks
            if len(self.streaks) < 25:
                self.streaks.append(WindStreak(self.current_direction))

            # Update streaks
            surviving = []
            for s in self.streaks:
                if s.update(dt):
                    surviving.append(s)
            self.streaks = surviving

        # Cycle finished: reset to 0.0
        else:
            self.timer = 0.0
            self.is_active = False
            self.is_warning = False
            self.streaks.clear()

    def on_ball_update(self, ball: Ball, dt: float = 0.0) -> None:
        if not self.is_enabled or not self.is_active:
            return

        # Apply constant acceleration in wind direction
        wind_vec = self.DIR_VECTORS[self.current_direction]
        ball.vel.x += wind_vec.x * WIND_FORCE * dt
        ball.vel.y += wind_vec.y * WIND_FORCE * dt

        # Clamp max ball speed so gameplay stays playable
        if ball.speed > MAX_BALL_SPEED:
            norm = ball.vel.normalized()
            ball.vel = norm * MAX_BALL_SPEED

    def on_round_start(self) -> None:
        pass  # Timer runs continuously; no pause needed

    def on_round_end(self) -> None:
        # Keep the timer running so wind continues uninterrupted across point losses.
        # Only clear the visual streaks to avoid orphaned particles during the reset pause.
        self.streaks.clear()

    def disable(self) -> None:
        super().disable()
        self.reset()

    def draw(self, renderer: pygame.Surface) -> None:
        if not self.is_enabled:
            return

        if self.font is None:
            self.font = pygame.font.SysFont("Consolas", 18, bold=True)

        center_x = SCREEN_WIDTH // 2

        # 1. Warning visuals (arrow fading in)
        if self.is_warning:
            calm_duration = WIND_CYCLE_DURATION - WIND_ACTIVE_DURATION
            fade_progress = (self.timer - (calm_duration - WIND_WARNING_DURATION)) / WIND_WARNING_DURATION
            alpha = int(max(0.0, min(1.0, fade_progress)) * 255)
            
            warn_surf = self.font.render(f"! WIND WARNING: {self.current_direction} !", True, (255, 200, 80))
            warn_surf.set_alpha(alpha)
            renderer.blit(warn_surf, (center_x - warn_surf.get_width() // 2, TOP_BOUND + 70))

        # 2. Active wind visuals
        if self.is_active:
            # Draw streak particles
            for s in self.streaks:
                s.draw(renderer)

            # Draw HUD Badge
            badge_text = f"WIND ACTIVE: {self.current_direction}"
            badge_surf = self.font.render(badge_text, True, (0, 235, 255))
            
            # Badge background pill
            badge_rect = pygame.Rect(
                center_x - badge_surf.get_width() // 2 - 12,
                int(TOP_BOUND) + 68,
                badge_surf.get_width() + 24,
                26
            )
            pill_surf = pygame.Surface((badge_rect.width, badge_rect.height), pygame.SRCALPHA)
            pill_surf.fill((0, 40, 80, 180))
            renderer.blit(pill_surf, badge_rect.topleft)
            pygame.draw.rect(renderer, (0, 235, 255), badge_rect, 1, border_radius=4)
            renderer.blit(badge_surf, (center_x - badge_surf.get_width() // 2, TOP_BOUND + 72))
