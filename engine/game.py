"""
Game Engine module.
Houses the core Game class, main game loop, frame-rate timing, and event dispatching.
"""
import sys
import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, COLOR_BG


class Game:
    """Core game class controlling main loop, states, and global services."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.is_running: bool = True
        self.dt: float = 0.0

    def handle_events(self) -> None:
        """Process input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.is_running = False

    def update(self, dt: float) -> None:
        """Update game logic using frame delta time dt."""
        pass

    def render(self) -> None:
        """Clear and draw frame to display surface."""
        self.screen.fill(COLOR_BG)
        pygame.display.flip()

    def run(self) -> None:
        """Main game loop."""
        while self.is_running:
            # dt in seconds, capped at max 0.1s to prevent physics explosions on hiccups
            self.dt = min(self.clock.tick(FPS) / 1000.0, 0.1)
            self.handle_events()
            self.update(self.dt)
            self.render()

        pygame.quit()
        sys.exit()
