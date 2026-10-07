"""
===============================================================================
PONG GAME ENGINE - MODE MANAGER MODULE
===============================================================================
Architectural Role: Central Orchestration for Active Game Modes
"""

from typing import List, Optional
import pygame
from engine.modes.base import GameMode
from engine.entities import Ball


class ModeManager:
    """
    Orchestrates game modes and exposes a single interface to the game loop.
    Ensures timers pause during game pause and reset cleanly.
    """
    def __init__(self):
        self.active_modes: List[GameMode] = []
        self._current_mode_name: str = "Classic"

    def set_mode(self, mode: Optional[GameMode]) -> None:
        """Disables current modes and enables the specified mode."""
        self.disable_all()
        self.active_modes.clear()
        if mode is not None:
            self.active_modes.append(mode)
            mode.enable()
            mode.reset()
            self._current_mode_name = mode.name
        else:
            self._current_mode_name = "Classic"

    def disable_all(self) -> None:
        """Disables and resets all active modes."""
        for mode in self.active_modes:
            mode.disable()
            mode.reset()

    def reset(self) -> None:
        """Resets all active modes."""
        for mode in self.active_modes:
            mode.reset()

    def update(self, dt: float) -> None:
        """Updates all enabled active modes with delta time."""
        for mode in self.active_modes:
            if mode.is_enabled:
                mode.update(dt)

    def draw(self, renderer: pygame.Surface) -> None:
        """Draws visuals for all enabled active modes."""
        for mode in self.active_modes:
            if mode.is_enabled:
                mode.draw(renderer)

    def on_ball_update(self, ball: Ball, dt: float = 0.0) -> None:
        """Propagates ball update hook to enabled active modes."""
        for mode in self.active_modes:
            if mode.is_enabled:
                mode.on_ball_update(ball, dt)

    def on_round_start(self) -> None:
        """Propagates round start hook to enabled active modes."""
        for mode in self.active_modes:
            if mode.is_enabled:
                mode.on_round_start()

    def on_round_end(self) -> None:
        """Propagates round end hook to enabled active modes."""
        for mode in self.active_modes:
            if mode.is_enabled:
                mode.on_round_end()

    @property
    def current_mode_name(self) -> str:
        if self.active_modes and self.active_modes[0].is_enabled:
            return self.active_modes[0].name
        return self._current_mode_name
