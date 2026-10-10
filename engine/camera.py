"""
Smooth Lerp Camera for viewport tracking.
"""
from typing import Tuple
import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT


class Camera:
    """Smooth tracking camera with linear interpolation (lerp)."""

    def __init__(self, width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT) -> None:
        self.width: int = width
        self.height: int = height
        # Camera center position
        self.pos: pygame.math.Vector2 = pygame.math.Vector2(width / 2, height / 2)
        # Smoothing factor: higher = faster snap, lower = smoother follow
        self.smoothness: float = 8.0

    def update(self, target_pos: pygame.math.Vector2, dt: float) -> None:
        """Interpolate camera towards target position."""
        # Lerp camera position towards target
        lerp_rate = 1.0 - (0.01 ** (dt * self.smoothness))
        self.pos += (target_pos - self.pos) * lerp_rate

    def snap_to(self, target_pos: pygame.math.Vector2) -> None:
        """Instantly teleport camera without lerp (e.g. entering new room)."""
        self.pos = pygame.math.Vector2(target_pos)

    def get_offset(self) -> Tuple[int, int]:
        """
        Calculates screen translation offset.
        Converts world coordinates to screen coordinates.
        """
        ox = int(self.width / 2 - self.pos.x)
        oy = int(self.height / 2 - self.pos.y)
        return (ox, oy)
