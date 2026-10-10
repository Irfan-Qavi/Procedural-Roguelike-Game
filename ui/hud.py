"""
HUD (Heads-Up Display) and Mini-Map renderer.
Draws Isaac-style Heart containers, Key/Coin counters, live Player stats, and an interactive top-right mini-map.
"""
from typing import Dict, Tuple
import pygame
from config import (
    SCREEN_WIDTH,
    COLOR_WHITE,
    COLOR_HEART,
    COLOR_COIN,
    COLOR_KEY,
    COLOR_HUD_BG,
    COLOR_MINIMAP_BG,
    COLOR_MINIMAP_ROOM,
    COLOR_MINIMAP_CURRENT,
    COLOR_MINIMAP_BOSS,
    COLOR_MINIMAP_TREASURE,
    COLOR_GRAY,
)
from world.room import Room, RoomType


class HUD:
    """Renders game status overlay, health containers, resource inventory, and minimap."""

    def __init__(self) -> None:
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 13)
        self.title_font = pygame.font.SysFont("Arial", 22, bold=True)

    def draw_hearts(self, surface: pygame.Surface, health: int, max_health: int, start_x: int = 24, start_y: int = 20) -> None:
        """
        Draw Isaac-style heart containers.
        Each full container represents 2 hit points (half heart = 1 HP).
        """
        containers = max_health // 2
        spacing = 26

        for i in range(containers):
            cx = start_x + i * spacing
            cy = start_y
            hp_in_container = max(0, min(2, health - i * 2))

            # Empty heart container background
            pts_left = [(cx - 8, cy - 2), (cx, cy - 2), (cx, cy + 8)]
            pts_right = [(cx, cy - 2), (cx + 8, cy - 2), (cx, cy + 8)]
            pygame.draw.circle(surface, (50, 40, 50), (cx - 4, cy - 4), 4)
            pygame.draw.circle(surface, (50, 40, 50), (cx + 4, cy - 4), 4)
            pygame.draw.polygon(surface, (50, 40, 50), [(cx - 8, cy - 2), (cx + 8, cy - 2), (cx, cy + 8)])

            # Outer boundary
            pygame.draw.circle(surface, (90, 30, 40), (cx - 4, cy - 4), 4, 1)
            pygame.draw.circle(surface, (90, 30, 40), (cx + 4, cy - 4), 4, 1)

            if hp_in_container >= 1:
                # Left half filled
                pygame.draw.circle(surface, COLOR_HEART, (cx - 4, cy - 4), 4)
                pygame.draw.polygon(surface, COLOR_HEART, [(cx - 8, cy - 2), (cx, cy - 2), (cx, cy + 8)])

            if hp_in_container == 2:
                # Right half filled
                pygame.draw.circle(surface, COLOR_HEART, (cx + 4, cy - 4), 4)
                pygame.draw.polygon(surface, COLOR_HEART, [(cx, cy - 2), (cx + 8, cy - 2), (cx, cy + 8)])

    def draw_inventory(self, surface: pygame.Surface, player, start_x: int = 24, start_y: int = 48) -> None:
        """Draw Coins and Keys counters."""
        # Coins
        pygame.draw.circle(surface, COLOR_COIN, (start_x + 6, start_y + 8), 6)
        pygame.draw.circle(surface, (180, 140, 20), (start_x + 6, start_y + 8), 6, 1)
        coin_txt = self.font.render(f"x {player.coins:02d}", True, COLOR_WHITE)
        surface.blit(coin_txt, (start_x + 18, start_y))

        # Keys
        ky = start_y + 24
        pygame.draw.circle(surface, COLOR_KEY, (start_x + 6, ky + 4), 3, 2)
        pygame.draw.line(surface, COLOR_KEY, (start_x + 6, ky + 7), (start_x + 6, ky + 13), 2)
        pygame.draw.line(surface, COLOR_KEY, (start_x + 6, ky + 11), (start_x + 9, ky + 11), 2)
        key_txt = self.font.render(f"x {player.keys:02d}", True, COLOR_WHITE)
        surface.blit(key_txt, (start_x + 18, ky))

        # Stats readout
        sy = ky + 24
        dmg_txt = self.small_font.render(f"DMG: {player.damage:.1f}", True, (240, 100, 100))
        spd_txt = self.small_font.render(f"SPD: {player.move_speed:.0f}", True, (100, 210, 255))
        rate_txt = self.small_font.render(f"TEARS: {1.0 / player.fire_cooldown:.1f}/s", True, (120, 240, 140))
        surface.blit(dmg_txt, (start_x, sy))
        surface.blit(spd_txt, (start_x, sy + 18))
        surface.blit(rate_txt, (start_x, sy + 36))
    def draw(self, surface: pygame.Surface, player, rooms, current_coord) -> None:
        self.draw_hearts(surface, player.health, player.max_health)
        self.draw_inventory(surface, player)
