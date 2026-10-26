from controller import GameController


def main() -> None:
    """Application entry point for the Pong game."""
    game = GameController()
    game.run()


if __name__ == "__main__":
    main()
