"""
===============================================================================
PONG GAME ENGINE - MODE 3: POWERUP MODE
===============================================================================
Architectural Role: Interactive collectibles, Freeze, Laser, & Ghost Ball abilities
"""

import math
import random
from typing import Optional, List, Dict, Tuple
import pygame

from engine.modes.base import GameMode
from engine.entities import Ball, Paddle
from engine.physics import Vector2D, AABB, check_aabb_intersection
from engine.config import (
    POWERUP_SPAWN_INTERVAL, POWERUP_LIFETIME, POWERUP_ORB_RADIUS, MAX_ACTIVE_ORBS,
    FREEZE_DURATION, LASER_SPEED, LASER_PUSH, GHOST_BALL_WINDOW,
    POWERUP_CARRYOVER_BETWEEN_ROUNDS,
    COLOR_ORB_FREEZE, COLOR_ORB_LASER, COLOR_ORB_GHOST,
    COLOR_ICE_TINT, COLOR_LASER_BEAM,
    SCREEN_WIDTH, SCREEN_HEIGHT, TOP_BOUND, BOTTOM_BOUND, LEFT_BOUND, RIGHT_BOUND,
    COLOR_TEXT, KEY_P1_ACTIVATE, KEY_P2_ACTIVATE
)


class PowerupType:
    FREEZE = "FREEZE"
    LASER = "LASER"
    GHOST_BALL = "GHOST_BALL"


class PowerupOrb:
    """Collectible orb on the playing field with enlarged hitbox."""
    def __init__(self, x: float, y: float, ptype: str):
        self.pos: Vector2D = Vector2D(x, y)
        self.ptype: str = ptype
        self.radius: float = POWERUP_ORB_RADIUS
        self.lifetime: float = POWERUP_LIFETIME
        self.max_lifetime: float = POWERUP_LIFETIME
        self.anim_time: float = 0.0

    @property
    def color(self) -> Tuple[int, int, int]:
        if self.ptype == PowerupType.FREEZE:
            return COLOR_ORB_FREEZE
        elif self.ptype == PowerupType.LASER:
            return COLOR_ORB_LASER
        return COLOR_ORB_GHOST

    @property
    def label(self) -> str:
        if self.ptype == PowerupType.FREEZE:
            return "F"
        elif self.ptype == PowerupType.LASER:
            return "L"
        return "G"

    def update(self, dt: float) -> bool:
        self.lifetime -= dt
        self.anim_time += dt
        return self.lifetime > 0

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        pulse = math.sin(self.anim_time * 5.0) * 3.0
        r = max(6, int(self.radius + pulse))
        center = (int(self.pos.x), int(self.pos.y))

        # Outer pulsing glow halo
        glow_radius = r + 8
        glow_surf = pygame.Surface((glow_radius * 2 + 4, glow_radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color, 45), (glow_radius + 2, glow_radius + 2), glow_radius)
        surface.blit(glow_surf, (center[0] - glow_radius - 2, center[1] - glow_radius - 2))

        # Core circle
        pygame.draw.circle(surface, self.color, center, r)
        pygame.draw.circle(surface, (255, 255, 255), center, r, width=3)

        # Bold letter symbol in center
        sym_font = pygame.font.SysFont("Consolas", int(r * 0.9), bold=True)
        sym_surf = sym_font.render(self.label, True, (15, 18, 28))
        surface.blit(sym_surf, sym_surf.get_rect(center=center))


class LaserProjectile:
    """Linear laser bolt traveling toward opponent."""
    def __init__(self, start_x: float, start_y: float, direction: int, owner_player: int):
        self.pos: Vector2D = Vector2D(start_x, start_y)
        self.vx: float = direction * LASER_SPEED
        self.width: float = 24.0
        self.height: float = 6.0
        self.owner_player: int = owner_player
        self.active: bool = True

    @property
    def aabb(self) -> AABB:
        return AABB(
            min_x=self.pos.x - self.width * 0.5,
            min_y=self.pos.y - self.height * 0.5,
            max_x=self.pos.x + self.width * 0.5,
            max_y=self.pos.y + self.height * 0.5
        )

    def update(self, dt: float) -> bool:
        self.pos.x += self.vx * dt
        if self.pos.x < LEFT_BOUND - 30 or self.pos.x > RIGHT_BOUND + 30:
            self.active = False
        return self.active

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return
        box = self.aabb
        rect = pygame.Rect(box.min_x, box.min_y, box.width, box.height)
        pygame.draw.rect(surface, (255, 255, 200), rect, border_radius=3)
        pygame.draw.rect(surface, COLOR_LASER_BEAM, rect, width=1, border_radius=3)


