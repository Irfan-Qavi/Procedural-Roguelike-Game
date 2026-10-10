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
from engine.particles import ParticleEmitter
from world.generator import DungeonGenerator
from world.room import Room, RoomType
from world.tile import TileType
from entities.player import Player
from entities.projectile import Projectile


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

        # Camera & FX setup
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.particles = ParticleEmitter()

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

    def handle_player_shooting(self) -> None:
        """Handle player tear shooting in 4 directions."""
        shoot_dir = self.player.handle_input()
        if shoot_dir.length_squared() > 0 and self.player.shoot_timer <= 0:
            # Spawn projectile slightly offset in shooting direction
            spawn_pos = self.player.pos + shoot_dir * 16
            proj = Projectile(
                spawn_pos.x,
                spawn_pos.y,
                shoot_dir,
                speed=self.player.bullet_speed,
                damage=self.player.damage,
                max_range=self.player.bullet_range,
                is_enemy=False,
            )
            self.current_room.projectiles.append(proj)
            self.player.shoot_timer = self.player.fire_cooldown

    def update(self, dt: float) -> None:
        """Update game logic using frame delta time dt."""
        solid_tiles = self.current_room.get_solid_tiles()
        obstacles = self.current_room.obstacles

        # Build blocked cells set for enemy pathfinding
        blocked_cells = {(t.grid_x, t.grid_y) for t in solid_tiles}
        for obs in obstacles:
            if not obs.is_destroyed:
                blocked_cells.add((obs.grid_x, obs.grid_y))

        # Update Player physics & collisions
        self.player.update(dt, solid_tiles, obstacles)

        # Player shooting
        self.handle_player_shooting()

        # Update Projectiles
        for proj in self.current_room.projectiles:
            hit = proj.update(dt, solid_tiles, obstacles)
            if hit:
                # Particle pop upon projectile impact
                self.particles.burst(proj.pos.x, proj.pos.y, count=5, color=(140, 210, 255), speed=80.0, size=3.0)

            # Bullet-to-Entity collision checks
            if not proj.is_dead:
                if not proj.is_enemy:
                    # Player tear hitting enemy
                    for enemy in self.current_room.enemies:
                        if not enemy.is_dead and enemy.hitbox_rect.colliderect(proj.rect):
                            proj.is_dead = True
                            knockback = proj.vel.normalize() * 120.0 if proj.vel.length_squared() > 0 else None
                            enemy.take_damage(proj.damage, knockback)
                            self.particles.burst(proj.pos.x, proj.pos.y, count=8, color=(220, 60, 60), speed=100.0, size=3.5)
                            break
                else:
                    # Enemy bullet hitting player
                    if self.player.hitbox_rect.colliderect(proj.rect):
                        proj.is_dead = True
                        knockback = proj.vel.normalize() * 140.0 if proj.vel.length_squared() > 0 else None
                        damaged = self.player.take_damage(proj.damage, knockback)
                        if damaged:
                            self.player.invulnerable_timer = 0.8
                            self.particles.burst(self.player.pos.x, self.player.pos.y, count=10, color=(255, 60, 60), speed=120.0, size=4.0)

        # Update Enemies
        for enemy in self.current_room.enemies:
            if not enemy.is_dead:
                enemy.update_ai(dt, self.player.pos, blocked_cells, self.current_room.projectiles)
                enemy.move_and_collide(dt, solid_tiles, obstacles)

                # Enemy melee collision with player
                if enemy.hitbox_rect.colliderect(self.player.hitbox_rect):
                    knockback = (self.player.pos - enemy.pos).normalize() * 160.0 if (self.player.pos - enemy.pos).length_squared() > 0 else None
                    damaged = self.player.take_damage(enemy.damage_amount, knockback)
                    if damaged:
                        self.player.invulnerable_timer = 0.8
                        self.particles.burst(self.player.pos.x, self.player.pos.y, count=10, color=(255, 60, 60), speed=120.0, size=4.0)

        # Clean dead enemies and check room clearance
        for enemy in self.current_room.enemies:
            if enemy.is_dead and not getattr(enemy, "_death_burst", False):
                enemy._death_burst = True
                self.particles.burst(enemy.pos.x, enemy.pos.y, count=18, color=enemy.color, speed=140.0, size=5.0)

        self.current_room.enemies = [e for e in self.current_room.enemies if not e.is_dead]
        if not self.current_room.enemies and not self.current_room.cleared:
            self.current_room.cleared = True

        # Clean dead projectiles
        self.current_room.projectiles = [p for p in self.current_room.projectiles if not p.is_dead]

        # Check for freshly destroyed obstacles and trigger burst
        for obs in obstacles:
            if obs.is_destroyed and not getattr(obs, "_burst_triggered", False):
                obs._burst_triggered = True
                self.particles.burst(obs.rect.centerx, obs.rect.centery, count=16, color=(160, 110, 65), speed=130.0, size=5.0)

        # Update particle emitter
        self.particles.update(dt)

        # Check door transitions (doors only open when room is cleared of active enemies)
        if self.current_room.cleared:
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

        # Draw room tiles & props
        self.current_room.draw(self.screen, cam_offset)

        # Draw projectiles
        for proj in self.current_room.projectiles:
            proj.draw(self.screen, cam_offset)

        # Draw enemies
        for enemy in self.current_room.enemies:
            enemy.draw(self.screen, cam_offset)

        # Draw particles
        self.particles.draw(self.screen, cam_offset)

        # Draw player
        self.player.draw(self.screen, cam_offset)

        # Instructions hint
        hint_surf = self.font.render("Move: WASD | Shoot: Arrow Keys | Map: M | Exit: ESC", True, COLOR_GRAY)
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
