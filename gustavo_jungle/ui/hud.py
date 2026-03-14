import pygame
from settings import (
    HP_BAR_WIDTH, HP_BAR_HEIGHT, XP_BAR_WIDTH, XP_BAR_HEIGHT,
    WHITE, BLACK, RED, GOLDEN, LIGHT_GREEN,
)


class HUD:

    def __init__(self):
        self.font = None

    def _ensure_font(self):
        if self.font is None:
            self.font = pygame.font.SysFont(None, 22)

    def draw(self, surface, player):
        self._ensure_font()

        x, y = 10, 10
        pygame.draw.rect(surface, BLACK, (x, y, HP_BAR_WIDTH, HP_BAR_HEIGHT))
        hp_ratio = max(0, player.hp / player.max_hp)
        pygame.draw.rect(surface, RED, (x, y, int(HP_BAR_WIDTH * hp_ratio), HP_BAR_HEIGHT))
        pygame.draw.rect(surface, WHITE, (x, y, HP_BAR_WIDTH, HP_BAR_HEIGHT), 1)
        hp_text = self.font.render(f"HP {player.hp}/{player.max_hp}", True, WHITE)
        surface.blit(hp_text, (x + 4, y + 2))

        y += HP_BAR_HEIGHT + 4
        pygame.draw.rect(surface, BLACK, (x, y, XP_BAR_WIDTH, XP_BAR_HEIGHT))
        xp_ratio = min(1.0, player.current_xp / max(1, player.xp_to_next_level))
        pygame.draw.rect(surface, GOLDEN, (x, y, int(XP_BAR_WIDTH * xp_ratio), XP_BAR_HEIGHT))
        pygame.draw.rect(surface, WHITE, (x, y, XP_BAR_WIDTH, XP_BAR_HEIGHT), 1)
        xp_text = self.font.render(f"Lv{player.level} XP {player.current_xp}/{player.xp_to_next_level}", True, WHITE)
        surface.blit(xp_text, (x + 4, y + 0))
