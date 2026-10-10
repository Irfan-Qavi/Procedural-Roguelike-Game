# Binding of Python: Procedural Roguelike

A top-down, procedurally generated 2D roguelike game built with Python and Pygame, inspired by classic roguelikes like *The Binding of Isaac*.

All graphics, particle effects, and user interfaces are generated procedurally with Pygame primitives and custom surfaces—requiring zero external asset downloads.

---

## Features

- **Procedural Dungeon Floor Generation**:
  - Frontier-growth random-walk algorithm generating 5 to 9 interconnected grid rooms.
  - Automatically identifies dead ends to designate a **Start Room**, a guaranteed **Treasure Room** (with golden chest rewards), normal **Enemy Rooms**, and a climactic **Boss Room**.
  - Passages and doorways seal during encounters until all enemies in the room are cleared.
- **Physics & Collision Physics**:
  - Vector math movement using `pygame.math.Vector2` with smooth acceleration and dampening friction.
  - Robust separate-axis AABB (Axis-Aligned Bounding Box) collision detection against wall tiles and solid props.
  - Smooth tracking Camera using exponential decay lerp (Linear Interpolation) with instant snap on door transitions.
- **Directional Combat & Breakables**:
  - 4-direction projectile attacks (tears) with variable damage, projectile speed, range, and cooldown rate.
  - Breakable pottery/urns that burst into debris particles and drop random coins and hearts.
- **Enemy AI & A\* Pathfinding**:
  - **Chaser (Zombie)**: Uses grid A\* search to hunt the player through corridors and around breakable objects.
  - **Ranger (Cultist)**: Maintains standoff distance and fires blood tears toward the player.
  - **Dungeon Boss**: Imposing demonic beast with high health bar and periodic 8-direction radial bullet storms.
  - Damage white-flashes, invulnerability timers, and knockback physics on hit.
- **Loot, Chests & Stat Power-ups**:
  - Collectible Hearts (half/full heart restoration), Gold Coins, and Skeleton Keys.
  - Treasure Chests with reward drops.
  - Permanent stat upgrades: **Damage Up**, **Speed Up**, and **Tear Rate Up**.
- **HUD & Minimap**:
  - Isaac-style heart containers displaying current and max health.
  - Real-time keys, coins, and stat readouts (DMG, SPD, TEARS/s).
  - Top-right dynamic Mini-map with exploration fog-of-war tracking.
  - Full-screen dungeon debug layout overview toggle (`M` key).
- **Game State Flow**:
  - Title Screen with instructions.
  - Game Over screen with instant replay (`R` key).
  - Boss Victory screen.

---

## Project Structure

```
├── .gitignore             # Ignore __pycache__, env, etc.
├── requirements.txt       # pygame dependency
├── main.py                # Main executable entry point
├── config.py              # Constants, dimensions, colors, and balance stats
├── engine/                # Core engine mechanics
│   ├── game.py            # Game loop, state machine, event handling
│   ├── camera.py          # Lerp-following camera
│   ├── particles.py       # Debris, sparks, tears, and dust particle emitter
│   └── pathfinding.py     # A* search algorithm for enemy AI
├── world/                 # World generation & tiles
│   ├── generator.py       # Procedural dungeon floor generator
│   ├── room.py            # Room layout, doors, and props
│   ├── tile.py            # Passable/impassable tile rendering
│   └── obstacle.py        # Destructible urns and crates
├── entities/              # Entity hierarchy
│   ├── entity.py          # Base physical actor with AABB collision
│   ├── player.py          # Player controls, stats, and rendering
│   ├── enemy.py           # Chaser, Ranger, and Boss state machines
│   └── projectile.py      # Player and enemy projectiles
├── items/                 # Collectibles & Chests
│   └── loot.py            # Pickups, stat upgrades, and chests
└── ui/                    # UI & HUD
    └── hud.py             # Heart containers, inventory, and minimap
```

---

## Installation & Running

### Requirements
- Python 3.10+
- Pygame 2.5.0+

### Setup
1. Clone or open the repository:
   ```bash
   cd "Procedural Roguelike Game"
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the game:
   ```bash
   python main.py
   ```

---

## Controls

| Key | Action |
| --- | --- |
| **W, A, S, D** | Move Character (Smooth physics with friction) |
| **Arrow Keys** (↑, ↓, ←, →) | Shoot Tears in 4 Directions |
| **M** | Toggle Full Map Debug Inspection |
| **R** | Restart Run (on Game Over or Victory screen) |
| **SPACE / ENTER** | Start Game / Return to Menu |
| **ESC** | Quit to Desktop |

---

## Procedural Algorithms Explained

1. **Dungeon Generation (Graph Expansion)**:
   - Starts with room `(0, 0)`.
   - In iterations, expands to open neighbor cardinal cells `(col + dx, row + dy)` while enforcing an adjacency density constraint (rooms cannot have more than 2 existing neighbors upon creation). This avoids clustered blobs and produces clean branch corridors.
   - Evaluates dead ends (degree 1 vertices) sorted by Manhattan distance from origin to assign the Boss room and Treasure room.
2. **A\* Pathfinding**:
   - Computes pathfinding across the room's tile grid for enemies using an admissible Manhattan distance heuristic `h(a, b) = |xa - xb| + |ya - yb|` with a min-heap priority queue. Avoids solid wall tiles and unbroken destructible urns.
3. **Smooth Camera Lerping**:
   - The camera uses time-step invariant lerp `cam += (target - cam) * (1.0 - 0.01^(dt * smoothness))` to eliminate jitter across variable frame rates.
