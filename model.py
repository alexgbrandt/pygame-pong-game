from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Keep a numeric value within a lower and upper bound."""
    return max(minimum, min(maximum, value))


@dataclass
class Paddle:
    """Represents a player-controlled paddle in the game."""

    x: float
    y: float
    width: float
    height: float
    speed: float
    color: Tuple[int, int, int]

    def reset(self, screen_height: int) -> None:
        """Center the paddle horizontally and place it at the vertical midpoint."""
        # A paddle is always centered vertically at the start of a round.
        self.y = (screen_height - self.height) / 2

    def move(self, direction: float, dt: float, screen_height: int) -> None:
        """Move the paddle up or down while keeping it inside the game area."""
        # direction is -1 for up, 0 for no movement, and 1 for down.
        minimum_y = 0
        maximum_y = screen_height - self.height

        self.y += direction * self.speed * dt
        self.y = clamp(self.y, minimum_y, maximum_y)


@dataclass
class Ball:
    """Represents the moving ball that bounces around the court."""

    x: float
    y: float
    radius: float
    speed: float
    vx: float
    vy: float
    color: Tuple[int, int, int]

    def reset(self, screen_width: int, screen_height: int) -> None:
        """Center the ball and launch it in a random direction."""
        self.x = screen_width / 2
        self.y = screen_height / 2

        # Choose a random horizontal direction so the rally feels fair and varied.
        direction = random.choice([-1, 1])
        angle = random.uniform(-1.0, 1.0)

        self.vx = direction * self.speed
        self.vy = angle * self.speed * 0.8

    def move(self, dt: float) -> None:
        """Advance the ball based on its current velocity and time elapsed."""
        self.x += self.vx * dt
        self.y += self.vy * dt

    def bounce_off_top_bottom(self, screen_height: int) -> None:
        """Reverse vertical velocity when the ball hits the top or bottom wall."""
        if self.y - self.radius <= 0:
            self.y = self.radius
            self.vy *= -1
        elif self.y + self.radius >= screen_height:
            self.y = screen_height - self.radius
            self.vy *= -1

    def handle_paddle_collision(
        self,
        paddle: Paddle,
        is_left_paddle: bool,
        screen_width: int,
        screen_height: int,
    ) -> None:
        """Bounce the ball when it touches either paddle."""
        # We only care about collisions when the ball is within the paddle's vertical range.
        paddle_top = paddle.y
        paddle_bottom = paddle.y + paddle.height
        within_vertical_range = paddle_top <= self.y <= paddle_bottom

        if not within_vertical_range:
            return

        if is_left_paddle:
            # Left paddle must be hit from the left side of the ball.
            if self.x - self.radius <= paddle.x + paddle.width and self.vx < 0:
                self.x = paddle.x + paddle.width + self.radius
                self.vx = abs(self.vx)
                self.vy += (self.y - (paddle_top + paddle.height / 2)) * 0.12
        else:
            # Right paddle must be hit from the right side of the ball.
            if self.x + self.radius >= paddle.x and self.vx > 0:
                self.x = paddle.x - self.radius
                self.vx = -abs(self.vx)
                self.vy += (self.y - (paddle_top + paddle.height / 2)) * 0.12

        # Clamp velocity so a paddle hit cannot make the ball travel too fast.
        self.vx = clamp(self.vx, -950, 950)
        self.vy = clamp(self.vy, -700, 700)


class GameModel:
    """The model contains the game state and rules for Pong."""

    # These constants define the board size and movement settings.
    WIDTH = 900
    HEIGHT = 600
    PADDLE_WIDTH = 18
    PADDLE_HEIGHT = 120
    PADDLE_SPEED = 540
    BALL_RADIUS = 10
    BALL_SPEED = 520

    def __init__(self) -> None:
        # Screen dimensions are stored here so the view and controller can reference them.
        self.screen_width = self.WIDTH
        self.screen_height = self.HEIGHT

        # mode is None before the player chooses a game mode.
        self.mode: Optional[str] = None  # "single" or "two_player"

        # Score tracks the current points for both players.
        self.score: Dict[str, int] = {"left": 0, "right": 0}

        # Create the left paddle with a white color for contrast.
        self.left_paddle = Paddle(
            x=30,
            y=(self.screen_height - self.PADDLE_HEIGHT) / 2,
            width=self.PADDLE_WIDTH,
            height=self.PADDLE_HEIGHT,
            speed=self.PADDLE_SPEED,
            color=(255, 255, 255),
        )

        # Create the right paddle on the opposite side of the screen.
        self.right_paddle = Paddle(
            x=self.screen_width - 30 - self.PADDLE_WIDTH,
            y=(self.screen_height - self.PADDLE_HEIGHT) / 2,
            width=self.PADDLE_WIDTH,
            height=self.PADDLE_HEIGHT,
            speed=self.PADDLE_SPEED,
            color=(255, 255, 255),
        )

        # Create the ball at the center of the board.
        self.ball = Ball(
            x=self.screen_width / 2,
            y=self.screen_height / 2,
            radius=self.BALL_RADIUS,
            speed=self.BALL_SPEED,
            vx=self.BALL_SPEED,
            vy=0,
            color=(255, 255, 255),
        )

    def start_mode(self, mode: str) -> None:
        """Start a specific game mode and reset the board for a new round."""
        # mode should be either "single" (player vs CPU) or "two_player".
        self.mode = mode
        self.reset_round()

    def reset_round(self) -> None:
        """Reposition paddles and ball to set up a fresh rally."""
        self.left_paddle.reset(self.screen_height)
        self.right_paddle.reset(self.screen_height)
        self.ball.reset(self.screen_width, self.screen_height)

    def update_cpu_paddle(self, dt: float) -> None:
        """Move the right paddle automatically in single-player mode."""
        if self.mode != "single":
            return

        # The CPU tries to align with the ball's current vertical position.
        target_y = self.ball.y - self.right_paddle.height / 2
        direction = 0

        if self.ball.x > self.screen_width / 2:
            if self.right_paddle.y < target_y:
                direction = 1
            elif self.right_paddle.y > target_y:
                direction = -1

        self.right_paddle.move(direction, dt, self.screen_height)

    def update(
        self,
        dt: float,
        left_up: bool,
        left_down: bool,
        right_up: bool,
        right_down: bool,
    ) -> None:
        """Update the game state for one frame based on player input and AI."""
        if self.mode is None:
            return

        # Handle left paddle movement using W and S.
        left_direction = 0
        if left_up:
            left_direction -= 1
        if left_down:
            left_direction += 1
        self.left_paddle.move(left_direction, dt, self.screen_height)

        # Update the right paddle based on selected mode.
        if self.mode == "single":
            self.update_cpu_paddle(dt)
        else:
            right_direction = 0
            if right_up:
                right_direction -= 1
            if right_down:
                right_direction += 1
            self.right_paddle.move(right_direction, dt, self.screen_height)

        # Ball movement and wall collisions.
        self.ball.move(dt)
        self.ball.bounce_off_top_bottom(self.screen_height)

        # Check collisions with both paddles.
        self.ball.handle_paddle_collision(
            self.left_paddle,
            is_left_paddle=True,
            screen_width=self.screen_width,
            screen_height=self.screen_height,
        )
        self.ball.handle_paddle_collision(
            self.right_paddle,
            is_left_paddle=False,
            screen_width=self.screen_width,
            screen_height=self.screen_height,
        )

        # Score a point when the ball passes a side boundary.
        if self.ball.x - self.ball.radius <= 0:
            self.score["right"] += 1
            self.reset_round()
        elif self.ball.x + self.ball.radius >= self.screen_width:
            self.score["left"] += 1
            self.reset_round()
