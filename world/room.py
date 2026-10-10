"""
Room representation and internal layout creation.
"""
from enum import Enum
from typing import List, Dict, Optional, Tuple
import pygame
from config import ROOM_GRID_WIDTH, ROOM_GRID_HEIGHT, TILE_SIZE
from world.tile import Tile, TileType


class RoomType(Enum):
    START = "Start"
    NORMAL = "Normal"
    TREASURE = "Treasure"
    BOSS = "Boss"


class Room:
    """Represents an individual room on the dungeon grid."""

    def __init__(self, grid_coord: Tuple[int, int], room_type: RoomType = RoomType.NORMAL) -> None:
        self.grid_coord: Tuple[int, int] = grid_coord  # (col, row) on the dungeon layout
        self.room_type: RoomType = room_type
        self.doors: Dict[str, Optional[Tuple[int, int]]] = {
            "N": None,
            "S": None,
            "E": None,
            "W": None,
        }
        self.door_locked: Dict[str, bool] = {
            "N": False,
            "S": False,
            "E": False,
            "W": False,
        }
        self.visited: bool = False
        self.cleared: bool = (room_type == RoomType.START or room_type == RoomType.TREASURE)

        # Entity lists in this room
        self.enemies: list = []
        self.projectiles: list = []
        self.obstacles: list = []  # Breakables (pots/crates)
        self.pickups: list = []    # Hearts, coins, keys, items

        # Tiles grid: 2D list [y][x]
        self.tiles: List[List[Tile]] = []
        self._build_tiles()

    def _build_tiles(self) -> None:
        """Construct the default boundary wall and floor tiles."""
        self.tiles = []
        for y in range(ROOM_GRID_HEIGHT):
            row: List[Tile] = []
            for x in range(ROOM_GRID_WIDTH):
                # Outer border tiles are walls
                if x == 0 or x == ROOM_GRID_WIDTH - 1 or y == 0 or y == ROOM_GRID_HEIGHT - 1:
                    row.append(Tile(x, y, TileType.WALL))
                else:
                    row.append(Tile(x, y, TileType.FLOOR))
            self.tiles.append(row)

    def update_doors(self) -> None:
        """Re-carve door tiles based on active connections."""
        mid_x = ROOM_GRID_WIDTH // 2
        mid_y = ROOM_GRID_HEIGHT // 2

        # North door
        if self.doors["N"] is not None:
            tile_type = TileType.DOOR_LOCKED if self.door_locked["N"] else TileType.DOOR
            self.tiles[0][mid_x] = Tile(mid_x, 0, tile_type, door_direction="N")
        else:
            self.tiles[0][mid_x] = Tile(mid_x, 0, TileType.WALL)

        # South door
        if self.doors["S"] is not None:
            tile_type = TileType.DOOR_LOCKED if self.door_locked["S"] else TileType.DOOR
            self.tiles[ROOM_GRID_HEIGHT - 1][mid_x] = Tile(mid_x, ROOM_GRID_HEIGHT - 1, tile_type, door_direction="S")
        else:
            self.tiles[ROOM_GRID_HEIGHT - 1][mid_x] = Tile(mid_x, ROOM_GRID_HEIGHT - 1, TileType.WALL)

        # West door
        if self.doors["W"] is not None:
            tile_type = TileType.DOOR_LOCKED if self.door_locked["W"] else TileType.DOOR
            self.tiles[mid_y][0] = Tile(0, mid_y, tile_type, door_direction="W")
        else:
            self.tiles[mid_y][0] = Tile(0, mid_y, TileType.WALL)

        # East door
        if self.doors["E"] is not None:
            tile_type = TileType.DOOR_LOCKED if self.door_locked["E"] else TileType.DOOR
            self.tiles[mid_y][ROOM_GRID_WIDTH - 1] = Tile(ROOM_GRID_WIDTH - 1, mid_y, tile_type, door_direction="E")
        else:
            self.tiles[mid_y][ROOM_GRID_WIDTH - 1] = Tile(ROOM_GRID_WIDTH - 1, mid_y, TileType.WALL)

    def get_door_spawn_pos(self, direction: str) -> pygame.math.Vector2:
        """
        Return the player spawn position (in room coordinates) when entering
        from a door at `direction`. Position is offset into the room.
        """
        mid_x = (ROOM_GRID_WIDTH // 2) * TILE_SIZE + TILE_SIZE // 2
        mid_y = (ROOM_GRID_HEIGHT // 2) * TILE_SIZE + TILE_SIZE // 2

        if direction == "N":  # Entering from North door (so player spawns near top, facing south)
            return pygame.math.Vector2(mid_x, TILE_SIZE * 1.6)
        elif direction == "S":  # Entering from South door
            return pygame.math.Vector2(mid_x, (ROOM_GRID_HEIGHT - 1.6) * TILE_SIZE)
        elif direction == "W":  # Entering from West door
            return pygame.math.Vector2(TILE_SIZE * 1.6, mid_y)
        elif direction == "E":  # Entering from East door
            return pygame.math.Vector2((ROOM_GRID_WIDTH - 1.6) * TILE_SIZE, mid_y)
        return pygame.math.Vector2(mid_x, mid_y)

    def get_solid_tiles(self) -> List[Tile]:
        """Return list of all solid barrier tiles in this room."""
        return [tile for row in self.tiles for tile in row if tile.is_solid]

    def get_door_tiles(self) -> List[Tile]:
        """Return list of all door tiles in this room."""
        return [tile for row in self.tiles for tile in row if tile.tile_type in (TileType.DOOR, TileType.DOOR_LOCKED)]

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int]) -> None:
        """Render all tiles in this room."""
        ox, oy = camera_offset
        for row in self.tiles:
            for tile in row:
                tile.draw(surface, ox, oy)
