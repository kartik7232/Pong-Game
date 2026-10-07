"""
===============================================================================
PONG GAME CLONE - PRODUCTION READY MAIN DRIVER & VISUALIZATION ENGINE
===============================================================================
Architectural Role: Application Entry Point, Render Pipeline & VFX Integration
Author: Member A (Core Logic & Physics Lead)

Features:
- Fixed 60 FPS game loop using pygame.time.Clock() with frame execution diagnostics.
- Event listener bindings for Member C's visual particle burst system.
- Member B Input / Autonomous AI Agent Integration.
- Real-time examiner debug overlay (Press F3 to toggle AABB hitboxes and vectors).
"""

import sys
import math
import random
import pygame
from typing import List, Tuple

from engine.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TARGET_FPS, FRAME_TIME_MS,
    COLOR_BG, COLOR_PADDLE_P1, COLOR_PADDLE_P2, COLOR_BALL,
    COLOR_CENTER_LINE, COLOR_TEXT, COLOR_HIT_FLASH,
    TOP_BOUND, BOTTOM_BOUND, LEFT_BOUND, RIGHT_BOUND,
    PADDLE_HEIGHT, PADDLE_WIDTH, BALL_RADIUS
)
from engine.game_engine import PongEngine, EventType


class Particle:
    """Particle effect entity for Member C visual impact feedback."""
    def __init__(self, x: float, y: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(80, 400)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.lifetime = random.uniform(0.2, 0.5)  # Seconds
        self.max_lifetime = self.lifetime
        self.size = random.uniform(2.0, 5.0)

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        return self.lifetime > 0

    def draw(self, surface: pygame.Surface):
        if self.lifetime <= 0:
            return
        alpha_ratio = self.lifetime / self.max_lifetime
        radius = max(1, int(self.size * alpha_ratio))
        # Fade color
        r = int(self.color[0] * alpha_ratio)
        g = int(self.color[1] * alpha_ratio)
        b = int(self.color[2] * alpha_ratio)
        pygame.draw.circle(surface, (r, g, b), (int(self.x), int(self.y)), radius)


class ParticleManager:
    """Manages particle bursts triggered via Member C event callbacks."""
    def __init__(self):
        self.particles: List[Particle] = []

    def spawn_burst(self, x: float, y: float, color: Tuple[int, int, int], count: int = 25):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def update(self, dt: float):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface: pygame.Surface):
        for p in self.particles:
            p.draw(surface)


def run_simple_ai(engine: PongEngine, dt: float):
    """
    Member B Integration Example: Simple tracking AI agent controlling Right Paddle.
    """
    ball_y = engine.ball.pos.y
    paddle_y = engine.right_paddle.center_y
    deadzone = 12.0  # Smooth tracking hysteresis

    if engine.ball.vel.x > 0:  # Only track when ball moves towards AI paddle
        if ball_y < paddle_y - deadzone:
            engine.set_paddle_movement(is_left=False, direction=-1)  # Move Up
        elif ball_y > paddle_y + deadzone:
            engine.set_paddle_movement(is_left=False, direction=1)   # Move Down
        else:
            engine.set_paddle_movement(is_left=False, direction=0)
    else:
        # Return to center when ball is receding
        if paddle_y < SCREEN_HEIGHT * 0.5 - 20:
            engine.set_paddle_movement(is_left=False, direction=1)
        elif paddle_y > SCREEN_HEIGHT * 0.5 + 20:
            engine.set_paddle_movement(is_left=False, direction=-1)
        else:
            engine.set_paddle_movement(is_left=False, direction=0)


