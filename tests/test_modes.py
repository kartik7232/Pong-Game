"""
===============================================================================
PONG GAME ENGINE - GAME MODES & SCENE UNIT TEST SUITE
===============================================================================
Architectural Role: Automated Verification for Wind, Portals, Powerups, Chaos,
and Base Game Compatibility
"""

import math
import unittest
import pygame

# Initialize pygame headless for tests
pygame.init()
pygame.display.set_mode((1, 1), pygame.NOFRAME)

from engine.config import (
    WIND_CYCLE_DURATION, WIND_ACTIVE_DURATION, WIND_FORCE, MAX_BALL_SPEED,
    PORTAL_COOLDOWN, FREEZE_DURATION, LASER_SPEED, LASER_PUSH,
    SCREEN_WIDTH, SCREEN_HEIGHT, TOP_BOUND, BOTTOM_BOUND,
    KEY_P1_UP, KEY_P1_DOWN
)
from engine.physics import Vector2D
from engine.entities import Paddle, Ball
from engine.game_engine import PongEngine
from engine.modes.mode_manager import ModeManager
from engine.modes.wind_mode import WindMode
from engine.modes.portal_mode import PortalMode
from engine.modes.powerup_mode import PowerupMode, PowerupType, LaserProjectile, PowerupOrb
from engine.modes.chaos_mode import ChaosMode
from engine.state import SceneState
from engine.ui import Menu


class TestBaseGameCompatibility(unittest.TestCase):
    """Verifies that base game physics, scoring, and paddle control remain intact."""
    def test_base_game_physics_without_modes(self):
        engine = PongEngine()
        mode_mgr = ModeManager()
        mode_mgr.set_mode(None)

        # Baseline position
        initial_x = engine.ball.pos.x
        initial_y = engine.ball.pos.y
        dt = 0.016

        engine.update_physics(dt)
        mode_mgr.on_ball_update(engine.ball, dt)

        # Ball should translate based purely on velocity
        self.assertNotEqual(engine.ball.pos.x, initial_x)
        self.assertEqual(engine.score_p1, 0)
        self.assertEqual(engine.score_p2, 0)

    def test_scoring_increments_and_resets_ball(self):
        engine = PongEngine()
        # Move ball out of right boundary
        engine.ball.pos = Vector2D(SCREEN_WIDTH + 50.0, SCREEN_HEIGHT * 0.5)
        engine.update_physics(0.016)

        self.assertEqual(engine.score_p1, 1)
        self.assertEqual(engine.score_p2, 0)
        # Ball served back near center
        self.assertAlmostEqual(engine.ball.pos.x, SCREEN_WIDTH * 0.5, delta=5.0)


class TestWindMode(unittest.TestCase):
    def test_wind_cycle_timing(self):
        wind = WindMode()
        wind.enable()
        wind.reset()

        # At t = 2.0s: Calm
        wind.update(2.0)
        self.assertFalse(wind.is_active)
        self.assertFalse(wind.is_warning)

        # At t = 7.6s (calm 8.0 - warn 0.5 = 7.5s): Warning active
        wind.update(5.6)
        self.assertTrue(wind.is_warning)
        self.assertFalse(wind.is_active)

        # At t = 8.5s: Active wind
        wind.update(0.9)
        self.assertTrue(wind.is_active)
        self.assertFalse(wind.is_warning)

        # At t = 10.1s: Reset cycle
        wind.update(1.6)
        self.assertFalse(wind.is_active)
        self.assertLess(wind.timer, 1.0)

    def test_wind_force_acceleration_and_clamping(self):
        wind = WindMode()
        wind.enable()
        wind.reset()
        wind.is_active = True
        wind.current_direction = "RIGHT"

        ball = Ball()
        ball.vel = Vector2D(500.0, 0.0)

        dt = 0.1
        wind.on_ball_update(ball, dt)

        expected_vx = 500.0 + WIND_FORCE * dt
        self.assertAlmostEqual(ball.vel.x, expected_vx)

        # Test velocity clamp
        ball.vel = Vector2D(MAX_BALL_SPEED + 100.0, 0.0)
        wind.on_ball_update(ball, dt)
        self.assertLessEqual(ball.speed, MAX_BALL_SPEED)

    def test_all_four_wind_directions_occur(self):
        wind = WindMode()
        wind.enable()
        directions_seen = set()
        for _ in range(100):
            wind.reset()
            wind.update(7.6)  # Triggers warning direction pick
            directions_seen.add(wind.current_direction)
        self.assertEqual(directions_seen, {"UP", "DOWN", "LEFT", "RIGHT"})


