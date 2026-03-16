import math
import time
import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, RED, GOLDEN, LIGHT_GREEN,
    VINE_WHIP, ROCK_THROW, JUNGLE_ROAR, DASH_ATTACK,
    SPEED_BOOST, HEALTH_REGEN, DOUBLE_XP,
)
from assets.asset_generator import AssetGenerator
from entities.enemy import Gorilla

_SKILLS = ["vine_whip", "rock_throw", "jungle_roar", "dash"]
_SKILL_MAX_CD = {
    "vine_whip": VINE_WHIP["cooldown"],
    "rock_throw": ROCK_THROW["cooldown"],
    "jungle_roar": JUNGLE_ROAR["cooldown"],
    "dash": DASH_ATTACK["cooldown"],
}
_BUFF_MAX_DUR = {
    "speed_boost": SPEED_BOOST["duration"],
    "health_regen": HEALTH_REGEN["duration"],
    "double_xp": DOUBLE_XP["duration"],
}
_BUFF_ABBR = {
    "speed_boost": "SPD",
    "health_regen": "RGN",
    "double_xp": "2XP",
}

_DARK_GRAY = (50, 50, 50)
_PANEL_BG = (30, 30, 30, 200)
_HP_W = 250
_HP_H = 24
_XP_H = 16
_SLOT_SZ = 48
_SLOT_GAP = 8
_BUFF_SZ = 24
_ENEMY_BAR_W = 40
_ENEMY_BAR_H = 4
_BOSS_BAR_W = 80
_BOSS_BAR_H = 6
_FADE_SECS = 3.0


