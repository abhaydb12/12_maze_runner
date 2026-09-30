import pygame
import time
import json
import os
from collections import deque

from game.maze import generate_maze, CELL
from game.player import Player


FPS = 60

BG = (240, 235, 220)
WALL_COLOR = (40, 40, 60)
EXIT_COLOR = (80, 200, 80)
PATH_COLOR = (255, 220, 80)

COLS, ROWS = 15, 13

WIDTH = COLS * CELL
HEIGHT = ROWS * CELL + 60

# Task 2: Fog of War
FOG_RADIUS = 3

# Task 3: Leaderboard
MAX_LEADERBOARD_ENTRIES = 5


class GameEngine:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT)
        )

        pygame.display.set_caption("Maze Runner")

        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont(
            "monospace",
            22
        )

        self.big_font = pygame.font.SysFont(
            "monospace",
            36,
            bold=True
        )

        # Task 3: Load saved leaderboard
        self.leaderboard_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "leaderboard.json"
        )

        self.leaderboard = self.load_leaderboard()

        self.reset()

    # ==========================================================
    # TASK 3: LEADERBOARD - LOAD
    # ==========================================================

    def load_leaderboard(self):
        """
        Load the leaderboard from leaderboard.json.

        If the file doesn't exist or contains invalid data,
        start with an empty leaderboard.
        """

        try:
            with open(
                self.leaderboard_file,
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

            if not isinstance(data, list):
                return []

            # Keep only valid numeric times
            valid_times = []

            for value in data:
                if isinstance(value, (int, float)):
                    if value >= 0:
                        valid_times.append(float(value))

            valid_times.sort()

            return valid_times[:MAX_LEADERBOARD_ENTRIES]

        except (
            FileNotFoundError,
            json.JSONDecodeError,
            OSError,
            TypeError,
            ValueError
        ):
            return []

    # ==========================================================
    # TASK 3: LEADERBOARD - SAVE
    # ==========================================================

    def save_leaderboard(self):
        """Save the current leaderboard to leaderboard.json."""

        try:
            with open(
                self.leaderboard_file,
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(
                    self.leaderboard,
                    file,
                    indent=4
                )

        except OSError:
            # The game should continue even if saving fails.
            pass

    # ==========================================================
    # TASK 3: ADD COMPLETION TIME
    # ==========================================================

    def add_completion_time(self):
        """
        Add the current completion time to the leaderboard.

        Only the best five times are retained.
        """

        self.leaderboard.append(float(self.elapsed))

        self.leaderboard.sort()

        self.leaderboard = self.leaderboard[
            :MAX_LEADERBOARD_ENTRIES
        ]

        self.save_leaderboard()

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):
        self.walls = generate_maze(
            COLS,
            ROWS
        )

        self.player = Player(0, 0)

        self.exit_rect = pygame.Rect(
            (COLS - 1) * CELL + 5,
            (ROWS - 1) * CELL + 5,
            CELL - 10,
            CELL - 10
        )

        self.start_time = time.time()

        self.elapsed = 0

        self.won = False

        # Task 1: Shortest path
        self.show_path = False
        self.solution_path = []

        # Task 3: Prevent recording the same
        # completion time more than once.
        self.score_saved = False

    # ==========================================================
    # TASK 1: SHORTEST PATH / BFS
    # ==========================================================

    def find_shortest_path(self):
        """Find the shortest valid path from start to exit using BFS."""

        start = (0, 0)
        goal = (ROWS - 1, COLS - 1)

        queue = deque([start])

        parent = {
            start: None
        }

        # N, S, E, W
        directions = [
            (-1, 0, 0, 1),
            (1, 0, 1, 0),
            (0, 1, 2, 3),
            (0, -1, 3, 2)
        ]

        while queue:
            r, c = queue.popleft()

            if (r, c) == goal:
                break

            for dr, dc, wall_dir, opposite_wall in directions:

                nr = r + dr
                nc = c + dc

                if not (
                    0 <= nr < ROWS
                    and 0 <= nc < COLS
                ):
                    continue

                # Wall in current cell
                if self.walls[r][c][wall_dir]:
                    continue

                # Wall in neighboring cell
                if self.walls[nr][nc][opposite_wall]:
                    continue

                neighbor = (nr, nc)

                if neighbor not in parent:
                    parent[neighbor] = (r, c)
                    queue.append(neighbor)

        if goal not in parent:
            return []

        path = []

        current = goal

        while current is not None:
            path.append(current)
            current = parent[current]

        path.reverse()

        return path

    # ==========================================================
    # EVENT HANDLING
    # ==========================================================

    def handle_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:

                # R = New Maze
                if event.key == pygame.K_r:
                    self.reset()

                # H = Shortest Path Hint
                elif event.key == pygame.K_h:

                    self.show_path = not self.show_path

                    if self.show_path:
                        self.solution_path = (
                            self.find_shortest_path()
                        )
                    else:
                        self.solution_path = []

        return True

    # ==========================================================
    # UPDATE
    # ==========================================================

    def update(self):

        if self.won:
            return

        keys = pygame.key.get_pressed()

        self.player.move(
            keys,
            self.walls,
            ROWS,
            COLS
        )

        self.elapsed = (
            time.time() - self.start_time
        )

        # Player reached exit
        if self.player.rect.colliderect(
            self.exit_rect
        ):

            self.won = True

            # Task 3:
            # Save completion time only once.
            if not self.score_saved:

                self.add_completion_time()

                self.score_saved = True

    # ==========================================================
    # DRAW MAZE
    # ==========================================================

    def draw_maze(self):

        wall_w = 3

        for r in range(ROWS):

            for c in range(COLS):

                x = c * CELL
                y = r * CELL

                w = self.walls[r][c]

                # North
                if w[0]:
                    pygame.draw.line(
                        self.screen,
                        WALL_COLOR,
                        (x, y),
                        (x + CELL, y),
                        wall_w
                    )

                # South
                if w[1]:
                    pygame.draw.line(
                        self.screen,
                        WALL_COLOR,
                        (x, y + CELL),
                        (x + CELL, y + CELL),
                        wall_w
                    )

                # East
                if w[2]:
                    pygame.draw.line(
                        self.screen,
                        WALL_COLOR,
                        (x + CELL, y),
                        (x + CELL, y + CELL),
                        wall_w
                    )

                # West
                if w[3]:
                    pygame.draw.line(
                        self.screen,
                        WALL_COLOR,
                        (x, y),
                        (x, y + CELL),
                        wall_w
                    )

    # ==========================================================
    # TASK 1: DRAW SHORTEST PATH
    # ==========================================================

    def draw_solution_path(self):

        if not self.show_path:
            return

        for r, c in self.solution_path:

            path_rect = pygame.Rect(
                c * CELL + 12,
                r * CELL + 12,
                CELL - 24,
                CELL - 24
            )

            pygame.draw.rect(
                self.screen,
                PATH_COLOR,
                path_rect,
                border_radius=5
            )

    # ==========================================================
    # TASK 2: FOG OF WAR
    # ==========================================================

    def draw_fog(self):

        maze_width = COLS * CELL
        maze_height = ROWS * CELL

        fog = pygame.Surface(
            (maze_width, maze_height),
            pygame.SRCALPHA
        )

        # Dark overlay
        fog.fill(
            (0, 0, 0, 220)
        )

        # Player position
        player_center = self.player.rect.center

        # Three-cell radius
        reveal_radius = FOG_RADIUS * CELL

        # Transparent area around player
        pygame.draw.circle(
            fog,
            (0, 0, 0, 0),
            player_center,
            reveal_radius
        )

        self.screen.blit(
            fog,
            (0, 0)
        )

    # ==========================================================
    # TASK 3: DRAW LEADERBOARD
    # ==========================================================

    def draw_leaderboard(self):

        title = self.font.render(
            "Leaderboard",
            True,
            (255, 255, 255)
        )

        self.screen.blit(
            title,
            (
                WIDTH // 2 - title.get_width() // 2,
                ROWS * CELL // 2 + 65
            )
        )

        for index, score in enumerate(
            self.leaderboard[:MAX_LEADERBOARD_ENTRIES],
            start=1
        ):

            score_text = self.font.render(
                f"{index}. {score:.1f}s",
                True,
                (220, 220, 220)
            )

            self.screen.blit(
                score_text,
                (
                    WIDTH // 2
                    - score_text.get_width() // 2,
                    ROWS * CELL // 2
                    + 95
                    + (index - 1) * 25
                )
            )

    # ==========================================================
    # DRAW
    # ==========================================================

    def draw(self):

        self.screen.fill(BG)

        # Maze
        self.draw_maze()

        # Shortest path
        self.draw_solution_path()

        # Exit
        pygame.draw.rect(
            self.screen,
            EXIT_COLOR,
            self.exit_rect,
            border_radius=4
        )

        ex_label = self.font.render(
            "EXIT",
            True,
            (20, 80, 20)
        )

        self.screen.blit(
            ex_label,
            (
                self.exit_rect.x + 2,
                self.exit_rect.y + 4
            )
        )

        # Player
        self.player.draw(
            self.screen
        )

        # Fog
        self.draw_fog()

        # HUD
        hud = pygame.Rect(
            0,
            ROWS * CELL,
            WIDTH,
            60
        )

        pygame.draw.rect(
            self.screen,
            (30, 30, 50),
            hud
        )

        time_surf = self.font.render(
            f"Time: {self.elapsed:.1f}s   "
            f"H = Hint   R = New Maze",
            True,
            (200, 200, 200)
        )

        self.screen.blit(
            time_surf,
            (
                10,
                ROWS * CELL + 18
            )
        )

        # ======================================================
        # WIN SCREEN
        # ======================================================

        if self.won:

            overlay = pygame.Surface(
                (WIDTH, ROWS * CELL),
                pygame.SRCALPHA
            )

            overlay.fill(
                (0, 0, 0, 180)
            )

            self.screen.blit(
                overlay,
                (0, 0)
            )

            msg = self.big_font.render(
                f"Solved in {self.elapsed:.1f}s!",
                True,
                (80, 240, 80)
            )

            self.screen.blit(
                msg,
                (
                    WIDTH // 2
                    - msg.get_width() // 2,
                    35
                )
            )

            # Task 3: Leaderboard
            self.draw_leaderboard()

            sub = self.font.render(
                "Press R for a new maze",
                True,
                (200, 200, 200)
            )

            self.screen.blit(
                sub,
                (
                    WIDTH // 2
                    - sub.get_width() // 2,
                    ROWS * CELL - 35
                )
            )

        pygame.display.flip()

    # ==========================================================
    # MAIN LOOP
    # ==========================================================

    def run(self):

        running = True

        while running:

            running = self.handle_events()

            self.update()

            self.draw()

            self.clock.tick(FPS)

        pygame.quit()