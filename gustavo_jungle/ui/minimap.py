import math
import pygame
from settings import (
    MAP_WIDTH, MAP_HEIGHT, MINIMAP_SIZE,
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE,
)

TILE_COLORS = {
    "grass": (0x22, 0x8B, 0x22),
    "tree": (0x00, 0x64, 0x00),
    "water": (0x40, 0xA4, 0xDF),
    "path": (0xD2, 0xB4, 0x8C),
    "bush": (0x90, 0xEE, 0x90),
}

MARGIN = 10
BG_ALPHA = 180
GOLDEN = (255, 215, 0)
WHITE = (255, 255, 255)
BRIGHT_GREEN = (0, 255, 0)
RED = (255, 0, 0)
BOSS_HP_THRESHOLD = 300


class Minimap:

    def __init__(self, map_width: int = MAP_WIDTH, map_height: int = MAP_HEIGHT,
                 minimap_size: int = MINIMAP_SIZE):
        self.map_width = map_width
        self.map_height = map_height
        self.minimap_size = minimap_size
        self.scale = minimap_size / max(map_width, map_height)
        self.terrain_surface: pygame.Surface | None = None
        self.pulse_timer = 0.0

    def generate_terrain_surface(self, map_grid: list[list[str]]) -> None:
        surf = pygame.Surface((self.minimap_size, self.minimap_size))
        surf.fill((0, 0, 0))
        rows = len(map_grid)
        cols = len(map_grid[0]) if rows else 0
        tile_w = self.minimap_size / cols if cols else 1
        tile_h = self.minimap_size / rows if rows else 1
        for r in range(rows):
            for c in range(cols):
                color = TILE_COLORS.get(map_grid[r][c], TILE_COLORS["grass"])
                rect = pygame.Rect(int(c * tile_w), int(r * tile_h),
                                   max(1, int(tile_w) + 1), max(1, int(tile_h) + 1))
                surf.fill(color, rect)
        self.terrain_surface = surf

    def draw(self, surface: pygame.Surface, player_pos: pygame.math.Vector2,
             enemies: pygame.sprite.Group, camera_offset: tuple[float, float]) -> None:
        mm = self.minimap_size
        dest_x = SCREEN_WIDTH - mm - MARGIN
        dest_y = SCREEN_HEIGHT - mm - MARGIN

        bg = pygame.Surface((mm, mm), pygame.SRCALPHA)
        bg.fill((0, 0, 0, BG_ALPHA))
        surface.blit(bg, (dest_x, dest_y))

        if self.terrain_surface is not None:
            surface.blit(self.terrain_surface, (dest_x, dest_y))

        px = int(player_pos.x * self.scale)
        py = int(player_pos.y * self.scale)
        pygame.draw.circle(surface, BRIGHT_GREEN, (dest_x + px, dest_y + py), 3)

        pulse_radius = 4 + int(math.sin(self.pulse_timer * 4) * 1.5)
        for enemy in enemies:
            if not enemy.is_alive:
                continue
            ex = int(enemy.pos.x * self.scale)
            ey = int(enemy.pos.y * self.scale)
            if enemy.max_hp > BOSS_HP_THRESHOLD:
                pygame.draw.circle(surface, RED, (dest_x + ex, dest_y + ey), pulse_radius)
            else:
                pygame.draw.circle(surface, RED, (dest_x + ex, dest_y + ey), 2)

        cam_x = int(camera_offset[0] * self.scale)
        cam_y = int(camera_offset[1] * self.scale)
        cam_w = int(SCREEN_WIDTH * self.scale)
        cam_h = int(SCREEN_HEIGHT * self.scale)
        pygame.draw.rect(surface, WHITE, (dest_x + cam_x, dest_y + cam_y, cam_w, cam_h), 1)

        pygame.draw.rect(surface, WHITE, (dest_x, dest_y, mm, mm), 1)
        pygame.draw.rect(surface, GOLDEN, (dest_x - 1, dest_y - 1, mm + 2, mm + 2), 1)

    def update(self, dt: float) -> None:
        self.pulse_timer += dt
