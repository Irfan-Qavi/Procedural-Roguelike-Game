"""
Main entrypoint for the Binding of Python Roguelike Game.
"""
from engine.game import Game


def main() -> None:
    """Instantiate and run the core game."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