class TestPortalMode(unittest.TestCase):
    def test_bidirectional_teleportation_and_velocity_preservation(self):
        portal_mode = PortalMode()
        portal_mode.enable()
        portal_mode.reset()

        ball = Ball()
        ball.pos = Vector2D(portal_mode.portal_a_pos.x, portal_mode.portal_a_pos.y)
        ball.vel = Vector2D(350.0, -150.0)

        portal_mode.on_ball_update(ball, 0.016)

        # Ball should teleport to Portal B center
        self.assertAlmostEqual(ball.pos.x, portal_mode.portal_b_pos.x)
        self.assertAlmostEqual(ball.pos.y, portal_mode.portal_b_pos.y)
        # Velocity vector is preserved exactly
        self.assertAlmostEqual(ball.vel.x, 350.0)
        self.assertAlmostEqual(ball.vel.y, -150.0)
        # Cooldown activated
        self.assertGreater(portal_mode.cooldown_timer, 0.0)

    def test_portal_b_to_a_teleport(self):
        portal_mode = PortalMode()
        portal_mode.enable()
        portal_mode.reset()

        ball = Ball()
        ball.pos = Vector2D(portal_mode.portal_b_pos.x, portal_mode.portal_b_pos.y)
        ball.vel = Vector2D(-400.0, 200.0)

        portal_mode.on_ball_update(ball, 0.016)

        # Ball should teleport to Portal A center
        self.assertAlmostEqual(ball.pos.x, portal_mode.portal_a_pos.x)
        self.assertAlmostEqual(ball.pos.y, portal_mode.portal_a_pos.y)
        self.assertAlmostEqual(ball.vel.x, -400.0)
        self.assertAlmostEqual(ball.vel.y, 200.0)

    def test_portal_cooldown_prevents_looping(self):
        portal_mode = PortalMode()
        portal_mode.enable()
        portal_mode.reset()

        ball = Ball()
        ball.pos = Vector2D(portal_mode.portal_a_pos.x, portal_mode.portal_a_pos.y)
        ball.vel = Vector2D(300.0, 0.0)

        portal_mode.on_ball_update(ball, 0.016)
        curr_x = ball.pos.x
        portal_mode.on_ball_update(ball, 0.016)
        # Should NOT teleport back to A because cooldown is still active
        self.assertEqual(ball.pos.x, curr_x)

    def test_anti_tunneling_swept_intersection(self):
        portal_mode = PortalMode()
        portal_mode.enable()
        portal_mode.reset()

        # Ball traveling extremely fast (jumping across portal in 1 frame)
        p0 = Vector2D(portal_mode.portal_a_pos.x - 40.0, portal_mode.portal_a_pos.y)
        p1 = Vector2D(portal_mode.portal_a_pos.x + 40.0, portal_mode.portal_a_pos.y)

        threshold = portal_mode.radius + 10.0
        hit = portal_mode._check_swept_intersection(p0, p1, portal_mode.portal_a_pos, threshold)
        self.assertTrue(hit)


