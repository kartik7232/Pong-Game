"""
===============================================================================
PONG GAME ENGINE - CORE PHYSICS & MATHEMATICS MODULE
===============================================================================
Architectural Role: Core Physics Engine & Vector Kinematics
Author: Member A (Core Logic & Physics Lead)

This module encapsulates all mathematical models used for kinematics, continuous
translation, boundary reflection (with tunneling protection), AABB collision
intersections, non-linear angle deflections, and dynamic velocity scaling.
"""

import math
from typing import Tuple, NamedTuple, Optional
from engine.config import (
    TOP_BOUND, BOTTOM_BOUND, SPEED_RAMP_FACTOR,
    MAX_BALL_SPEED, MAX_DEFLECTION_ANGLE_RAD
)


class Vector2D:
    """Rigorous 2D Vector implementation for deterministic motion calculations."""
    __slots__ = ('x', 'y')

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x: float = float(x)
        self.y: float = float(y)

    def magnitude(self) -> float:
        """Returns Euclidean length ||v|| of the vector."""
        return math.hypot(self.x, self.y)

    def normalized(self) -> 'Vector2D':
        """Returns unit vector v / ||v||. Handles zero vector safely."""
        mag = self.magnitude()
        if mag == 0.0:
            return Vector2D(0.0, 0.0)
        return Vector2D(self.x / mag, self.y / mag)

    def __add__(self, other: 'Vector2D') -> 'Vector2D':
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Vector2D') -> 'Vector2D':
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> 'Vector2D':
        return Vector2D(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> 'Vector2D':
        return Vector2D(self.x * scalar, self.y * scalar)

    def __repr__(self) -> str:
        return f"Vector2D(x={self.x:.3f}, y={self.y:.3f})"


class AABB(NamedTuple):
    """Axis-Aligned Bounding Box representation (min_x, min_y, max_x, max_y)."""
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    @property
    def center_x(self) -> float:
        return (self.min_x + self.max_x) * 0.5

    @property
    def center_y(self) -> float:
        return (self.min_y + self.max_y) * 0.5


def check_aabb_intersection(box_a: AABB, box_b: AABB) -> bool:
    """
    Performs standard Axis-Aligned Bounding Box (AABB) intersection testing.
    
    Theorem: Two AABBs intersect if and only if their projections along all 
    orthogonal axes (X and Y) overlap simultaneously.
    """
    return (
        box_a.min_x < box_b.max_x and
        box_a.max_x > box_b.min_x and
        box_a.min_y < box_b.max_y and
        box_a.max_y > box_b.min_y
    )


def process_wall_boundaries(
    pos_y: float, 
    vel_y: float, 
    radius: float, 
    top_bound: float = TOP_BOUND, 
    bottom_bound: float = BOTTOM_BOUND
) -> Tuple[float, float, bool]:
    """
    Handles upper and lower wall reflections with anti-tunneling clamping.

    Returns:
        Tuple[new_pos_y, new_vel_y, wall_hit_occurred]
    """
    hit = False
    new_y = pos_y
    new_vy = vel_y

    # Upper screen boundary collision check
    if pos_y - radius <= top_bound:
        new_y = top_bound + radius  # Hard boundary repositioning prevents sticking/tunneling
        new_vy = abs(vel_y)        # Guarantee positive Y velocity (moving downwards)
        hit = True

    # Lower screen boundary collision check
    elif pos_y + radius >= bottom_bound:
        new_y = bottom_bound - radius  # Hard boundary repositioning
        new_vy = -abs(vel_y)          # Guarantee negative Y velocity (moving upwards)
        hit = True

    return new_y, new_vy, hit


def calculate_paddle_deflection(
    ball_pos: Vector2D,
    ball_vel: Vector2D,
    ball_radius: float,
    paddle_aabb: AABB,
    is_left_paddle: bool
) -> Tuple[Vector2D, Vector2D, float]:
    """
    Computes dynamic non-linear trajectory deflection and speed ramping upon paddle impact.

    Mathematical Model:
    1. Impact Offset: Normalized y-distance relative to paddle center in range [-1.0, 1.0].
       normalized_offset = (ball_y - paddle_center_y) / (paddle_half_height + ball_radius)
    2. Deflection Angle Mapping: 
       theta = normalized_offset * MAX_DEFLECTION_ANGLE_RAD
    3. Speed Dynamic Ramping:
       new_speed = min(current_speed * SPEED_RAMP_FACTOR, MAX_BALL_SPEED)
    4. Anti-Tunneling Clamping:
       Immediately repositions ball outside paddle bounding box.

    Returns:
        Tuple[new_ball_pos, new_ball_vel, new_speed]
    """
    current_speed = ball_vel.magnitude()
    if current_speed == 0.0:
        current_speed = 1.0

    # 1. Dynamic velocity scaling (~7% speed ramping capped at MAX_BALL_SPEED)
    ramped_speed = min(current_speed * SPEED_RAMP_FACTOR, MAX_BALL_SPEED)

    # 2. Compute normalized impact point along paddle vertical axis
    paddle_center_y = paddle_aabb.center_y
    paddle_half_height = paddle_aabb.height * 0.5
    
    # Distance from center normalized to [-1.0, 1.0]
    relative_impact_y = (ball_pos.y - paddle_center_y) / (paddle_half_height + ball_radius * 0.5)
    # Clamp offset to enforce maximum defined deflection angle
    clamped_offset = max(-1.0, min(1.0, relative_impact_y))

    # 3. Non-linear trigonometric deflection angle
    deflection_angle = clamped_offset * MAX_DEFLECTION_ANGLE_RAD

    # 4. Resolve horizontal direction (+1 for rightward reflection, -1 for leftward reflection)
    direction_x = 1.0 if is_left_paddle else -1.0

    new_vx = direction_x * ramped_speed * math.cos(deflection_angle)
    new_vy = ramped_speed * math.sin(deflection_angle)

    # 5. Position repositioning / clamping to eliminate boundary tunneling
    offset_epsilon = 1.0  # Safety buffer
    if is_left_paddle:
        corrected_x = paddle_aabb.max_x + ball_radius + offset_epsilon
    else:
        corrected_x = paddle_aabb.min_x - ball_radius - offset_epsilon

    new_pos = Vector2D(corrected_x, ball_pos.y)
    new_vel = Vector2D(new_vx, new_vy)

    return new_pos, new_vel, ramped_speed
