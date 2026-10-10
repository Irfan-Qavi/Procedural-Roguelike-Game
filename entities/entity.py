"""
Base Entity class for actors in the dungeon (Player, Enemies, NPCs).
"""
from typing import Tuple, List, Optional
import pygame
from config import TILE_SIZE


class Entity:
    """Base class for all interactive physical actors."""

    def __init__(self, x: float, y: float, width: int, height: int, color: Tuple[int, int, int]) -> None:
        self.pos: pygame.math.Vector2 = pygame.math.Vector2(x, y)
        self.vel: pygame.math.Vector2 = pygame.math.Vector2(0, 0)
        self.width: int = width
        self.height: int = height
        self.color: Tuple[int, int, int] = color

        # Collision hitbox (centered or bottom-aligned for good depth feel)
        self.hitbox_rect: pygame.Rect = pygame.Rect(
            int(self.pos.x - self.width / 2),
            int(self.pos.y - self.height / 2),
            self.width,
            self.height,
        )

        # Health & State
        self.health: float = 1.0
        self.max_health: float = 1.0
        self.invulnerable_timer: float = 0.0
        self.flash_timer: float = 0.0
        self.is_dead: bool = False

    def update_hitbox(self) -> None:
        """Update rectangle position based on float vector position."""
        self.hitbox_rect.x = int(self.pos.x - self.width / 2)
        self.hitbox_rect.y = int(self.pos.y - self.height / 2)

    def move_and_collide(self, dt: float, solid_tiles: list, obstacles: list) -> None:
        """
        Move entity with separate X and Y Axis-Aligned Bounding Box (AABB) collision checks.
        Prevents corner snagging and wall clipping.
        """
        # Horizontal Movement
        self.pos.x += self.vel.x * dt
        self.update_hitbox()
        for tile in solid_tiles:
            if self.hitbox_rect.colliderect(tile.rect):
                if self.vel.x > 0:  # Moving right
                    self.hitbox_rect.right = tile.rect.left
                    self.pos.x = self.hitbox_rect.centerx
                elif self.vel.x < 0:  # Moving left
                    self.hitbox_rect.left = tile.rect.right
                    self.pos.x = self.hitbox_rect.centerx

        for obs in obstacles:
            if not obs.is_destroyed and self.hitbox_rect.colliderect(obs.rect):
                if self.vel.x > 0:
                    self.hitbox_rect.right = obs.rect.left
                    self.pos.x = self.hitbox_rect.centerx
                elif self.vel.x < 0:
                    self.hitbox_rect.left = obs.rect.right
                    self.pos.x = self.hitbox_rect.centerx

        # Vertical Movement
        self.pos.y += self.vel.y * dt
        self.update_hitbox()
        for tile in solid_tiles:
            if self.hitbox_rect.colliderect(tile.rect):
                if self.vel.y > 0:  # Moving down
                    self.hitbox_rect.bottom = tile.rect.top
                    self.pos.y = self.hitbox_rect.centery
                elif self.vel.y < 0:  # Moving up
                    self.hitbox_rect.top = tile.rect.bottom
                    self.pos.y = self.hitbox_rect.centery

        for obs in obstacles:
            if not obs.is_destroyed and self.hitbox_rect.colliderect(obs.rect):
                if self.vel.y > 0:
                    self.hitbox_rect.bottom = obs.rect.top
                    self.pos.y = self.hitbox_rect.centery
                elif self.vel.y < 0:
                    self.hitbox_rect.top = obs.rect.bottom
                    self.pos.y = self.hitbox_rect.centery

    def take_damage(self, amount: float, knockback: Optional[pygame.math.Vector2] = None) -> bool:
        """Apply damage and trigger flash timer. Returns True if damage was taken."""
        if self.invulnerable_timer > 0 or self.is_dead:
            return False
        self.health -= amount
        self.flash_timer = 0.15
        if knockback and knockback.length() > 0:
            self.vel += knockback
        if self.health <= 0:
            self.health = 0
            self.is_dead = True
        return True

    def update(self, dt: float) -> None:
        """Update base cooldowns and timers."""
        if self.invulnerable_timer > 0:
            self.invulnerable_timer = max(0.0, self.invulnerable_timer - dt)
        if self.flash_timer > 0:
            self.flash_timer = max(0.0, self.flash_timer - dt)

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int]) -> None:
        """Render entity on surface with camera offset."""
        ox, oy = camera_offset
        dest_rect = self.hitbox_rect.copy()
        dest_rect.x += ox
        dest_rect.y += oy

        color = (255, 255, 255) if self.flash_timer > 0 else self.color
        pygame.draw.rect(surface, color, dest_rect)
