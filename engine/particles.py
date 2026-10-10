"""
Particle systems for impacts, pot destruction, bullet pops, and movement dust.
"""
from typing import Tuple, List
import random
import pygame


class Particle:
    """Single animated visual particle."""

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        color: Tuple[int, int, int],
        lifetime: float,
        size: float = 4.0,
        gravity: float = 0.0,
    ) -> None:
        self.pos: pygame.math.Vector2 = pygame.math.Vector2(x, y)
        self.vel: pygame.math.Vector2 = pygame.math.Vector2(vx, vy)
        self.color: Tuple[int, int, int] = color
        self.lifetime: float = lifetime
        self.max_lifetime: float = lifetime
        self.size: float = size
        self.gravity: float = gravity
        self.is_dead: bool = False

    def update(self, dt: float) -> None:
        """Update particle physics and fade timer."""
        self.pos += self.vel * dt
        self.vel.y += self.gravity * dt
        self.vel *= 0.95  # Air friction
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.is_dead = True

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int]) -> None:
        """Draw fading particle."""
        if self.is_dead:
            return
        ox, oy = camera_offset
        # Dynamic shrink
        current_size = max(1.0, self.size * (self.lifetime / self.max_lifetime))
        px = int(self.pos.x + ox)
        py = int(self.pos.y + oy)
        rect = pygame.Rect(int(px - current_size / 2), int(py - current_size / 2), int(current_size), int(current_size))
        pygame.draw.rect(surface, self.color, rect)


class ParticleEmitter:
    """Manages spawning and updating collections of particles."""

    def __init__(self) -> None:
        self.particles: List[Particle] = []

    def burst(
        self,
        x: float,
        y: float,
        count: int = 12,
        color: Tuple[int, int, int] = (200, 160, 110),
        speed: float = 120.0,
        size: float = 4.0,
        lifetime: float = 0.35,
    ) -> None:
        """Spawns an omnidirectional burst of debris particles."""
        for _ in range(count):
            angle = random.uniform(0, 6.28318)
            spd = random.uniform(speed * 0.4, speed)
            vx = spd * pygame.math.Vector2(1, 0).rotate_rad(angle).x
            vy = spd * pygame.math.Vector2(1, 0).rotate_rad(angle).y
            life = random.uniform(lifetime * 0.6, lifetime * 1.3)
            # Slight color variation
            r = min(255, max(0, color[0] + random.randint(-15, 15)))
            g = min(255, max(0, color[1] + random.randint(-15, 15)))
            b = min(255, max(0, color[2] + random.randint(-15, 15)))
            self.particles.append(Particle(x, y, vx, vy, (r, g, b), life, size=size))

    def update(self, dt: float) -> None:
        """Update all live particles and remove expired ones."""
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if not p.is_dead]

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int]) -> None:
        """Render active particles."""
        for p in self.particles:
            p.draw(surface, camera_offset)
