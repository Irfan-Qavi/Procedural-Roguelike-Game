"""
Game Configuration and Constants.
Defines display parameters, color palettes, grid configurations, and default balance metrics.
"""

# Display & Engine settings
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
TITLE = "Binding of Python: Procedural Roguelike"

# Tile & Room Dimensions
TILE_SIZE = 48  # Pixels per tile
ROOM_GRID_WIDTH = 15  # Tiles across inside room
ROOM_GRID_HEIGHT = 11  # Tiles high inside room

# Room pixel dimensions
ROOM_PIXEL_WIDTH = ROOM_GRID_WIDTH * TILE_SIZE
ROOM_PIXEL_HEIGHT = ROOM_GRID_HEIGHT * TILE_SIZE

# Color Palette (Dark Dungeon Aesthetic)
COLOR_BG = (16, 14, 23)
COLOR_WALL = (45, 38, 56)
COLOR_WALL_OUTLINE = (30, 24, 38)
COLOR_FLOOR = (82, 75, 96)
COLOR_FLOOR_ALT = (74, 67, 88)
COLOR_DOOR = (194, 133, 62)
COLOR_DOOR_FRAME = (120, 80, 36)
COLOR_DOOR_LOCKED = (180, 40, 40)

# Entities Colors
COLOR_PLAYER = (86, 172, 236)
COLOR_PLAYER_EYE = (255, 255, 255)
COLOR_PLAYER_PUPIL = (20, 30, 45)
COLOR_TEAR = (130, 205, 255)

COLOR_ENEMY_CHASER = (220, 70, 70)
COLOR_ENEMY_RANGER = (175, 65, 195)
COLOR_ENEMY_BOSS = (195, 35, 45)
COLOR_ENEMY_BULLET = (255, 105, 90)

# Destructible & Items
COLOR_POT = (160, 110, 65)
COLOR_CHEST = (215, 160, 40)
COLOR_CHEST_OUTLINE = (130, 90, 20)
COLOR_COIN = (250, 215, 60)
COLOR_HEART = (235, 55, 80)
COLOR_KEY = (240, 200, 70)
COLOR_STAT_UP = (90, 230, 130)

# UI & Text
COLOR_WHITE = (245, 245, 250)
COLOR_GRAY = (140, 140, 150)
COLOR_DARK_GRAY = (40, 40, 50)
COLOR_BLACK = (10, 10, 12)
COLOR_HUD_BG = (22, 20, 30, 210)
COLOR_MINIMAP_BG = (15, 15, 20, 180)
COLOR_MINIMAP_ROOM = (70, 70, 85)
COLOR_MINIMAP_CURRENT = (240, 230, 100)
COLOR_MINIMAP_BOSS = (230, 60, 60)
COLOR_MINIMAP_TREASURE = (240, 190, 40)

# Player Balance Defaults
PLAYER_SPEED = 240.0         # Pixels per second
PLAYER_MAX_HEALTH = 6        # 3 full hearts (each heart = 2 HP)
PLAYER_FIRE_COOLDOWN = 0.28  # Seconds between shots (~3.5 tears/sec)
PLAYER_DAMAGE = 3.5          # Damage per tear
PLAYER_BULLET_SPEED = 460.0  # Pixels per second
PLAYER_BULLET_RANGE = 420.0  # Max travel distance
PLAYER_FRICTION = 0.82       # Velocity dampening per frame (~60fps)

# Enemy Balance Defaults
CHASER_SPEED = 140.0
CHASER_HEALTH = 10.0
CHASER_DAMAGE = 1

RANGER_SPEED = 90.0
RANGER_HEALTH = 8.0
RANGER_DAMAGE = 1
RANGER_FIRE_RATE = 1.6
RANGER_BULLET_SPEED = 260.0

BOSS_HEALTH = 85.0
BOSS_SPEED = 85.0
BOSS_DAMAGE = 2
BOSS_FIRE_RATE = 1.1

# Dungeon Generator
MIN_ROOMS = 7
MAX_ROOMS = 9
