"""
===============================================================================
PONG GAME ENGINE - SCENE & STATE MACHINE MODULE
===============================================================================
Architectural Role: Finite State Machine & Scene Definitions
"""

from enum import Enum, auto


class SceneState(Enum):
    MAIN_MENU = auto()
    PLAYER_SELECT = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    TUTORIAL = auto()
    EXIT_CONFIRM = auto()

