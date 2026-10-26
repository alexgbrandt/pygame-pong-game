from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Keep a numeric value within a lower and upper bound."""
    return max(minimum, min(maximum, value))


PADDLE_COLORS: Dict[str, Tuple[int, int, int]] = {
    "white": (255, 255, 255),
    "red": (255, 100, 100),
    "blue": (100, 170, 255),
    "green": (110, 230, 120),
    "purple": (196, 120, 255),
    "gold": (255, 214, 102),
}

PADDLE_UNLOCKS: Dict[str, float] = {
    "white": 0.0,
    "red": 5.0,
    "blue": 12.0,
    "green": 20.0,
    "purple": 35.0,
    "gold": 60.0,
}

HIGH_SCORE_PATH = os.path.join(os.path.dirname(__file__), "pong_save.json")


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
        self.y = (screen_height - self.height) / 2

    def move(self, direction: float, dt: float, screen_height: int) -> None:
        """Move the paddle up or down while keeping it inside the game area."""
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
        paddle_top = paddle.y
        paddle_bottom = paddle.y + paddle.height
        within_vertical_range = paddle_top <= self.y <= paddle_bottom

        if not within_vertical_range:
            return

        if is_left_paddle:
            if self.x - self.radius <= paddle.x + paddle.width and self.vx < 0:
                self.x = paddle.x + paddle.width + self.radius
                self.vx = abs(self.vx)
                self.vy += (self.y - (paddle_top + paddle.height / 2)) * 0.12
        else:
            if self.x + self.radius >= paddle.x and self.vx > 0:
                self.x = paddle.x - self.radius
                self.vx = -abs(self.vx)
                self.vy += (self.y - (paddle_top + paddle.height / 2)) * 0.12

        self.vx = clamp(self.vx, -950, 950)
        self.vy = clamp(self.vy, -700, 700)


class GameModel:
    """The model contains the game state and rules for Pong."""

    WIDTH = 900
    HEIGHT = 600
    PADDLE_WIDTH = 18
    PADDLE_HEIGHT = 120
    PADDLE_SPEED = 540
    BALL_RADIUS = 10
    BALL_SPEED = 520

    def __init__(self) -> None:
        self.screen_width = self.WIDTH
        self.screen_height = self.HEIGHT
        self.mode: Optional[str] = None
        self.score: Dict[str, int] = {"left": 0, "right": 0}

        self.high_score = 0.0
        self.single_player_time = 0.0
        self.selected_paddle_color = "white"
        self.unlocked_paddle_colors = ["white"]

        self.load_progress()

        self.left_paddle = Paddle(
            x=30,
            y=(self.screen_height - self.PADDLE_HEIGHT) / 2,
            width=self.PADDLE_WIDTH,
            height=self.PADDLE_HEIGHT,
            speed=self.PADDLE_SPEED,
            color=PADDLE_COLORS[self.selected_paddle_color],
        )

        self.right_paddle = Paddle(
            x=self.screen_width - 30 - self.PADDLE_WIDTH,
            y=(self.screen_height - self.PADDLE_HEIGHT) / 2,
            width=self.PADDLE_WIDTH,
            height=self.PADDLE_HEIGHT,
            speed=self.PADDLE_SPEED,
            color=PADDLE_COLORS[self.selected_paddle_color],
        )

        self.ball = Ball(
            x=self.screen_width / 2,
            y=self.screen_height / 2,
            radius=self.BALL_RADIUS,
            speed=self.BALL_SPEED,
            vx=self.BALL_SPEED,
            vy=0,
            color=(255, 255, 255),
        )

        self.update_unlocked_colors()
        self.apply_selected_color()

    def load_progress(self) -> None:
        """Read the saved high score and unlock data from disk if it exists."""
        if not os.path.exists(HIGH_SCORE_PATH):
            self.high_score = 0.0
            self.selected_paddle_color = "white"
            self.unlocked_paddle_colors = ["white"]
            return

        try:
            with open(HIGH_SCORE_PATH, "r", encoding="utf-8") as save_file:
                data = json.load(save_file)

            self.high_score = float(data.get("high_score", 0.0))
            self.selected_paddle_color = data.get("selected_color", "white")
            if self.selected_paddle_color not in PADDLE_COLORS:
                self.selected_paddle_color = "white"

            unlocked = data.get("unlocked_colors", ["white"])
            self.unlocked_paddle_colors = [
                color_name for color_name in unlocked if color_name in PADDLE_COLORS
            ]
            if not self.unlocked_paddle_colors:
                self.unlocked_paddle_colors = ["white"]

            if self.selected_paddle_color not in self.unlocked_paddle_colors:
                self.selected_paddle_color = self.unlocked_paddle_colors[0]

        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            self.high_score = 0.0
            self.selected_paddle_color = "white"
            self.unlocked_paddle_colors = ["white"]

    def save_progress(self) -> None:
        """Persist the current high score, unlocks, and selected color."""
        self.update_unlocked_colors()
        data = {
            "high_score": round(self.high_score, 1),
            "selected_color": self.selected_paddle_color,
            "unlocked_colors": self.unlocked_paddle_colors,
        }

        with open(HIGH_SCORE_PATH, "w", encoding="utf-8") as save_file:
            json.dump(data, save_file)

    def update_unlocked_colors(self) -> None:
        """Unlock paddle colors as the player reaches the required high score."""
        self.unlocked_paddle_colors = ["white"]
        for color_name, threshold in PADDLE_UNLOCKS.items():
            if color_name == "white":
                continue
            if self.high_score >= threshold:
                self.unlocked_paddle_colors.append(color_name)

        if self.selected_paddle_color not in self.unlocked_paddle_colors:
            self.selected_paddle_color = self.unlocked_paddle_colors[0]

    def apply_selected_color(self) -> None:
        """Apply the selected paddle color to both paddles."""
        color = PADDLE_COLORS.get(self.selected_paddle_color, PADDLE_COLORS["white"])
        self.left_paddle.color = color
        self.right_paddle.color = color

    def cycle_paddle_color(self) -> None:
        """Move to the next unlocked paddle color and save the selection."""
        if not self.unlocked_paddle_colors:
            return

        current_index = self.unlocked_paddle_colors.index(self.selected_paddle_color)
        next_index = (current_index + 1) % len(self.unlocked_paddle_colors)
        self.selected_paddle_color = self.unlocked_paddle_colors[next_index]
        self.apply_selected_color()
        self.save_progress()

    def start_mode(self, mode: str) -> None:
        """Start a specific game mode and reset the board for a new round."""
        self.mode = mode
        self.score = {"left": 0, "right": 0}
        if mode == "single":
            self.single_player_time = 0.0
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

        target_y = self.ball.y - self.right_paddle.height / 2
        direction = 0

        if self.ball.x > self.screen_width / 2:
            if self.right_paddle.y < target_y:
                direction = 1
            elif self.right_paddle.y > target_y:
                direction = -1

        self.right_paddle.move(direction, dt, self.screen_height)

    def update(self, dt: float, left_up: bool, left_down: bool, right_up: bool, right_down: bool) -> None:
        """Update the game state for one frame based on player input and AI."""
        if self.mode is None:
            return

        if self.mode == "single":
            self.single_player_time += dt

        left_direction = 0
        if left_up:
            left_direction -= 1
        if left_down:
            left_direction += 1
        self.left_paddle.move(left_direction, dt, self.screen_height)

        if self.mode == "single":
            self.update_cpu_paddle(dt)
        else:
            right_direction = 0
            if right_up:
                right_direction -= 1
            if right_down:
                right_direction += 1
            self.right_paddle.move(right_direction, dt, self.screen_height)

        self.ball.move(dt)
        self.ball.bounce_off_top_bottom(self.screen_height)

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

        if self.ball.x - self.ball.radius <= 0:
            # The player conceded a point in single-player mode.
            if self.mode == "single":
                self.high_score = max(self.high_score, self.single_player_time)
                self.single_player_time = 0.0
                self.update_unlocked_colors()
                self.save_progress()
            self.score["right"] += 1
            self.reset_round()
        elif self.ball.x + self.ball.radius >= self.screen_width:
            # The player scored a point; keep the survival timer running.
            self.score["left"] += 1
            self.reset_round()
