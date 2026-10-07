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
    PORTAL_RADIUS, PORTAL_RX, PORTAL_RY, PORTAL_COOLDOWN,
    PORTAL_REPOSITION_INTERVAL,
    PORTAL_DEFAULT_Y_OFFSET, PORTAL_JITTER_X,
    COLOR_PORTAL_A, COLOR_PORTAL_B, SCREEN_WIDTH, SCREEN_HEIGHT,
    TOP_BOUND, BOTTOM_BOUND, LEFT_BOUND, RIGHT_BOUND
)

# Effective collision radius: geometric mean of the two oval semi-axes.
# Gives a single circular threshold that approximates the oval's area.
_PORTAL_COLLISION_RADIUS: float = math.sqrt(PORTAL_RX * PORTAL_RY)


class PortalFlash:
    def __init__(self, x: float, y: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.color = color
        self.radius = 10.0
        self.max_radius = 55.0
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
        # Flash ring drawn as a thin oval matching the portal shape
        rx = int(PORTAL_RX + self.radius * 0.4)
        ry = int(PORTAL_RY + self.radius * 0.6)
        flash_surf = pygame.Surface((rx * 2 + 4, ry * 2 + 4), pygame.SRCALPHA)
        pygame.draw.ellipse(
            flash_surf,
            (*self.color, alpha),
            pygame.Rect(2, 2, rx * 2, ry * 2),
            width=3
        )
        surface.blit(flash_surf, (self.x - rx - 2, self.y - ry - 2))


class PortalMode(GameMode):
    """
    Mode 2 - Portals Mode
    - Two portals (A: Electric Blue, B: Neon Orange) rendered as vertical ovals.
    - Portals reposition one-by-one every 20 seconds (A moves first, then B, alternating).
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

        # Alternating reposition: 0 = Portal A moves next, 1 = Portal B moves next
        self._reposition_timer: float = PORTAL_REPOSITION_INTERVAL
        self._next_to_move: int = 0  # 0 → A, 1 → B

    def reset(self) -> None:
        self.cooldown_timer = 0.0
        self.flashes.clear()
        self._prev_ball_pos = None
        self._reposition_timer = PORTAL_REPOSITION_INTERVAL
        self._next_to_move = 0
        self._randomize_positions()

    def _randomize_positions(self) -> None:
        """Positions both portals within central 40% area with round-by-round jitter."""
        center_x = SCREEN_WIDTH * 0.5
        center_y = SCREEN_HEIGHT * 0.5

        # Clamp so the oval (RY taller) stays inside play area
        margin_y = PORTAL_RY + 10.0
        min_y = TOP_BOUND + margin_y
        max_y = BOTTOM_BOUND - margin_y

        jitter_x = random.uniform(-PORTAL_JITTER_X, PORTAL_JITTER_X)
        jitter_ya = random.uniform(-15.0, 15.0)
        jitter_yb = random.uniform(-15.0, 15.0)

        self.portal_a_pos = Vector2D(
            center_x + jitter_x,
            max(min_y, min(max_y, center_y - PORTAL_DEFAULT_Y_OFFSET + jitter_ya))
        )
        self.portal_b_pos = Vector2D(
            center_x - jitter_x * 0.5,
            max(min_y, min(max_y, center_y + PORTAL_DEFAULT_Y_OFFSET + jitter_yb))
        )

    def _randomize_single(self, which: int) -> None:
        """Repositions only one portal (0 = A, 1 = B) to a new random central position."""
        center_x = SCREEN_WIDTH * 0.5
        center_y = SCREEN_HEIGHT * 0.5
        margin_y = PORTAL_RY + 10.0
        min_y = TOP_BOUND + margin_y
        max_y = BOTTOM_BOUND - margin_y

        # Keep portals separated vertically to avoid overlap
        sep = PORTAL_DEFAULT_Y_OFFSET * 0.6

        jitter_x = random.uniform(-PORTAL_JITTER_X, PORTAL_JITTER_X)

        if which == 0:
            new_y = center_y + random.uniform(-PORTAL_DEFAULT_Y_OFFSET, -sep)
            new_y = max(min_y, min(max_y, new_y + random.uniform(-10.0, 10.0)))
            self.portal_a_pos = Vector2D(center_x + jitter_x, new_y)
        else:
            new_y = center_y + random.uniform(sep, PORTAL_DEFAULT_Y_OFFSET)
            new_y = max(min_y, min(max_y, new_y + random.uniform(-10.0, 10.0)))
            self.portal_b_pos = Vector2D(center_x - jitter_x * 0.5, new_y)

    def update(self, dt: float) -> None:
        if not self.is_enabled:
            return

        self.anim_time += dt

        if self.cooldown_timer > 0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

        # Update flashes
        self.flashes = [f for f in self.flashes if f.update(dt)]

        # Alternating 20-second reposition: one portal at a time
        self._reposition_timer -= dt
        if self._reposition_timer <= 0:
            self._randomize_single(self._next_to_move)
            self._next_to_move = 1 - self._next_to_move  # toggle A ↔ B
            self._reposition_timer = PORTAL_REPOSITION_INTERVAL

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
            # Use oval geometric-mean radius as the effective collision threshold
            threshold = _PORTAL_COLLISION_RADIUS + ball.radius * 0.5

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
        # Reset reposition cycle on new round
        self._reposition_timer = PORTAL_REPOSITION_INTERVAL
        self._next_to_move = 0

    def on_round_end(self) -> None:
        self.cooldown_timer = 0.0
        self._prev_ball_pos = None

    def disable(self) -> None:
        super().disable()
        self.reset()

    def _draw_oval_portal(
        self,
        renderer: pygame.Surface,
        cx: int,
        cy: int,
        pulse_offset: float,
        bg_color: Tuple[int, int, int],
        ring_color: Tuple[int, int, int],
        core_color: Tuple[int, int, int],
    ) -> None:
        """Draws a single vertical-oval portal with glow, ring, and inner core."""
        rx = int(PORTAL_RX + pulse_offset * 0.6)
        ry = int(PORTAL_RY + pulse_offset)

        # Background glow (slightly larger oval)
        bg_rx = rx + 5
        bg_ry = ry + 5
        glow_surf = pygame.Surface((bg_rx * 2 + 2, bg_ry * 2 + 2), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (*bg_color, 180), glow_surf.get_rect())
        renderer.blit(glow_surf, (cx - bg_rx - 1, cy - bg_ry - 1))

        # Outer ring
        pygame.draw.ellipse(renderer, ring_color, pygame.Rect(cx - rx, cy - ry, rx * 2, ry * 2), width=3)

        # Inner glow core (small ellipse)
        core_rx = max(2, rx // 4)
        core_ry = max(3, ry // 4)
        pygame.draw.ellipse(renderer, core_color, pygame.Rect(cx - core_rx, cy - core_ry, core_rx * 2, core_ry * 2))

    def draw(self, renderer: pygame.Surface) -> None:
        if not self.is_enabled:
            return

        pulse_offset = math.sin(self.anim_time * 6.0) * 2.5

        # Draw Portal A (Electric Blue)
        self._draw_oval_portal(
            renderer,
            int(self.portal_a_pos.x), int(self.portal_a_pos.y),
            pulse_offset,
            bg_color=(10, 40, 70),
            ring_color=COLOR_PORTAL_A,
            core_color=(200, 240, 255),
        )

        # Draw Portal B (Neon Orange)
        self._draw_oval_portal(
            renderer,
            int(self.portal_b_pos.x), int(self.portal_b_pos.y),
            pulse_offset,
            bg_color=(70, 30, 10),
            ring_color=COLOR_PORTAL_B,
            core_color=(255, 230, 180),
        )

        # Draw teleport flashes
        for flash in self.flashes:
            flash.draw(renderer)