class TestPowerupMode(unittest.TestCase):
    def setUp(self):
        class MockGame:
            def __init__(self):
                self.engine = PongEngine()
        self.game = MockGame()
        self.powerup_mode = PowerupMode()
        self.powerup_mode.init(self.game)
        self.powerup_mode.enable()
        self.powerup_mode.reset()

    def test_freeze_powerup_immobility(self):
        self.powerup_mode.player_powerups[1] = PowerupType.FREEZE
        activated = self.powerup_mode.activate_powerup(1)
        self.assertTrue(activated)

        opponent_paddle = self.game.engine.right_paddle
        self.assertAlmostEqual(opponent_paddle.frozen_timer, FREEZE_DURATION)

        # Try to move frozen paddle
        initial_y = opponent_paddle.center_y
        opponent_paddle.move_dir = 1
        opponent_paddle.update(0.5)

        # Paddle center_y should not change while frozen
        self.assertEqual(opponent_paddle.center_y, initial_y)
        self.assertAlmostEqual(opponent_paddle.frozen_timer, FREEZE_DURATION - 0.5)

    def test_laser_hits_paddle_push(self):
        self.powerup_mode.player_powerups[1] = PowerupType.LASER
        self.powerup_mode.activate_powerup(1)

        self.assertEqual(len(self.powerup_mode.lasers), 1)
        laser = self.powerup_mode.lasers[0]

        # Place laser colliding with right paddle
        opponent = self.game.engine.right_paddle
        initial_x = opponent.center_x
        laser.pos = Vector2D(opponent.center_x, opponent.center_y)

        consumed = self.powerup_mode._check_laser_collisions(laser)
        self.assertTrue(consumed)
        # Opponent paddle was knocked back toward right wall
        self.assertGreater(opponent.center_x, initial_x)

    def test_laser_destroys_ball_no_point(self):
        self.powerup_mode.player_powerups[1] = PowerupType.LASER
        self.powerup_mode.activate_powerup(1)
        laser = self.powerup_mode.lasers[0]

        ball = self.game.engine.ball
        laser.pos = Vector2D(ball.pos.x, ball.pos.y)

        initial_p1_score = self.game.engine.score_p1
        consumed = self.powerup_mode._check_laser_collisions(laser)
        self.assertTrue(consumed)

        # Ball should be neutralized with reserve scheduled
        self.assertGreater(self.powerup_mode.ball_reserve_timer, 0.0)
        self.assertEqual(self.game.engine.score_p1, initial_p1_score)

    def test_ghost_ball_flicker_and_crossing(self):
        self.powerup_mode.player_powerups[1] = PowerupType.GHOST_BALL
        self.powerup_mode.activate_powerup(1)

        ball = self.game.engine.ball
        center_x = SCREEN_WIDTH * 0.5
        ball.vel = Vector2D(500.0, 0.0)  # Heading toward P2

        # Far from net: visible
        ball.pos = Vector2D(center_x - 300.0, SCREEN_HEIGHT * 0.5)
        self.powerup_mode.on_ball_update(ball, 0.016)
        self.assertTrue(ball.is_visible)

        # Right before net (within 0.20s * 500 = 100px window): invisible
        ball.pos = Vector2D(center_x - 40.0, SCREEN_HEIGHT * 0.5)
        self.powerup_mode.on_ball_update(ball, 0.016)
        self.assertFalse(ball.is_visible)

        # Crossed net: visible again and effect consumed
        ball.pos = Vector2D(center_x + 20.0, SCREEN_HEIGHT * 0.5)
        self.powerup_mode.on_ball_update(ball, 0.016)
        self.assertTrue(ball.is_visible)
        self.assertIsNone(self.powerup_mode.ghost_armed_for_player)

    def test_powerup_orb_collection_and_inventory_capacity(self):
        # Place orb in center
        orb1 = PowerupOrb(SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.5, PowerupType.FREEZE)
        self.powerup_mode.active_orbs = [orb1]
        ball = self.game.engine.ball
        ball.last_hit_player = 1
        ball.pos = Vector2D(SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.5)

        # Ball touches orb -> P1 collects
        self.powerup_mode.on_ball_update(ball, 0.016)
        self.assertEqual(self.powerup_mode.player_powerups[1], PowerupType.FREEZE)
        self.assertEqual(len(self.powerup_mode.active_orbs), 0)

        # Spawn a second orb; P1 already has a powerup, so second orb should NOT be collected
        orb2 = PowerupOrb(SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.5, PowerupType.LASER)
        self.powerup_mode.active_orbs = [orb2]
        self.powerup_mode.on_ball_update(ball, 0.016)
        # P1 inventory retains FREEZE, second orb remains on field
        self.assertEqual(self.powerup_mode.player_powerups[1], PowerupType.FREEZE)
        self.assertEqual(len(self.powerup_mode.active_orbs), 1)

    def test_multiple_simultaneous_orbs(self):
        orb1 = PowerupOrb(SCREEN_WIDTH * 0.4, SCREEN_HEIGHT * 0.4, PowerupType.FREEZE)
        orb2 = PowerupOrb(SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.5, PowerupType.LASER)
        orb3 = PowerupOrb(SCREEN_WIDTH * 0.6, SCREEN_HEIGHT * 0.6, PowerupType.GHOST_BALL)
        self.powerup_mode.active_orbs = [orb1, orb2, orb3]

        self.assertEqual(len(self.powerup_mode.active_orbs), 3)
        self.powerup_mode.update(1.0)
        # All 3 orbs still active after 1s
        self.assertEqual(len(self.powerup_mode.active_orbs), 3)

    def test_powerup_persistence_across_round_end(self):
        orb = PowerupOrb(SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.5, PowerupType.FREEZE)
        self.powerup_mode.active_orbs = [orb]
        self.powerup_mode.player_powerups[1] = PowerupType.LASER

        # Round ends (player loses/scores a point)
        self.powerup_mode.on_round_end()

        # Orbs on court and stored powerups must persist
        self.assertEqual(len(self.powerup_mode.active_orbs), 1)
        self.assertEqual(self.powerup_mode.player_powerups[1], PowerupType.LASER)

    def test_orb_15s_lifetime(self):
        orb = PowerupOrb(SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.5, PowerupType.FREEZE)
        self.assertEqual(orb.lifetime, 15.0)

        # Active after 14s
        still_alive = orb.update(14.0)
        self.assertTrue(still_alive)

        # Despawns after 15s total
        still_alive = orb.update(1.1)
        self.assertFalse(still_alive)

    def test_mode_cleanup_on_disable(self):
        self.powerup_mode.player_powerups[1] = PowerupType.FREEZE
        self.game.engine.left_paddle.frozen_timer = 2.0
        self.powerup_mode.active_orbs = [PowerupOrb(SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.5, PowerupType.LASER)]

        self.powerup_mode.disable()

        # All effects must be purged
        self.assertIsNone(self.powerup_mode.player_powerups[1])
        self.assertEqual(len(self.powerup_mode.active_orbs), 0)
        self.assertEqual(self.game.engine.left_paddle.frozen_timer, 0.0)


