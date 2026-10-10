"""
Game Engine module.
Houses the core Game class, main game loop, frame-rate timing, and event dispatching.
"""
import sys
import pygame
from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    TITLE,
    COLOR_BG,
    COLOR_WHITE,
    COLOR_GRAY,
    COLOR_MINIMAP_BOSS,
    COLOR_MINIMAP_TREASURE,
    COLOR_MINIMAP_CURRENT,
    COLOR_MINIMAP_ROOM,
    TILE_SIZE,
    ROOM_GRID_WIDTH,
    ROOM_GRID_HEIGHT,
)
from engine.camera import Camera
from world.generator import DungeonGenerator
from world.room import Room, RoomType
from world.tile import TileType
from entities.player import Player


class Game:
    """Core game class controlling main loop, states, and global services."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.is_running: bool = True
        self.dt: float = 0.0

        # Dungeon initialization
        self.dungeon_gen = DungeonGenerator()
        self.rooms = self.dungeon_gen.generate()
        self.current_coord = (0, 0)
        self.current_room = self.rooms[self.current_coord]

        # Camera setup
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Player setup - spawn in center of start room
        spawn_x = (ROOM_GRID_WIDTH // 2) * TILE_SIZE + TILE_SIZE // 2
        spawn_y = (ROOM_GRID_HEIGHT // 2) * TILE_SIZE + TILE_SIZE // 2
        self.player = Player(spawn_x, spawn_y)
        self.camera.snap_to(self.player.pos)

        # Debug mode for map-wide inspection
        self.show_debug_map: bool = False
        self.font = pygame.font.SysFont("Arial", 16, bold=True)

    def handle_events(self) -> None:
        """Process input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.is_running = False
                elif event.key == pygame.K_m:
                    self.show_debug_map = not self.show_debug_map

    def check_room_transitions(self) -> None:
        """Check if player stepped onto an active door tile to switch rooms."""
        door_tiles = self.current_room.get_door_tiles()
        for tile in door_tiles:
            if tile.tile_type == TileType.DOOR and self.player.hitbox_rect.colliderect(tile.rect):
                dir_name = tile.door_direction
                if dir_name and self.current_room.doors.get(dir_name) is not None:
                    next_coord = self.current_room.doors[dir_name]
                    if next_coord in self.rooms:
                        # Change room
                        self.current_coord = next_coord
                        self.current_room = self.rooms[self.current_coord]
                        self.current_room.visited = True

                        # Position player entering from opposite doorway
                        opp_dir = {"N": "S", "S": "N", "E": "W", "W": "E"}[dir_name]
                        new_pos = self.current_room.get_door_spawn_pos(opp_dir)
                        self.player.pos = pygame.math.Vector2(new_pos)
                        self.player.update_hitbox()
                        self.camera.snap_to(self.player.pos)
                        break

    def update(self, dt: float) -> None:
        """Update game logic using frame delta time dt."""
        solid_tiles = self.current_room.get_solid_tiles()
        obstacles = self.current_room.obstacles

        # Update Player physics & collisions
        self.player.update(dt, solid_tiles, obstacles)

        # Check door transitions
        self.check_room_transitions()

        # Update Camera following player
        self.camera.update(self.player.pos, dt)

    def render_debug_map(self) -> None:
        """Render dungeon layout overview across whole screen."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 16, 235))
        self.screen.blit(overlay, (0, 0))

        title_surf = self.font.render("[DEBUG MAP VIEW] - Press 'M' to toggle back to room view", True, COLOR_WHITE)
        self.screen.blit(title_surf, (20, 20))

        # Center map
        mid_x = SCREEN_WIDTH // 2
        mid_y = SCREEN_HEIGHT // 2
        cell_size = 56
        spacing = 74

        for coord, room in self.rooms.items():
            cx = mid_x + coord[0] * spacing
            cy = mid_y + coord[1] * spacing
            rect = pygame.Rect(cx - cell_size // 2, cy - cell_size // 2, cell_size, cell_size)

            # Pick color based on room type
            if coord == self.current_coord:
                color = COLOR_MINIMAP_CURRENT
            elif room.room_type == RoomType.BOSS:
                color = COLOR_MINIMAP_BOSS
            elif room.room_type == RoomType.TREASURE:
                color = COLOR_MINIMAP_TREASURE
            else:
                color = COLOR_MINIMAP_ROOM

            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            pygame.draw.rect(self.screen, COLOR_WHITE, rect, width=2, border_radius=6)

            # Draw doorways
            for direction, neighbor in room.doors.items():
                if neighbor is not None:
                    if direction == "N":
                        door_rect = pygame.Rect(rect.centerx - 6, rect.top - 6, 12, 6)
                    elif direction == "S":
                        door_rect = pygame.Rect(rect.centerx - 6, rect.bottom, 12, 6)
                    elif direction == "W":
                        door_rect = pygame.Rect(rect.left - 6, rect.centery - 6, 6, 12)
                    elif direction == "E":
                        door_rect = pygame.Rect(rect.right, rect.centery - 6, 6, 12)
                    pygame.draw.rect(self.screen, (220, 220, 120), door_rect)

            label = room.room_type.value[0]
            txt = self.font.render(label, True, (20, 20, 20))
            txt_rect = txt.get_rect(center=rect.center)
            self.screen.blit(txt, txt_rect)

    def render(self) -> None:
        """Clear and draw frame to display surface."""
        self.screen.fill(COLOR_BG)

        # Camera viewport translation
        cam_offset = self.camera.get_offset()

        # Draw room tiles
        self.current_room.draw(self.screen, cam_offset)

        # Draw player
        self.player.draw(self.screen, cam_offset)

        # Instructions hint
        hint_surf = self.font.render("Move: WASD | Map: M | Exit: ESC", True, COLOR_GRAY)
        self.screen.blit(hint_surf, (16, 16))

        if self.show_debug_map:
            self.render_debug_map()

        pygame.display.flip()

    def run(self) -> None:
        """Main game loop."""
        while self.is_running:
            self.dt = min(self.clock.tick(FPS) / 1000.0, 0.1)
            self.handle_events()
            self.update(self.dt)
            self.render()

        pygame.quit()
        sys.exit()
