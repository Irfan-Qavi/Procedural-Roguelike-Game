"""
Pickups, Chests, and Stat-modifying Items.
Includes Hearts, Coins, Keys, and Stat Power-ups (Damage Up, Speed Up, Tear Rate Up).
"""
from enum import Enum
from typing import Tuple, Optional
import math
import random
import pygame
from config import (
    COLOR_HEART,
    COLOR_COIN,
    COLOR_KEY,
    COLOR_STAT_UP,
    COLOR_CHEST,
    COLOR_CHEST_OUTLINE,
    TILE_SIZE,
)


class PickupType(Enum):
    HEART = "Heart"
    COIN = "Coin"
    KEY = "Key"
    STAT_DAMAGE = "Damage Up"
    STAT_SPEED = "Speed Up"
    STAT_TEAR_RATE = "Tear Rate Up"


class Pickup:
    """Collectible item dropped in rooms or spawned from chests."""

    def __init__(self, x: float, y: float, pickup_type: PickupType) -> None:
        self.pos: pygame.math.Vector2 = pygame.math.Vector2(x, y)
        self.pickup_type: PickupType = pickup_type
        self.is_collected: bool = False
        self.radius: int = 10
        self.float_timer: float = random.uniform(0, 6.28)
        self.rect: pygame.Rect = pygame.Rect(int(x - 10), int(y - 10), 20, 20)

    def update(self, dt: float) -> None:
        """Subtle floating/bobbing animation."""
        self.float_timer += dt * 3.0

    def apply_to_player(self, player) -> bool:
        """
        Apply effect to player stats or inventory.
        Returns True if successfully collected.
        """
        if self.pickup_type == PickupType.HEART:
            if player.health < player.max_health:
                player.health = min(player.max_health, player.health + 2)  # 1 full heart
                self.is_collected = True
                return True
            return False  # Don't consume if full health

        elif self.pickup_type == PickupType.COIN:
            player.coins += 1
            self.is_collected = True
            return True

        elif self.pickup_type == PickupType.KEY:
            player.keys += 1
            self.is_collected = True
            return True

        elif self.pickup_type == PickupType.STAT_DAMAGE:
            player.damage += 1.2
            player.items_collected.append("Damage Up")
            self.is_collected = True
            return True

        elif self.pickup_type == PickupType.STAT_SPEED:
            player.move_speed = min(400.0, player.move_speed + 35.0)
            player.items_collected.append("Speed Up")
            self.is_collected = True
            return True

        elif self.pickup_type == PickupType.STAT_TEAR_RATE:
            player.fire_cooldown = max(0.12, player.fire_cooldown * 0.82)
            player.items_collected.append("Tear Rate Up")
            self.is_collected = True
            return True

        return False

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int]) -> None:
        """Render distinct geometric pixel-style collectibles."""
        if self.is_collected:
            return
        ox, oy = camera_offset
        bob_offset = math.sin(self.float_timer) * 3.0
        cx = int(self.pos.x + ox)
        cy = int(self.pos.y + oy + bob_offset)

        # Shadow on floor
        pygame.draw.ellipse(surface, (15, 12, 20), (cx - 8, int(self.pos.y + oy) + 6, 16, 6))

        if self.pickup_type == PickupType.HEART:
            # Heart geometry
            pygame.draw.circle(surface, COLOR_HEART, (cx - 4, cy - 3), 4)
            pygame.draw.circle(surface, COLOR_HEART, (cx + 4, cy - 3), 4)
            pts = [(cx - 8, cy - 2), (cx + 8, cy - 2), (cx, cy + 7)]
            pygame.draw.polygon(surface, COLOR_HEART, pts)

        elif self.pickup_type == PickupType.COIN:
            # Gold coin
            pygame.draw.circle(surface, COLOR_COIN, (cx, cy), 7)
            pygame.draw.circle(surface, (180, 140, 20), (cx, cy), 7, 2)
            pygame.draw.circle(surface, (255, 240, 130), (cx - 1, cy - 1), 3)

        elif self.pickup_type == PickupType.KEY:
            # Skeleton Key
            pygame.draw.circle(surface, COLOR_KEY, (cx, cy - 4), 4, 2)
            pygame.draw.line(surface, COLOR_KEY, (cx, cy - 1), (cx, cy + 6), 2)
            pygame.draw.line(surface, COLOR_KEY, (cx, cy + 4), (cx + 3, cy + 4), 2)
            pygame.draw.line(surface, COLOR_KEY, (cx, cy + 6), (cx + 3, cy + 6), 2)

        elif self.pickup_type == PickupType.STAT_DAMAGE:
            # Red sword/spiked pentagram
            pts = [(cx, cy - 8), (cx + 7, cy + 6), (cx - 7, cy + 6)]
            pygame.draw.polygon(surface, (240, 60, 60), pts)
            pygame.draw.polygon(surface, (255, 255, 255), pts, 1)

        elif self.pickup_type == PickupType.STAT_SPEED:
            # Winged / Lightning boot
            pts = [(cx - 4, cy - 8), (cx + 4, cy - 3), (cx, cy - 1), (cx + 5, cy + 8), (cx - 3, cy + 2), (cx + 1, cy)]
            pygame.draw.polygon(surface, (70, 210, 245), pts)

        elif self.pickup_type == PickupType.STAT_TEAR_RATE:
            # Swirling blue vortex tear
            pygame.draw.circle(surface, (60, 180, 255), (cx, cy), 8)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 5, 2)
