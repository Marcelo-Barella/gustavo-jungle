import random
import pygame
from settings import (
    MAP_COLS, MAP_ROWS, TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,
    SCREEN_WIDTH, SCREEN_HEIGHT,
)


class Camera:

    def __init__(self):
        self.offset = pygame.math.Vector2(0, 0)
        self.shake_timer = 0.0
        self.shake_intensity = 0.0
        self.shake_offset = pygame.math.Vector2(0, 0)
        self._shake_duration = 0.0

    def shake(self, intensity: float = 5.0, duration: float = 0.3):
        self.shake_intensity = intensity
        self.shake_timer = duration
        self._shake_duration = duration

    def update(self, target_pos: pygame.math.Vector2, dt: float = 0.0):
        desired = pygame.math.Vector2(
            target_pos.x - SCREEN_WIDTH // 2,
            target_pos.y - SCREEN_HEIGHT // 2,
        )
        self.offset += (desired - self.offset) * 0.1
        self.offset.x = max(0, min(MAP_WIDTH - SCREEN_WIDTH, self.offset.x))
        self.offset.y = max(0, min(MAP_HEIGHT - SCREEN_HEIGHT, self.offset.y))

        if self.shake_timer > 0:
            self.shake_timer -= dt
            decay = self.shake_timer / self._shake_duration if self._shake_duration > 0 else 0
            intensity = self.shake_intensity * decay
            self.shake_offset.x = random.uniform(-intensity, intensity)
            self.shake_offset.y = random.uniform(-intensity, intensity)
        else:
            self.shake_offset.x = 0
            self.shake_offset.y = 0

    def get_offset(self) -> tuple[float, float]:
        return (self.offset.x + self.shake_offset.x, self.offset.y + self.shake_offset.y)


class MapManager:

    def __init__(self, asset_gen):
        self.asset_gen = asset_gen
        self.grid: list[list[str]] = []
        self.collision_rects: list[pygame.Rect] = []
        self.generate_map()

    def generate_map(self):
        random.seed(42)
        self.grid = [["grass"] * MAP_COLS for _ in range(MAP_ROWS)]

        num_tree_clusters = 18
        for _ in range(num_tree_clusters):
            cx = random.randint(2, MAP_COLS - 3)
            cy = random.randint(2, MAP_ROWS - 3)
            size = random.randint(2, 5)
            for dx in range(-size, size + 1):
                for dy in range(-size, size + 1):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < MAP_COLS and 0 <= ny < MAP_ROWS:
                        if dx * dx + dy * dy <= size * size and random.random() < 0.6:
                            self.grid[ny][nx] = "tree"

        num_rivers = 3
        for _ in range(num_rivers):
            x = random.randint(0, MAP_COLS - 1)
            y = 0
            while y < MAP_ROWS:
                for w in range(random.randint(1, 3)):
                    wx = x + w
                    if 0 <= wx < MAP_COLS:
                        self.grid[y][wx] = "water"
                y += 1
                x += random.choice([-1, 0, 0, 1])
                x = max(0, min(MAP_COLS - 1, x))

        for _ in range(40):
            bx = random.randint(0, MAP_COLS - 1)
            by = random.randint(0, MAP_ROWS - 1)
            if self.grid[by][bx] == "grass":
                self.grid[by][bx] = "bush"

        px = random.randint(0, MAP_COLS - 1)
        for y in range(MAP_ROWS):
            for w in range(-1, 2):
                nx = px + w
                if 0 <= nx < MAP_COLS and self.grid[y][nx] == "grass":
                    self.grid[y][nx] = "path"
            px += random.choice([-1, 0, 0, 1])
            px = max(1, min(MAP_COLS - 2, px))

        center_r = 3
        center_x, center_y = MAP_COLS // 2, MAP_ROWS // 2
        for dy in range(-center_r, center_r + 1):
            for dx in range(-center_r, center_r + 1):
                nx, ny = center_x + dx, center_y + dy
                if 0 <= nx < MAP_COLS and 0 <= ny < MAP_ROWS:
                    self.grid[ny][nx] = "grass"

        self.collision_rects = []
        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                if self.grid[row][col] in ("tree", "water"):
                    self.collision_rects.append(
                        pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    )

    def get_collision_rects(self) -> list[pygame.Rect]:
        return self.collision_rects

    def draw(self, surface: pygame.Surface, camera_offset: tuple[float, float]):
        ox, oy = camera_offset
        start_col = max(0, int(ox) // TILE_SIZE)
        start_row = max(0, int(oy) // TILE_SIZE)
        end_col = min(MAP_COLS, start_col + SCREEN_WIDTH // TILE_SIZE + 2)
        end_row = min(MAP_ROWS, start_row + SCREEN_HEIGHT // TILE_SIZE + 2)

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                tile_type = self.grid[row][col]
                tile_surf = self.asset_gen.get_tile(tile_type)
                surface.blit(tile_surf, (col * TILE_SIZE - ox, row * TILE_SIZE - oy))
