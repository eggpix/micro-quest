"""Command-line entrypoint for Micro Quest."""

import argparse

from game import Game

def main() -> None:
    """Parse command-line options and start the game."""
    parser = argparse.ArgumentParser(
        description="Micro Quest: A text-based adventure game engine."
    )
    parser.add_argument("-f", "--file", help="Quickly load a game from file path")
    args = parser.parse_args()

    game = Game()
    game.run(args.file)

if __name__ == "__main__":
    main()
