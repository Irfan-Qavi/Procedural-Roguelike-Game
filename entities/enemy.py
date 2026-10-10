"""
Enemy AI, State Machines, Pathfinding tracking, and distinct combat behaviors (Chaser, Ranger, Boss).
"""
from enum import Enum
from typing import Tuple, List, Optional, Set
import random
import pygame
from config import (
    TILE_SIZE,
    COLOR_ENEMY_CHASER,
    COLOR_ENEMY_RANGER,
    COLOR_ENEMY_BOSS,
    COLOR_ENEMY_BULLET,
    CHASER_SPEED,
    CHASER_HEALTH,
    CHASER_DAMAGE,
    RANGER_SPEED,
    RANGER_HEALTH,
    RANGER_DAMAGE,
    RANGER_FIRE_RATE,
    RANGER_BULLET_SPEED,
    BOSS_HEALTH,
    BOSS_SPEED,
    BOSS_DAMAGE,
    BOSS_FIRE_RATE,
)
from entities.entity import Entity
from entities.projectile import Projectile
from engine.pathfinding import astar_path


class EnemyState(Enum):
    WANDERING = "Wandering"
    CHASING = "Chasing"
    ATTACKING = "Attacking"


class Enemy(Entity):
    """Base class for all monster types with state machines and pathfinding."""

    def __init__(self, x: float, y: float, width: int, height: int, color: Tuple[int, int, int]) -> None:
        super().__init__(x, y, width, height, color)
        self.state: EnemyState = EnemyState.WANDERING
        self.state_timer: float = random.uniform(0.5, 1.5)
        self.damage_amount: float = 1.0
        self.target_path: List[Tuple[int, int]] = []
        self.repath_timer: float = 0.0

    def get_grid_pos(self) -> Tuple[int, int]:
        """Convert pixel center to room grid coordinate."""
        return (int(self.pos.x // TILE_SIZE), int(self.pos.y // TILE_SIZE))

    def update_ai(
        self,
        dt: float,
        player_pos: pygame.math.Vector2,
        blocked_cells: Set[Tuple[int, int]],
        room_projectiles: list,
    ) -> None:
        """Subclasses implement specific state logic."""
        pass


class ChaserEnemy(Enemy):
    """Fast melee zombie that hunts the player using A* pathfinding."""

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, width=26, height=26, color=COLOR_ENEMY_CHASER)
        self.health = CHASER_HEALTH
        self.max_health = CHASER_HEALTH
        self.damage_amount = CHASER_DAMAGE
        self.speed = CHASER_SPEED

    def update_ai(
        self,
        dt: float,
        player_pos: pygame.math.Vector2,
        blocked_cells: Set[Tuple[int, int]],
        room_projectiles: list,
    ) -> None:
        super().update(dt)
        self.repath_timer -= dt

        # Distance to player
        to_player = player_pos - self.pos
        dist = to_player.length()

        if dist < 450:
            self.state = EnemyState.CHASING
        else:
            self.state = EnemyState.WANDERING

        if self.state == EnemyState.CHASING:
            if self.repath_timer <= 0:
                self.repath_timer = 0.35  # Recalculate A* path periodically
                start_cell = self.get_grid_pos()
                goal_cell = (int(player_pos.x // TILE_SIZE), int(player_pos.y // TILE_SIZE))
                path = astar_path(start_cell, goal_cell, blocked_cells)
                if path and len(path) > 1:
                    self.target_path = path[1:]  # Next waypoint
                else:
                    self.target_path = []

            # Follow path or move direct if close
            if self.target_path:
                waypoint_grid = self.target_path[0]
                waypoint_world = pygame.math.Vector2(
                    waypoint_grid[0] * TILE_SIZE + TILE_SIZE // 2,
                    waypoint_grid[1] * TILE_SIZE + TILE_SIZE // 2,
                )
                to_wp = waypoint_world - self.pos
                if to_wp.length() < 12:
                    self.target_path.pop(0)
                elif to_wp.length_squared() > 0:
                    self.vel = to_wp.normalize() * self.speed
            else:
                if dist > 0:
                    self.vel = to_player.normalize() * self.speed
        else:
            # Wandering / Idle jitter
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state_timer = random.uniform(1.0, 2.0)
                angle = random.uniform(0, 6.28318)
                self.vel = pygame.math.Vector2(1, 0).rotate_rad(angle) * (self.speed * 0.4)

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int]) -> None:
        """Render aggressive red demonic crawler."""
        ox, oy = camera_offset
        center_x = int(self.pos.x + ox)
        center_y = int(self.pos.y + oy)
        radius = self.width // 2

        color = (255, 255, 255) if self.flash_timer > 0 else self.color
        # Horns/Spikes
        pygame.draw.polygon(
            surface,
            (160, 30, 30),
            [(center_x - 10, center_y - 8), (center_x - 14, center_y - 18), (center_x - 4, center_y - 12)],
        )
        pygame.draw.polygon(
            surface,
            (160, 30, 30),
            [(center_x + 10, center_y - 8), (center_x + 14, center_y - 18), (center_x + 4, center_y - 12)],
        )
        # Main round body
        pygame.draw.circle(surface, color, (center_x, center_y), radius)
        pygame.draw.circle(surface, (120, 20, 20), (center_x, center_y), radius, 2)
        # Glowing angry eyes
        pygame.draw.circle(surface, (255, 255, 120), (center_x - 5, center_y - 2), 3)
        pygame.draw.circle(surface, (255, 255, 120), (center_x + 5, center_y - 2), 3)


class RangerEnemy(Enemy):
    """Ranged cultist that stays at a distance and shoots blood projectiles at the player."""

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, width=24, height=24, color=COLOR_ENEMY_RANGER)
        self.health = RANGER_HEALTH
        self.max_health = RANGER_HEALTH
        self.damage_amount = RANGER_DAMAGE
        self.speed = RANGER_SPEED
        self.shoot_timer: float = random.uniform(0.8, 1.8)

    def update_ai(
        self,
        dt: float,
        player_pos: pygame.math.Vector2,
        blocked_cells: Set[Tuple[int, int]],
        room_projectiles: list,
    ) -> None:
        super().update(dt)
        self.shoot_timer -= dt

        to_player = player_pos - self.pos
        dist = to_player.length()

        # Keep safe distance (~180-260 pixels)
        if dist < 160:
            # Back away
            self.vel = -to_player.normalize() * self.speed
        elif dist > 270:
            # Approach
            self.vel = to_player.normalize() * self.speed
        else:
            # Strafe sideways
            perp = pygame.math.Vector2(-to_player.y, to_player.x).normalize()
            self.vel = perp * (self.speed * 0.7)

        # Shoot at player
        if self.shoot_timer <= 0 and dist < 420:
            self.shoot_timer = RANGER_FIRE_RATE
            dir_to_player = to_player.normalize()
            bullet = Projectile(
                self.pos.x,
                self.pos.y,
                dir_to_player,
                speed=RANGER_BULLET_SPEED,
                damage=self.damage_amount,
                max_range=380.0,
                is_enemy=True,
                color=COLOR_ENEMY_BULLET,
                radius=6,
            )
            room_projectiles.append(bullet)

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int]) -> None:
        """Render purple floating eye/cultist."""
        ox, oy = camera_offset
        dest_rect = self.hitbox_rect.copy()
        dest_rect.x += ox
        dest_rect.y += oy

        color = (255, 255, 255) if self.flash_timer > 0 else self.color
        # Diamond shape
        points = [
            (dest_rect.centerx, dest_rect.top),
            (dest_rect.right, dest_rect.centery),
            (dest_rect.centerx, dest_rect.bottom),
            (dest_rect.left, dest_rect.centery),
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, (90, 20, 110), points, 2)
        # Giant eye
        pygame.draw.circle(surface, (255, 240, 240), dest_rect.center, 5)
        pygame.draw.circle(surface, (200, 30, 60), dest_rect.center, 2)