class PowerupMode(GameMode):
    """
    Mode 3 - Powerup Mode
    - Spawns collectible orbs in the middle court (15s lifetime, up to MAX_ACTIVE_ORBS).
    - Orbs stay on the court even after a player scores/loses a point.
    - Large 28px hitbox makes it easy for the ball to collide.
    - Collected by ball; collector is player who last hit ball.
    - Each player holds at most 1 powerup.
    - Types: FREEZE (2s opponent lock), LASER (destroys ball or knocks paddle), GHOST BALL (invisibility).
    """
    TYPES = [PowerupType.FREEZE, PowerupType.LASER, PowerupType.GHOST_BALL]

    def __init__(self):
        super().__init__("Powerup Mode")
        self.spawn_timer: float = 0.0
        self.active_orbs: List[PowerupOrb] = []
        self.player_powerups: Dict[int, Optional[str]] = {1: None, 2: None}
        self.lasers: List[LaserProjectile] = []
        self.ghost_armed_for_player: Optional[int] = None
        self.ball_reserve_timer: float = 0.0
        self.font: Optional[pygame.font.Font] = None

    def reset(self) -> None:
        self.spawn_timer = 0.0
        self.active_orbs.clear()
        self.player_powerups = {1: None, 2: None}
        self.lasers.clear()
        self.ghost_armed_for_player = None
        self.ball_reserve_timer = 0.0

    def update(self, dt: float) -> None:
        if not self.is_enabled:
            return

        # Delayed re-serve for ball destroyed by laser
        if self.ball_reserve_timer > 0.0:
            self.ball_reserve_timer -= dt
            if self.ball_reserve_timer <= 0.0 and self.game is not None:
                self.game.engine.reset_ball_neutral()

        # Update active orbs lifetime & remove expired
        self.active_orbs = [orb for orb in self.active_orbs if orb.update(dt)]

        # Periodic spawn timer up to MAX_ACTIVE_ORBS
        self.spawn_timer += dt
        if self.spawn_timer >= POWERUP_SPAWN_INTERVAL:
            self.spawn_timer = 0.0
            if len(self.active_orbs) < MAX_ACTIVE_ORBS:
                self._spawn_orb()

        # Update lasers
        surviving_lasers = []
        for laser in self.lasers:
            if laser.update(dt):
                if self._check_laser_collisions(laser):
                    continue  # Laser was consumed by hit
                surviving_lasers.append(laser)
        self.lasers = surviving_lasers

    def _spawn_orb(self) -> None:
        center_x = SCREEN_WIDTH * 0.5
        for _ in range(10):  # Try finding non-overlapping coordinate
            x = random.uniform(center_x - 140.0, center_x + 140.0)
            y = random.uniform(TOP_BOUND + 60.0, BOTTOM_BOUND - 60.0)
            # Ensure distance from other existing orbs
            if all(math.hypot(x - o.pos.x, y - o.pos.y) > 45.0 for o in self.active_orbs):
                ptype = random.choice(self.TYPES)
                self.active_orbs.append(PowerupOrb(x, y, ptype))
                break

    def activate_powerup(self, player_id: int) -> bool:
        """Activates stored powerup for the specified player."""
        if not self.is_enabled or self.game is None:
            return False

        ptype = self.player_powerups.get(player_id)
        if ptype is None:
            return False

        # Consume powerup from inventory
        self.player_powerups[player_id] = None

        if ptype == PowerupType.FREEZE:
            # Freezes opponent paddle for FREEZE_DURATION
            opponent = self.game.engine.right_paddle if player_id == 1 else self.game.engine.left_paddle
            opponent.frozen_timer = FREEZE_DURATION
            return True

        elif ptype == PowerupType.LASER:
            paddle = self.game.engine.left_paddle if player_id == 1 else self.game.engine.right_paddle
            direction = 1 if player_id == 1 else -1
            spawn_x = paddle.center_x + (paddle.width if player_id == 1 else -paddle.width)
            self.lasers.append(LaserProjectile(spawn_x, paddle.center_y, direction, player_id))
            return True

        elif ptype == PowerupType.GHOST_BALL:
            self.ghost_armed_for_player = player_id
            return True

        return False

    def _check_laser_collisions(self, laser: LaserProjectile) -> bool:
        """Checks laser intersection with ball or opponent paddle."""
        if self.game is None:
            return False

        ball = self.game.engine.ball
        opponent_id = 2 if laser.owner_player == 1 else 1
        opponent_paddle = self.game.engine.right_paddle if laser.owner_player == 1 else self.game.engine.left_paddle

        # 1. Check ball intersection
        dist_to_ball = math.hypot(laser.pos.x - ball.pos.x, laser.pos.y - ball.pos.y)
        if dist_to_ball <= (ball.radius + laser.width * 0.5):
            laser.active = False
            if hasattr(self.game, 'particle_mgr'):
                self.game.particle_mgr.spawn_burst(ball.pos.x, ball.pos.y, (255, 255, 200), count=40)
            ball.pos = Vector2D(-500.0, -500.0)
            ball.vel = Vector2D(0.0, 0.0)
            self.ball_reserve_timer = 0.4
            return True

        # 2. Check opponent paddle collision
        if check_aabb_intersection(laser.aabb, opponent_paddle.aabb):
            laser.active = False
            opponent_paddle.push(LASER_PUSH)
            if hasattr(self.game, 'particle_mgr'):
                self.game.particle_mgr.spawn_burst(laser.pos.x, laser.pos.y, COLOR_LASER_BEAM, count=25)
            return True

        return False

    def on_ball_update(self, ball: Ball, dt: float = 0.0) -> None:
        if not self.is_enabled:
            return

        # 1. Check collection of any active orb on court
        collected_orb: Optional[PowerupOrb] = None
        for orb in self.active_orbs:
            dist = math.hypot(ball.pos.x - orb.pos.x, ball.pos.y - orb.pos.y)
            if dist <= (ball.radius + orb.radius):
                collector = ball.last_hit_player
                # Collect only if collector is known and has empty inventory
                if collector in (1, 2) and self.player_powerups[collector] is None:
                    self.player_powerups[collector] = orb.ptype
                    if self.game is not None and hasattr(self.game, 'particle_mgr'):
                        self.game.particle_mgr.spawn_burst(
                            orb.pos.x, orb.pos.y,
                            orb.color, count=35
                        )
                    collected_orb = orb
                    break

        if collected_orb is not None:
            self.active_orbs.remove(collected_orb)

        # 2. Check Ghost Ball mechanics
        if self.ghost_armed_for_player is not None:
            center_x = SCREEN_WIDTH * 0.5

            if self.ghost_armed_for_player == 1 and ball.vel.x > 0:
                dist_to_net = center_x - ball.pos.x
                if 0 < dist_to_net <= ball.speed * GHOST_BALL_WINDOW:
                    ball.is_visible = False
                elif ball.pos.x >= center_x:
                    ball.is_visible = True
                    self.ghost_armed_for_player = None

            elif self.ghost_armed_for_player == 2 and ball.vel.x < 0:
                dist_to_net = ball.pos.x - center_x
                if 0 < dist_to_net <= ball.speed * GHOST_BALL_WINDOW:
                    ball.is_visible = False
                elif ball.pos.x <= center_x:
                    ball.is_visible = True
                    self.ghost_armed_for_player = None
        else:
            ball.is_visible = True

    def on_round_start(self) -> None:
        if self.game is not None:
            self.game.engine.ball.is_visible = True
        self.ghost_armed_for_player = None

    def on_round_end(self) -> None:
        """
        Called when a point is scored.
        Active court orbs and stored powerups stay on the field across round ends.
        """
        if not POWERUP_CARRYOVER_BETWEEN_ROUNDS:
            self.player_powerups = {1: None, 2: None}
        # Note: self.active_orbs is intentionally retained!
        self.lasers.clear()
        self.ghost_armed_for_player = None
        if self.game is not None:
            self.game.engine.ball.is_visible = True

    def disable(self) -> None:
        super().disable()
        if self.game is not None:
            self.game.engine.ball.is_visible = True
            self.game.engine.left_paddle.frozen_timer = 0.0
            self.game.engine.right_paddle.frozen_timer = 0.0
        self.reset()

    def draw(self, renderer: pygame.Surface) -> None:
        if not self.is_enabled:
            return

        if self.font is None:
            self.font = pygame.font.SysFont("Consolas", 14, bold=True)

        # 1. Draw all active orbs
        for orb in self.active_orbs:
            orb.draw(renderer, self.font)

        # 2. Draw Lasers
        for laser in self.lasers:
            laser.draw(renderer)

        # 3. Draw Paddle Freezing Overlays
        if self.game is not None:
            for paddle in (self.game.engine.left_paddle, self.game.engine.right_paddle):
                if paddle.frozen_timer > 0:
                    box = paddle.aabb
                    # Ice tint overlay
                    ice_surf = pygame.Surface((box.width + 8, box.height + 8), pygame.SRCALPHA)
                    ice_surf.fill((*COLOR_ICE_TINT, 140))
                    renderer.blit(ice_surf, (box.min_x - 4, box.min_y - 4))
                    pygame.draw.rect(
                        renderer, (200, 240, 255),
                        pygame.Rect(box.min_x - 4, box.min_y - 4, box.width + 8, box.height + 8),
                        width=2, border_radius=4
                    )
                    # Timer bar
                    timer_ratio = paddle.frozen_timer / FREEZE_DURATION
                    bar_w = int((box.width + 8) * timer_ratio)
                    pygame.draw.rect(
                        renderer, (255, 255, 255),
                        pygame.Rect(box.min_x - 4, box.min_y - 10, bar_w, 4)
                    )

        # 4. Draw Stored Powerup Badges in HUD
        center_x = SCREEN_WIDTH // 2
        
        # P1 Badge (Left of scoreboard)
        p1_ptype = self.player_powerups.get(1)
        if p1_ptype:
            self._draw_powerup_badge(renderer, p1_ptype, center_x - 110, int(TOP_BOUND) + 26, "P1 [D]")

        # P2 Badge (Right of scoreboard)
        p2_ptype = self.player_powerups.get(2)
        if p2_ptype:
            self._draw_powerup_badge(renderer, p2_ptype, center_x + 110, int(TOP_BOUND) + 26, "P2 [<-]")

    def _draw_powerup_badge(self, surface: pygame.Surface, ptype: str, x: int, y: int, key_hint: str) -> None:
        color = COLOR_ORB_FREEZE if ptype == PowerupType.FREEZE else (
            COLOR_ORB_LASER if ptype == PowerupType.LASER else COLOR_ORB_GHOST
        )
        badge_rect = pygame.Rect(x - 28, y - 14, 56, 28)
        pygame.draw.rect(surface, (18, 22, 34), badge_rect, border_radius=4)
        pygame.draw.rect(surface, color, badge_rect, width=2, border_radius=4)

        tag = "ICE" if ptype == PowerupType.FREEZE else ("LSR" if ptype == PowerupType.LASER else "GST")
        tag_surf = self.font.render(tag, True, color)
        surface.blit(tag_surf, tag_surf.get_rect(center=badge_rect.center))

        hint_surf = self.font.render(key_hint, True, (140, 160, 190))
        surface.blit(hint_surf, (x - hint_surf.get_width() // 2, y + 16))
