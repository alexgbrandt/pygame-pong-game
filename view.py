from __future__ import annotations

import pygame

from model import GameModel


class GameView:
    """Draws the game scene to the screen using the current model state."""

    def __init__(self, screen: pygame.Surface) -> None:
        """Initialize the view and prepare fonts for labels and text."""
        self.screen = screen

        # Use a few font sizes for title text, menu text, and score display.
        self.font_large = pygame.font.SysFont("arial", 60)
        self.font_medium = pygame.font.SysFont("arial", 32)
        self.font_small = pygame.font.SysFont("arial", 20)

    def draw(self, model: GameModel) -> None:
        """Render the board, paddles, ball, score, and menu when needed."""
        self.screen.fill((10, 10, 20))

        # Draw the center divider line to separate the two halves of the field.
        divider_color = (255, 255, 255)
        divider_width = 4
        divider_height = 18
        gap = 12
        for y in range(0, model.screen_height, divider_height + gap):
            pygame.draw.rect(
                self.screen,
                divider_color,
                (model.screen_width / 2 - divider_width / 2, y, divider_width, divider_height),
            )

        # Draw the left paddle.
        pygame.draw.rect(
            self.screen,
            model.left_paddle.color,
            (model.left_paddle.x, model.left_paddle.y, model.left_paddle.width, model.left_paddle.height),
        )

        # Draw the right paddle.
        pygame.draw.rect(
            self.screen,
            model.right_paddle.color,
            (model.right_paddle.x, model.right_paddle.y, model.right_paddle.width, model.right_paddle.height),
        )

        # Draw the ball as a circle.
        pygame.draw.circle(
            self.screen,
            model.ball.color,
            (int(model.ball.x), int(model.ball.y)),
            model.ball.radius,
        )

        # Render the scores with large text.
        left_score = self.font_large.render(f"{model.score['left']}", True, (255, 255, 255))
        right_score = self.font_large.render(f"{model.score['right']}", True, (255, 255, 255))

        self.screen.blit(left_score, (model.screen_width / 2 - 120, 30))
        self.screen.blit(right_score, (model.screen_width / 2 + 70, 30))

        # Show the mode menu before the game starts.
        if model.mode is None:
            self.draw_menu()

    def draw_menu(self) -> None:
        """Display the menu text with instructions for choosing a game mode."""
        title = self.font_large.render("PONG", True, (255, 255, 255))
        subtitle = self.font_medium.render("Press 1 for 1 Player", True, (255, 255, 255))
        subtitle_2 = self.font_medium.render("Press 2 for 2 Players", True, (255, 255, 255))
        controls = self.font_small.render(
            "W/S move left paddle | Arrow keys move right paddle",
            True,
            (255, 255, 255),
        )

        self.screen.blit(title, (360, 120))
        self.screen.blit(subtitle, (250, 220))
        self.screen.blit(subtitle_2, (250, 280))
        self.screen.blit(controls, (135, 520))
