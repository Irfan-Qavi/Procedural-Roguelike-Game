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

    def draw_minimap(
        self,
        surface: pygame.Surface,
        rooms: Dict[Tuple[int, int], Room],
        current_coord: Tuple[int, int],
    ) -> None:
        """Draw top-right minimap showing visited/connected rooms."""
        mm_w = 144
        mm_h = 114
        mm_x = SCREEN_WIDTH - mm_w - 20
        mm_y = 20

        # Background frame
        bg_surface = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
        bg_surface.fill(COLOR_MINIMAP_BG)
        surface.blit(bg_surface, (mm_x, mm_y))
        pygame.draw.rect(surface, (80, 75, 100), (mm_x, mm_y, mm_w, mm_h), 2, border_radius=4)

        # Center on current room
        center_x = mm_x + mm_w // 2
        center_y = mm_y + mm_h // 2
        cell_size = 14
        step = 20

        for coord, room in rooms.items():
            # Only draw room if it was visited, or if adjacent to a visited room
            is_adjacent_to_visited = any(
                rooms.get((coord[0] + dx, coord[1] + dy)) and rooms[(coord[0] + dx, coord[1] + dy)].visited
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))
            )

            if not room.visited and not is_adjacent_to_visited:
                continue

            rel_x = coord[0] - current_coord[0]
            rel_y = coord[1] - current_coord[1]
            rx = center_x + rel_x * step - cell_size // 2
            ry = center_y + rel_y * step - cell_size // 2

            # Clip within minimap box
            if rx < mm_x + 4 or rx + cell_size > mm_x + mm_w - 4 or ry < mm_y + 4 or ry + cell_size > mm_y + mm_h - 4:
                continue

            rect = pygame.Rect(rx, ry, cell_size, cell_size)

            if coord == current_coord:
                color = COLOR_MINIMAP_CURRENT
            elif not room.visited:
                color = (45, 45, 60)  # Unvisited neighbor silhouette
            elif room.room_type == RoomType.BOSS:
                color = COLOR_MINIMAP_BOSS
            elif room.room_type == RoomType.TREASURE:
                color = COLOR_MINIMAP_TREASURE
            else:
                color = COLOR_MINIMAP_ROOM

            pygame.draw.rect(surface, color, rect, border_radius=2)
            pygame.draw.rect(surface, (20, 20, 25), rect, 1, border_radius=2)

            # Icon letters for Boss / Treasure
            if room.visited:
                if room.room_type == RoomType.BOSS:
                    b_txt = self.small_font.render("B", True, (255, 255, 255))
                    surface.blit(b_txt, (rx + 2, ry - 1))
                elif room.room_type == RoomType.TREASURE:
                    t_txt = self.small_font.render("T", True, (20, 20, 20))
                    surface.blit(t_txt, (rx + 2, ry - 1))

    def draw(
        self,
        surface: pygame.Surface,
        player,
        rooms: Dict[Tuple[int, int], Room],
        current_coord: Tuple[int, int],
    ) -> None:
        """Render complete HUD."""
        self.draw_hearts(surface, int(player.health), int(player.max_health))
        self.draw_inventory(surface, player)
        self.draw_minimap(surface, rooms, current_coord)
