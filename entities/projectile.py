"""
Projectiles (Tears/Bullets) for Player and Enemy combat.
"""
from typing import Tuple, List, Optional
import pygame
from config import COLOR_TEAR


class Projectile:
    """Moving tear/bullet projectile."""

    def __init__(
        self,
        x: float,
        y: float,
        direction: pygame.math.Vector2,
        speed: float,
        damage: float,
        max_range: float,
        is_enemy: bool = False,
        color: Tuple[int, int, int] = COLOR_TEAR,
        radius: int = 5,
    ) -> None:
        self.pos: pygame.math.Vector2 = pygame.math.Vector2(x, y)
        self.vel: pygame.math.Vector2 = direction.normalize() * speed if direction.length_squared() > 0 else pygame.math.Vector2(0, 0)
        self.damage: float = damage
        self.max_range: float = max_range
        self.distance_traveled: float = 0.0
        self.is_enemy: bool = is_enemy
        self.color: Tuple[int, int, int] = color
        self.radius: int = radius
        self.is_dead: bool = False

        self.rect: pygame.Rect = pygame.Rect(
            int(self.pos.x - radius),
            int(self.pos.y - radius),
            radius * 2,
            radius * 2,
        )

    def update(self, dt: float, solid_tiles: list, obstacles: list) -> bool:
        """
        Advance projectile, perform collision with walls and breakable obstacles.
        Returns True if collided (destroyed).
        """
        move_step = self.vel * dt
        self.pos += move_step
        self.distance_traveled += move_step.length()

        # Update rect
        self.rect.x = int(self.pos.x - self.radius)
        self.rect.y = int(self.pos.y - self.radius)

        # Range limit check
        if self.distance_traveled >= self.max_range:
            self.is_dead = True
            return True

        # Solid wall collision
        for tile in solid_tiles:
            if self.rect.colliderect(tile.rect):
                self.is_dead = True
                return True

        # Destructible obstacle collision
        for obs in obstacles:
            if not obs.is_destroyed and self.rect.colliderect(obs.rect):
                obs.take_damage(self.damage)
                self.is_dead = True
                return True

        return False

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int]) -> None:
        """Render teardrop projectile with shine highlight."""
        if self.is_dead:
            return
        ox, oy = camera_offset
        px = int(self.pos.x + ox)
        py = int(self.pos.y + oy)

        # Outer body
        pygame.draw.circle(surface, self.color, (px, py), self.radius)
        # Specular shine
        pygame.draw.circle(surface, (255, 255, 255), (px - 1, py - 2), max(1, self.radius // 3))