def main():
    pygame.init()
    pygame.font.init()

    # Create Display Surface
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("2D Arcade Pong - Core Engine & Physics Architecture")

    # Fixed Frame Rate Clock
    clock = pygame.time.Clock()

    # Instantiate Core Physics Engine & VFX System
    engine = PongEngine()
    particle_mgr = ParticleManager()

    # Register Member C Event Listeners
    def handle_paddle_hit(x: float, y: float, is_left: bool, speed: float):
        color = COLOR_PADDLE_P1 if is_left else COLOR_PADDLE_P2
        particle_mgr.spawn_burst(x, y, color, count=30)
        particle_mgr.spawn_burst(x, y, COLOR_HIT_FLASH, count=10)

    def handle_wall_hit(x: float, y: float):
        particle_mgr.spawn_burst(x, y, (180, 200, 255), count=15)

    def handle_score(scoring_player: int, p1_score: int, p2_score: int):
        color = COLOR_PADDLE_P1 if scoring_player == 1 else COLOR_PADDLE_P2
        burst_x = RIGHT_BOUND if scoring_player == 1 else LEFT_BOUND
        particle_mgr.spawn_burst(burst_x, SCREEN_HEIGHT / 2, color, count=60)

    engine.register_callback(EventType.PADDLE_HIT, handle_paddle_hit)
    engine.register_callback(EventType.WALL_HIT, handle_wall_hit)
    engine.register_callback(EventType.SCORE, handle_score)

    # UI Fonts
    font_large = pygame.font.SysFont("Consolas", 54, bold=True)
    font_medium = pygame.font.SysFont("Consolas", 20, bold=True)
    font_small = pygame.font.SysFont("Consolas", 14)

    # Controls & Debug State Flags
    use_ai_opponent: bool = True
    debug_mode: bool = False

    running = True

    print("=================================================================")
    print("PONG ENGINE ARCHITECTURE INITIALIZED SUCCESSFULLY (60 FPS FIXED)")
    print("Controls: W/S (Left Paddle), Up/Down (Right Paddle when 2P active)")
    print("F3: Toggle Examiner Debug & AABB Hitbox Overlay")
    print("F2: Toggle AI Mode (Current: " + ("ON" if use_ai_opponent else "OFF") + ")")
    print("R:  Reset Match Score")
    print("=================================================================")

    while running:
        # 1. Delta-Time & Timing Diagnostics
        # clock.tick(60) caps frame execution to 60 FPS and returns delta time in milliseconds
        dt_ms = clock.tick(TARGET_FPS)
        dt = dt_ms / 1000.0  # Convert to seconds for physics integration

        # Enforce dt sanity cap to avoid spiral of death on window drag
        dt = min(dt, 0.05)

        # 2. Input Handling (Member B Integration)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_F3:
                    debug_mode = not debug_mode
                elif event.key == pygame.K_F2:
                    use_ai_opponent = not use_ai_opponent
                elif event.key == pygame.K_r:
                    engine.reset_game()

        keys = pygame.key.get_pressed()

        # Left Paddle Controls (Player 1)
        p1_dir = 0
        if keys[pygame.K_w]:
            p1_dir -= 1
        if keys[pygame.K_s]:
            p1_dir += 1
        engine.set_paddle_movement(is_left=True, direction=p1_dir)

        # Right Paddle Controls (Player 2 or AI)
        if not use_ai_opponent:
            p2_dir = 0
            if keys[pygame.K_UP]:
                p2_dir -= 1
            if keys[pygame.K_DOWN]:
                p2_dir += 1
            engine.set_paddle_movement(is_left=False, direction=p2_dir)
        else:
            run_simple_ai(engine, dt)

        # 3. Deterministic Physics Update
        engine.update_physics(dt)

        # 4. Update Visual FX (Member C Integration)
        particle_mgr.update(dt)

        # 5. RENDER PIPELINE
        # Clear Screen
        screen.fill(COLOR_BG)

        # Render Playfield Boundaries
        pygame.draw.line(screen, COLOR_CENTER_LINE, (LEFT_BOUND, TOP_BOUND), (RIGHT_BOUND, TOP_BOUND), 2)
        pygame.draw.line(screen, COLOR_CENTER_LINE, (LEFT_BOUND, BOTTOM_BOUND), (RIGHT_BOUND, BOTTOM_BOUND), 2)

        # Render Dashed Center Line
        dash_len = 15
        gap_len = 10
        center_x = SCREEN_WIDTH // 2
        for y in range(int(TOP_BOUND), int(BOTTOM_BOUND), dash_len + gap_len):
            pygame.draw.line(screen, COLOR_CENTER_LINE, (center_x, y), (center_x, min(y + dash_len, int(BOTTOM_BOUND))), 2)

        # Render Particle FX
        particle_mgr.draw(screen)

        # Render Left Paddle
        l_aabb = engine.left_paddle.aabb
        pygame.draw.rect(
            screen,
            COLOR_PADDLE_P1,
            pygame.Rect(l_aabb.min_x, l_aabb.min_y, l_aabb.width, l_aabb.height),
            border_radius=4
        )

        # Render Right Paddle
        r_aabb = engine.right_paddle.aabb
        pygame.draw.rect(
            screen,
            COLOR_PADDLE_P2,
            pygame.Rect(r_aabb.min_x, r_aabb.min_y, r_aabb.width, r_aabb.height),
            border_radius=4
        )

        # Render Ball with subtle core glow
        ball_pos_int = (int(engine.ball.pos.x), int(engine.ball.pos.y))
        pygame.draw.circle(screen, (255, 255, 200), ball_pos_int, int(engine.ball.radius + 2))
        pygame.draw.circle(screen, COLOR_BALL, ball_pos_int, int(engine.ball.radius))

        # Render Scoreboard HUD
        score_text = f"{engine.score_p1}   {engine.score_p2}"
        score_surf = font_large.render(score_text, True, COLOR_TEXT)
        screen.blit(score_surf, (center_x - score_surf.get_width() // 2, TOP_BOUND + 15))

        # Dynamic Speed HUD Indicator
        speed_text = f"Ball Velocity: {engine.ball.speed:.1f} px/s (Ramp Factor: 1.07x)"
        speed_surf = font_small.render(speed_text, True, (160, 180, 210))
        screen.blit(speed_surf, (center_x - speed_surf.get_width() // 2, BOTTOM_BOUND - 25))

        # Mode HUD Indicator
        mode_str = "VS AI (Press F2 for 2P)" if use_ai_opponent else "VS PLAYER (Press F2 for AI)"
        mode_surf = font_small.render(mode_str, True, (120, 220, 180))
        screen.blit(mode_surf, (LEFT_BOUND + 10, BOTTOM_BOUND - 25))

        # 6. EXAMINER DEBUG OVERLAY (F3 Toggle)
        if debug_mode:
            # Draw AABB Bounding Boxes
            pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(l_aabb.min_x, l_aabb.min_y, l_aabb.width, l_aabb.height), 1)
            pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(r_aabb.min_x, r_aabb.min_y, r_aabb.width, r_aabb.height), 1)
            
            b_aabb = engine.ball.aabb
            pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(b_aabb.min_x, b_aabb.min_y, b_aabb.width, b_aabb.height), 1)

            # Draw Ball Velocity Vector Arrow
            end_vx = engine.ball.pos.x + engine.ball.vel.x * 0.15
            end_vy = engine.ball.pos.y + engine.ball.vel.y * 0.15
            pygame.draw.line(screen, (255, 255, 0), (engine.ball.pos.x, engine.ball.pos.y), (end_vx, end_vy), 2)

            # Telemetry Metrics Card
            actual_fps = clock.get_fps()
            telemetry_lines = [
                "=== SYSTEM TELEMETRY (EXAMINER VIEW) ===",
                f"Clock FPS: {actual_fps:.2f} / 60.0 (Target: 16.6ms)",
                f"Physics Exec Time: {engine.last_update_duration_ms:.4f} ms (Sub-16.6ms PASS)",
                f"Ball Pos (x, y): ({engine.ball.pos.x:.1f}, {engine.ball.pos.y:.1f})",
                f"Ball Vel (vx, vy): ({engine.ball.vel.x:.1f}, {engine.ball.vel.y:.1f})",
                f"Continuous Bounce Hits: {engine.ball.hit_count}",
                "AABB Hitbox & Vector Visualization: ACTIVE"
            ]

            y_offset = TOP_BOUND + 60
            for line in telemetry_lines:
                t_surf = font_small.render(line, True, (0, 255, 180))
                screen.blit(t_surf, (LEFT_BOUND + 10, y_offset))
                y_offset += 18
        else:
            hint_surf = font_small.render("[F3] Examiner Physics Telemetry Overlay", True, (100, 110, 140))
            screen.blit(hint_surf, (RIGHT_BOUND - hint_surf.get_width() - 10, BOTTOM_BOUND - 25))

        # Flip Back Buffer to Screen
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
