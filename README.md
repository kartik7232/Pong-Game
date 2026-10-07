# 2D High-Performance Classic Arcade Pong Engine
**Role:** Member A (Core Logic & Physics Lead)  
**Tech Stack:** Python 3.12, Pygame 2.6  

---

## 🌟 Architectural Highlights

1. **Deterministic Game Loop**: Fixed 60 FPS update clock using `pygame.time.Clock()` with delta-time (`dt`) scaling guaranteeing sub-16.6ms frame execution.
2. **Kinematics & Boundary Physics**: Floating-point continuous 2D position translation ($p_{t+\Delta t} = p_t + v \cdot \Delta t$) and wall reflections with hard boundary re-positioning to prevent boundary sticking and tunneling.
3. **Advanced Collision & Deflections**: Axis-Aligned Bounding Box (AABB) intersection testing coupled with non-linear trigonometric angle deflection:
   $$\theta = \left(\frac{y_{\text{ball}} - y_{\text{paddle}}}{\frac{h_{\text{paddle}}}{2} + r}\right) \times \theta_{\max}$$
4. **Dynamic Velocity Ramping**: Accelerates ball speed by **7% (1.07x multiplier)** after every successful paddle bounce, capped at `MAX_BALL_SPEED` (1200 px/s).
5. **Modular Subsystem Interfaces**:
   - **Member B (Inputs & AI)**: Clean paddle direction control API (`set_paddle_movement`) and state vector exporter (`get_state_vector`).
   - **Member C (VFX & Audio)**: Event callback bus triggering on `PADDLE_HIT`, `WALL_HIT`, and `SCORE`.

---

## 📁 Repository Structure

```
Pong-Game/
├── engine/
│   ├── __init__.py
│   ├── config.py         # Central display, physics, key bindings, & mode tunables
│   ├── physics.py        # Vector2D, AABB math, non-linear deflections, boundary clamping
│   ├── entities.py       # Ball and Paddle entity encapsulated state, frozen timer & knockback
│   ├── game_engine.py    # PongEngine state manager, event bus & 60 FPS clock handler
│   ├── state.py          # SceneState enum definitions (MAIN_MENU, PLAYING, PAUSED, etc.)
│   ├── ui.py             # Interactive Menu component with keyboard & mouse navigation
│   ├── tutorial.py       # Multi-page tutorial viewer with live visual demos
│   └── modes/
│       ├── __init__.py
│       ├── base.py       # GameMode abstract base interface
│       ├── mode_manager.py # ModeManager coordinating active modes
│       ├── wind_mode.py  # Mode 1: 10s cycle, 4 directions, acceleration
│       ├── portal_mode.py # Mode 2: Swept collision, velocity-preserving wormholes
│       ├── powerup_mode.py# Mode 3: Freeze, Laser, and Ghost Ball abilities
│       └── chaos_mode.py # Mode 4: 60s rotation reusing Wind, Portals, Powerups
├── tests/
│   ├── __init__.py
│   ├── test_physics.py   # Unit test suite verifying collisions, speed scaling & clamping
│   └── test_modes.py     # Unit tests verifying all 4 modes, transitions, and timers
├── main.py               # Production executable app with scene state machine & HUD
└── README.md             # Architecture documentation & technical defense script
```

---

## 🎮 Selectable Game Modes

1. **Wind Mode**: 10s cycle (8s calm, 2s active). Accelerates ball in one of 4 uniform random directions (UP, DOWN, LEFT, RIGHT). Includes pre-wind warning indicator and animated streak particles.
2. **Portals Mode**: Two linked pulsing wormhole rings. Teleports the ball bidirectionally while preserving velocity vector exactly. Features continuous swept-segment collision testing to eliminate tunneling at max ball speeds and a 0.3s cooldown against looping.
3. **Powerup Mode**: Central zone orb spawns with enlarged **28px hitboxes** (~76px effective ball collision zone). Up to **4 simultaneous orbs** co-exist on court, lasting **15.0s** each and **persisting across point losses/round resets**.
   - **Freeze [F]**: Freezes opponent paddle for 2.0s with ice tint and countdown bar.
   - **Laser [L]**: Fires high-speed projectile that destroys the ball (neutral re-serve without points) or knocks back opponent paddle.
   - **Ghost Ball [G]**: Ball turns invisible during approach window before crossing the center net.
4. **Chaos Mode**: Meta-mode that randomly selects and runs one mode for 60s before transitioning to a different mode (never repeats back-to-back), with a 2s transition announcement banner and full state cleanup.

---

## 🚀 How to Run

### 1. Launch Game
```bash
python main.py
```

### 2. Controls Reference Table

