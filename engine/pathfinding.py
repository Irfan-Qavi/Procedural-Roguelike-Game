"""
Grid-based Pathfinding module (A* algorithm) for enemy navigation through corridors and obstacles.
"""
from typing import List, Tuple, Dict, Set, Optional
import heapq
from config import ROOM_GRID_WIDTH, ROOM_GRID_HEIGHT


def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    """Manhattan distance heuristic."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar_path(
    start: Tuple[int, int],
    goal: Tuple[int, int],
    blocked_cells: Set[Tuple[int, int]],
) -> Optional[List[Tuple[int, int]]]:
    """
    Find shortest grid path from start to goal using A* search.
    Returns list of grid coordinates [(x1, y1), (x2, y2), ...] or None.
    """
    if start == goal:
        return [start]

    # Priority queue storing (f_score, current_node)
    open_set: list = []
    heapq.heappush(open_set, (0, start))

    came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
    g_score: Dict[Tuple[int, int], float] = {start: 0.0}
    f_score: Dict[Tuple[int, int], float] = {start: heuristic(start, goal)}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            # Reconstruct path
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        cx, cy = current
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            neighbor = (cx + dx, cy + dy)

            # Check room boundaries
            if not (0 <= neighbor[0] < ROOM_GRID_WIDTH and 0 <= neighbor[1] < ROOM_GRID_HEIGHT):
                continue

            # Don't walk through blocked walls/pots unless it's the goal itself
            if neighbor in blocked_cells and neighbor != goal:
                continue

            tentative_g = g_score[current] + 1.0

            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return None