class TestChaosMode(unittest.TestCase):
    def test_chaos_mode_rotation_and_cleanup(self):
        wind = WindMode()
        portals = PortalMode()
        powerups = PowerupMode()
        chaos = ChaosMode(wind, portals, powerups)
        chaos.enable()
        chaos.reset()

        initial_submode = chaos.current_submode
        self.assertTrue(initial_submode.is_enabled)

        # Fast forward 60.1s
        chaos.update(60.1)

        # Submode must switch to a different mode
        new_submode = chaos.current_submode
        self.assertNotEqual(new_submode, initial_submode)
        self.assertTrue(new_submode.is_enabled)
        self.assertFalse(initial_submode.is_enabled)
        self.assertAlmostEqual(chaos.switch_timer, 60.0, delta=0.5)


class TestMenuNavigation(unittest.TestCase):
    def test_keyboard_menu_navigation(self):
        menu = Menu([("Opt 1", "OPT_1"), ("Opt 2", "OPT_2"), ("Opt 3", "OPT_3")])
        self.assertEqual(menu.selected_index, 0)

        # Down arrow
        down_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
        menu.handle_event(down_event)
        self.assertEqual(menu.selected_index, 1)

        # Enter key triggers action
        enter_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        action = menu.handle_event(enter_event)
        self.assertEqual(action, "OPT_2")

    def test_player_select_menu_actions(self):
        player_menu = Menu([
            ("1. One Player (vs AI)", "ONE_PLAYER"),
            ("2. Two Player (Local 1v1)", "TWO_PLAYER")
        ])
        # Default index 0 is One Player
        enter_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        self.assertEqual(player_menu.handle_event(enter_event), "ONE_PLAYER")

        # Navigate down
        down_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
        player_menu.handle_event(down_event)
        self.assertEqual(player_menu.selected_index, 1)
        self.assertEqual(player_menu.handle_event(enter_event), "TWO_PLAYER")


if __name__ == "__main__":
    unittest.main()
