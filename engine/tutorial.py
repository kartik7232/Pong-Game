"""
===============================================================================
PONG GAME ENGINE - TUTORIAL SYSTEM
===============================================================================
Architectural Role: Interactive multi-page tutorial with animated canvas demos
"""

import math
from typing import List, Tuple, Optional
import pygame

from engine.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TOP_BOUND, BOTTOM_BOUND,
    COLOR_BG, COLOR_TEXT, COLOR_MENU_SELECTED, COLOR_MENU_UNSELECTED,
    COLOR_MENU_ACCENT, COLOR_PORTAL_A, COLOR_PORTAL_B,
    COLOR_ORB_FREEZE, COLOR_ORB_LASER, COLOR_ORB_GHOST,
    COLOR_PADDLE_P1, COLOR_PADDLE_P2, COLOR_BALL, COLOR_CENTER_LINE,
    COLOR_MODAL_BG
)


class TutorialViewer:
    """
    Paged tutorial viewer supporting:
    - 5 pages: Basic Controls, Wind Mode, Portals, Powerups, Chaos Mode
    - Keyboard (Left/Right to switch, Esc to exit)
    - Mouse navigation (< Prev, Next >, Back to Menu buttons)
    - Live renderer illustrations & animations
    """
    TOTAL_PAGES = 5

    def __init__(self):
        self.current_page: int = 0
        self.anim_time: float = 0.0

        # Fonts
        self.font_title: pygame.font.Font = pygame.font.SysFont("Consolas", 32, bold=True)
        self.font_heading: pygame.font.Font = pygame.font.SysFont("Consolas", 20, bold=True)
        self.font_body: pygame.font.Font = pygame.font.SysFont("Consolas", 15)
        self.font_btn: pygame.font.Font = pygame.font.SysFont("Consolas", 16, bold=True)

        # UI Navigation Buttons
        self.prev_btn_rect: pygame.Rect = pygame.Rect(60, SCREEN_HEIGHT - 60, 120, 36)
        self.next_btn_rect: pygame.Rect = pygame.Rect(SCREEN_WIDTH - 180, SCREEN_HEIGHT - 60, 120, 36)
        self.back_btn_rect: pygame.Rect = pygame.Rect(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT - 60, 160, 36)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Handles navigation events. Returns "BACK" if user exits tutorial.
        """
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.current_page = (self.current_page - 1) % self.TOTAL_PAGES
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.current_page = (self.current_page + 1) % self.TOTAL_PAGES
            elif event.key == pygame.K_ESCAPE:
                return "BACK"

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if self.prev_btn_rect.collidepoint(mouse_pos):
                self.current_page = (self.current_page - 1) % self.TOTAL_PAGES
            elif self.next_btn_rect.collidepoint(mouse_pos):
                self.current_page = (self.current_page + 1) % self.TOTAL_PAGES
            elif self.back_btn_rect.collidepoint(mouse_pos):
                return "BACK"

        return None

    def update(self, dt: float) -> None:
        self.anim_time += dt

    def draw(self, surface: pygame.Surface) -> None:
        # Background
        surface.fill(COLOR_BG)

        # Main container panel
        panel_rect = pygame.Rect(40, 30, SCREEN_WIDTH - 80, SCREEN_HEIGHT - 110)
        pygame.draw.rect(surface, COLOR_MODAL_BG, panel_rect, border_radius=8)
        pygame.draw.rect(surface, (40, 50, 75), panel_rect, width=2, border_radius=8)

        # Draw page-specific content
        if self.current_page == 0:
            self._draw_page_controls(surface, panel_rect)
        elif self.current_page == 1:
            self._draw_page_wind(surface, panel_rect)
        elif self.current_page == 2:
            self._draw_page_portals(surface, panel_rect)
        elif self.current_page == 3:
            self._draw_page_powerups(surface, panel_rect)
        elif self.current_page == 4:
            self._draw_page_chaos(surface, panel_rect)

        # Bottom Navigation Bar
        mouse_pos = pygame.mouse.get_pos()

        # Page indicator
        page_str = f"Page {self.current_page + 1} of {self.TOTAL_PAGES}  (Use Left / Right Arrows)"
        page_surf = self.font_body.render(page_str, True, COLOR_MENU_UNSELECTED)
        surface.blit(page_surf, (SCREEN_WIDTH // 2 - page_surf.get_width() // 2, 42))

        # Prev Button
        prev_hover = self.prev_btn_rect.collidepoint(mouse_pos)
        pygame.draw.rect(surface, (30, 40, 60) if not prev_hover else (0, 180, 220), self.prev_btn_rect, border_radius=5)
        pygame.draw.rect(surface, COLOR_MENU_SELECTED, self.prev_btn_rect, width=1, border_radius=5)
        prev_text = self.font_btn.render("< Previous", True, COLOR_TEXT)
        surface.blit(prev_text, prev_text.get_rect(center=self.prev_btn_rect.center))

        # Next Button
        next_hover = self.next_btn_rect.collidepoint(mouse_pos)
        pygame.draw.rect(surface, (30, 40, 60) if not next_hover else (0, 180, 220), self.next_btn_rect, border_radius=5)
        pygame.draw.rect(surface, COLOR_MENU_SELECTED, self.next_btn_rect, width=1, border_radius=5)
        next_text = self.font_btn.render("Next >", True, COLOR_TEXT)
        surface.blit(next_text, next_text.get_rect(center=self.next_btn_rect.center))

        # Back to Menu Button
        back_hover = self.back_btn_rect.collidepoint(mouse_pos)
        pygame.draw.rect(surface, (50, 30, 45) if not back_hover else (220, 0, 100), self.back_btn_rect, border_radius=5)
        pygame.draw.rect(surface, COLOR_MENU_ACCENT, self.back_btn_rect, width=1, border_radius=5)
        back_text = self.font_btn.render("[Esc] Back to Menu", True, COLOR_TEXT)
        surface.blit(back_text, back_text.get_rect(center=self.back_btn_rect.center))

    def _draw_page_controls(self, surface: pygame.Surface, panel: pygame.Rect):
        title = self.font_title.render("1. BASIC CONTROLS & SYSTEM SHORTCUTS", True, COLOR_MENU_SELECTED)
        surface.blit(title, (panel.x + 30, panel.y + 35))

        lines = [
            ("PLAYER 1 (LEFT PADDLE):", COLOR_MENU_SELECTED),
            ("  * Move Up / Down:        [W] / [S]", COLOR_TEXT),
            ("  * Activate Stored Powerup: [D]", COLOR_TEXT),
            ("", COLOR_TEXT),
            ("PLAYER 2 (RIGHT PADDLE):", COLOR_PADDLE_P2),
            ("  * Move Up / Down:        [Up Arrow] / [Down Arrow]", COLOR_TEXT),
            ("  * Activate Stored Powerup: [Left Arrow]", COLOR_TEXT),
            ("", COLOR_TEXT),
            ("SYSTEM SHORTCUTS:", COLOR_MENU_ACCENT),
            ("  * [ESC]: Open In-Match Pause Menu (Resume / Restart / Main Menu)", COLOR_TEXT),
            ("  * [F2] : Toggle Autonomous AI Opponent for Player 2", COLOR_TEXT),
            ("  * [F3] : Toggle Real-Time Examiner Telemetry & AABB Hitbox Overlay", COLOR_TEXT),
            ("  * [R]  : Reset Match Score", COLOR_TEXT)
        ]

        y = panel.y + 80
        for text, col in lines:
            rendered = self.font_body.render(text, True, col)
            surface.blit(rendered, (panel.x + 35, y))
            y += 24

        # Illustration: Mini Pong Court
        demo_rect = pygame.Rect(panel.right - 280, panel.y + 85, 240, 270)
        pygame.draw.rect(surface, (14, 18, 30), demo_rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_CENTER_LINE, demo_rect, width=1, border_radius=6)
        # Center line
        for cy in range(demo_rect.y + 10, demo_rect.bottom - 10, 16):
            pygame.draw.line(surface, COLOR_CENTER_LINE, (demo_rect.centerx, cy), (demo_rect.centerx, cy + 8), 1)
        # P1 paddle
        pygame.draw.rect(surface, COLOR_PADDLE_P1, (demo_rect.x + 15, demo_rect.centery - 25, 8, 50), border_radius=2)
        # P2 paddle
        pygame.draw.rect(surface, COLOR_PADDLE_P2, (demo_rect.right - 23, demo_rect.centery - 25, 8, 50), border_radius=2)
        # Ball
        ball_y = demo_rect.centery + int(math.sin(self.anim_time * 4.0) * 30)
        ball_x = demo_rect.centerx + int(math.cos(self.anim_time * 4.0) * 60)
        pygame.draw.circle(surface, COLOR_BALL, (ball_x, ball_y), 6)

    def _draw_page_wind(self, surface: pygame.Surface, panel: pygame.Rect):
        title = self.font_title.render("2. WIND MODE RULES & MECHANICS", True, COLOR_MENU_SELECTED)
        surface.blit(title, (panel.x + 30, panel.y + 35))

        lines = [
            ("ATMOSPHERIC FORCES IN PLAY:", COLOR_MENU_SELECTED),
            ("  - Cycle Length: 10 seconds total (8.0s calm, then 2.0s active wind).", COLOR_TEXT),
            ("  - Directions: When wind begins, UP, DOWN, LEFT, or RIGHT is picked uniformly at random.", COLOR_TEXT),
            ("  - Physical Effect: Constant 400 px/s^2 acceleration is applied to the ball.", COLOR_TEXT),
            ("    Velocity magnitude is clamped to 1200 px/s to preserve gameplay balance.", COLOR_TEXT),
            ("  - Paddle Immobility Immunity: Paddles are unaffected by wind.", COLOR_TEXT),
            ("  - Telemetry & Warning: A warning arrow fades in 0.5s before wind activates.", COLOR_TEXT),
            ("    Streaming wind streaks visually indicate wind vector and intensity.", COLOR_TEXT),
            ("  - Pausing: Wind timers pause in menus and reset cleanly between rounds.", COLOR_TEXT)
        ]

        y = panel.y + 85
        for text, col in lines:
            rendered = self.font_body.render(text, True, col)
            surface.blit(rendered, (panel.x + 35, y))
            y += 26

        # Animated illustration
        demo_rect = pygame.Rect(panel.x + 35, y + 10, panel.width - 70, 110)
        pygame.draw.rect(surface, (14, 18, 30), demo_rect, border_radius=6)
        pygame.draw.rect(surface, (0, 160, 220), demo_rect, width=1, border_radius=6)

        # Streaming streaks
        streak_dir = "RIGHT"
        offset = (self.anim_time * 260) % (demo_rect.width - 40)
        for sy in (demo_rect.y + 25, demo_rect.y + 55, demo_rect.y + 85):
            sx = demo_rect.x + 20 + int(offset)
            if sx < demo_rect.right - 40:
                pygame.draw.line(surface, (120, 220, 255), (sx, sy), (sx + 35, sy), 2)

        # Arrow indicator
        arrow_lbl = self.font_heading.render("ACTIVE WIND: [ -> EAST ]", True, COLOR_MENU_SELECTED)
        surface.blit(arrow_lbl, (demo_rect.centerx - arrow_lbl.get_width() // 2, demo_rect.centery - arrow_lbl.get_height() // 2))

    def _draw_page_portals(self, surface: pygame.Surface, panel: pygame.Rect):
        title = self.font_title.render("3. PORTALS MODE RULES & MECHANICS", True, COLOR_MENU_SELECTED)
        surface.blit(title, (panel.x + 30, panel.y + 35))

        lines = [
            ("BIDIRECTIONAL WORMHOLES:", COLOR_MENU_SELECTED),
            ("  - Placement: Portal A (Blue) and Portal B (Orange) spawn in the central court area.", COLOR_TEXT),
            ("    Positions jitter slightly each round while staying inside the central 40% zone.", COLOR_TEXT),
            ("  - Trajectory Preservation: Velocity vector is preserved exactly (v_exit == v_entry).", COLOR_TEXT),
            ("    Ball re-emerges from the center of the opposite portal with original speed & angle.", COLOR_TEXT),
            ("  - Anti-Tunneling Swept Collision: Continuous segment intersection testing", COLOR_TEXT),
            ("    guarantees the ball cannot tunnel through portals even at maximum 1200 px/s speed.", COLOR_TEXT),
            ("  - Teleport Cooldown: A 0.3s cooldown prevents instant ping-pong looping.", COLOR_TEXT),
            ("  - Visuals: Dual glowing neon rings pulse and trigger particle flash rings on entry.", COLOR_TEXT)
        ]

        y = panel.y + 85
        for text, col in lines:
            rendered = self.font_body.render(text, True, col)
            surface.blit(rendered, (panel.x + 35, y))
            y += 26

        # Animated illustration
        demo_rect = pygame.Rect(panel.x + 35, y + 10, panel.width - 70, 110)
        pygame.draw.rect(surface, (14, 18, 30), demo_rect, border_radius=6)
        pygame.draw.rect(surface, (0, 180, 255), demo_rect, width=1, border_radius=6)

        p_a = (demo_rect.x + 160, demo_rect.centery)
        p_b = (demo_rect.right - 160, demo_rect.centery)
        r = 22 + int(math.sin(self.anim_time * 6.0) * 3)

        pygame.draw.circle(surface, COLOR_PORTAL_A, p_a, r, width=3)
        pygame.draw.circle(surface, COLOR_PORTAL_B, p_b, r, width=3)

        lbl_a = self.font_btn.render("PORTAL A", True, COLOR_PORTAL_A)
        lbl_b = self.font_btn.render("PORTAL B", True, COLOR_PORTAL_B)
        surface.blit(lbl_a, (p_a[0] - lbl_a.get_width() // 2, p_a[1] + 30))
        surface.blit(lbl_b, (p_b[0] - lbl_b.get_width() // 2, p_b[1] + 30))

        flow_txt = self.font_heading.render("<==== TELEPORT LINKED ====>", True, (240, 245, 255))
        surface.blit(flow_txt, (demo_rect.centerx - flow_txt.get_width() // 2, demo_rect.centery - flow_txt.get_height() // 2))

    def _draw_page_powerups(self, surface: pygame.Surface, panel: pygame.Rect):
        title = self.font_title.render("4. POWERUP MODE: PICKUPS & ABILITIES", True, COLOR_MENU_SELECTED)
        surface.blit(title, (panel.x + 30, panel.y + 35))

        lines = [
            ("COLLECTION & INVENTORY RULES:", COLOR_MENU_SELECTED),
            ("  - Spawning: Up to 4 orbs spawn every ~6s (15s lifetime, stay across point loss).", COLOR_TEXT),
            ("  - Enlarged Hitbox: Large 28px orbs make contact during rallies easy and frequent.", COLOR_TEXT),
            ("  - Collection: Ball touching orb grants it to whoever last hit the ball.", COLOR_TEXT),
            ("  - Storage: Max 1 stored powerup per player. Stored icon shows beside scoreboard.", COLOR_TEXT),
            ("  - Activation Keys: Player 1: [D]  |  Player 2: [Left Arrow]", COLOR_MENU_ACCENT),
            ("", COLOR_TEXT),
            ("THREE RANDOM POWERUP TYPES:", COLOR_MENU_SELECTED),
            ("  1. FREEZE [F]     : Freezes opponent paddle for exactly 2.0s (ice tint + gauge).", COLOR_ORB_FREEZE),
            ("  2. LASER [L]      : Fires fast linear bolt from paddle. Destroys ball (re-serves", COLOR_ORB_LASER),
            ("                      from center with no point awarded) or knocks back paddle.", COLOR_TEXT),
            ("  3. GHOST BALL [G] : Turns ball invisible before crossing center net towards opponent.", COLOR_ORB_GHOST),
            ("                      Reappears upon net crossing; physics remain 100% normal.", COLOR_TEXT)
        ]

        y = panel.y + 80
        for text, col in lines:
            rendered = self.font_body.render(text, True, col)
            surface.blit(rendered, (panel.x + 35, y))
            y += 24

        # Mini icons preview
        demo_x = panel.right - 240
        for i, (sym, col, name) in enumerate([
            ("F", COLOR_ORB_FREEZE, "FREEZE"),
            ("L", COLOR_ORB_LASER, "LASER"),
            ("G", COLOR_ORB_GHOST, "GHOST BALL")
        ]):
            cy = panel.y + 90 + i * 50
            pygame.draw.circle(surface, col, (demo_x, cy), 16)
            pygame.draw.circle(surface, (255, 255, 255), (demo_x, cy), 16, width=2)
            letter = self.font_heading.render(sym, True, (20, 24, 36))
            surface.blit(letter, letter.get_rect(center=(demo_x, cy)))
            name_txt = self.font_btn.render(name, True, col)
            surface.blit(name_txt, (demo_x + 28, cy - name_txt.get_height() // 2))

    def _draw_page_chaos(self, surface: pygame.Surface, panel: pygame.Rect):
        title = self.font_title.render("5. CHAOS MODE RULES & ROTATION", True, COLOR_MENU_SELECTED)
        surface.blit(title, (panel.x + 30, panel.y + 35))

        lines = [
            ("DYNAMIC META-MODE ARCHITECTURE:", COLOR_MENU_SELECTED),
            ("  - Combination: Combines Wind, Portals, and Powerup Modes into one dynamic match.", COLOR_TEXT),
            ("  - Single Active Rule: Exactly ONE mode is active at any given moment.", COLOR_TEXT),
            ("  - 60-Second Rotation: Switches to a different random mode every 60 seconds.", COLOR_TEXT),
            ("  - No Immediate Repeats: The next mode is guaranteed to be different from the current.", COLOR_TEXT),
            ("  - Full State Purge: Previous mode is cleanly disabled upon switch (purges active", COLOR_TEXT),
            ("    portals, wind streaks, active orbs, lasers, frozen paddle timers, and ghost states).", COLOR_TEXT),
            ("  - Broadcast Banner: A 2.0-second animated announcement announces each new mode.", COLOR_TEXT),
            ("  - HUD Countdown: Live HUD timer displays seconds remaining until next Chaos Shift.", COLOR_TEXT)
        ]

        y = panel.y + 85
        for text, col in lines:
            rendered = self.font_body.render(text, True, col)
            surface.blit(rendered, (panel.x + 35, y))
            y += 26

        # Animated illustration
        demo_rect = pygame.Rect(panel.x + 35, y + 10, panel.width - 70, 110)
        pygame.draw.rect(surface, (14, 18, 30), demo_rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_MENU_ACCENT, demo_rect, width=1, border_radius=6)

        banner_text = self.font_title.render("CHAOS SHIFT: [ WIND -> PORTALS -> POWERUPS ]", True, COLOR_MENU_SELECTED)
        surface.blit(banner_text, (demo_rect.centerx - banner_text.get_width() // 2, demo_rect.centery - banner_text.get_height() // 2))
