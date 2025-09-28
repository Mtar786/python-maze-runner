"""
Maze Runner Game
=================

This Python script implements an interactive maze game in the terminal.  A
random maze is generated using a depth‑first search algorithm, and the player
must navigate from the starting position (top‑left corner) to the exit (bottom‑right corner).
The game uses the built‑in `curses` module to draw the maze and handle user
input.  Additionally, a breadth‑first search algorithm is provided to compute
and display the shortest solution path when requested.

Features
--------

* Randomly generated mazes of configurable size
* Interactive navigation using the arrow keys
* Optional display of the shortest solution path
* Option to generate a new maze or quit at any time

Usage
-----

Run the script with Python 3:

```
python maze_game.py
```

Follow the on‑screen instructions to play the game.  Use the arrow keys to
move, `s` to toggle the solution display, `n` to generate a new maze and
restart, and `q` to quit.

This script requires no third‑party dependencies.
"""

import curses
import random
from collections import deque


class Maze:
    """Generate and manage a maze grid.

    The maze is represented as a 2‑D grid where 0 denotes a passage and
    1 denotes a wall.  Passages occur at odd indices, with walls between
    them.  This representation makes it straightforward to carve passages
    by removing walls between adjacent cells.
    """

    def __init__(self, width: int, height: int) -> None:
        # Ensure the maze dimensions are odd numbers to have walls around
        # every passage cell and borders around the maze.
        if width % 2 == 0:
            width += 1
        if height % 2 == 0:
            height += 1
        self.width = width
        self.height = height
        # Initialize a grid full of walls (1)
        self.grid = [[1 for _ in range(width)] for _ in range(height)]
        self._generate()

    def _generate(self) -> None:
        """Generate the maze using recursive backtracking (depth‑first search)."""
        # Start in the top‑left passage cell
        start_x, start_y = 1, 1
        self.grid[start_y][start_x] = 0
        stack = [(start_x, start_y)]

        # Directions: (dx, dy) pairs for N, S, E, W
        directions = [(0, -2), (0, 2), (2, 0), (-2, 0)]

        while stack:
            x, y = stack[-1]
            random.shuffle(directions)
            carved = False
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                # Check bounds
                if 1 <= nx < self.width - 1 and 1 <= ny < self.height - 1:
                    if self.grid[ny][nx] == 1:
                        # Carve passage: remove wall between (x, y) and (nx, ny)
                        self.grid[ny][nx] = 0
                        self.grid[y + dy // 2][x + dx // 2] = 0
                        stack.append((nx, ny))
                        carved = True
                        break
            if not carved:
                stack.pop()

    def neighbors(self, x: int, y: int):
        """Yield walkable neighbors (passages) from a given cell."""
        for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                if self.grid[ny][nx] == 0:
                    yield (nx, ny)

    def solve(self, start: tuple[int, int], goal: tuple[int, int]):
        """Compute shortest path from start to goal using BFS.

        Returns a dictionary mapping each visited cell to its predecessor.  If
        no path exists, returns an empty dict.
        """
        queue: deque[tuple[int, int]] = deque([start])
        predecessors: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
        while queue:
            current = queue.popleft()
            if current == goal:
                break
            for neighbor in self.neighbors(*current):
                if neighbor not in predecessors:
                    predecessors[neighbor] = current
                    queue.append(neighbor)
        return predecessors if goal in predecessors else {}

    def reconstruct_path(
        self, predecessors: dict[tuple[int, int], tuple[int, int] | None], goal: tuple[int, int]
    ) -> list[tuple[int, int]]:
        """Reconstruct the path from the predecessor map."""
        path: list[tuple[int, int]] = []
        current: tuple[int, int] | None = goal
        while current is not None:
            path.append(current)
            current = predecessors[current]
        path.reverse()
        return path


class MazeGame:
    """Interactive maze game using curses."""

    def __init__(self, stdscr: curses.window, width: int = 21, height: int = 21) -> None:
        self.stdscr = stdscr
        self.maze = Maze(width, height)
        self.player_pos = (1, 1)
        self.goal_pos = (self.maze.width - 2, self.maze.height - 2)
        self.show_solution = False
        # Precompute solution path (list of positions) or empty list
        preds = self.maze.solve(self.player_pos, self.goal_pos)
        self.solution_path = (
            self.maze.reconstruct_path(preds, self.goal_pos) if preds else []
        )

    def draw(self) -> None:
        """Draw the maze, player, solution (optional) and UI instructions."""
        self.stdscr.clear()
        # Draw maze walls and passages
        for y in range(self.maze.height):
            for x in range(self.maze.width):
                ch = '█' if self.maze.grid[y][x] == 1 else ' '
                self.stdscr.addch(y, x, ch)

        # Draw solution path if toggled on
        if self.show_solution and self.solution_path:
            for (x, y) in self.solution_path:
                # Avoid overwriting start and goal positions
                if (x, y) not in {self.player_pos, self.goal_pos}:
                    self.stdscr.addch(y, x, '.')

        # Draw player
        px, py = self.player_pos
        self.stdscr.addch(py, px, '@')
        # Draw goal
        gx, gy = self.goal_pos
        self.stdscr.addch(gy, gx, 'X')

        # Draw instructions at bottom
        offset_y = self.maze.height + 1
        instructions = [
            "Use arrow keys to move",
            "Press 's' to toggle solution",
            "Press 'n' to generate new maze",
            "Press 'q' to quit",
        ]
        for idx, text in enumerate(instructions):
            self.stdscr.addstr(offset_y + idx, 0, text)

        self.stdscr.refresh()

    def handle_input(self) -> bool:
        """Handle a single keypress.  Returns True to continue, False to quit."""
        key = self.stdscr.getch()
        # Movement mapping for arrow keys
        keymap = {
            curses.KEY_UP: (0, -1),
            curses.KEY_DOWN: (0, 1),
            curses.KEY_LEFT: (-1, 0),
            curses.KEY_RIGHT: (1, 0),
        }
        if key in keymap:
            dx, dy = keymap[key]
            new_x, new_y = self.player_pos[0] + dx, self.player_pos[1] + dy
            # Move only if new position is a passage
            if self.maze.grid[new_y][new_x] == 0:
                self.player_pos = (new_x, new_y)
                # Recompute solution path from new position
                preds = self.maze.solve(self.player_pos, self.goal_pos)
                self.solution_path = (
                    self.maze.reconstruct_path(preds, self.goal_pos) if preds else []
                )
        elif key in (ord('q'), ord('Q')):
            return False
        elif key in (ord('s'), ord('S')):
            self.show_solution = not self.show_solution
        elif key in (ord('n'), ord('N')):
            # Start a new maze
            self.maze = Maze(self.maze.width, self.maze.height)
            self.player_pos = (1, 1)
            self.goal_pos = (self.maze.width - 2, self.maze.height - 2)
            preds = self.maze.solve(self.player_pos, self.goal_pos)
            self.solution_path = (
                self.maze.reconstruct_path(preds, self.goal_pos) if preds else []
            )
            self.show_solution = False
        # Check win condition
        if self.player_pos == self.goal_pos:
            self._show_win_message()
            self.handle_win_input()
        return True

    def _show_win_message(self) -> None:
        """Display a congratulatory message when the player reaches the goal."""
        self.stdscr.clear()
        message_lines = [
            "Congratulations! You've completed the maze.",
            "Press 'n' for a new maze or 'q' to quit.",
        ]
        # Center the message horizontally
        max_y, max_x = self.stdscr.getmaxyx()
        for idx, line in enumerate(message_lines):
            y = self.maze.height // 2 + idx
            x = max(0, (max_x - len(line)) // 2)
            self.stdscr.addstr(y, x, line)
        self.stdscr.refresh()

    def handle_win_input(self) -> None:
        """Wait for user input after winning the maze."""
        while True:
            key = self.stdscr.getch()
            if key in (ord('q'), ord('Q')):
                # Quit to outer loop by raising StopIteration
                raise StopIteration
            elif key in (ord('n'), ord('N')):
                # Generate new maze and return to game
                self.maze = Maze(self.maze.width, self.maze.height)
                self.player_pos = (1, 1)
                self.goal_pos = (self.maze.width - 2, self.maze.height - 2)
                preds = self.maze.solve(self.player_pos, self.goal_pos)
                self.solution_path = (
                    self.maze.reconstruct_path(preds, self.goal_pos) if preds else []
                )
                self.show_solution = False
                return


def main(stdscr: curses.window) -> None:
    # Hide cursor
    curses.curs_set(0)
    # Enable non‑blocking mode (optional: comment out to wait for key)
    stdscr.nodelay(False)
    # Create game instance
    game = MazeGame(stdscr)
    try:
        while True:
            game.draw()
            cont = game.handle_input()
            if not cont:
                break
    except StopIteration:
        # Win loop uses StopIteration to break out of nested loops
        pass


if __name__ == "__main__":
    curses.wrapper(main)