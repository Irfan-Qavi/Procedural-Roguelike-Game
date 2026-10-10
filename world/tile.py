"""
Tile types and representations.
"""
from enum import Enum
import pygame
from config import (
    TILE_SIZE,
    COLOR_WALL,
    COLOR_WALL_OUTLINE,
    COLOR_FLOOR,
    COLOR_FLOOR_ALT,
    COLOR_DOOR,
    COLOR_DOOR_FRAME,
    COLOR_DOOR_LOCKED,
)


class TileType(Enum):
    FLOOR = 0
    WALL = 1
    DOOR = 2
    DOOR_LOCKED = 3


class Tile:
    """Represents a single grid cell in a room."""

    def __init__(self, x: int, y: int, tile_type: TileType, door_direction: str | None = None) -> None:
        """
        x, y: Grid coordinates within the room.
        door_direction: 'N', 'S', 'E', 'W' if this is a door tile.
        """
        self.grid_x = x
        self.grid_y = y
        self.tile_type = tile_type
        self.door_direction = door_direction
        self.rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

    @property
    def is_solid(self) -> bool:
        """Wall tiles and locked doors are solid to entities."""
        return self.tile_type in (TileType.WALL, TileType.DOOR_LOCKED)

    def draw(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0) -> None:
        """Render tile with slight procedural shading."""
        screen_rect = pygame.Rect(
            self.rect.x + offset_x,
            self.rect.y + offset_y,
            TILE_SIZE,
            TILE_SIZE,
        )

        if self.tile_type == TileType.WALL:
            # Dark stone wall with beveled border
            pygame.draw.rect(surface, COLOR_WALL, screen_rect)
            pygame.draw.rect(surface, COLOR_WALL_OUTLINE, screen_rect, 2)
            # Brick mortar accents
            mid_y = screen_rect.y + TILE_SIZE // 2
            pygame.draw.line(surface, COLOR_WALL_OUTLINE, (screen_rect.x, mid_y), (screen_rect.right, mid_y), 1)
        elif self.tile_type == TileType.FLOOR:
            # Checkerboard or subtle texture
            color = COLOR_FLOOR if (self.grid_x + self.grid_y) % 2 == 0 else COLOR_FLOOR_ALT
            pygame.draw.rect(surface, color, screen_rect)
            # Subtle corner dots for paved stone look
            pygame.draw.rect(surface, (color[0] - 8, color[1] - 8, color[2] - 8), screen_rect, 1)
        elif self.tile_type in (TileType.DOOR, TileType.DOOR_LOCKED):
            # Passable doorway or locked door
            color_frame = COLOR_DOOR_FRAME
            color_center = COLOR_DOOR_LOCKED if self.tile_type == TileType.DOOR_LOCKED else COLOR_DOOR
            pygame.draw.rect(surface, color_frame, screen_rect)
            inner_rect = screen_rect.inflate(-8, -8)
            pygame.draw.rect(surface, color_center, inner_rect)
            if self.tile_type == TileType.DOOR_LOCKED:
                # Keyhole emblem
                center = screen_rect.center
                pygame.draw.circle(surface, (30, 20, 20), (center[0], center[1] - 2), 4)
                pygame.draw.rect(surface, (30, 20, 20), (center[0] - 2, center[1], 4, 6))
