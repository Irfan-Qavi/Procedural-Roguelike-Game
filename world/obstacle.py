"""
Destructible environment obstacles (Pots, Crates) that can block movement and burst.
"""
from typing import Tuple, Optional
import pygame
from config import TILE_SIZE, COLOR_POT


class Destructible:
    """Breakable obstacle in dungeon rooms."""

    def __init__(self, grid_x: int, grid_y: int, health: float = 1.0) -> None:
        self.grid_x: int = grid_x
        self.grid_y: int = grid_y
        self.rect: pygame.Rect = pygame.Rect(grid_x * TILE_SIZE + 4, grid_y * TILE_SIZE + 4, TILE_SIZE - 8, TILE_SIZE - 8)
        self.health: float = health
        self.max_health: float = health
        self.is_destroyed: bool = False
        self.color: Tuple[int, int, int] = COLOR_POT

    def take_damage(self, amount: float) -> bool:
        """Apply damage; return True if just broke."""
        if self.is_destroyed:
            return False
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.is_destroyed = True
            return True
        return False

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int]) -> None:
        """Render ancient ceramic urn / pot."""
        if self.is_destroyed:
            return
        ox, oy = camera_offset
        dest_rect = self.rect.copy()
        dest_rect.x += ox
        dest_rect.y += oy

        # Shadow
        pygame.draw.ellipse(surface, (20, 16, 25), (dest_rect.x, dest_rect.bottom - 6, dest_rect.width, 8))

        # Pot main body
        body_rect = dest_rect.inflate(-4, -6)
        pygame.draw.ellipse(surface, self.color, body_rect)
        pygame.draw.ellipse(surface, (110, 70, 35), body_rect, 2)

        # Pot rim / neck
        rim_rect = pygame.Rect(dest_rect.centerx - 7, dest_rect.top + 2, 14, 6)
        pygame.draw.ellipse(surface, (185, 130, 80), rim_rect)
        pygame.draw.ellipse(surface, (70, 45, 20), rim_rect, 1)

        # Cracked detail if damaged
        if self.health < self.max_health:
            pygame.draw.line(surface, (70, 45, 20), (dest_rect.centerx, dest_rect.centery), (dest_rect.centerx + 5, dest_rect.centery + 7), 2)