class HUD:

    def __init__(self):
        self.font = None
        self.small_font = None
        self.tiny_font = None
        self.kill_count = 0
        self._asset_gen = AssetGenerator()
        self._skill_icons: dict[str, pygame.Surface] = {}
        self._enemy_damage_times: dict[int, float] = {}
        self._enemy_last_hp: dict[int, int] = {}
        self._pulse_time = 0.0
        self._xp_grad: pygame.Surface | None = None

    def _ensure_fonts(self):
        if self.font is None:
            self.font = pygame.font.SysFont(None, 22)
        if self.small_font is None:
            self.small_font = pygame.font.SysFont(None, 18)
        if self.tiny_font is None:
            self.tiny_font = pygame.font.SysFont(None, 14)

    def _ensure_skill_icons(self):
        if not self._skill_icons:
            for skill in _SKILLS:
                raw = self._asset_gen.get_skill_icon(skill)
                self._skill_icons[skill] = pygame.transform.smoothscale(raw, (32, 32))

    def _ensure_xp_gradient(self, w):
        if self._xp_grad is not None and self._xp_grad.get_width() == w:
            return
        self._xp_grad = pygame.Surface((w, _XP_H), pygame.SRCALPHA)
        for px in range(w):
            t = px / max(1, w - 1)
            r = int(180 + 75 * t)
            g = int(150 + 65 * t)
            pygame.draw.line(self._xp_grad, (r, g, 0), (px, 0), (px, _XP_H - 1))

    @staticmethod
    def _hp_color(ratio):
        if ratio > 0.5:
            return (0, 200, 0)
        if ratio > 0.25:
            return (200, 200, 0)
        return (200, 0, 0)

    def _text_shadow(self, surface, font, text, pos, color=WHITE):
        surface.blit(font.render(text, True, BLACK), (pos[0] + 1, pos[1] + 1))
        surface.blit(font.render(text, True, color), pos)

    @staticmethod
    def _draw_heart(surface, x, y, sz=12):
        qs = sz // 4
        hs = sz // 2
        pygame.draw.circle(surface, RED, (x + qs, y + qs), qs)
        pygame.draw.circle(surface, RED, (x + hs + qs, y + qs), qs)
        pygame.draw.polygon(surface, RED, [(x, y + qs), (x + hs, y + sz), (x + sz, y + qs)])

    @staticmethod
    def _draw_star(surface, cx, cy, r=6):
        pts = []
        for i in range(10):
            a = math.radians(i * 36 - 90)
            rad = r if i % 2 == 0 else r * 0.4
            pts.append((int(cx + rad * math.cos(a)), int(cy + rad * math.sin(a))))
        pygame.draw.polygon(surface, GOLDEN, pts)

    @staticmethod
    def _draw_skull(surface, x, y, sz=14):
        cx = x + sz // 2
        cy = y + sz // 2 - 1
        r = sz // 2 - 1
        pygame.draw.circle(surface, WHITE, (cx, cy), r)
        jaw_w = r
        jaw_h = sz // 4
        pygame.draw.rect(surface, WHITE, (cx - jaw_w // 2, cy + r - 1, jaw_w, jaw_h))
        er = max(2, r // 3)
        pygame.draw.circle(surface, BLACK, (cx - er, cy - 1), er)
        pygame.draw.circle(surface, BLACK, (cx + er, cy - 1), er)
        for i in range(3):
            tx = cx - jaw_w // 2 + i * (jaw_w // 2)
            pygame.draw.line(surface, BLACK, (tx, cy + r - 1), (tx, cy + r - 1 + jaw_h), 1)

    @staticmethod
    def _draw_padlock(surface, cx, cy, sz=16):
        bw = sz * 2 // 3
        bh = sz // 2
        by = cy
        pygame.draw.rect(surface, (120, 120, 120), (cx - bw // 2, by, bw, bh))
        sw = bw * 2 // 3
        sh = sz // 3
        arc_rect = pygame.Rect(cx - sw // 2, by - sh, sw, sh * 2)
        pygame.draw.arc(surface, (120, 120, 120), arc_rect, 0, math.pi, 2)

    def draw(self, surface, player, wave_spawner=None, powerup_system=None):
        self._ensure_fonts()
        self._ensure_skill_icons()
        self._pulse_time += 1.0 / 60.0

        x, y = 10, 10
        self._draw_hp_bar(surface, x, y, player)
        y += _HP_H + 4
        self._draw_xp_bar(surface, x, y, player)
        y += _XP_H + 6
        self._draw_wave_counter(surface, x, y, wave_spawner)
        y += 22
        self._draw_kill_counter(surface, x, y)

        if powerup_system is not None:
            self._draw_buffs(surface, powerup_system)

        self._draw_skill_bar(surface, player)

    def _draw_hp_bar(self, surface, x, y, player):
        icon_space = 18
        self._draw_heart(surface, x, y + (_HP_H - 12) // 2, 12)
        bx = x + icon_space
        bw = _HP_W - icon_space

        pygame.draw.rect(surface, _DARK_GRAY, (bx, y, bw, _HP_H))

        ratio = max(0.0, min(1.0, player.hp / player.max_hp))
        fw = int(bw * ratio)
        if fw > 0:
            pygame.draw.rect(surface, self._hp_color(ratio), (bx, y, fw, _HP_H))
            hl = pygame.Surface((fw, 2), pygame.SRCALPHA)
            hl.fill((255, 255, 255, 90))
            surface.blit(hl, (bx, y + 1))

        pygame.draw.rect(surface, BLACK, (bx, y, bw, _HP_H), 2)

        txt = f"HP {player.hp}/{player.max_hp}"
        tw, th = self.font.size(txt)
        tx = bx + (bw - tw) // 2
        ty = y + (_HP_H - th) // 2
        self._text_shadow(surface, self.font, txt, (tx, ty))

    def _draw_xp_bar(self, surface, x, y, player):
        icon_space = 18
        self._draw_star(surface, x + 7, y + _XP_H // 2, 6)
        bx = x + icon_space
        bw = _HP_W - icon_space

        pygame.draw.rect(surface, _DARK_GRAY, (bx, y, bw, _XP_H))

        ratio = min(1.0, player.current_xp / max(1, player.xp_to_next_level))
        fw = int(bw * ratio)
        if fw > 0:
            self._ensure_xp_gradient(bw)
            surface.blit(self._xp_grad, (bx, y), (0, 0, fw, _XP_H))

        pygame.draw.rect(surface, BLACK, (bx, y, bw, _XP_H), 1)

        txt = f"Lv {player.level} - {player.current_xp}/{player.xp_to_next_level} XP"
        tw, th = self.small_font.size(txt)
        tx = bx + (bw - tw) // 2
        ty = y + (_XP_H - th) // 2
        self._text_shadow(surface, self.small_font, txt, (tx, ty))

    def _draw_wave_counter(self, surface, x, y, wave_spawner):
        if wave_spawner is None:
            return
        wn = wave_spawner.current_wave_number
        is_boss = wn > 0 and wn % 5 == 0

        panel = pygame.Surface((140, 20), pygame.SRCALPHA)
        panel.fill(_PANEL_BG)
        surface.blit(panel, (x, y))

        if is_boss:
            pulse = int(128 + 127 * math.sin(self._pulse_time * 6))
            self._text_shadow(surface, self.font, f"Wave {wn}  BOSS!", (x + 4, y + 2), (pulse, 0, 0))
        else:
            self._text_shadow(surface, self.font, f"Wave {wn}", (x + 4, y + 2))

    def _draw_kill_counter(self, surface, x, y):
        self._draw_skull(surface, x, y, 14)
        self._text_shadow(surface, self.small_font, str(self.kill_count), (x + 18, y + 1))

    def _draw_buffs(self, surface, powerup_system):
        buffs = powerup_system.get_active()
        if not buffs:
            return
        bx = SCREEN_WIDTH - 10
        by = 10
        for buff in buffs:
            kind = buff["kind"]
            timer = buff["timer"]
            max_dur = _BUFF_MAX_DUR.get(kind, 15.0)
            ratio = min(1.0, timer / max_dur)

            ix = bx - _BUFF_SZ
            pygame.draw.rect(surface, _DARK_GRAY, (ix, by, _BUFF_SZ, _BUFF_SZ), border_radius=4)

            center = (ix + _BUFF_SZ // 2, by + _BUFF_SZ // 2)
            ar = _BUFF_SZ // 2 - 2
            if ar > 0:
                start = math.pi / 2
                end = start + 2 * math.pi * ratio
                rect = pygame.Rect(center[0] - ar, center[1] - ar, ar * 2, ar * 2)
                pygame.draw.arc(surface, LIGHT_GREEN, rect, start, end, 2)

            abbr = _BUFF_ABBR.get(kind, kind[:3].upper())
            ts = self.tiny_font.render(abbr, True, WHITE)
            surface.blit(ts, (ix + (_BUFF_SZ - ts.get_width()) // 2, by + _BUFF_SZ + 1))

            bx -= _BUFF_SZ + 6

    def _draw_skill_bar(self, surface, player):
        total = 4 * _SLOT_SZ + 3 * _SLOT_GAP
        sx = (SCREEN_WIDTH - total) // 2
        sy = SCREEN_HEIGHT - _SLOT_SZ - 12

        for i, skill in enumerate(_SKILLS):
            slot_x = sx + i * (_SLOT_SZ + _SLOT_GAP)
            unlocked = skill in player.unlocked_skills

            pygame.draw.rect(surface, (20, 20, 20), (slot_x, sy, _SLOT_SZ, _SLOT_SZ))

            if unlocked:
                cd = player.skill_cooldowns.get(skill, 0)
                icon = self._skill_icons.get(skill)
                icx = slot_x + (_SLOT_SZ - 32) // 2
                icy = sy + (_SLOT_SZ - 32) // 2
                if cd > 0:
                    if icon:
                        dim = icon.copy()
                        dim.set_alpha(100)
                        surface.blit(dim, (icx, icy))
                    max_cd = _SKILL_MAX_CD.get(skill, 1.0)
                    sweep_h = int(_SLOT_SZ * min(1.0, cd / max_cd))
                    if sweep_h > 0:
                        ov = pygame.Surface((_SLOT_SZ, sweep_h), pygame.SRCALPHA)
                        ov.fill((0, 0, 0, 150))
                        surface.blit(ov, (slot_x, sy))
                    pygame.draw.rect(surface, (100, 100, 100), (slot_x, sy, _SLOT_SZ, _SLOT_SZ), 2)
                else:
                    if icon:
                        surface.blit(icon, (icx, icy))
                    pygame.draw.rect(surface, GOLDEN, (slot_x, sy, _SLOT_SZ, _SLOT_SZ), 2)
            else:
                self._draw_padlock(surface, slot_x + _SLOT_SZ // 2, sy + _SLOT_SZ // 2, 16)
                pygame.draw.rect(surface, (100, 100, 100), (slot_x, sy, _SLOT_SZ, _SLOT_SZ), 2)

            key_txt = self.tiny_font.render(f"[{i + 1}]", True, WHITE)
            surface.blit(key_txt, (slot_x + 2, sy + 2))

    def draw_enemy_hp_bars(self, surface, enemies, camera_offset):
        self._ensure_fonts()
        now = time.time()
        live_ids = set()

        for enemy in enemies:
            if not enemy.is_alive:
                continue
            eid = id(enemy)
            live_ids.add(eid)

            prev = self._enemy_last_hp.get(eid, enemy.max_hp)
            if enemy.hp < prev:
                self._enemy_damage_times[eid] = now
            self._enemy_last_hp[eid] = enemy.hp

            if enemy.hp >= enemy.max_hp:
                continue
            last_t = self._enemy_damage_times.get(eid)
            if last_t is None:
                continue
            elapsed = now - last_t
            if elapsed > _FADE_SECS:
                continue

            is_boss = isinstance(enemy, Gorilla)
            bw = _BOSS_BAR_W if is_boss else _ENEMY_BAR_W
            bh = _BOSS_BAR_H if is_boss else _ENEMY_BAR_H

            ex = enemy.pos.x - camera_offset[0] - bw / 2
            ey = enemy.pos.y - camera_offset[1] - enemy.image.get_height() / 2 - bh - 4

            alpha = 255
            if elapsed > _FADE_SECS - 1.0:
                alpha = max(0, int(255 * (_FADE_SECS - elapsed)))

            ratio = max(0.0, min(1.0, enemy.hp / enemy.max_hp))
            color = self._hp_color(ratio)

            bar = pygame.Surface((bw, bh), pygame.SRCALPHA)
            bar.fill((0, 0, 0, alpha))
            fw = int(bw * ratio)
            if fw > 0:
                pygame.draw.rect(bar, (*color, alpha), (0, 0, fw, bh))
            surface.blit(bar, (ex, ey))

            if is_boss:
                name = type(enemy).__name__
                ns = self.tiny_font.render(name, True, WHITE)
                ns.set_alpha(alpha)
                surface.blit(ns, (ex + (bw - ns.get_width()) / 2, ey - 12))

        stale = [k for k in self._enemy_last_hp if k not in live_ids]
        for k in stale:
            self._enemy_last_hp.pop(k, None)
            self._enemy_damage_times.pop(k, None)
