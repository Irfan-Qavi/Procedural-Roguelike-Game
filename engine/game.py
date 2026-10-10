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
from enum import Enum
import random
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
from entities.enemy import BossEnemy
from ui.hud import HUD


class GameState(Enum):
    START_MENU = 0
    PLAYING = 1
    GAME_OVER = 2
    VICTORY = 3


class Game:
    """Core game class controlling main loop, states, and global services."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.is_running: bool = True
        self.dt: float = 0.0

        # UI & HUD
        self.hud = HUD()
        self.state: GameState = GameState.START_MENU

        # Fonts
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 38, bold=True)
        self.banner_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.show_debug_map: bool = False

        self.reset_game()

    def reset_game(self) -> None:
        """Reset dungeon, player, and entities for a new run."""
        self.dungeon_gen = DungeonGenerator()
        self.rooms = self.dungeon_gen.generate()
        self.current_coord = (0, 0)
        self.current_room = self.rooms[self.current_coord]

        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.particles = ParticleEmitter()

        spawn_x = (ROOM_GRID_WIDTH // 2) * TILE_SIZE + TILE_SIZE // 2
        spawn_y = (ROOM_GRID_HEIGHT // 2) * TILE_SIZE + TILE_SIZE // 2
        self.player = Player(spawn_x, spawn_y)
        self.camera.snap_to(self.player.pos)

    def handle_events(self) -> None:
        """Process input events depending on game state."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.is_running = False

                if self.state == GameState.START_MENU:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.state = GameState.PLAYING

                elif self.state == GameState.PLAYING:
                    if event.key == pygame.K_m:
                        self.show_debug_map = not self.show_debug_map

                elif self.state in (GameState.GAME_OVER, GameState.VICTORY):
                    if event.key == pygame.K_r:
                        self.reset_game()
                        self.state = GameState.PLAYING
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.reset_game()
                        self.state = GameState.START_MENU

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
        if self.state != GameState.PLAYING:
            return

        solid_tiles = self.current_room.get_solid_tiles()
        obstacles = self.current_room.obstacles

        # Build blocked cells set for enemy pathfinding
        blocked_cells = {(t.grid_x, t.grid_y) for t in solid_tiles}
        for obs in obstacles:
            if not obs.is_destroyed:
                blocked_cells.add((obs.grid_x, obs.grid_y))

        # Update Player physics & collisions
        self.player.update(dt, solid_tiles, obstacles)

        # Footstep dust particles when moving
        if self.player.vel.length_squared() > 1200:
            if random.random() < 0.25:
                foot_offset = pygame.math.Vector2(random.uniform(-6, 6), 10)
                self.particles.burst(
                    self.player.pos.x + foot_offset.x,
                    self.player.pos.y + foot_offset.y,
                    count=1,
                    color=(95, 90, 110),
                    speed=15.0,
                    size=3.0,
                    lifetime=0.25,
                )

        # Check Player Death
        if self.player.is_dead:
            self.state = GameState.GAME_OVER
            self.particles.burst(self.player.pos.x, self.player.pos.y, count=30, color=(255, 60, 60), speed=160.0, size=5.0)
            return

        # Player shooting
        self.handle_player_shooting()

        # Update Projectiles
        for proj in self.current_room.projectiles:
            hit = proj.update(dt, solid_tiles, obstacles)
            if hit:
                self.particles.burst(proj.pos.x, proj.pos.y, count=5, color=(140, 210, 255), speed=80.0, size=3.0)

            # Bullet-to-Entity collision checks
            if not proj.is_dead:
                if not proj.is_enemy:
                    for enemy in self.current_room.enemies:
                        if not enemy.is_dead and enemy.hitbox_rect.colliderect(proj.rect):
                            proj.is_dead = True
                            knockback = proj.vel.normalize() * 120.0 if proj.vel.length_squared() > 0 else None
                            enemy.take_damage(proj.damage, knockback)
                            self.particles.burst(proj.pos.x, proj.pos.y, count=8, color=(220, 60, 60), speed=100.0, size=3.5)
                            break
                else:
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

        # Clean dead enemies & check for Boss defeat (Victory)
        from items.loot import Pickup, PickupType
        for enemy in self.current_room.enemies:
            if enemy.is_dead and not getattr(enemy, "_death_burst", False):
                enemy._death_burst = True
                self.particles.burst(enemy.pos.x, enemy.pos.y, count=24, color=enemy.color, speed=160.0, size=6.0)

                # Check if this defeated enemy was the Boss
                if isinstance(enemy, BossEnemy):
                    self.state = GameState.VICTORY
                    return

                # Drop table
                drop_roll = random.random()
                if drop_roll < 0.25:
                    self.current_room.pickups.append(Pickup(enemy.pos.x, enemy.pos.y, PickupType.COIN))
                elif drop_roll < 0.40:
                    self.current_room.pickups.append(Pickup(enemy.pos.x, enemy.pos.y, PickupType.HEART))
                elif drop_roll < 0.48:
                    self.current_room.pickups.append(Pickup(enemy.pos.x, enemy.pos.y, PickupType.KEY))

        self.current_room.enemies = [e for e in self.current_room.enemies if not e.is_dead]
        if not self.current_room.enemies and not self.current_room.cleared:
            self.current_room.cleared = True

        # Clean dead projectiles
        self.current_room.projectiles = [p for p in self.current_room.projectiles if not p.is_dead]

        # Check for destroyed obstacles
        for obs in obstacles:
            if obs.is_destroyed and not getattr(obs, "_burst_triggered", False):
                obs._burst_triggered = True
                self.particles.burst(obs.rect.centerx, obs.rect.centery, count=16, color=(160, 110, 65), speed=130.0, size=5.0)
                p_roll = random.random()
                if p_roll < 0.22:
                    self.current_room.pickups.append(Pickup(obs.rect.centerx, obs.rect.centery, PickupType.COIN))
                elif p_roll < 0.35:
                    self.current_room.pickups.append(Pickup(obs.rect.centerx, obs.rect.centery, PickupType.HEART))

        # Chest interaction
        for chest in self.current_room.chests:
            if not chest.is_opened and self.player.hitbox_rect.colliderect(chest.rect):
                loot = chest.interact(self.player)
                if loot:
                    self.current_room.pickups.append(loot)
                    self.particles.burst(chest.pos.x, chest.pos.y, count=16, color=(255, 220, 80), speed=120.0, size=4.0)

        # Pickups collection
        for pickup in self.current_room.pickups:
            pickup.update(dt)
            if not pickup.is_collected and self.player.hitbox_rect.colliderect(pickup.rect):
                collected = pickup.apply_to_player(self.player)
                if collected:
                    self.particles.burst(pickup.pos.x, pickup.pos.y, count=12, color=(120, 240, 140), speed=100.0, size=3.5)

        self.current_room.pickups = [p for p in self.current_room.pickups if not p.is_collected]

        # Update particles
        self.particles.update(dt)

        # Check room door transitions
        if self.current_room.cleared:
            self.check_room_transitions()

        # Camera lerp
        self.camera.update(self.player.pos, dt)

    def render_debug_map(self) -> None:
        """Render dungeon layout overview across whole screen."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 16, 235))
        self.screen.blit(overlay, (0, 0))

        title_surf = self.font.render("[DEBUG MAP VIEW] - Press 'M' to toggle back to room view", True, COLOR_WHITE)
        self.screen.blit(title_surf, (20, 20))

        mid_x = SCREEN_WIDTH // 2
        mid_y = SCREEN_HEIGHT // 2
        cell_size = 56
        spacing = 74

        for coord, room in self.rooms.items():
            cx = mid_x + coord[0] * spacing
            cy = mid_y + coord[1] * spacing
            rect = pygame.Rect(cx - cell_size // 2, cy - cell_size // 2, cell_size, cell_size)

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

    def render_start_menu(self) -> None:
        """Render Title Screen."""
        self.screen.fill((14, 12, 20))

        # Title
        title_text = self.banner_font.render("BINDING OF PYTHON", True, (240, 70, 70))
        sub_text = self.font.render("A Procedural Top-Down Roguelike Dungeon Crawler", True, (200, 200, 210))
        prompt_text = self.title_font.render("Press SPACE or ENTER to Start", True, (255, 230, 90))

        t_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 - 30))
        s_rect = sub_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 + 30))
        p_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))

        self.screen.blit(title_text, t_rect)
        self.screen.blit(sub_text, s_rect)
        self.screen.blit(prompt_text, p_rect)

        # Controls info box
        box_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 + 130, 400, 140)
        pygame.draw.rect(self.screen, (28, 24, 36), box_rect, border_radius=8)
        pygame.draw.rect(self.screen, (70, 60, 85), box_rect, 2, border_radius=8)

        c1 = self.font.render("Movement: [W, A, S, D]", True, COLOR_WHITE)
        c2 = self.font.render("Shoot Tears: [Arrow Keys]", True, (130, 205, 255))
        c3 = self.font.render("Inspect Map: [M] | Exit: [ESC]", True, COLOR_GRAY)
        c4 = self.font.render("Goal: Clear rooms, loot items, defeat Boss [B]", True, (250, 210, 80))

        self.screen.blit(c1, (box_rect.x + 24, box_rect.y + 16))
        self.screen.blit(c2, (box_rect.x + 24, box_rect.y + 44))
        self.screen.blit(c3, (box_rect.x + 24, box_rect.y + 72))
        self.screen.blit(c4, (box_rect.x + 24, box_rect.y + 100))

    def render_game_over(self) -> None:
        """Render Game Over Screen."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((20, 5, 5, 220))
        self.screen.blit(overlay, (0, 0))

        gov_text = self.banner_font.render("YOU DIED", True, (230, 40, 40))
        sub_text = self.title_font.render("Press 'R' to Restart | ENTER for Menu", True, COLOR_WHITE)

        g_rect = gov_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        s_rect = sub_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))

        self.screen.blit(gov_text, g_rect)
        self.screen.blit(sub_text, s_rect)

    def render_victory(self) -> None:
        """Render Victory Screen."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 25, 15, 225))
        self.screen.blit(overlay, (0, 0))

        vic_text = self.banner_font.render("VICTORY ACHIEVED!", True, (255, 225, 70))
        sub_text = self.title_font.render("The Dungeon Boss Has Fallen!", True, (100, 240, 140))
        rst_text = self.font.render("Press 'R' to Play Again | ENTER for Menu", True, COLOR_WHITE)

        v_rect = vic_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        s_rect = sub_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        r_rect = rst_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))

        self.screen.blit(vic_text, v_rect)
        self.screen.blit(sub_text, s_rect)
        self.screen.blit(rst_text, r_rect)

    def render(self) -> None:
        """Clear and draw frame to display surface based on game state."""
        if self.state == GameState.START_MENU:
            self.render_start_menu()
            pygame.display.flip()
            return

        self.screen.fill(COLOR_BG)
        cam_offset = self.camera.get_offset()

        # Draw room tiles, obstacles, chests, pickups
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
        if not self.player.is_dead:
            self.player.draw(self.screen, cam_offset)

        # Draw HUD overlay (Hearts, Keys, Coins, Minimap)
        self.hud.draw(self.screen, self.player, self.rooms, self.current_coord)

        if self.show_debug_map:
            self.render_debug_map()

        if self.state == GameState.GAME_OVER:
            self.render_game_over()
        elif self.state == GameState.VICTORY:
            self.render_victory()

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
