"""
===============================================================================
PONG GAME ENGINE - MODE 2: PORTALS MODE
===============================================================================
Architectural Role: Bidirectional spatial wormholes with swept collision
"""

import math
import random
from typing import Tuple, List, Optional
import pygame

from engine.modes.base import GameMode
from engine.entities import Ball
from engine.physics import Vector2D
from engine.config import (
    PORTAL_RADIUS, PORTAL_COOLDOWN, PORTAL_DEFAULT_Y_OFFSET, PORTAL_JITTER_X,
    COLOR_PORTAL_A, COLOR_PORTAL_B, SCREEN_WIDTH, SCREEN_HEIGHT,
    TOP_BOUND, BOTTOM_BOUND, LEFT_BOUND, RIGHT_BOUND
)


class PortalFlash:
    def __init__(self, x: float, y: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.color = color
        self.radius = 10.0
        self.max_radius = 45.0
        self.lifetime = 0.25
        self.max_lifetime = 0.25

    def update(self, dt: float) -> bool:
        self.lifetime -= dt
        progress = 1.0 - (self.lifetime / self.max_lifetime)
        self.radius = 10.0 + progress * (self.max_radius - 10.0)
        return self.lifetime > 0

    def draw(self, surface: pygame.Surface):
        if self.lifetime <= 0:
            return
        alpha = int((self.lifetime / self.max_lifetime) * 220)
        flash_surf = pygame.Surface((int(self.radius * 2) + 4, int(self.radius * 2) + 4), pygame.SRCALPHA)
        pygame.draw.circle(
            flash_surf,
            (*self.color, alpha),
            (int(self.radius) + 2, int(self.radius) + 2),
            int(self.radius),
            width=3
        )
        surface.blit(flash_surf, (self.x - self.radius - 2, self.y - self.radius - 2))


class PortalMode(GameMode):
    """
    Mode 2 - Portals Mode
    - Two portals (A: Electric Blue, B: Neon Orange) in the central area.
    - Bidirectional teleportation preserving velocity vector.
    - Swept segment intersection prevents high-speed ball tunneling.
    - 0.3s teleport cooldown prevents infinite loop.
    """
    def __init__(self):
        super().__init__("Portals")
        self.portal_a_pos: Vector2D = Vector2D(SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.5 - PORTAL_DEFAULT_Y_OFFSET)
        self.portal_b_pos: Vector2D = Vector2D(SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.5 + PORTAL_DEFAULT_Y_OFFSET)
        self.radius: float = PORTAL_RADIUS
        self.cooldown_timer: float = 0.0
        self.anim_time: float = 0.0
        self.flashes: List[PortalFlash] = []
        self._prev_ball_pos: Optional[Vector2D] = None

    def reset(self) -> None:
        self.cooldown_timer = 0.0
        self.flashes.clear()
        self._prev_ball_pos = None
        self._randomize_positions()

    def _randomize_positions(self) -> None:
        """Positions portals within central 40% area with round-by-round jitter."""
        center_x = SCREEN_WIDTH * 0.5
        center_y = SCREEN_HEIGHT * 0.5
        
        # Central 40% bounds: x within [0.3 * W, 0.7 * W]
        jitter_x = random.uniform(-PORTAL_JITTER_X, PORTAL_JITTER_X)
        jitter_ya = random.uniform(-15.0, 15.0)
        jitter_yb = random.uniform(-15.0, 15.0)

        self.portal_a_pos = Vector2D(
            center_x + jitter_x,
            center_y - PORTAL_DEFAULT_Y_OFFSET + jitter_ya
        )
        self.portal_b_pos = Vector2D(
            center_x - jitter_x * 0.5,
            center_y + PORTAL_DEFAULT_Y_OFFSET + jitter_yb
        )

    def update(self, dt: float) -> None:
        if not self.is_enabled:
            return

        self.anim_time += dt
        if self.cooldown_timer > 0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

        # Update flashes
        self.flashes = [f for f in self.flashes if f.update(dt)]

    def _check_swept_intersection(self, p0: Vector2D, p1: Vector2D, portal_center: Vector2D, threshold: float) -> bool:
        """
        Swept segment-to-point distance check to prevent fast ball tunneling.
        Computes shortest distance from portal_center to segment (p0 -> p1).
        """
        dx = p1.x - p0.x
        dy = p1.y - p0.y
        seg_len_sq = dx * dx + dy * dy

        if seg_len_sq == 0.0:
            dist = math.hypot(p0.x - portal_center.x, p0.y - portal_center.y)
            return dist <= threshold

        # Projection parameter t clamped to [0, 1]
        t = max(0.0, min(1.0, ((portal_center.x - p0.x) * dx + (portal_center.y - p0.y) * dy) / seg_len_sq))
        closest_x = p0.x + t * dx
        closest_y = p0.y + t * dy

        dist = math.hypot(closest_x - portal_center.x, closest_y - portal_center.y)
        return dist <= threshold

    def on_ball_update(self, ball: Ball, dt: float = 0.0) -> None:
        if not self.is_enabled:
            return

        # Initialize previous position if first frame
        if self._prev_ball_pos is None:
            self._prev_ball_pos = Vector2D(ball.pos.x - ball.vel.x * dt, ball.pos.y - ball.vel.y * dt)

        if self.cooldown_timer <= 0:
            threshold = self.radius + ball.radius * 0.5

            hit_a = self._check_swept_intersection(self._prev_ball_pos, ball.pos, self.portal_a_pos, threshold)
            hit_b = self._check_swept_intersection(self._prev_ball_pos, ball.pos, self.portal_b_pos, threshold)

            if hit_a:
                # Teleport from A to B: exit velocity is identical to entry velocity
                self.flashes.append(PortalFlash(self.portal_a_pos.x, self.portal_a_pos.y, COLOR_PORTAL_A))
                self.flashes.append(PortalFlash(self.portal_b_pos.x, self.portal_b_pos.y, COLOR_PORTAL_B))
                ball.pos = Vector2D(self.portal_b_pos.x, self.portal_b_pos.y)
                self.cooldown_timer = PORTAL_COOLDOWN

            elif hit_b:
                # Teleport from B to A: exit velocity is identical to entry velocity
                self.flashes.append(PortalFlash(self.portal_b_pos.x, self.portal_b_pos.y, COLOR_PORTAL_B))
                self.flashes.append(PortalFlash(self.portal_a_pos.x, self.portal_a_pos.y, COLOR_PORTAL_A))
                ball.pos = Vector2D(self.portal_a_pos.x, self.portal_a_pos.y)
                self.cooldown_timer = PORTAL_COOLDOWN

        # Store for next swept test
        self._prev_ball_pos = Vector2D(ball.pos.x, ball.pos.y)

    def on_round_start(self) -> None:
        self.cooldown_timer = 0.0
        self._prev_ball_pos = None
        self._randomize_positions()

    def on_round_end(self) -> None:
        self.cooldown_timer = 0.0
        self._prev_ball_pos = None

    def disable(self) -> None:
        super().disable()
        self.reset()

    def draw(self, renderer: pygame.Surface) -> None:
        if not self.is_enabled:
            return

        pulse_offset = math.sin(self.anim_time * 6.0) * 2.5
        r = int(self.radius + pulse_offset)

        # Draw Portal A (Electric Blue)
        pos_a = (int(self.portal_a_pos.x), int(self.portal_a_pos.y))
        pygame.draw.circle(renderer, (10, 40, 70), pos_a, r + 4)
        pygame.draw.circle(renderer, COLOR_PORTAL_A, pos_a, r, width=3)
        pygame.draw.circle(renderer, (200, 240, 255), pos_a, max(2, r // 3))

        # Draw Portal B (Neon Orange)
        pos_b = (int(self.portal_b_pos.x), int(self.portal_b_pos.y))
        pygame.draw.circle(renderer, (70, 30, 10), pos_b, r + 4)
        pygame.draw.circle(renderer, COLOR_PORTAL_B, pos_b, r, width=3)
        pygame.draw.circle(renderer, (255, 230, 180), pos_b, max(2, r // 3))

        # Draw teleport flashes
        for flash in self.flashes:
            flash.draw(renderer)
