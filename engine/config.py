"""
===============================================================================
PONG GAME ENGINE - CONFIGURATION MODULE
===============================================================================
Architectural Role: Core Configuration & Tunable Parameters
Author: Member A (Core Logic & Physics Lead)

Provides central tuning parameters for render resolution, physics parameters,
speed scaling factors, collision thresholds, and visual design tokens.
"""

from dataclasses import dataclass
from typing import Tuple

# Screen & Render Dimensions
SCREEN_WIDTH: int = 1000
SCREEN_HEIGHT: int = 600
TARGET_FPS: int = 60
FRAME_TIME_MS: float = 1000.0 / TARGET_FPS  # ~16.666 ms per frame

# Field Play Area Bounds (inner padding for clean borders)
BORDER_PADDING: int = 15
TOP_BOUND: float = float(BORDER_PADDING)
BOTTOM_BOUND: float = float(SCREEN_HEIGHT - BORDER_PADDING)
LEFT_BOUND: float = float(BORDER_PADDING)
RIGHT_BOUND: float = float(SCREEN_WIDTH - BORDER_PADDING)

# Paddle Physics Parameters
PADDLE_WIDTH: float = 16.0
PADDLE_HEIGHT: float = 100.0
PADDLE_SPEED: float = 550.0  # Pixels per second
PADDLE_MARGIN: float = 35.0   # Distance from screen edge to paddle center

# Ball Physics Parameters
BALL_RADIUS: float = 10.0
INITIAL_BALL_SPEED: float = 450.0       # Pixels per second starting magnitude
SPEED_RAMP_FACTOR: float = 1.07         # 7% acceleration per successful paddle bounce
MAX_BALL_SPEED: float = 1200.0          # Hard velocity cap to preserve determinism & gameplay
MAX_DEFLECTION_ANGLE_RAD: float = 1.0472 # ~60 degrees in radians (pi/3)

# Aesthetics & Color Palette (Neon Arcade Theme)
COLOR_BG: Tuple[int, int, int] = (12, 14, 24)           # Deep Space Dark Blue
COLOR_PADDLE_P1: Tuple[int, int, int] = (0, 235, 255)   # Cyan Glow
COLOR_PADDLE_P2: Tuple[int, int, int] = (255, 0, 128)   # Neon Pink/Magenta
COLOR_BALL: Tuple[int, int, int] = (255, 230, 100)      # Arcade Gold
COLOR_CENTER_LINE: Tuple[int, int, int] = (60, 70, 100) # Subtle Grid Accent
COLOR_TEXT: Tuple[int, int, int] = (240, 245, 255)      # Crisp White
COLOR_HIT_FLASH: Tuple[int, int, int] = (255, 255, 255) # Whiteout particle flash

# Game Rules & Scoring
WINNING_SCORE: int = 7

# Control Keys (Pygame Key Constants)
import pygame
KEY_P1_UP: int = pygame.K_w
KEY_P1_DOWN: int = pygame.K_s
KEY_P1_ACTIVATE: int = pygame.K_d
KEY_P2_UP: int = pygame.K_UP
KEY_P2_DOWN: int = pygame.K_DOWN
KEY_P2_ACTIVATE: int = pygame.K_LEFT

# UI / Scene Styling Tokens
COLOR_MENU_SELECTED: Tuple[int, int, int] = (0, 235, 255)     # Cyan
COLOR_MENU_UNSELECTED: Tuple[int, int, int] = (150, 165, 195) # Soft Grey-Blue
COLOR_MENU_ACCENT: Tuple[int, int, int] = (255, 0, 128)       # Neon Pink
COLOR_MODAL_BG: Tuple[int, int, int] = (18, 22, 36)           # Deep Slate Panel
COLOR_HUD_MUTED: Tuple[int, int, int] = (120, 135, 165)

# Mode 1: Wind Mode Tunables
WIND_CYCLE_DURATION: float = 6.0    # 6s total cycle (shortened interval)
WIND_ACTIVE_DURATION: float = 2.0  # 2s active wind
WIND_WARNING_DURATION: float = 0.5 # 0.5s pre-wind warning
WIND_FORCE: float = 400.0          # Ball acceleration in pixels/s^2

# Mode 2: Portal Mode Tunables
PORTAL_RADIUS: float = 26.0
PORTAL_RX: float = 28.0            # Oval horizontal semi-axis (slightly wider than radius)
PORTAL_RY: float = 44.0            # Oval vertical semi-axis (taller — vertical oval shape)
PORTAL_COOLDOWN: float = 0.3       # Seconds before ball can re-teleport
PORTAL_ZONE_W_RATIO: float = 0.40  # Keep inside central 40% of field width
PORTAL_ZONE_H_RATIO: float = 0.50  # Keep inside central 50% of field height
PORTAL_DEFAULT_Y_OFFSET: float = 120.0
PORTAL_JITTER_X: float = 40.0
PORTAL_REPOSITION_INTERVAL: float = 20.0  # Seconds between each portal's position shift
COLOR_PORTAL_A: Tuple[int, int, int] = (0, 200, 255)   # Electric Blue
COLOR_PORTAL_B: Tuple[int, int, int] = (255, 130, 0)   # Neon Orange

# Mode 3: Powerup Mode Tunables
POWERUP_SPAWN_INTERVAL: float = 6.0   # Seconds between orb spawns (frequent spawns)
POWERUP_LIFETIME: float = 15.0        # Seconds orb stays on field
POWERUP_ORB_RADIUS: float = 28.0      # Enlarged hitbox radius for easier ball collision
MAX_ACTIVE_ORBS: int = 4              # Max simultaneous powerup orbs on court
FREEZE_DURATION: float = 2.0          # Seconds opponent paddle is frozen
LASER_SPEED: float = 1400.0           # Projectile velocity (px/s)
LASER_PUSH: float = 40.0              # Paddle displacement on hit (px)
GHOST_BALL_WINDOW: float = 0.20       # Seconds before crossing center net
POWERUP_CARRYOVER_BETWEEN_ROUNDS: bool = True  # Orbs & stored powers persist across point loss

COLOR_ORB_FREEZE: Tuple[int, int, int] = (100, 220, 255) # Ice Cyan
COLOR_ORB_LASER: Tuple[int, int, int] = (255, 60, 80)    # Crimson
COLOR_ORB_GHOST: Tuple[int, int, int] = (200, 100, 255)  # Violet
COLOR_ICE_TINT: Tuple[int, int, int] = (120, 220, 255)
COLOR_LASER_BEAM: Tuple[int, int, int] = (255, 60, 90)

# Mode 4: Chaos Mode Tunables
CHAOS_MODE_DURATION: float = 60.0    # Seconds per mode before switching
CHAOS_BANNER_DURATION: float = 2.0   # Seconds transition announcement displays

