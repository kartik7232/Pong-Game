"""
===============================================================================
PONG GAME ENGINE - UNIT TEST SUITE
===============================================================================
Architectural Role: Core Physics Verification & Mathematical Validation
Author: Member A (Core Logic & Physics Lead)

Tests key requirements:
1. Continuous Translation & Deterministic Physics Update.
2. AABB Collision detection accuracy.
3. Upper/Lower boundary inversion & anti-tunneling positioning.
4. Non-linear trigonometric angle deflections & 1.07 velocity dynamic ramping.
5. Hard velocity capping at MAX_BALL_SPEED.
"""

import math
import unittest
from engine.config import (
    SPEED_RAMP_FACTOR, MAX_BALL_SPEED, INITIAL_BALL_SPEED,
    TOP_BOUND, BOTTOM_BOUND, MAX_DEFLECTION_ANGLE_RAD
)
from engine.physics import (
    Vector2D, AABB, check_aabb_intersection,
    process_wall_boundaries, calculate_paddle_deflection
)
from engine.entities import Paddle, Ball
from engine.game_engine import PongEngine, EventType


class TestVector2D(unittest.TestCase):
    def test_vector_magnitude(self):
        v = Vector2D(3.0, 4.0)
        self.assertAlmostEqual(v.magnitude(), 5.0)

    def test_vector_normalization(self):
        v = Vector2D(10.0, 0.0)
        norm = v.normalized()
        self.assertAlmostEqual(norm.x, 1.0)
        self.assertAlmostEqual(norm.y, 0.0)


class TestAABBCollision(unittest.TestCase):
    def test_intersection_true(self):
        box1 = AABB(min_x=0.0, min_y=0.0, max_x=10.0, max_y=10.0)
        box2 = AABB(min_x=5.0, min_y=5.0, max_x=15.0, max_y=15.0)
        self.assertTrue(check_aabb_intersection(box1, box2))

    def test_intersection_false(self):
        box1 = AABB(min_x=0.0, min_y=0.0, max_x=10.0, max_y=10.0)
        box2 = AABB(min_x=20.0, min_y=20.0, max_x=30.0, max_y=30.0)
        self.assertFalse(check_aabb_intersection(box1, box2))


class TestBoundaryPhysics(unittest.TestCase):
    def test_top_wall_reflection_and_anti_tunneling(self):
        radius = 10.0
        # Ball center at top_bound (so ball edge top_bound - 10 is penetrating top wall)
        pos_y = TOP_BOUND - 5.0
        vel_y = -400.0  # Moving up

        new_y, new_vy, hit = process_wall_boundaries(pos_y, vel_y, radius, TOP_BOUND, BOTTOM_BOUND)

        self.assertTrue(hit)
        # Position must be clamped outside wall boundary
        self.assertAlmostEqual(new_y, TOP_BOUND + radius)
        # Y velocity must be inverted to positive (moving down)
        self.assertGreater(new_vy, 0.0)

    def test_bottom_wall_reflection_and_anti_tunneling(self):
        radius = 10.0
        pos_y = BOTTOM_BOUND + 5.0
        vel_y = 400.0  # Moving down

        new_y, new_vy, hit = process_wall_boundaries(pos_y, vel_y, radius, TOP_BOUND, BOTTOM_BOUND)

        self.assertTrue(hit)
        self.assertAlmostEqual(new_y, BOTTOM_BOUND - radius)
        self.assertLess(new_vy, 0.0)


class TestPaddleDeflectionAndRamping(unittest.TestCase):
    def test_dynamic_velocity_ramping_factor(self):
        """Verifies 7% speed acceleration (1.07 scaling factor) on paddle bounce."""
        ball_pos = Vector2D(50.0, 300.0)
        ball_vel = Vector2D(-500.0, 0.0)  # Initial speed 500
        paddle = Paddle(center_x=30.0, center_y=300.0, is_left=True)

        new_pos, new_vel, speed = calculate_paddle_deflection(
            ball_pos=ball_pos,
            ball_vel=ball_vel,
            ball_radius=10.0,
            paddle_aabb=paddle.aabb,
            is_left_paddle=True
        )

        expected_speed = 500.0 * SPEED_RAMP_FACTOR  # 535.0
        self.assertAlmostEqual(speed, expected_speed)
        self.assertAlmostEqual(new_vel.magnitude(), expected_speed)

    def test_speed_capping_at_maximum(self):
        """Verifies velocity ramping stops at MAX_BALL_SPEED limit."""
        ball_pos = Vector2D(50.0, 300.0)
        ball_vel = Vector2D(-1180.0, 0.0)  # Near max speed
        paddle = Paddle(center_x=30.0, center_y=300.0, is_left=True)

        new_pos, new_vel, speed = calculate_paddle_deflection(
            ball_pos=ball_pos,
            ball_vel=ball_vel,
            ball_radius=10.0,
            paddle_aabb=paddle.aabb,
            is_left_paddle=True
        )

        self.assertLessEqual(speed, MAX_BALL_SPEED)
        self.assertAlmostEqual(speed, MAX_BALL_SPEED)

    def test_non_linear_deflection_angle_at_top_corner(self):
        """Impact at upper top edge of paddle should produce maximum upward angle ~60 deg."""
        paddle = Paddle(center_x=30.0, center_y=300.0, is_left=True)
        # Impact point far top on paddle
        ball_pos = Vector2D(50.0, paddle.aabb.min_y - 5.0)
        ball_vel = Vector2D(-500.0, 0.0)

        new_pos, new_vel, speed = calculate_paddle_deflection(
            ball_pos=ball_pos,
            ball_vel=ball_vel,
            ball_radius=10.0,
            paddle_aabb=paddle.aabb,
            is_left_paddle=True
        )

        # Deflection angle should be negative Y (upwards)
        self.assertLess(new_vel.y, 0.0)
        # Angle magnitude should be close to MAX_DEFLECTION_ANGLE_RAD
        computed_angle = math.atan2(new_vel.y, new_vel.x)
        self.assertAlmostEqual(abs(computed_angle), MAX_DEFLECTION_ANGLE_RAD, delta=0.05)


class TestPongEngineIntegration(unittest.TestCase):
    def test_event_callback_registration(self):
        engine = PongEngine()
        events_received = []

        def on_paddle_hit(x, y, is_left, speed):
            events_received.append((x, y, is_left, speed))

        engine.register_callback(EventType.PADDLE_HIT, on_paddle_hit)

        # Force a paddle hit by placing ball directly in front of left paddle moving left
        engine.ball.pos = Vector2D(engine.left_paddle.aabb.max_x + 5.0, engine.left_paddle.center_y)
        engine.ball.vel = Vector2D(-400.0, 0.0)

        engine.update_physics(0.016)

        self.assertEqual(len(events_received), 1)
        self.assertTrue(events_received[0][2])  # Left paddle hit == True


if __name__ == "__main__":
    unittest.main()
