from __future__ import annotations

import pygame

from model import GameModel


class GameController:
    """Coordinates the game loop, user input, and mode switching."""

    def __init__(self) -> None:
        """Set up the game window and initialize the game state."""
        pygame.init()
        pygame.display.set_caption("Pong")

        # Create the game window using the dimensions defined in the model.
        self.screen = pygame.display.set_mode((GameModel.WIDTH, GameModel.HEIGHT))
        self.clock = pygame.time.Clock()
        self.model = GameModel()
        self.running = True

    def handle_events(self) -> None:
        """Process keyboard input and quit events for the current frame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Pressing Esc closes the game.
                    self.running = False

                elif event.key == pygame.K_1:
                    # Start single-player mode against the CPU.
                    self.model.start_mode("single")

                elif event.key == pygame.K_2:
                    # Start local two-player mode on the same keyboard.
                    self.model.start_mode("two_player")

                elif event.key == pygame.K_r and self.model.mode is not None:
                    # Reset the current round without changing the game mode.
                    self.model.reset_round()

    def run(self) -> None:
        """Run the main game loop until the user exits."""
        while self.running:
            # Limit the frame rate to 60 FPS and compute frame time in seconds.
            dt = self.clock.tick(60) / 1000.0

            # Listen for keyboard and window events.
            self.handle_events()

            # Read the state of all keys on the keyboard.
            keys = pygame.key.get_pressed()

            # Left paddle uses W and S.
            left_up = keys[pygame.K_w]
            left_down = keys[pygame.K_s]

            # Right paddle input depends on the game mode.
            if self.model.mode == "single":
                # In single-player mode, the right paddle is controlled by the CPU.
                right_up = False
                right_down = False
            else:
                # In two-player mode, the right paddle responds to the arrow keys.
                right_up = keys[pygame.K_UP]
                right_down = keys[pygame.K_DOWN]

            # Update the game state using the current inputs and time elapsed.
            self.model.update(dt, left_up, left_down, right_up, right_down)

            # Draw the visible game world.
            from view import GameView
            view = GameView(self.screen)
            view.draw(self.model)

            # Render the updated frame to the display.
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    controller = GameController()
    controller.run()
