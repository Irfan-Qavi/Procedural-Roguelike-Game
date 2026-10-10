"""
Player entity with input handling, physics friction, and Isaac-style visual rendering.
"""
from typing import Tuple, List, Optional
import pygame
from config import (
    COLOR_PLAYER,
    COLOR_PLAYER_EYE,
    COLOR_PLAYER_PUPIL,
    PLAYER_SPEED,
    PLAYER_MAX_HEALTH,
    PLAYER_FIRE_COOLDOWN,
    PLAYER_DAMAGE,
    PLAYER_BULLET_SPEED,
    PLAYER_BULLET_RANGE,
    PLAYER_FRICTION,
)
from entities.entity import Entity


class Player(Entity):
    """Controllable player character."""

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, width=28, height=28, color=COLOR_PLAYER)
        # Dynamic stats
        self.max_health: int = PLAYER_MAX_HEALTH
        self.health: int = PLAYER_MAX_HEALTH
        self.move_speed: float = PLAYER_SPEED
        self.fire_cooldown: float = PLAYER_FIRE_COOLDOWN
        self.damage: float = PLAYER_DAMAGE
        self.bullet_speed: float = PLAYER_BULLET_SPEED
        self.bullet_range: float = PLAYER_BULLET_RANGE

        # Inventory
        self.coins: int = 0
        self.keys: int = 1
        self.items_collected: list = []

        # State timers
        self.shoot_timer: float = 0.0
        self.face_dir: pygame.math.Vector2 = pygame.math.Vector2(0, 1)  # Default facing south

    def handle_input(self) -> pygame.math.Vector2:
        """Read WASD keys for movement direction and Arrow keys for shooting direction."""
        keys = pygame.key.get_pressed()
        move_dir = pygame.math.Vector2(0, 0)

        # Movement with WASD
        if keys[pygame.K_w] or keys[pygame.K_z]:
            move_dir.y -= 1
        if keys[pygame.K_s]:
            move_dir.y += 1
        if keys[pygame.K_a] or keys[pygame.K_q]:
            move_dir.x -= 1
        if keys[pygame.K_d]:
            move_dir.x += 1

        if move_dir.length_squared() > 0:
            move_dir = move_dir.normalize()
            self.face_dir = pygame.math.Vector2(move_dir)

        # Check shoot input
        shoot_dir = pygame.math.Vector2(0, 0)
        if keys[pygame.K_UP]:
            shoot_dir.y -= 1
        elif keys[pygame.K_DOWN]:
            shoot_dir.y += 1
        elif keys[pygame.K_LEFT]:
            shoot_dir.x -= 1
        elif keys[pygame.K_RIGHT]:
            shoot_dir.x += 1

        return shoot_dir

    def update(self, dt: float, solid_tiles: list, obstacles: list) -> None:
        """Update physics with dampening and collision detection."""
        super().update(dt)

        # Input movement force
        keys = pygame.key.get_pressed()
        move_dir = pygame.math.Vector2(0, 0)
        if keys[pygame.K_w]:
            move_dir.y -= 1
        if keys[pygame.K_s]:
            move_dir.y += 1
        if keys[pygame.K_a]:
            move_dir.x -= 1
        if keys[pygame.K_d]:
            move_dir.x += 1

        if move_dir.length_squared() > 0:
            move_dir = move_dir.normalize()
            target_vel = move_dir * self.move_speed
            # Accelerate towards target velocity
            self.vel += (target_vel - self.vel) * min(1.0, 15.0 * dt)
        else:
            # Friction dampening when not pressing keys
            self.vel *= (PLAYER_FRICTION ** (dt * 60.0))
            if self.vel.length_squared() < 100:
                self.vel = pygame.math.Vector2(0, 0)

        # Shoot timer countdown
        if self.shoot_timer > 0:
            self.shoot_timer = max(0.0, self.shoot_timer - dt)

        # AABB move with collision
        self.move_and_collide(dt, solid_tiles, obstacles)

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int]) -> None:
        """Render Isaac-style round character with teardrop eyes."""
        ox, oy = camera_offset
        center_x = int(self.pos.x + ox)
        center_y = int(self.pos.y + oy)
        radius = self.width // 2

        # Invulnerability flicker
        if self.invulnerable_timer > 0 and int(self.invulnerable_timer * 15) % 2 == 0:
            return

        body_color = (255, 255, 255) if self.flash_timer > 0 else self.color

        # Round body
        pygame.draw.circle(surface, (40, 60, 90), (center_x, center_y + 2), radius)  # Drop shadow
        pygame.draw.circle(surface, body_color, (center_x, center_y), radius)
        pygame.draw.circle(surface, (40, 110, 170), (center_x, center_y), radius, 2)  # Outline

        # Big expressive Isaac teardrop eyes
        eye_offset_x = 5
        eye_offset_y = -2
        pupil_dir = self.face_dir * 1.5

        # Left eye
        pygame.draw.ellipse(surface, COLOR_PLAYER_EYE, (center_x - eye_offset_x - 3, center_y + eye_offset_y - 4, 7, 9))
        pygame.draw.circle(surface, COLOR_PLAYER_PUPIL, (int(center_x - eye_offset_x + pupil_dir.x), int(center_y + eye_offset_y + pupil_dir.y)), 2)

        # Right eye
        pygame.draw.ellipse(surface, COLOR_PLAYER_EYE, (center_x + eye_offset_x - 4, center_y + eye_offset_y - 4, 7, 9))
        pygame.draw.circle(surface, COLOR_PLAYER_PUPIL, (int(center_x + eye_offset_x + pupil_dir.x), int(center_y + eye_offset_y + pupil_dir.y)), 2)