class BossEnemy(Enemy):
    """Monstrous Dungeon Boss with multi-directional attacks and high health."""

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, width=54, height=54, color=COLOR_ENEMY_BOSS)
        self.health = BOSS_HEALTH
        self.max_health = BOSS_HEALTH
        self.damage_amount = BOSS_DAMAGE
        self.speed = BOSS_SPEED
        self.attack_timer: float = 1.0

    def update_ai(
        self,
        dt: float,
        player_pos: pygame.math.Vector2,
        blocked_cells: Set[Tuple[int, int]],
        room_projectiles: list,
    ) -> None:
        super().update(dt)
        self.attack_timer -= dt

        to_player = player_pos - self.pos
        dist = to_player.length()

        # Relentless lumbering pursuit
        if dist > 0:
            self.vel = to_player.normalize() * self.speed

        # Periodic radial ring / burst attack
        if self.attack_timer <= 0:
            self.attack_timer = BOSS_FIRE_RATE
            # 8-direction bullet ring
            for angle_deg in range(0, 360, 45):
                dir_vec = pygame.math.Vector2(1, 0).rotate(angle_deg)
                bullet = Projectile(
                    self.pos.x,
                    self.pos.y,
                    dir_vec,
                    speed=180.0,
                    damage=1.0,
                    max_range=440.0,
                    is_enemy=True,
                    color=COLOR_ENEMY_BULLET,
                    radius=7,
                )
                room_projectiles.append(bullet)

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int]) -> None:
        """Render imposing boss demon with health bar overhead."""
        ox, oy = camera_offset
        center_x = int(self.pos.x + ox)
        center_y = int(self.pos.y + oy)
        radius = self.width // 2

        color = (255, 255, 255) if self.flash_timer > 0 else self.color
        # Shadow
        pygame.draw.ellipse(surface, (15, 10, 18), (center_x - radius, center_y + radius - 10, self.width, 18))
        # Main body
        pygame.draw.circle(surface, color, (center_x, center_y), radius)
        pygame.draw.circle(surface, (100, 15, 20), (center_x, center_y), radius, 3)

        # Horns
        pygame.draw.polygon(surface, (70, 10, 15), [(center_x - 20, center_y - 12), (center_x - 30, center_y - 32), (center_x - 10, center_y - 20)])
        pygame.draw.polygon(surface, (70, 10, 15), [(center_x + 20, center_y - 12), (center_x + 30, center_y - 32), (center_x + 10, center_y - 20)])

        # Glowing demonic maw
        pygame.draw.ellipse(surface, (50, 10, 15), (center_x - 12, center_y + 4, 24, 12))
        # Yellow angry eyes
        pygame.draw.circle(surface, (255, 220, 60), (center_x - 12, center_y - 6), 6)
        pygame.draw.circle(surface, (255, 60, 40), (center_x - 12, center_y - 6), 2)
        pygame.draw.circle(surface, (255, 220, 60), (center_x + 12, center_y - 6), 6)
        pygame.draw.circle(surface, (255, 60, 40), (center_x + 12, center_y - 6), 2)

        # Boss health bar overhead
        bar_w = 64
        bar_h = 6
        bx = center_x - bar_w // 2
        by = center_y - radius - 14
        pct = max(0.0, self.health / self.max_health)
        pygame.draw.rect(surface, (40, 20, 20), (bx, by, bar_w, bar_h))
        pygame.draw.rect(surface, (220, 40, 40), (bx, by, int(bar_w * pct), bar_h))
        pygame.draw.rect(surface, (240, 240, 240), (bx, by, bar_w, bar_h), 1)
