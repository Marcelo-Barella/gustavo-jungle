import pygame
from settings import (
    HP_BAR_WIDTH, HP_BAR_HEIGHT, XP_BAR_WIDTH, XP_BAR_HEIGHT,
    SCREEN_WIDTH, WHITE, BLACK, RED, GOLDEN, LIGHT_GREEN,
)


class HUD:

    def __init__(self):
        self.font = None
        self.small_font = None

    def _ensure_font(self):
        if self.font is None:
            self.font = pygame.font.SysFont(None, 22)
        if self.small_font is None:
            self.small_font = pygame.font.SysFont(None, 18)

    def draw(self, surface, player, wave_spawner=None, powerup_system=None):
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
        xp_text = self.font.render(
            f"Lv{player.level} XP {player.current_xp}/{player.xp_to_next_level}", True, WHITE)
        surface.blit(xp_text, (x + 4, y + 0))

        if wave_spawner is not None:
            y += XP_BAR_HEIGHT + 6
            wave_text = self.font.render(f"Wave {wave_spawner.current_wave_number}", True, WHITE)
            surface.blit(wave_text, (x, y))

        if powerup_system is not None:
            buffs = powerup_system.get_active()
            if buffs:
                bx = SCREEN_WIDTH - 160
                by = 10
                for buff in buffs:
                    label = buff["kind"].replace("_", " ").title()
                    t = int(buff["timer"])
                    txt = self.small_font.render(f"{label} {t}s", True, LIGHT_GREEN)
                    surface.blit(txt, (bx, by))
                    by += 16

        self._draw_skill_cooldowns(surface, player)

    def _draw_skill_cooldowns(self, surface, player):
        if not player.unlocked_skills:
            return
        sx = 10
        sy = surface.get_height() - 30
        for i, skill in enumerate(["vine_whip", "rock_throw", "jungle_roar", "dash"]):
            if skill not in player.unlocked_skills:
                continue
            cd = player.skill_cooldowns.get(skill, 0)
            key_label = str(i + 1)
            if cd > 0:
                color = (120, 120, 120)
                label = f"[{key_label}] {cd:.1f}s"
            else:
                color = GOLDEN
                label = f"[{key_label}] Ready"
            txt = self.small_font.render(label, True, color) if self.small_font else None
            if txt:
                surface.blit(txt, (sx, sy))
                sx += txt.get_width() + 12
