"""
===============================================================================
PONG GAME CLONE - PRODUCTION READY MAIN DRIVER & SCENE MANAGER
===============================================================================
Architectural Role: Application Entry Point, Scene State Machine & Game Coordinator
Author: Member A (Core Logic & Physics Lead)

Features:
- Scene State Machine: MAIN_MENU, PLAYING, PAUSED, GAME_OVER, TUTORIAL, EXIT_CONFIRM.
- 4 Modular Selectable Game Modes: Wind Mode, Portals, Powerups, Chaos Mode.
- Full Keyboard (Up/Down/Enter/Esc) & Pointer Mouse navigation.
- Fixed 60 FPS delta-time physics and visual particle burst engine.
- Real-time examiner debug overlay (Press F3 to toggle hitboxes and telemetry).
"""

import sys
import math
import random
import asyncio
import pygame
from typing import List, Tuple, Optional

from engine.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TARGET_FPS, FRAME_TIME_MS,
    COLOR_BG, COLOR_PADDLE_P1, COLOR_PADDLE_P2, COLOR_BALL,
    COLOR_CENTER_LINE, COLOR_TEXT, COLOR_HIT_FLASH,
    COLOR_MENU_SELECTED, COLOR_MENU_UNSELECTED, COLOR_MENU_ACCENT,
    COLOR_MODAL_BG, COLOR_HUD_MUTED,
    TOP_BOUND, BOTTOM_BOUND, LEFT_BOUND, RIGHT_BOUND,
    PADDLE_HEIGHT, PADDLE_WIDTH, BALL_RADIUS,
    WINNING_SCORE,
    KEY_P1_UP, KEY_P1_DOWN, KEY_P1_ACTIVATE,
    KEY_P2_UP, KEY_P2_DOWN, KEY_P2_ACTIVATE
)
from engine.game_engine import PongEngine, EventType
from engine.state import SceneState
from engine.ui import Menu
from engine.tutorial import TutorialViewer
from engine.modes.mode_manager import ModeManager
from engine.modes.wind_mode import WindMode
from engine.modes.portal_mode import PortalMode
from engine.modes.powerup_mode import PowerupMode
from engine.modes.chaos_mode import ChaosMode


