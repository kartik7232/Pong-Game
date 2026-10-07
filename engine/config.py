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
