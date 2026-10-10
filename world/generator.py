"""
Procedural dungeon floor generator.
Uses random walk / frontier expansion with backtracking to generate connected rooms
matching 'The Binding of Isaac' dungeon layout requirements.
"""
import random
from typing import Dict, List, Tuple
from config import MIN_ROOMS, MAX_ROOMS, ROOM_GRID_WIDTH, ROOM_GRID_HEIGHT, TILE_SIZE
from world.room import Room, RoomType


# Directions: (dx, dy, dir_name, opposite_dir_name)
DIRECTIONS = [
    (0, -1, "N", "S"),
    (0, 1, "S", "N"),
    (1, 0, "E", "W"),
    (-1, 0, "W", "E"),
]


class DungeonGenerator:
    """Procedural generator for floor layout."""

    def __init__(self, min_rooms: int = MIN_ROOMS, max_rooms: int = MAX_ROOMS) -> None:
        self.min_rooms: int = min_rooms
        self.max_rooms: int = max_rooms

    def generate(self) -> Dict[Tuple[int, int], Room]:
        """
        Generate connected rooms on an integer 2D grid.
        Returns a dictionary mapping (col, row) coordinates to Room instances.
        """
        target_count = random.randint(self.min_rooms, self.max_rooms)
        rooms: Dict[Tuple[int, int], Room] = {}

        # 1. Place Start Room at (0, 0)
        start_coord = (0, 0)
        start_room = Room(start_coord, RoomType.START)
        start_room.visited = True
        rooms[start_coord] = start_room

        # Queue / Frontier of coordinates eligible for expanding
        frontier = [start_coord]

        # 2. Random expansion until target room count reached
        while len(rooms) < target_count and frontier:
            current_coord = random.choice(frontier)
            valid_neighbors = []

            for dx, dy, dir_name, opp_dir in DIRECTIONS:
                neighbor_coord = (current_coord[0] + dx, current_coord[1] + dy)
                if neighbor_coord not in rooms:
                    # Check neighbor's neighbors to prevent excessively clumpy layouts
                    adjacent_existing_count = sum(
                        1 for ndx, ndy, _, _ in DIRECTIONS
                        if (neighbor_coord[0] + ndx, neighbor_coord[1] + ndy) in rooms
                    )
                    # Isaac dungeon generation keeps branching clean by limiting neighbor collisions
                    if adjacent_existing_count <= 2:
                        valid_neighbors.append((neighbor_coord, dir_name, opp_dir))

            if valid_neighbors:
                next_coord, dir_name, opp_dir = random.choice(valid_neighbors)
                new_room = Room(next_coord, RoomType.NORMAL)
                rooms[next_coord] = new_room
                frontier.append(next_coord)
            else:
                frontier.remove(current_coord)

        # 3. Connect doors between adjacent rooms
        for coord, room in rooms.items():
            for dx, dy, dir_name, opp_dir in DIRECTIONS:
                neighbor_coord = (coord[0] + dx, coord[1] + dy)
                if neighbor_coord in rooms:
                    room.doors[dir_name] = neighbor_coord

        # 4. Assign Special Room Types (Boss Room & Treasure Room)
        # Find dead-end rooms (rooms with only 1 connected door), excluding Start Room
        dead_ends = [
            coord for coord, room in rooms.items()
            if coord != (0, 0) and sum(1 for d in room.doors.values() if d is not None) == 1
        ]

        # Sort dead ends by Manhattan distance from start (0, 0)
        dead_ends.sort(key=lambda c: abs(c[0]) + abs(c[1]), reverse=True)

        if dead_ends:
            # Farthest dead end becomes Boss Room
            boss_coord = dead_ends[0]
            rooms[boss_coord].room_type = RoomType.BOSS
            rooms[boss_coord].cleared = False

            if len(dead_ends) > 1:
                # Second farthest dead end becomes Treasure Room
                treasure_coord = dead_ends[1]
                rooms[treasure_coord].room_type = RoomType.TREASURE
                rooms[treasure_coord].cleared = True
            else:
                # Choose farthest non-boss, non-start room
                candidates = [c for c in rooms if c != (0, 0) and c != boss_coord]
                if candidates:
                    candidates.sort(key=lambda c: abs(c[0]) + abs(c[1]), reverse=True)
                    treasure_coord = candidates[0]
                    rooms[treasure_coord].room_type = RoomType.TREASURE
                    rooms[treasure_coord].cleared = True
        else:
            # Fallback if no single dead end: pick highest distance rooms
            all_other = [c for c in rooms if c != (0, 0)]
            all_other.sort(key=lambda c: abs(c[0]) + abs(c[1]), reverse=True)
            if all_other:
                rooms[all_other[0]].room_type = RoomType.BOSS
                rooms[all_other[0]].cleared = False
            if len(all_other) > 1:
                rooms[all_other[1]].room_type = RoomType.TREASURE
                rooms[all_other[1]].cleared = True

        # 5. Finalize tile structures for doors and populate room props & enemies
        from world.obstacle import Destructible
        from entities.enemy import ChaserEnemy, RangerEnemy, BossEnemy

        for coord, room in rooms.items():
            room.update_doors()

            if room.room_type == RoomType.BOSS:
                # Spawn Boss at center
                bx = (ROOM_GRID_WIDTH // 2) * TILE_SIZE + TILE_SIZE // 2
                by = (ROOM_GRID_HEIGHT // 2) * TILE_SIZE + TILE_SIZE // 2
                room.enemies.append(BossEnemy(bx, by))

            elif room.room_type == RoomType.NORMAL and coord != (0, 0):
                # Spawn breakable pots
                pot_spots = [
                    (2, 2), (ROOM_GRID_WIDTH - 3, 2),
                    (2, ROOM_GRID_HEIGHT - 3), (ROOM_GRID_WIDTH - 3, ROOM_GRID_HEIGHT - 3),
                    (3, 3), (ROOM_GRID_WIDTH - 4, 3)
                ]
                chosen_spots = random.sample(pot_spots, k=random.randint(2, 4))
                for px, py in chosen_spots:
                    room.obstacles.append(Destructible(px, py))

                # Spawn 2 to 4 enemies (mix of Chaser and Ranger)
                enemy_count = random.randint(2, 4)
                spawn_positions = [
                    (3 * TILE_SIZE, 3 * TILE_SIZE),
                    ((ROOM_GRID_WIDTH - 4) * TILE_SIZE, 3 * TILE_SIZE),
                    (3 * TILE_SIZE, (ROOM_GRID_HEIGHT - 4) * TILE_SIZE),
                    ((ROOM_GRID_WIDTH - 4) * TILE_SIZE, (ROOM_GRID_HEIGHT - 4) * TILE_SIZE),
                ]
                random.shuffle(spawn_positions)
                for i in range(min(enemy_count, len(spawn_positions))):
                    ex, ey = spawn_positions[i]
                    if random.random() < 0.6:
                        room.enemies.append(ChaserEnemy(ex, ey))
                    else:
                        room.enemies.append(RangerEnemy(ex, ey))

            elif room.room_type == RoomType.TREASURE:
                # Pots in treasure room
                for px, py in [(2, 2), (ROOM_GRID_WIDTH - 3, 2)]:
                    room.obstacles.append(Destructible(px, py))
                # Spawn guaranteed Golden Item Chest in center of Treasure Room
                from items.loot import Chest
                cx = (ROOM_GRID_WIDTH // 2) * TILE_SIZE + TILE_SIZE // 2
                cy = (ROOM_GRID_HEIGHT // 2) * TILE_SIZE + TILE_SIZE // 2
                room.chests.append(Chest(cx, cy, requires_key=False))

        return rooms