class Particle:
    """Particle effect entity for visual impact feedback."""
    def __init__(self, x: float, y: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(80, 400)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.lifetime = random.uniform(0.2, 0.5)
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
        r = int(self.color[0] * alpha_ratio)
        g = int(self.color[1] * alpha_ratio)
        b = int(self.color[2] * alpha_ratio)
        pygame.draw.circle(surface, (r, g, b), (int(self.x), int(self.y)), radius)


class ParticleManager:
    """Manages particle bursts triggered via event callbacks."""
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


class PongGameApp:
    """
    Central Game Application Coordinator.
    Manages scene transitions, menus, mode orchestrations, and rendering.
    """
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("2D Arcade Pong - Extended Edition")
        self.clock: pygame.time.Clock = pygame.time.Clock()

        # Core subsystems
        self.engine: PongEngine = PongEngine()
        self.particle_mgr: ParticleManager = ParticleManager()
        self.mode_manager: ModeManager = ModeManager()

        # Instantiate self-contained game modes
        self.wind_mode: WindMode = WindMode()
        self.portal_mode: PortalMode = PortalMode()
        self.powerup_mode: PowerupMode = PowerupMode()
        self.chaos_mode: ChaosMode = ChaosMode(self.wind_mode, self.portal_mode, self.powerup_mode)

        # Initialize modes with game context reference
        for m in (self.wind_mode, self.portal_mode, self.powerup_mode, self.chaos_mode):
            m.init(self)

        # UI & Scene Managers
        self.scene: SceneState = SceneState.MAIN_MENU
        self.tutorial_viewer: TutorialViewer = TutorialViewer()

        # Main Menu (In exact requested order: 1. Wind, 2. Portals, 3. Powerups, 4. Chaos, 5. Tutorial, 6. Exit)
        self.main_menu: Menu = Menu([
            ("1. Wind Mode", "MODE_WIND"),
            ("2. Portals", "MODE_PORTALS"),
            ("3. Powerup Mode", "MODE_POWERUPS"),
            ("4. Chaos Mode", "MODE_CHAOS"),
            ("5. Tutorial", "TUTORIAL"),
            ("6. Exit", "EXIT")
        ], start_y=210, spacing=52)

        # Player Select Menu (One Player vs Two Player)
        self.pending_mode_id: str = "MODE_WIND"
        self.player_select_menu: Menu = Menu([
            ("1. One Player (vs AI)", "ONE_PLAYER"),
            ("2. Two Player (Local 1v1)", "TWO_PLAYER")
        ], start_y=260, spacing=60)

        # Pause Menu
        self.pause_menu: Menu = Menu([
            ("Resume", "RESUME"),
            ("Restart", "RESTART"),
            ("Back to Main Menu", "MAIN_MENU")
        ], start_y=250, spacing=54)

        # Game Over Menu
        self.game_over_menu: Menu = Menu([
            ("Rematch", "REMATCH"),
            ("Back to Main Menu", "MAIN_MENU")
        ], start_y=320, spacing=56)

        # Exit Confirm Menu
        self.exit_confirm_menu: Menu = Menu([
            ("Yes, Quit", "CONFIRM_QUIT"),
            ("No, Stay", "CANCEL_QUIT")
        ], start_y=290, spacing=56)

        # Fonts
        self.font_large = pygame.font.SysFont("Consolas", 54, bold=True)
        self.font_title = pygame.font.SysFont("Consolas", 36, bold=True)
        self.font_medium = pygame.font.SysFont("Consolas", 20, bold=True)
        self.font_small = pygame.font.SysFont("Consolas", 14)

        # Settings & State Flags
        self.use_ai_opponent: bool = True
        self.debug_mode: bool = False
        self.running: bool = True
        self.winner_id: int = 0
        self.ai_powerup_timer: float = 0.0

        # Register callbacks
        self._setup_event_callbacks()

    def _setup_event_callbacks(self) -> None:
        def on_paddle_hit(x: float, y: float, is_left: bool, speed: float):
            col = COLOR_PADDLE_P1 if is_left else COLOR_PADDLE_P2
            self.particle_mgr.spawn_burst(x, y, col, count=30)
            self.particle_mgr.spawn_burst(x, y, COLOR_HIT_FLASH, count=10)

        def on_wall_hit(x: float, y: float):
            self.particle_mgr.spawn_burst(x, y, (180, 200, 255), count=15)

        def on_score(scoring_player: int, p1_score: int, p2_score: int):
            col = COLOR_PADDLE_P1 if scoring_player == 1 else COLOR_PADDLE_P2
            burst_x = RIGHT_BOUND if scoring_player == 1 else LEFT_BOUND
            self.particle_mgr.spawn_burst(burst_x, SCREEN_HEIGHT / 2, col, count=60)
            
            # Hook mode round end / start
            self.mode_manager.on_round_end()
            self.mode_manager.on_round_start()

            # Win condition check
            if p1_score >= WINNING_SCORE:
                self.winner_id = 1
                self.scene = SceneState.GAME_OVER
            elif p2_score >= WINNING_SCORE:
                self.winner_id = 2
                self.scene = SceneState.GAME_OVER

        self.engine.register_callback(EventType.PADDLE_HIT, on_paddle_hit)
        self.engine.register_callback(EventType.WALL_HIT, on_wall_hit)
        self.engine.register_callback(EventType.SCORE, on_score)

    def start_match(self, mode_id: str) -> None:
        """Configures the selected mode and starts a fresh match."""
        if mode_id == "MODE_WIND":
            self.mode_manager.set_mode(self.wind_mode)
        elif mode_id == "MODE_PORTALS":
            self.mode_manager.set_mode(self.portal_mode)
        elif mode_id == "MODE_POWERUPS":
            self.mode_manager.set_mode(self.powerup_mode)
        elif mode_id == "MODE_CHAOS":
            self.mode_manager.set_mode(self.chaos_mode)
        else:
            self.mode_manager.set_mode(None)

        self.engine.reset_game()
        self.winner_id = 0
        self.ai_powerup_timer = 0.0
        self.scene = SceneState.PLAYING

    def run_ai_opponent(self, dt: float) -> None:
        """Tracking AI controlling Right Paddle with smart powerup activation."""
        ball_y = self.engine.ball.pos.y
        paddle_y = self.engine.right_paddle.center_y
        deadzone = 12.0

        if self.engine.ball.vel.x > 0:
            if ball_y < paddle_y - deadzone:
                self.engine.set_paddle_movement(is_left=False, direction=-1)
            elif ball_y > paddle_y + deadzone:
                self.engine.set_paddle_movement(is_left=False, direction=1)
            else:
                self.engine.set_paddle_movement(is_left=False, direction=0)
        else:
            if paddle_y < SCREEN_HEIGHT * 0.5 - 20:
                self.engine.set_paddle_movement(is_left=False, direction=1)
            elif paddle_y > SCREEN_HEIGHT * 0.5 + 20:
                self.engine.set_paddle_movement(is_left=False, direction=-1)
            else:
                self.engine.set_paddle_movement(is_left=False, direction=0)

        # AI Powerup activation logic
        self.ai_powerup_timer += dt
        if self.ai_powerup_timer >= 2.5:
            self.ai_powerup_timer = 0.0
            if self.powerup_mode.is_enabled and self.powerup_mode.player_powerups.get(2) is not None:
                self.powerup_mode.activate_powerup(2)

    def run(self) -> None:
        """Main application lifecycle loop."""
        while self.running:
            dt_ms = self.clock.tick(TARGET_FPS)
            dt = min(dt_ms / 1000.0, 0.05)

            # Process Events & Input
            self._handle_events()

            # Update State
            self._update(dt)

            # Render Scene
            self._render()

            pygame.display.flip()

        pygame.quit()
        if sys.platform != "emscripten":
            sys.exit(0)

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            # Scene 1: MAIN MENU
            if self.scene == SceneState.MAIN_MENU:
                action = self.main_menu.handle_event(event)
                if action in ("MODE_WIND", "MODE_PORTALS", "MODE_POWERUPS", "MODE_CHAOS"):
                    self.pending_mode_id = action
                    self.player_select_menu.selected_index = 0
                    self.scene = SceneState.PLAYER_SELECT
                elif action == "TUTORIAL":
                    self.scene = SceneState.TUTORIAL
                elif action == "EXIT":
                    self.scene = SceneState.EXIT_CONFIRM

            # Scene 1B: PLAYER SELECT (One Player vs Two Player)
            elif self.scene == SceneState.PLAYER_SELECT:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.scene = SceneState.MAIN_MENU
                else:
                    action = self.player_select_menu.handle_event(event)
                    if action == "ONE_PLAYER":
                        self.use_ai_opponent = True
                        self.start_match(self.pending_mode_id)
                    elif action == "TWO_PLAYER":
                        self.use_ai_opponent = False
                        self.start_match(self.pending_mode_id)

            # Scene 2: PLAYING
            elif self.scene == SceneState.PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.scene = SceneState.PAUSED
                    elif event.key == pygame.K_F3:
                        self.debug_mode = not self.debug_mode
                    elif event.key == pygame.K_F2:
                        self.use_ai_opponent = not self.use_ai_opponent
                    elif event.key == pygame.K_r:
                        self.engine.reset_game()
                        self.mode_manager.reset()
                    # Player 1 Activate Powerup
                    elif event.key == KEY_P1_ACTIVATE:
                        if self.powerup_mode.is_enabled:
                            self.powerup_mode.activate_powerup(1)
                    # Player 2 Activate Powerup (when not AI)
                    elif event.key == KEY_P2_ACTIVATE and not self.use_ai_opponent:
                        if self.powerup_mode.is_enabled:
                            self.powerup_mode.activate_powerup(2)

            # Scene 3: PAUSED
            elif self.scene == SceneState.PAUSED:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.scene = SceneState.PLAYING
                else:
                    action = self.pause_menu.handle_event(event)
                    if action == "RESUME":
                        self.scene = SceneState.PLAYING
                    elif action == "RESTART":
                        self.engine.reset_game()
                        self.mode_manager.reset()
                        self.scene = SceneState.PLAYING
                    elif action == "MAIN_MENU":
                        self.mode_manager.disable_all()
                        self.scene = SceneState.MAIN_MENU

            # Scene 4: GAME OVER
            elif self.scene == SceneState.GAME_OVER:
                action = self.game_over_menu.handle_event(event)
                if action == "REMATCH":
                    self.engine.reset_game()
                    self.mode_manager.reset()
                    self.scene = SceneState.PLAYING
                elif action == "MAIN_MENU":
                    self.mode_manager.disable_all()
                    self.scene = SceneState.MAIN_MENU

            # Scene 5: TUTORIAL
            elif self.scene == SceneState.TUTORIAL:
                action = self.tutorial_viewer.handle_event(event)
                if action == "BACK":
                    self.scene = SceneState.MAIN_MENU

            # Scene 6: EXIT CONFIRM
            elif self.scene == SceneState.EXIT_CONFIRM:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.scene = SceneState.MAIN_MENU
                else:
                    action = self.exit_confirm_menu.handle_event(event)
                    if action == "CONFIRM_QUIT":
                        self.running = False
                    elif action == "CANCEL_QUIT":
                        self.scene = SceneState.MAIN_MENU

        # Continuous Keyboard Polling during PLAYING
        if self.scene == SceneState.PLAYING:
            keys = pygame.key.get_pressed()
            # Player 1 translation
            p1_dir = 0
            if keys[KEY_P1_UP]:
                p1_dir -= 1
            if keys[KEY_P1_DOWN]:
                p1_dir += 1
            self.engine.set_paddle_movement(is_left=True, direction=p1_dir)

            # Player 2 translation
            if not self.use_ai_opponent:
                p2_dir = 0
                if keys[KEY_P2_UP]:
                    p2_dir -= 1
                if keys[KEY_P2_DOWN]:
                    p2_dir += 1
                self.engine.set_paddle_movement(is_left=False, direction=p2_dir)

    def _update(self, dt: float) -> None:
        if self.scene == SceneState.PLAYING:
            # AI Opponent
            if self.use_ai_opponent:
                self.run_ai_opponent(dt)

            # 1. Update active modes before physics kinematics
            self.mode_manager.update(dt)

            # 2. Update core physics integration
            self.engine.update_physics(dt)

            # 3. Hook ball state to active modes (Wind force, Portals swept collision, Powerups)
            self.mode_manager.on_ball_update(self.engine.ball, dt)

            # 4. Update Particle VFX
            self.particle_mgr.update(dt)

        elif self.scene == SceneState.TUTORIAL:
            self.tutorial_viewer.update(dt)

    def _render(self) -> None:
        self.screen.fill(COLOR_BG)

        if self.scene == SceneState.MAIN_MENU:
            self._render_main_menu()

        elif self.scene == SceneState.PLAYER_SELECT:
            self._render_player_select()

        elif self.scene == SceneState.PLAYING:
            self._render_playfield()

        elif self.scene == SceneState.PAUSED:
            self._render_playfield()
            self._render_pause_overlay()

        elif self.scene == SceneState.GAME_OVER:
            self._render_playfield()
            self._render_game_over_overlay()

        elif self.scene == SceneState.TUTORIAL:
            self.tutorial_viewer.draw(self.screen)

        elif self.scene == SceneState.EXIT_CONFIRM:
            self._render_main_menu()
            self._render_exit_confirm_modal()

    def _get_mode_display_name(self, mode_id: str) -> str:
        mapping = {
            "MODE_WIND": "WIND MODE",
            "MODE_PORTALS": "PORTALS",
            "MODE_POWERUPS": "POWERUP MODE",
            "MODE_CHAOS": "CHAOS MODE"
        }
        return mapping.get(mode_id, "PONG MATCH")

    def _render_player_select(self) -> None:
        center_x = SCREEN_WIDTH // 2

        # Title
        title_surf = self.font_large.render("SELECT PLAYERS", True, COLOR_MENU_SELECTED)
        self.screen.blit(title_surf, (center_x - title_surf.get_width() // 2, 80))

        # Subtitle displaying chosen mode
        mode_name = self._get_mode_display_name(self.pending_mode_id)
        sub_text = f"Selected Match: {mode_name}"
        sub_surf = self.font_medium.render(sub_text, True, COLOR_MENU_ACCENT)
        self.screen.blit(sub_surf, (center_x - sub_surf.get_width() // 2, 160))

        # Render menu
        self.player_select_menu.draw(self.screen)

        # Footer Hint
        hint_surf = self.font_small.render("[Esc] Back to Main Menu  |  [Up / Down / Enter] or Mouse to Select", True, COLOR_HUD_MUTED)
        self.screen.blit(hint_surf, (center_x - hint_surf.get_width() // 2, SCREEN_HEIGHT - 50))

    def _render_main_menu(self) -> None:
        center_x = SCREEN_WIDTH // 2

        # Title Banner
        title_surf = self.font_large.render("PONG: ARCADE EVOLUTION", True, COLOR_MENU_SELECTED)
        self.screen.blit(title_surf, (center_x - title_surf.get_width() // 2, 70))

        sub_surf = self.font_medium.render("SELECT GAME MODE OR TUTORIAL", True, COLOR_MENU_UNSELECTED)
        self.screen.blit(sub_surf, (center_x - sub_surf.get_width() // 2, 140))

        # Render Main Menu
        self.main_menu.draw(self.screen)

        # Footer Hint
        hint_surf = self.font_small.render("Use [Up / Down / Enter] or Mouse to Select", True, COLOR_HUD_MUTED)
        self.screen.blit(hint_surf, (center_x - hint_surf.get_width() // 2, SCREEN_HEIGHT - 40))

    def _render_playfield(self) -> None:
        center_x = SCREEN_WIDTH // 2

        # Playfield Boundaries
        pygame.draw.line(self.screen, COLOR_CENTER_LINE, (LEFT_BOUND, TOP_BOUND), (RIGHT_BOUND, TOP_BOUND), 2)
        pygame.draw.line(self.screen, COLOR_CENTER_LINE, (LEFT_BOUND, BOTTOM_BOUND), (RIGHT_BOUND, BOTTOM_BOUND), 2)

        # Center Dashed Line
        dash_len = 15
        gap_len = 10
        for y in range(int(TOP_BOUND), int(BOTTOM_BOUND), dash_len + gap_len):
            pygame.draw.line(self.screen, COLOR_CENTER_LINE, (center_x, y), (center_x, min(y + dash_len, int(BOTTOM_BOUND))), 2)

        # Draw Active Mode Visuals (Wind streaks, Portals, Powerups, Chaos banners)
        self.mode_manager.draw(self.screen)

        # Particles
        self.particle_mgr.draw(self.screen)

        # Render Left Paddle (P1)
        l_aabb = self.engine.left_paddle.aabb
        pygame.draw.rect(
            self.screen, COLOR_PADDLE_P1,
            pygame.Rect(l_aabb.min_x, l_aabb.min_y, l_aabb.width, l_aabb.height),
            border_radius=4
        )

        # Render Right Paddle (P2)
        r_aabb = self.engine.right_paddle.aabb
        pygame.draw.rect(
            self.screen, COLOR_PADDLE_P2,
            pygame.Rect(r_aabb.min_x, r_aabb.min_y, r_aabb.width, r_aabb.height),
            border_radius=4
        )

        # Render Ball (taking into account Ghost Ball invisibility)
        if self.engine.ball.is_visible:
            ball_pos_int = (int(self.engine.ball.pos.x), int(self.engine.ball.pos.y))
            pygame.draw.circle(self.screen, (255, 255, 200), ball_pos_int, int(self.engine.ball.radius + 2))
            pygame.draw.circle(self.screen, COLOR_BALL, ball_pos_int, int(self.engine.ball.radius))
        else:
            # Ghost effect: subtle faint indicator
            ball_pos_int = (int(self.engine.ball.pos.x), int(self.engine.ball.pos.y))
            ghost_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(ghost_surf, (200, 150, 255, 40), (15, 15), int(self.engine.ball.radius))
            self.screen.blit(ghost_surf, (ball_pos_int[0] - 15, ball_pos_int[1] - 15))

        # Scoreboard
        score_text = f"{self.engine.score_p1}   {self.engine.score_p2}"
        score_surf = self.font_large.render(score_text, True, COLOR_TEXT)
        self.screen.blit(score_surf, (center_x - score_surf.get_width() // 2, TOP_BOUND + 15))

        # Mode HUD Banner
        mode_badge = f"MODE: {self.mode_manager.current_mode_name.upper()}"
        mode_badge_surf = self.font_small.render(mode_badge, True, COLOR_MENU_SELECTED)
        self.screen.blit(mode_badge_surf, (center_x - mode_badge_surf.get_width() // 2, TOP_BOUND + 74))

        # Ball Velocity HUD
        speed_text = f"Ball Velocity: {self.engine.ball.speed:.1f} px/s (Cap: 1200)"
        speed_surf = self.font_small.render(speed_text, True, (160, 180, 210))
        self.screen.blit(speed_surf, (center_x - speed_surf.get_width() // 2, BOTTOM_BOUND - 25))

        # Opponent Indicator
        mode_str = "VS AI (Press F2 for 2P)" if self.use_ai_opponent else "VS PLAYER (Press F2 for AI)"
        mode_surf = self.font_small.render(mode_str, True, (120, 220, 180))
        self.screen.blit(mode_surf, (LEFT_BOUND + 10, BOTTOM_BOUND - 25))

        # Pause Shortcut Hint
        pause_hint = "[ESC] Pause Menu"
        p_surf = self.font_small.render(pause_hint, True, COLOR_HUD_MUTED)
        self.screen.blit(p_surf, (RIGHT_BOUND - p_surf.get_width() - 10, BOTTOM_BOUND - 25))

        # Examiner Telemetry Overlay (F3)
        if self.debug_mode:
            self._render_examiner_overlay(l_aabb, r_aabb)

    def _render_examiner_overlay(self, l_aabb, r_aabb):
        # AABB Bounding Boxes
        pygame.draw.rect(self.screen, (255, 0, 0), pygame.Rect(l_aabb.min_x, l_aabb.min_y, l_aabb.width, l_aabb.height), 1)
        pygame.draw.rect(self.screen, (255, 0, 0), pygame.Rect(r_aabb.min_x, r_aabb.min_y, r_aabb.width, r_aabb.height), 1)
        b_aabb = self.engine.ball.aabb
        pygame.draw.rect(self.screen, (0, 255, 0), pygame.Rect(b_aabb.min_x, b_aabb.min_y, b_aabb.width, b_aabb.height), 1)

        # Velocity Vector Arrow
        end_vx = self.engine.ball.pos.x + self.engine.ball.vel.x * 0.15
        end_vy = self.engine.ball.pos.y + self.engine.ball.vel.y * 0.15
        pygame.draw.line(self.screen, (255, 255, 0), (self.engine.ball.pos.x, self.engine.ball.pos.y), (end_vx, end_vy), 2)

        actual_fps = self.clock.get_fps()
        telemetry_lines = [
            "=== SYSTEM TELEMETRY (EXAMINER VIEW) ===",
            f"Clock FPS: {actual_fps:.2f} / 60.0",
            f"Active Mode: {self.mode_manager.current_mode_name}",
            f"Physics Duration: {self.engine.last_update_duration_ms:.4f} ms",
            f"Ball Pos: ({self.engine.ball.pos.x:.1f}, {self.engine.ball.pos.y:.1f})",
            f"Ball Vel: ({self.engine.ball.vel.x:.1f}, {self.engine.ball.vel.y:.1f})",
            f"Last Hit Player: {self.engine.ball.last_hit_player}"
        ]
        y_offset = TOP_BOUND + 60
        for line in telemetry_lines:
            t_surf = self.font_small.render(line, True, (0, 255, 180))
            self.screen.blit(t_surf, (LEFT_BOUND + 10, y_offset))
            y_offset += 18

    def _render_pause_overlay(self) -> None:
        dim_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim_surf.fill((8, 10, 18, 180))
        self.screen.blit(dim_surf, (0, 0))

        center_x = SCREEN_WIDTH // 2
        title_surf = self.font_large.render("MATCH PAUSED", True, COLOR_MENU_SELECTED)
        self.screen.blit(title_surf, (center_x - title_surf.get_width() // 2, 150))

        self.pause_menu.draw(self.screen)

    def _render_game_over_overlay(self) -> None:
        dim_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim_surf.fill((8, 10, 18, 200))
        self.screen.blit(dim_surf, (0, 0))

        center_x = SCREEN_WIDTH // 2
        title_surf = self.font_large.render("MATCH COMPLETED!", True, COLOR_MENU_ACCENT)
        self.screen.blit(title_surf, (center_x - title_surf.get_width() // 2, 140))

        winner_name = "PLAYER 1" if self.winner_id == 1 else ("PLAYER 2 (AI)" if self.use_ai_opponent else "PLAYER 2")
        winner_text = f"VICTOR: {winner_name}  ({self.engine.score_p1} - {self.engine.score_p2})"
        w_surf = self.font_title.render(winner_text, True, COLOR_MENU_SELECTED)
        self.screen.blit(w_surf, (center_x - w_surf.get_width() // 2, 220))

        self.game_over_menu.draw(self.screen)

    def _render_exit_confirm_modal(self) -> None:
        dim_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim_surf.fill((4, 6, 12, 210))
        self.screen.blit(dim_surf, (0, 0))

        modal_w, modal_h = 480, 260
        modal_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - modal_w // 2,
            SCREEN_HEIGHT // 2 - modal_h // 2,
            modal_w, modal_h
        )
        pygame.draw.rect(self.screen, COLOR_MODAL_BG, modal_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_MENU_ACCENT, modal_rect, width=2, border_radius=8)

        confirm_title = self.font_heading = pygame.font.SysFont("Consolas", 24, bold=True).render(
            "ARE YOU SURE YOU WANT TO QUIT?", True, COLOR_TEXT
        )
        self.screen.blit(confirm_title, (modal_rect.centerx - confirm_title.get_width() // 2, modal_rect.y + 35))

        self.exit_confirm_menu.draw(self.screen)


async def main_async():
    """Async entry point required by pygbag for browser/WASM runtime."""
    app = PongGameApp()
    while app.running:
        dt_ms = app.clock.tick(TARGET_FPS)
        dt = min(dt_ms / 1000.0, 0.05)
        app._handle_events()
        app._update(dt)
        app._render()
        pygame.display.flip()
        await asyncio.sleep(0)
    pygame.quit()
    if sys.platform != "emscripten":
        sys.exit(0)


def main():
    """Desktop entry point — unchanged behaviour for native runs."""
    app = PongGameApp()
    app.run()


if __name__ == "__main__":
    if sys.platform == "emscripten":
        asyncio.run(main_async())
    else:
        main()
