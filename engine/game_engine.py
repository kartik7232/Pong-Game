"""
===============================================================================
PONG GAME ENGINE - DETERMINISTIC GAME ENGINE & EVENT BUS
===============================================================================
Architectural Role: State Orchestration, Deterministic Loop, & Subsystem Interfaces
Author: Member A (Core Logic & Physics Lead)

This module provides the central PongEngine class managing:
1. Deterministic game state loop & timestep accumulator.
2. Collision resolution pipeline.
3. Event callback bus for Member B (Inputs/AI) & Member C (VFX/Particles/Audio).
"""

import time
from typing import Dict, List, Callable, Any, Tuple, Optional
from engine.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TARGET_FPS, PADDLE_MARGIN,
    LEFT_BOUND, RIGHT_BOUND
)
from engine.physics import check_aabb_intersection, calculate_paddle_deflection, Vector2D
from engine.entities import Paddle, Ball


class EventType:
    PADDLE_HIT = "PADDLE_HIT"
    WALL_HIT = "WALL_HIT"
    SCORE = "SCORE"


class PongEngine:
    """
    Central Core Physics & Logic Engine.
    
    Exposes a deterministic, decoupled interface designed for team collaboration:
    - Member B hooks paddle control (Player or AI) via set_paddle_movement()
    - Member C registers particle/audio callbacks via register_callback()
    """
    def __init__(self):
        # Initialize Entities
        p1_x = LEFT_BOUND + PADDLE_MARGIN
        p2_x = RIGHT_BOUND - PADDLE_MARGIN
        center_y = SCREEN_HEIGHT * 0.5

        self.left_paddle: Paddle = Paddle(center_x=p1_x, center_y=center_y, is_left=True)
        self.right_paddle: Paddle = Paddle(center_x=p2_x, center_y=center_y, is_left=False)
        self.ball: Ball = Ball(x=SCREEN_WIDTH * 0.5, y=center_y)

        # Score Tracking
        self.score_p1: int = 0
        self.score_p2: int = 0

        # Performance & Timing Diagnostics
        self.frame_count: int = 0
        self.last_update_duration_ms: float = 0.0
        self.current_fps: float = 60.0

        # Event Dispatcher Callback Registry for Subsystems (Member C: VFX / Audio)
        self._listeners: Dict[str, List[Callable[..., None]]] = {
            EventType.PADDLE_HIT: [],
            EventType.WALL_HIT: [],
            EventType.SCORE: []
        }

    # =========================================================================
    # SUBSYSTEM INTEGRATION INTERFACES (MEMBER B & MEMBER C HOOKS)
    # =========================================================================

    def register_callback(self, event_type: str, callback: Callable[..., None]) -> None:
        """
        Allows Member C (FX Lead) or Member B (Audio/UI Lead) to subscribe to core events.
        
        Callback Signatures:
        - PADDLE_HIT: callback(x: float, y: float, is_left_paddle: bool, speed: float)
        - WALL_HIT: callback(x: float, y: float)
        - SCORE: callback(scoring_player: int, score_p1: int, score_p2: int)
        """
        if event_type in self._listeners:
            self._listeners[event_type].append(callback)

    def _trigger_event(self, event_type: str, *args: Any) -> None:
        """Internal helper to dispatch events to registered callbacks synchronously."""
        for cb in self._listeners.get(event_type, []):
            try:
                cb(*args)
            except Exception as e:
                print(f"[Engine Event Error] Exception in callback for {event_type}: {e}")

    def set_paddle_movement(self, is_left: bool, direction: int) -> None:
        """
        Member B Interface: Directly sets paddle translation direction.
        
        Args:
            is_left (bool): True for Player 1 (Left), False for Player 2 / AI (Right).
            direction (int): -1 for Up, 0 for Stop, +1 for Down.
        """
        target_paddle = self.left_paddle if is_left else self.right_paddle
        target_paddle.move_dir = max(-1, min(1, direction))

    def get_state_vector(self) -> Dict[str, Any]:
        """
        Member B Interface: Exposes complete deterministic state payload for AI agents.
        
        Returns:
            Dict containing normalized ball position, velocity, paddle positions, and score.
        """
        return {
            "ball_x": self.ball.pos.x,
            "ball_y": self.ball.pos.y,
            "ball_vx": self.ball.vel.x,
            "ball_vy": self.ball.vel.y,
            "ball_speed": self.ball.speed,
            "p1_y": self.left_paddle.center_y,
            "p2_y": self.right_paddle.center_y,
            "score_p1": self.score_p1,
            "score_p2": self.score_p2,
        }

    # =========================================================================
    # CORE PHYSICS & COLLISION PIPELINE
    # =========================================================================

    def update_physics(self, dt: float) -> None:
        """
        Executes single deterministic physics step:
        1. Paddle positional integration & boundary checks.
        2. Ball continuous translation & top/bottom wall reflections.
        3. AABB intersection testing against left & right paddles.
        4. Non-linear trigonometric angle deflection & dynamic speed scaling.
        5. Left/Right goal post scoring checks and ball reset.
        """
        start_time = time.perf_counter()

        # 1. Update paddles
        self.left_paddle.update(dt)
        self.right_paddle.update(dt)

        # 2. Continuous translation of ball & wall checks
        wall_hit = self.ball.update_kinematics(dt)
        if wall_hit:
            self._trigger_event(EventType.WALL_HIT, self.ball.pos.x, self.ball.pos.y)

        # 3 & 4. Collision Detection & Deflection Resolution
        ball_aabb = self.ball.aabb

        # Test collision with Left Paddle (only if ball is moving leftwards towards paddle)
        if self.ball.vel.x < 0 and check_aabb_intersection(ball_aabb, self.left_paddle.aabb):
            new_pos, new_vel, speed = calculate_paddle_deflection(
                ball_pos=self.ball.pos,
                ball_vel=self.ball.vel,
                ball_radius=self.ball.radius,
                paddle_aabb=self.left_paddle.aabb,
                is_left_paddle=True
            )
            self.ball.pos = new_pos
            self.ball.vel = new_vel
            self.ball.hit_count += 1
            self.ball.last_hit_player = 1
            self._trigger_event(EventType.PADDLE_HIT, new_pos.x, new_pos.y, True, speed)

        # Test collision with Right Paddle (only if ball is moving rightwards towards paddle)
        elif self.ball.vel.x > 0 and check_aabb_intersection(ball_aabb, self.right_paddle.aabb):
            new_pos, new_vel, speed = calculate_paddle_deflection(
                ball_pos=self.ball.pos,
                ball_vel=self.ball.vel,
                ball_radius=self.ball.radius,
                paddle_aabb=self.right_paddle.aabb,
                is_left_paddle=False
            )
            self.ball.pos = new_pos
            self.ball.vel = new_vel
            self.ball.hit_count += 1
            self.ball.last_hit_player = 2
            self._trigger_event(EventType.PADDLE_HIT, new_pos.x, new_pos.y, False, speed)

        # 5. Goal Post & Out of Bounds Detection
        # Left boundary goal check (P2 Scores)
        if self.ball.pos.x + self.ball.radius < 0:
            self.score_p2 += 1
            self._trigger_event(EventType.SCORE, 2, self.score_p1, self.score_p2)
            self.ball.reset(serve_left=False)

        # Right boundary goal check (P1 Scores)
        elif self.ball.pos.x - self.ball.radius > SCREEN_WIDTH:
            self.score_p1 += 1
            self._trigger_event(EventType.SCORE, 1, self.score_p1, self.score_p2)
            self.ball.reset(serve_left=True)

        end_time = time.perf_counter()
        self.last_update_duration_ms = (end_time - start_time) * 1000.0
        self.frame_count += 1

    def reset_ball_neutral(self) -> None:
        """Re-serves the ball from center without scoring any points (used by Laser hit)."""
        import random
        self.ball.reset(serve_left=random.choice([True, False]))

    def reset_game(self) -> None:
        """Resets scores and entity states for a fresh match."""
        self.score_p1 = 0
        self.score_p2 = 0
        self.left_paddle.reset_position(SCREEN_HEIGHT * 0.5)
        self.right_paddle.reset_position(SCREEN_HEIGHT * 0.5)
        self.ball.reset(serve_left=True)

