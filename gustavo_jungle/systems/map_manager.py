import math
import random
import pygame
from settings import (
    MAP_COLS, MAP_ROWS, TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,
    SCREEN_WIDTH, SCREEN_HEIGHT,
)


class Camera:

    def __init__(self):
        self.offset = pygame.math.Vector2(0, 0)

    def update(self, target_pos: pygame.math.Vector2):
        desired = pygame.math.Vector2(
            target_pos.x - SCREEN_WIDTH // 2,
            target_pos.y - SCREEN_HEIGHT // 2,
        )
        self.offset += (desired - self.offset) * 0.1
        self.offset.x = max(0, min(MAP_WIDTH - SCREEN_WIDTH, self.offset.x))
        self.offset.y = max(0, min(MAP_HEIGHT - SCREEN_HEIGHT, self.offset.y))

    def get_offset(self) -> tuple[float, float]:
        return (self.offset.x, self.offset.y)


def _noise(x, y, seed=0):
    n = int(x * 73 + y * 179 + seed * 31)
    n = (n << 13) ^ n
    return ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7FFFFFFF) / 2147483647.0


class MapManager:

    def __init__(self, asset_gen):
        self.asset_gen = asset_gen
        self.grid: list[list[str]] = []
        self.collision_rects: list[pygame.Rect] = []
        self.water_rects: list[pygame.Rect] = []
        self.tall_grass_rects: list[pygame.Rect] = []
        self.campfire_rects: list[pygame.Rect] = []
        self.generate_map()

    def _get_biome(self, col, row):
        cx, cy = MAP_COLS // 2, MAP_ROWS // 2
        dx, dy = col - cx, row - cy
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 5:
            return "center"
        if dx < -4 and dy < -4:
            return "dense_jungle"
        if dx < -2 and dy > 4:
            return "swamp"
        if dx > 4 and dy < -2:
            return "ruins_area"
        return "normal"

    def generate_map(self):
        random.seed(42)
        self.grid = [["grass"] * MAP_COLS for _ in range(MAP_ROWS)]

        num_tree_clusters = 22
        for i in range(num_tree_clusters):
            cx = random.randint(2, MAP_COLS - 3)
            cy = random.randint(2, MAP_ROWS - 3)
            biome = self._get_biome(cx, cy)
            if biome == "dense_jungle":
                size = random.randint(3, 6)
                density = 0.75
            elif biome == "ruins_area":
                size = random.randint(1, 3)
                density = 0.3
            else:
                size = random.randint(2, 5)
                density = 0.6
            for ddx in range(-size, size + 1):
                for ddy in range(-size, size + 1):
                    nx, ny = cx + ddx, cy + ddy
                    if 0 <= nx < MAP_COLS and 0 <= ny < MAP_ROWS:
                        if ddx * ddx + ddy * ddy <= size * size and random.random() < density:
                            self.grid[ny][nx] = "tree"

        num_rivers = 3
        for r in range(num_rivers):
            x = random.randint(5, MAP_COLS - 6)
            y = 0
            phase = random.uniform(0, math.pi * 2)
            while y < MAP_ROWS:
                width = int(1 + abs(math.sin(y * 0.15 + phase)) * 2.5)
                biome = self._get_biome(x, y)
                if biome == "swamp":
                    width += 1
                for w in range(-width // 2, width // 2 + 1):
                    wx = x + w
                    if 0 <= wx < MAP_COLS:
                        self.grid[y][wx] = "water"
                y += 1
                curve = math.sin(y * 0.2 + phase) * 1.5
                x += int(round(curve)) + random.choice([-1, 0, 0, 1])
                x = max(2, min(MAP_COLS - 3, x))

        for _ in range(30):
            bx = random.randint(0, MAP_COLS - 1)
            by = random.randint(0, MAP_ROWS - 1)
            if self.grid[by][bx] == "grass":
                self.grid[by][bx] = "bush"

        for _ in range(2):
            px = random.randint(5, MAP_COLS - 6)
            for y in range(MAP_ROWS):
                for w in range(-1, 2):
                    nx = px + w
                    if 0 <= nx < MAP_COLS and self.grid[y][nx] in ("grass", "bush"):
                        self.grid[y][nx] = "path"
                px += random.choice([-1, 0, 0, 1])
                px = max(1, min(MAP_COLS - 2, px))

        ruins_centers = []
        for _ in range(4):
            attempts = 0
            while attempts < 30:
                rcx = random.randint(4, MAP_COLS - 5)
                rcy = random.randint(4, MAP_ROWS - 5)
                biome = self._get_biome(rcx, rcy)
                if biome in ("ruins_area", "normal") and biome != "center":
                    ruins_centers.append((rcx, rcy))
                    break
                attempts += 1
        for rcx, rcy in ruins_centers:
            rsize = random.randint(2, 3)
            for ddx in range(-rsize, rsize + 1):
                for ddy in range(-rsize, rsize + 1):
                    nx, ny = rcx + ddx, rcy + ddy
                    if 0 <= nx < MAP_COLS and 0 <= ny < MAP_ROWS:
                        if random.random() < 0.5:
                            self.grid[ny][nx] = "ruins"
                        elif self.grid[ny][nx] == "grass":
                            self.grid[ny][nx] = "path"

        campfire_count = 0
        while campfire_count < 4:
            cfx = random.randint(3, MAP_COLS - 4)
            cfy = random.randint(3, MAP_ROWS - 4)
            biome = self._get_biome(cfx, cfy)
            if biome != "center" and self.grid[cfy][cfx] in ("grass", "path"):
                self.grid[cfy][cfx] = "campfire"
                campfire_count += 1

        tg_placed = 0
        while tg_placed < 30:
            tgx = random.randint(1, MAP_COLS - 2)
            tgy = random.randint(1, MAP_ROWS - 2)
            biome = self._get_biome(tgx, tgy)
            if self.grid[tgy][tgx] == "grass":
                prob = 0.8 if biome == "swamp" else 0.4
                if random.random() < prob:
                    self.grid[tgy][tgx] = "tall_grass"
                    tg_placed += 1

        for _ in range(25):
            fx = random.randint(0, MAP_COLS - 1)
            fy = random.randint(0, MAP_ROWS - 1)
            if self.grid[fy][fx] == "grass":
                self.grid[fy][fx] = "flowers"

        for _ in range(20):
            rx = random.randint(0, MAP_COLS - 1)
            ry = random.randint(0, MAP_ROWS - 1)
            if self.grid[ry][rx] == "grass":
                self.grid[ry][rx] = "rocks"

        center_r = 3
        center_x, center_y = MAP_COLS // 2, MAP_ROWS // 2
        for ddy in range(-center_r, center_r + 1):
            for ddx in range(-center_r, center_r + 1):
                nx, ny = center_x + ddx, center_y + ddy
                if 0 <= nx < MAP_COLS and 0 <= ny < MAP_ROWS:
                    self.grid[ny][nx] = "grass"

        self.collision_rects = []
        self.water_rects = []
        self.tall_grass_rects = []
        self.campfire_rects = []
        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                tile = self.grid[row][col]
                r = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if tile == "tree":
                    self.collision_rects.append(r)
                elif tile == "water":
                    self.water_rects.append(r)
                elif tile == "tall_grass":
                    self.tall_grass_rects.append(r)
                elif tile == "campfire":
                    self.campfire_rects.append(r)

    def get_collision_rects(self) -> list[pygame.Rect]:
        return self.collision_rects

    def get_water_rects(self) -> list[pygame.Rect]:
        return self.water_rects

    def get_tall_grass_rects(self) -> list[pygame.Rect]:
        return self.tall_grass_rects

    def get_campfire_rects(self) -> list[pygame.Rect]:
        return self.campfire_rects

    def get_grass_positions(self) -> list[tuple[int, int]]:
        positions = []
        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                if self.grid[row][col] == "grass":
                    positions.append((col * TILE_SIZE + TILE_SIZE // 2,
                                      row * TILE_SIZE + TILE_SIZE // 2))
        return positions

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
