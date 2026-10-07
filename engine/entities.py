"""
===============================================================================
PONG GAME ENGINE - GAME ENTITIES MODULE
===============================================================================
Architectural Role: State Encapsulation for Physical Entities
Author: Member A (Core Logic & Physics Lead)

Encapsulates state, sub-pixel floating-point kinematics, and geometric bounding
boxes for Paddles and the Ball.
"""

import math
import random
from typing import Tuple
from engine.config import (
    PADDLE_WIDTH, PADDLE_HEIGHT, PADDLE_SPEED,
    BALL_RADIUS, INITIAL_BALL_SPEED, TOP_BOUND, BOTTOM_BOUND,
    SCREEN_WIDTH, SCREEN_HEIGHT
)
from engine.physics import Vector2D, AABB, process_wall_boundaries


class Paddle:
    """
    Encapsulates paddle physics, vertical translation, and AABB computation.
    """
    def __init__(self, center_x: float, center_y: float, is_left: bool):
        self.center_x: float = float(center_x)
        self.center_y: float = float(center_y)
        self.width: float = PADDLE_WIDTH
        self.height: float = PADDLE_HEIGHT
        self.speed: float = PADDLE_SPEED
        self.is_left: bool = is_left
        
        # Velocity control (-1: up, 0: stationary, +1: down)
        self.move_dir: int = 0

    @property
    def aabb(self) -> AABB:
        """Computes current Axis-Aligned Bounding Box (AABB)."""
        half_w = self.width * 0.5
        half_h = self.height * 0.5
        return AABB(
            min_x=self.center_x - half_w,
            min_y=self.center_y - half_h,
            max_x=self.center_x + half_w,
            max_y=self.center_y + half_h
        )

    def update(self, dt: float) -> None:
        """
        Translates paddle vertically based on movement direction and delta time dt.
        Clamps position to enforce playfield vertical boundaries.
        """
        if self.move_dir != 0:
            self.center_y += self.move_dir * self.speed * dt

        # Enforce boundary limits so paddle cannot clip outside screen bounds
        half_h = self.height * 0.5
        min_allowed_y = TOP_BOUND + half_h
        max_allowed_y = BOTTOM_BOUND - half_h

        if self.center_y < min_allowed_y:
            self.center_y = min_allowed_y
        elif self.center_y > max_allowed_y:
            self.center_y = max_allowed_y


class Ball:
    """
    Encapsulates ball kinematics, continuous translation, wall reflection,
    and velocity scaling state.
    """
    def __init__(self, x: float = SCREEN_WIDTH / 2, y: float = SCREEN_HEIGHT / 2):
        self.pos: Vector2D = Vector2D(x, y)
        self.vel: Vector2D = Vector2D(0.0, 0.0)
        self.radius: float = BALL_RADIUS
        self.hit_count: int = 0
        self.reset(serve_left=random.choice([True, False]))

    @property
    def speed(self) -> float:
        """Returns scalar speed magnitude ||vel||."""
        return self.vel.magnitude()

    @property
    def aabb(self) -> AABB:
        """Computes current AABB for intersection checking."""
        return AABB(
            min_x=self.pos.x - self.radius,
            min_y=self.pos.y - self.radius,
            max_x=self.pos.x + self.radius,
            max_y=self.pos.y + self.radius
        )

    def reset(self, serve_left: bool = True) -> None:
        """
        Resets ball position to screen center and calculates initial velocity vector
        with controlled random launch angle [-30 deg, +30 deg].
        """
        self.pos = Vector2D(SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.5)
        self.hit_count = 0

        # Random angle between -30° and +30° (-pi/6 to +pi/6)
        launch_angle = random.uniform(-math.pi / 6.0, math.pi / 6.0)
        direction_x = -1.0 if serve_left else 1.0

        vx = direction_x * INITIAL_BALL_SPEED * math.cos(launch_angle)
        vy = INITIAL_BALL_SPEED * math.sin(launch_angle)

        self.vel = Vector2D(vx, vy)

    def update_kinematics(self, dt: float) -> bool:
        """
        Performs continuous 2D position translation: p(t + dt) = p(t) + v * dt.
        Processes top and bottom boundary reflections with zero tunneling.

        Returns:
            bool: True if top/bottom wall collision occurred this frame.
        """
        # Translation update
        self.pos.x += self.vel.x * dt
        self.pos.y += self.vel.y * dt

        # Boundary inversion & clamping
        new_y, new_vy, hit_wall = process_wall_boundaries(
            pos_y=self.pos.y,
            vel_y=self.vel.y,
            radius=self.radius,
            top_bound=TOP_BOUND,
            bottom_bound=BOTTOM_BOUND
        )

        if hit_wall:
            self.pos.y = new_y
            self.vel.y = new_vy

        return hit_wall
