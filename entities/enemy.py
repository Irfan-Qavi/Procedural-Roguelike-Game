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
