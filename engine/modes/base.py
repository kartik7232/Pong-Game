"""
===============================================================================
PONG GAME ENGINE - GAME MODE BASE INTERFACE
===============================================================================
Architectural Role: Abstract Base Class defining standard interface for modes
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import pygame
from engine.entities import Ball


class GameMode(ABC):
    """
    Standard interface that every selectable game mode must implement:
    - init(game)
    - reset()
    - update(dt)
    - draw(renderer)
    - on_ball_update(ball)
    - on_round_start()
    - on_round_end()
    - enable()
    - disable()
    """
    def __init__(self, name: str):
        self.name: str = name
        self.is_enabled: bool = False
        self.game: Any = None

    def init(self, game: Any) -> None:
        """Called once when mode is instantiated with reference to game/engine."""
        self.game = game

    @abstractmethod
    def reset(self) -> None:
        """Resets all internal mode timers, states, and active entities."""
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """Called every frame during active play. Delta-time based."""
        pass

    @abstractmethod
    def draw(self, renderer: pygame.Surface) -> None:
        """Renders mode-specific visuals onto the renderer surface."""
        pass

    @abstractmethod
    def on_ball_update(self, ball: Ball, dt: float = 0.0) -> None:
        """Hook called when the ball's position / kinematics are updated."""
        pass

    @abstractmethod
    def on_round_start(self) -> None:
        """Hook called when a new round starts / ball is served."""
        pass

    @abstractmethod
    def on_round_end(self) -> None:
        """Hook called when a point is scored / round finishes."""
        pass

    def enable(self) -> None:
        """Activates the mode."""
        self.is_enabled = True

    def disable(self) -> None:
        """Deactivates the mode and cleans up all active effects."""
        self.is_enabled = False