| Action | Player 1 (Left) | Player 2 (Right) | Menu / System |
| :--- | :--- | :--- | :--- |
| **Move Up** | `W` | `Up Arrow` | `Up Arrow` / `W` |
| **Move Down** | `S` | `Down Arrow` | `Down Arrow` / `S` |
| **Activate Powerup** | `D` | `Left Arrow` | - |
| **Select / Confirm** | - | - | `Enter` / `Space` / `Mouse Click` |
| **Pause / Back** | `ESC` | `ESC` | `ESC` |
| **AI Opponent Toggle** | `F2` | `F2` | - |
| **Examiner Telemetry (HUD)** | `F3` | `F3` | - |
| **Reset Match Score** | `R` | `R` | - |
| **Tutorial Navigation** | - | - | `Left Arrow` / `Right Arrow` / Buttons |

---

## ⚙️ Configuration Options (`engine/config.py`)

All speeds, sizes, timers, and color tokens live in `engine/config.py` without magic numbers:

- `WINNING_SCORE` (`7`): Score threshold required to trigger match completion (`GAME_OVER`).
- `WIND_CYCLE_DURATION` (`10.0`s) & `WIND_ACTIVE_DURATION` (`2.0`s): Cycle intervals for Wind Mode.
- `WIND_FORCE` (`400.0` px/s²): Acceleration applied to the ball during active wind.
- `PORTAL_RADIUS` (`26.0` px) & `PORTAL_COOLDOWN` (`0.3`s): Portal dimensions and teleport re-entry cooldown.
- `POWERUP_ORB_RADIUS` (`28.0` px): Enlarged collision radius yielding a 76px ball-orb contact threshold.
- `POWERUP_SPAWN_INTERVAL` (`6.0`s) & `POWERUP_LIFETIME` (`15.0`s): Spawn cadence and extended 15s court presence.
- `MAX_ACTIVE_ORBS` (`4`): Ceiling on concurrent collectible orbs on court.
- `POWERUP_CARRYOVER_BETWEEN_ROUNDS` (`True`): Uncollected orbs and player inventories persist across point losses.
- `FREEZE_DURATION` (`2.0`s): Opponent immobility duration.
- `LASER_SPEED` (`1400.0` px/s) & `LASER_PUSH` (`40.0` px): Laser projectile velocity and paddle knockback displacement.
- `GHOST_BALL_WINDOW` (`0.20`s): Pre-net crossing invisibility threshold.
- `CHAOS_MODE_DURATION` (`60.0`s): Duration each mode remains active in Chaos Mode before shifting.

---

## 🧪 Execute Automated Unit Tests

```bash
python -m unittest discover -s tests
```
Runs 31 test cases validating kinematics, boundary clamping, angle deflections, wind cycles, swept portal collisions, enlarged multi-orb powerup lifecycles, point-loss persistence, and the player selection state transition.

---

## 🎤 Examiner Technical Defense Script (Extended Architecture)

> **Point 1: Scene State Machine & Player Selection Transition**  
> *"The application encapsulates state into a finite state machine (`SceneState`), cleanly transitioning between `MAIN_MENU` -> `PLAYER_SELECT` -> `PLAYING`, as well as `PAUSED`, `GAME_OVER`, `TUTORIAL`, and `EXIT_CONFIRM`. UI menus accept dual input: discrete keyboard navigation (`Up`/`Down`/`Enter`/`Esc`) and continuous pointer coordinates, eliminating input contention."*

> **Point 2: Swept-Segment Anti-Tunneling & Vector Preservation in Portals**  
> *"Fast-moving balls (traveling up to 1200 px/s) can jump 20+ pixels in a single 60 FPS tick. Our Portals implementation avoids discrete point tests by performing continuous swept-segment distance checks ($d(C, P_0 \to P_1) \le R_{\text{portal}} + R_{\text{ball}}$), guaranteeing zero tunneling. Entry velocity vectors ($\vec{v}$) are preserved identically at exit."*

> **Point 3: Multi-Orb Concurrency & Point-Loss Persistence**  
> *"Powerup Mode supports up to 4 concurrent orbs with an expanded 28px radius (76px effective collision diameter) and 15.0s lifespan. When a player scores, `on_round_end()` preserves active court orbs rather than wiping them, maintaining rally flow and maximizing strategic ability usage."*

> **Point 4: Self-Contained Mode Interface & Polymorphic Chaos Rotation**  
> *"All four game modes implement the polymorphic `GameMode` interface (`init`, `reset`, `update`, `draw`, `on_ball_update`, `on_round_start`, `on_round_end`, `enable`, `disable`). Chaos Mode achieves zero code duplication by composing the existing Wind, Portals, and Powerup instances, enforcing strict 60s rotation without back-to-back repetitions and purging all stale timers/entities on shift."*