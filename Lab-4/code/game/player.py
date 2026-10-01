import pygame
from game.maze import CELL

SPEED = 3


class Player:
    def __init__(self, r, c):
        self.r = r
        self.c = c

        x = c * CELL + CELL // 2
        y = r * CELL + CELL // 2

        self.rect = pygame.Rect(x - 10, y - 10, 20, 20)
        self.color = (60, 120, 220)

    def move(self, keys, walls, rows, cols):
        dx, dy = 0, 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = SPEED

        # Move horizontally while respecting maze walls
        new_rect = self.rect.move(dx, 0)
        if not self._hits_wall(new_rect, walls, rows, cols):
            self.rect = new_rect

        # Move vertically while respecting maze walls
        new_rect = self.rect.move(0, dy)
        if not self._hits_wall(new_rect, walls, rows, cols):
            self.rect = new_rect

    def _hits_wall(self, rect, walls, rows, cols):
        # Check outer maze boundaries
        if rect.left < 0 or rect.right > cols * CELL:
            return True

        if rect.top < 0 or rect.bottom > rows * CELL:
            return True

        # Determine which cells the player currently overlaps
        min_col = rect.left // CELL
        max_col = (rect.right - 1) // CELL
        min_row = rect.top // CELL
        max_row = (rect.bottom - 1) // CELL

        # Check walls of every cell touched by the player
        for r in range(min_row, max_row + 1):
            for c in range(min_col, max_col + 1):

                cell_x = c * CELL
                cell_y = r * CELL

                # N wall
                if walls[r][c][0] and rect.top < cell_y:
                    return True

                # S wall
                if walls[r][c][1] and rect.bottom > cell_y + CELL:
                    return True

                # E wall
                if walls[r][c][2] and rect.right > cell_x + CELL:
                    return True

                # W wall
                if walls[r][c][3] and rect.left < cell_x:
                    return True

        return False

    def draw(self, screen):
        pygame.draw.ellipse(screen, self.color, self.rect)
