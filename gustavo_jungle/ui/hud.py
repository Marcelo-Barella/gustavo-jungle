import math
import pygame
from settings import (
    HP_BAR_WIDTH, HP_BAR_HEIGHT, XP_BAR_WIDTH, XP_BAR_HEIGHT,
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, RED, GOLDEN, LIGHT_GREEN,
    MINIMAP_SIZE, MAP_WIDTH, MAP_HEIGHT, MAP_COLS, MAP_ROWS,
    VINE_WHIP, ROCK_THROW, JUNGLE_ROAR, DASH_ATTACK,
)

SKILL_NAMES = ["vine_whip", "rock_throw", "jungle_roar", "dash"]
SKILL_MAX_CD = {
    "vine_whip": VINE_WHIP["cooldown"],
    "rock_throw": ROCK_THROW["cooldown"],
    "jungle_roar": JUNGLE_ROAR["cooldown"],
    "dash": DASH_ATTACK["cooldown"],
}
COMBO_WINDOW = 3.0
BANNER_DURATION = 2.0

MINIMAP_TILE_COLORS = {
    "grass": (0, 80, 0),
    "tree": (0, 50, 0),
    "water": (64, 164, 223),
    "path": (210, 180, 140),
    "bush": (0, 80, 0),
}


class HUD:

    def __init__(self):
        self.font = None
        self.small_font = None
        self.large_font = None

        self._minimap_bg = None

        self._prev_wave = 0
        self._wave_banner_timer = 0.0
        self._wave_banner_text = ""
        self._wave_banner_is_boss = False

        self._combo_count = 0
        self._combo_timer = 0.0
        self._combo_font = None
        self._combo_font_size = 0

        self._pulse_timer = 0.0

    def _ensure_font(self):
        if self.font is None:
            self.font = pygame.font.SysFont(None, 22)
        if self.small_font is None:
            self.small_font = pygame.font.SysFont(None, 18)
        if self.large_font is None:
            self.large_font = pygame.font.SysFont(None, 64)

    def register_kill(self):
        if self._combo_timer > 0:
            self._combo_count += 1
        else:
            self._combo_count = 1
        self._combo_timer = COMBO_WINDOW

    def draw(self, surface, player, wave_spawner=None, powerup_system=None,
             enemies=None, asset_gen=None, map_manager=None, camera_offset=None, dt=0.0):
        self._ensure_font()
        self._pulse_timer += dt

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
            surface.blit(wave_text, (10, y))

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

        self._draw_minimap(surface, player, enemies, map_manager, camera_offset)
        self._draw_wave_banner(surface, wave_spawner, dt)
        self._draw_skill_bar(surface, player, asset_gen)
        self._draw_combo(surface, dt)

    def _build_minimap_bg(self, map_manager):
        size = MINIMAP_SIZE
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill((20, 20, 20, 180))

        tile_w = size / MAP_COLS
        tile_h = size / MAP_ROWS

        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                tile = map_manager.grid[row][col]
                color = MINIMAP_TILE_COLORS.get(tile, (0, 80, 0))
                px = int(col * tile_w)
                py = int(row * tile_h)
                pw = max(1, int((col + 1) * tile_w) - px)
                ph = max(1, int((row + 1) * tile_h) - py)
                pygame.draw.rect(surf, color, (px, py, pw, ph))

        self._minimap_bg = surf

    def _draw_minimap(self, surface, player, enemies, map_manager, camera_offset):
        if map_manager is None:
            return

        if self._minimap_bg is None:
            self._build_minimap_bg(map_manager)

        size = MINIMAP_SIZE
        minimap = self._minimap_bg.copy()

        scale_x = size / MAP_WIDTH
        scale_y = size / MAP_HEIGHT

        px = int(player.pos.x * scale_x)
        py = int(player.pos.y * scale_y)
        pygame.draw.circle(minimap, (0, 255, 0), (px, py), 3)

        if enemies:
            for enemy in enemies:
                if enemy.is_alive:
                    ex = int(enemy.pos.x * scale_x)
                    ey = int(enemy.pos.y * scale_y)
                    pygame.draw.circle(minimap, (255, 0, 0), (ex, ey), 2)

        if camera_offset:
            vx = int(camera_offset[0] * scale_x)
            vy = int(camera_offset[1] * scale_y)
            vw = max(1, int(SCREEN_WIDTH * scale_x))
            vh = max(1, int(SCREEN_HEIGHT * scale_y))
            pygame.draw.rect(minimap, WHITE, (vx, vy, vw, vh), 1)

        dest_x = SCREEN_WIDTH - size - 10
        dest_y = SCREEN_HEIGHT - size - 10

        pygame.draw.rect(surface, (40, 40, 40), (dest_x - 2, dest_y - 2, size + 4, size + 4))
        surface.blit(minimap, (dest_x, dest_y))
        pygame.draw.rect(surface, (80, 80, 80), (dest_x - 2, dest_y - 2, size + 4, size + 4), 2)

    def _draw_wave_banner(self, surface, wave_spawner, dt):
        if wave_spawner is None:
            return

        current = wave_spawner.current_wave_number
        if current != self._prev_wave and current > 0:
            self._prev_wave = current
            self._wave_banner_timer = BANNER_DURATION
            self._wave_banner_is_boss = (current % 5 == 0)
            if self._wave_banner_is_boss:
                self._wave_banner_text = f"WAVE {current} - BOSS WAVE!"
            else:
                self._wave_banner_text = f"WAVE {current}"

        if self._wave_banner_timer <= 0:
            return

        self._wave_banner_timer -= dt

        if self._wave_banner_timer < 0.5:
            alpha = max(0, int(255 * (self._wave_banner_timer / 0.5)))
        else:
            alpha = 255

        color = (220, 20, 20) if self._wave_banner_is_boss else GOLDEN

        shadow = self.large_font.render(self._wave_banner_text, True, BLACK)
        shadow.set_alpha(alpha)
        text_surf = self.large_font.render(self._wave_banner_text, True, color)
        text_surf.set_alpha(alpha)

        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 3

        surface.blit(shadow, (cx - shadow.get_width() // 2 + 2,
                              cy - shadow.get_height() // 2 + 2))
        surface.blit(text_surf, (cx - text_surf.get_width() // 2,
                                 cy - text_surf.get_height() // 2))

    def _draw_skill_bar(self, surface, player, asset_gen):
        if asset_gen is None:
            return

        box_size = 40
        gap = 8
        total_w = len(SKILL_NAMES) * box_size + (len(SKILL_NAMES) - 1) * gap
        start_x = (SCREEN_WIDTH - total_w) // 2
        start_y = SCREEN_HEIGHT - box_size - 10

        for i, skill in enumerate(SKILL_NAMES):
            bx = start_x + i * (box_size + gap)
            by = start_y

            is_unlocked = skill in player.unlocked_skills
            cd = player.skill_cooldowns.get(skill, 0) if is_unlocked else 0

            icon = asset_gen.get_skill_icon(skill)
            scaled_icon = pygame.transform.scale(icon, (box_size - 8, box_size - 8))

            if not is_unlocked:
                pygame.draw.rect(surface, (40, 40, 40), (bx, by, box_size, box_size))
                gray_icon = scaled_icon.copy()
                gray_overlay = pygame.Surface(gray_icon.get_size(), pygame.SRCALPHA)
                gray_overlay.fill((0, 0, 0, 160))
                gray_icon.blit(gray_overlay, (0, 0))
                surface.blit(gray_icon, (bx + 4, by + 4))
                lock_text = self.small_font.render("X", True, (200, 200, 200))
                surface.blit(lock_text, (bx + box_size // 2 - lock_text.get_width() // 2,
                                         by + box_size // 2 - lock_text.get_height() // 2))
            elif cd > 0:
                pygame.draw.rect(surface, (30, 30, 30), (bx, by, box_size, box_size))
                dark_icon = scaled_icon.copy()
                dark_overlay = pygame.Surface(dark_icon.get_size(), pygame.SRCALPHA)
                dark_overlay.fill((0, 0, 0, 120))
                dark_icon.blit(dark_overlay, (0, 0))
                surface.blit(dark_icon, (bx + 4, by + 4))

                max_cd = SKILL_MAX_CD.get(skill, 1)
                cd_ratio = min(1.0, cd / max_cd)
                sweep_h = int(box_size * cd_ratio)
                if sweep_h > 0:
                    sweep_surf = pygame.Surface((box_size, sweep_h), pygame.SRCALPHA)
                    sweep_surf.fill((0, 0, 0, 140))
                    surface.blit(sweep_surf, (bx, by + box_size - sweep_h))

                cd_text = self.small_font.render(f"{cd:.1f}", True, WHITE)
                surface.blit(cd_text, (bx + box_size // 2 - cd_text.get_width() // 2,
                                       by + box_size // 2 - cd_text.get_height() // 2))
            else:
                pulse = abs(math.sin(self._pulse_timer * 3)) * 30
                bg_val = int(50 + pulse)
                pygame.draw.rect(surface, (bg_val, bg_val, bg_val), (bx, by, box_size, box_size))
                surface.blit(scaled_icon, (bx + 4, by + 4))

            pygame.draw.rect(surface, (180, 180, 180), (bx, by, box_size, box_size), 2)

            key_text = self.small_font.render(str(i + 1), True, WHITE)
            surface.blit(key_text, (bx + 2, by + 2))

    def _draw_combo(self, surface, dt):
        if self._combo_timer > 0:
            self._combo_timer -= dt

        if self._combo_count < 2 or self._combo_timer <= 0:
            if self._combo_timer <= 0:
                self._combo_count = 0
            return

        alpha = 255
        if self._combo_timer < 0.5:
            alpha = max(0, int(255 * (self._combo_timer / 0.5)))

        desired_size = min(48, 28 + self._combo_count * 2)
        if self._combo_font is None or self._combo_font_size != desired_size:
            self._combo_font = pygame.font.SysFont(None, desired_size)
            self._combo_font_size = desired_size

        if self._combo_count >= 10:
            color = (220, 20, 20)
        elif self._combo_count >= 5:
            color = GOLDEN
        else:
            color = WHITE

        text = f"x{self._combo_count} COMBO!"
        rendered = self._combo_font.render(text, True, color)
        rendered.set_alpha(alpha)
        shadow = self._combo_font.render(text, True, BLACK)
        shadow.set_alpha(alpha)

        tx = SCREEN_WIDTH - rendered.get_width() - 20
        ty = SCREEN_HEIGHT // 2

        surface.blit(shadow, (tx + 1, ty + 1))
        surface.blit(rendered, (tx, ty))
