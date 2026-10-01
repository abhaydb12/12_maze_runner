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

# Task 4: Difficulty settings
DIFFICULTIES = {
    "Easy": (10, 8),
    "Medium": (15, 13),
    "Hard": (20, 18),
}

FOG_RADIUS = 3
MAX_LEADERBOARD_ENTRIES = 5
HUD_HEIGHT = 60


class GameEngine:

    def __init__(self):
        pygame.init()

        self.screen = None
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

        self.leaderboard_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "leaderboard.json"
        )

        self.leaderboard = self.load_leaderboard()

        # Task 4
        self.difficulty = None
        self.cols = None
        self.rows = None
        self.width = None
        self.height = None

        self.walls = None
        self.player = None
        self.exit_rect = None

        self.start_time = None
        self.elapsed = 0
        self.won = False

        # Task 1
        self.show_path = False
        self.solution_path = []

        # Task 3
        self.score_saved = False

        # Start with difficulty selection
        self.show_difficulty_screen = True

    # ==========================================================
    # TASK 3: LOAD LEADERBOARD
    # ==========================================================

    def load_leaderboard(self):
        try:
            with open(
                self.leaderboard_file,
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

            if not isinstance(data, list):
                return []

            valid_times = []

            for value in data:
                if isinstance(value, (int, float)) and value >= 0:
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
    # TASK 3: SAVE LEADERBOARD
    # ==========================================================

    def save_leaderboard(self):
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
            pass

    # ==========================================================
    # TASK 3: ADD COMPLETION TIME
    # ==========================================================

    def add_completion_time(self):
        self.leaderboard.append(float(self.elapsed))

        self.leaderboard.sort()

        self.leaderboard = self.leaderboard[
            :MAX_LEADERBOARD_ENTRIES
        ]

        self.save_leaderboard()

    # ==========================================================
    # TASK 4: SET DIFFICULTY
    # ==========================================================

    def set_difficulty(self, difficulty):
        self.difficulty = difficulty

        self.cols, self.rows = DIFFICULTIES[difficulty]

        self.width = self.cols * CELL
        self.height = self.rows * CELL + HUD_HEIGHT

        self.screen = pygame.display.set_mode(
            (self.width, self.height)
        )

        pygame.display.set_caption(
            f"Maze Runner - {difficulty}"
        )

        self.show_difficulty_screen = False

        self.reset()

    # ==========================================================
    # TASK 4: DIFFICULTY SCREEN
    # ==========================================================

    def draw_difficulty_screen(self):
        self.screen.fill(BG)

        title = self.big_font.render(
            "MAZE RUNNER",
            True,
            (30, 30, 50)
        )

        subtitle = self.font.render(
            "Select Difficulty",
            True,
            (50, 50, 70)
        )

        self.screen.blit(
            title,
            (
                400 - title.get_width() // 2,
                80
            )
        )

        self.screen.blit(
            subtitle,
            (
                400 - subtitle.get_width() // 2,
                140
            )
        )

        button_width = 300
        button_height = 60
        button_x = 250

        difficulties = [
            ("Easy", 10, 8),
            ("Medium", 15, 13),
            ("Hard", 20, 18),
        ]

        for index, (name, cols, rows) in enumerate(difficulties):

            y = 220 + index * 90

            button_rect = pygame.Rect(
                button_x,
                y,
                button_width,
                button_height
            )

            pygame.draw.rect(
                self.screen,
                (60, 70, 100),
                button_rect,
                border_radius=8
            )

            label = self.font.render(
                f"{name} ({cols}x{rows})",
                True,
                (255, 255, 255)
            )

            self.screen.blit(
                label,
                (
                    button_rect.centerx
                    - label.get_width() // 2,
                    button_rect.centery
                    - label.get_height() // 2
                )
            )

        pygame.display.flip()

    # ==========================================================
    # TASK 4: DIFFICULTY SCREEN EVENTS
    # ==========================================================

    def handle_difficulty_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:

                    button_width = 300
                    button_height = 60
                    button_x = 250

                    difficulties = [
                        ("Easy", 10, 8),
                        ("Medium", 15, 13),
                        ("Hard", 20, 18),
                    ]

                    for index, (name, cols, rows) in enumerate(
                        difficulties
                    ):

                        y = 220 + index * 90

                        button_rect = pygame.Rect(
                            button_x,
                            y,
                            button_width,
                            button_height
                        )

                        if button_rect.collidepoint(event.pos):
                            self.set_difficulty(name)
                            break

        return True

    # ==========================================================
    # RESET CURRENT MAZE
    # ==========================================================

    def reset(self):

        self.walls = generate_maze(
            self.cols,
            self.rows
        )

        self.player = Player(0, 0)

        self.exit_rect = pygame.Rect(
            (self.cols - 1) * CELL + 5,
            (self.rows - 1) * CELL + 5,
            CELL - 10,
            CELL - 10
        )

        self.start_time = time.time()

        self.elapsed = 0

        self.won = False

        # Task 1
        self.show_path = False
        self.solution_path = []

        # Task 3
        self.score_saved = False

    # ==========================================================
    # TASK 1: BFS SHORTEST PATH
    # ==========================================================

    def find_shortest_path(self):

        start = (0, 0)
        goal = (self.rows - 1, self.cols - 1)

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
                    0 <= nr < self.rows
                    and 0 <= nc < self.cols
                ):
                    continue

                if self.walls[r][c][wall_dir]:
                    continue

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

                # R = new maze at current difficulty
                if event.key == pygame.K_r:
                    self.reset()

                # H = shortest path
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
            self.rows,
            self.cols
        )

        self.elapsed = (
            time.time() - self.start_time
        )

        if self.player.rect.colliderect(
            self.exit_rect
        ):

            self.won = True

            if not self.score_saved:

                self.add_completion_time()

                self.score_saved = True

    # ==========================================================
    # DRAW MAZE
    # ==========================================================

    def draw_maze(self):

        wall_w = 3

        for r in range(self.rows):

            for c in range(self.cols):

                x = c * CELL
                y = r * CELL

                w = self.walls[r][c]

                if w[0]:
                    pygame.draw.line(
                        self.screen,
                        WALL_COLOR,
                        (x, y),
                        (x + CELL, y),
                        wall_w
                    )

                if w[1]:
                    pygame.draw.line(
                        self.screen,
                        WALL_COLOR,
                        (x, y + CELL),
                        (x + CELL, y + CELL),
                        wall_w
                    )

                if w[2]:
                    pygame.draw.line(
                        self.screen,
                        WALL_COLOR,
                        (x + CELL, y),
                        (x + CELL, y + CELL),
                        wall_w
                    )

                if w[3]:
                    pygame.draw.line(
                        self.screen,
                        WALL_COLOR,
                        (x, y),
                        (x, y + CELL),
                        wall_w
                    )

    # ==========================================================
    # TASK 1: DRAW PATH
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

        maze_width = self.cols * CELL
        maze_height = self.rows * CELL

        fog = pygame.Surface(
            (maze_width, maze_height),
            pygame.SRCALPHA
        )

        fog.fill(
            (0, 0, 0, 220)
        )

        player_center = self.player.rect.center

        reveal_radius = FOG_RADIUS * CELL

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
    # TASK 3: LEADERBOARD
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
                self.width // 2
                - title.get_width() // 2,
                self.rows * CELL // 2 + 65
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
                    self.width // 2
                    - score_text.get_width() // 2,
                    self.rows * CELL // 2
                    + 95
                    + (index - 1) * 25
                )
            )

    # ==========================================================
    # DRAW GAME
    # ==========================================================

    def draw(self):

        self.screen.fill(BG)

        self.draw_maze()

        self.draw_solution_path()

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

        self.player.draw(
            self.screen
        )

        self.draw_fog()

        # HUD
        hud = pygame.Rect(
            0,
            self.rows * CELL,
            self.width,
            HUD_HEIGHT
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
                self.rows * CELL + 18
            )
        )

        # Win screen
        if self.won:

            overlay = pygame.Surface(
                (
                    self.width,
                    self.rows * CELL
                ),
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
                    self.width // 2
                    - msg.get_width() // 2,
                    35
                )
            )

            self.draw_leaderboard()

            sub = self.font.render(
                "Press R for a new maze",
                True,
                (200, 200, 200)
            )

            self.screen.blit(
                sub,
                (
                    self.width // 2
                    - sub.get_width() // 2,
                    self.rows * CELL - 35
                )
            )

        pygame.display.flip()

    # ==========================================================
    # MAIN LOOP
    # ==========================================================

    def run(self):

        running = True

        while running:

            if self.show_difficulty_screen:

                # The selection screen needs a fixed window
                # before a difficulty has been selected.
                if self.screen is None:
                    self.screen = pygame.display.set_mode(
                        (800, 520)
                    )

                running = self.handle_difficulty_events()

                if running and self.show_difficulty_screen:
                    self.draw_difficulty_screen()

            else:

                running = self.handle_events()

                self.update()

                self.draw()

                self.clock.tick(FPS)

        pygame.quit()