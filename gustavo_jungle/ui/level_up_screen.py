import pygame
import random
import math

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    GOLDEN, BLACK, WHITE, RED, RIVER_BLUE, JUNGLE_GREEN, DARK_GREEN, LIGHT_GREEN,
)

CARD_W = 200
CARD_H = 280
CARD_GAP = 30
ICON_SIZE = 60
BTN_W = 140
BTN_H = 36

STAT_UPGRADES = [
    {
        "name": "+10 Max HP",
        "desc": "Increase maximum\nHP by 10",
        "color": RED,
        "type": "stat",
        "apply": lambda p: _apply_stat(p, "_base_hp", 10),
    },
    {
        "name": "+3 Attack",
        "desc": "Increase base\nattack by 3",
        "color": RED,
        "type": "stat",
        "apply": lambda p: _apply_stat(p, "_base_attack", 3),
    },
    {
        "name": "+2 Defense",
        "desc": "Increase base\ndefense by 2",
        "color": RED,
        "type": "stat",
        "apply": lambda p: _apply_stat(p, "_base_defense", 2),
    },
    {
        "name": "+0.3 Speed",
        "desc": "Increase base\nspeed by 0.3",
        "color": RIVER_BLUE,
        "type": "stat",
        "apply": lambda p: _apply_stat(p, "_base_speed", 0.3),
    },
    {
        "name": "+3 Luck",
        "desc": "Increase base\nluck by 3",
        "color": GOLDEN,
        "type": "stat",
        "apply": lambda p: _apply_stat(p, "_base_luck", 3),
    },
]

SKILL_UNLOCKS = [
    {"name": "Unlock Vine Whip", "skill": "vine_whip", "desc": "Unlock the Vine\nWhip skill", "color": JUNGLE_GREEN, "type": "skill"},
    {"name": "Unlock Rock Throw", "skill": "rock_throw", "desc": "Unlock the Rock\nThrow skill", "color": JUNGLE_GREEN, "type": "skill"},
    {"name": "Unlock Jungle Roar", "skill": "jungle_roar", "desc": "Unlock the Jungle\nRoar skill", "color": JUNGLE_GREEN, "type": "skill"},
    {"name": "Unlock Dash", "skill": "dash", "desc": "Unlock the\nDash skill", "color": JUNGLE_GREEN, "type": "skill"},
]

SKILL_ENHANCEMENTS = [
    {"name": "Vine Whip +20% Damage", "skill": "vine_whip", "key": "vine_whip_damage", "mult": 0.20, "desc": "Vine Whip deals\n20% more damage", "color": LIGHT_GREEN, "type": "enhance"},
    {"name": "Rock Throw +25% Damage", "skill": "rock_throw", "key": "rock_throw_damage", "mult": 0.25, "desc": "Rock Throw deals\n25% more damage", "color": LIGHT_GREEN, "type": "enhance"},
    {"name": "Jungle Roar +30% Radius", "skill": "jungle_roar", "key": "jungle_roar_radius", "mult": 0.30, "desc": "Jungle Roar radius\nincreased by 30%", "color": LIGHT_GREEN, "type": "enhance"},
    {"name": "Dash +50 Distance", "skill": "dash", "key": "dash_distance", "mult": 50, "desc": "Dash distance\nincreased by 50", "color": LIGHT_GREEN, "type": "enhance"},
]

SPECIALS = [
    {
        "name": "Full Heal",
        "desc": "Restore HP\nto maximum",
        "color": GOLDEN,
        "type": "special",
        "apply": lambda p: _apply_full_heal(p),
    },
    {
        "name": "+25% Max HP",
        "desc": "Increase maximum\nHP by 25%",
        "color": GOLDEN,
        "type": "special",
        "apply": lambda p: _apply_percent_hp(p),
    },
    {
        "name": "Critical Strike\nChance +5%",
        "desc": "Gain +5% critical\nstrike chance",
        "color": GOLDEN,
        "type": "special",
        "apply": lambda p: _apply_crit(p),
    },
]


def _apply_stat(player, attr, amount):
    setattr(player, attr, getattr(player, attr) + amount)
    player._recalc_stats()


def _apply_full_heal(player):
    player.hp = player.max_hp


def _apply_percent_hp(player):
    player._base_hp = int(player._base_hp * 1.25)
    player._recalc_stats()


def _apply_crit(player):
    if not hasattr(player, "skill_enhancements"):
        player.skill_enhancements = {}
    player.skill_enhancements["crit_chance"] = player.skill_enhancements.get("crit_chance", 0) + 0.05


def _apply_skill_unlock(player, skill):
    if skill not in player.unlocked_skills:
        player.unlocked_skills.append(skill)


def _apply_skill_enhancement(player, key, mult):
    if not hasattr(player, "skill_enhancements"):
        player.skill_enhancements = {}
    player.skill_enhancements[key] = player.skill_enhancements.get(key, 0) + mult


class LevelUpScreen:

    def __init__(self):
        self.active = False
        self._callback = None
        self._choices = []
        self._player = None
        self._card_rects: list[pygame.Rect] = []
        self._btn_rects: list[pygame.Rect] = []
        self._hover_index = -1
        self._pulse_timer = 0.0
        self._title_font = pygame.font.SysFont(None, 56)
        self._name_font = pygame.font.SysFont(None, 26)
        self._desc_font = pygame.font.SysFont(None, 20)
        self._btn_font = pygame.font.SysFont(None, 24)
        self._level_font = pygame.font.SysFont(None, 32)

    def _build_pool(self, player):
        pool = list(STAT_UPGRADES)
        for su in SKILL_UNLOCKS:
            if su["skill"] not in player.unlocked_skills:
                pool.append(su)
        for se in SKILL_ENHANCEMENTS:
            if se["skill"] in player.unlocked_skills:
                pool.append(se)
        pool.extend(SPECIALS)
        return pool

    def show(self, player, on_choose_callback):
        pool = self._build_pool(player)
        self._choices = random.sample(pool, min(3, len(pool)))
        self._callback = on_choose_callback
        self._player = player
        self._hover_index = -1
        self._pulse_timer = 0.0
        self.active = True
        self._layout_cards()

    def _layout_cards(self):
        total_w = len(self._choices) * CARD_W + (len(self._choices) - 1) * CARD_GAP
        start_x = (SCREEN_WIDTH - total_w) // 2
        start_y = (SCREEN_HEIGHT - CARD_H) // 2 + 20
        self._card_rects = []
        self._btn_rects = []
        for i in range(len(self._choices)):
            x = start_x + i * (CARD_W + CARD_GAP)
            self._card_rects.append(pygame.Rect(x, start_y, CARD_W, CARD_H))
            bx = x + (CARD_W - BTN_W) // 2
            by = start_y + CARD_H - BTN_H - 14
            self._btn_rects.append(pygame.Rect(bx, by, BTN_W, BTN_H))

    def handle_event(self, event):
        if not self.active:
            return False
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self._hover_index = -1
            for i, r in enumerate(self._card_rects):
                if r.collidepoint(mx, my):
                    self._hover_index = i
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for i, r in enumerate(self._btn_rects):
                if r.collidepoint(mx, my):
                    self._select(i)
                    return True
            for i, r in enumerate(self._card_rects):
                if r.collidepoint(mx, my):
                    self._select(i)
                    return True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1 and len(self._choices) >= 1:
                self._select(0)
                return True
            elif event.key == pygame.K_2 and len(self._choices) >= 2:
                self._select(1)
                return True
            elif event.key == pygame.K_3 and len(self._choices) >= 3:
                self._select(2)
                return True
        return True

    def _select(self, index):
        choice = self._choices[index]
        self.apply_choice(self._player, choice)
        self.active = False
        if self._callback:
            self._callback(choice)

    def apply_choice(self, player, choice):
        ctype = choice["type"]
        if ctype == "stat" or ctype == "special":
            choice["apply"](player)
        elif ctype == "skill":
            _apply_skill_unlock(player, choice["skill"])
        elif ctype == "enhance":
            _apply_skill_enhancement(player, choice["key"], choice["mult"])

    def update(self, dt):
        if not self.active:
            return
        self._pulse_timer += dt

    def draw(self, surface):
        if not self.active:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        pulse = math.sin(self._pulse_timer * 4.0) * 4.0
        title_text = self._title_font.render("LEVEL UP!", True, GOLDEN)
        tx = SCREEN_WIDTH // 2 - title_text.get_width() // 2
        ty = 60 + int(pulse)
        surface.blit(title_text, (tx, ty))

        level_text = self._level_font.render(f"Level {self._player.level}", True, WHITE)
        lx = SCREEN_WIDTH // 2 - level_text.get_width() // 2
        surface.blit(level_text, (lx, ty + title_text.get_height() + 4))

        for i, choice in enumerate(self._choices):
            self._draw_card(surface, i, choice)

    def _draw_card(self, surface, index, choice):
        rect = self._card_rects[index]
        is_hover = index == self._hover_index
        y_off = -5 if is_hover else 0
        card_rect = pygame.Rect(rect.x, rect.y + y_off, rect.w, rect.h)

        if is_hover:
            glow = pygame.Surface((card_rect.w + 8, card_rect.h + 8), pygame.SRCALPHA)
            glow.fill((255, 215, 0, 60))
            surface.blit(glow, (card_rect.x - 4, card_rect.y - 4))

        card_surf = pygame.Surface((card_rect.w, card_rect.h), pygame.SRCALPHA)
        card_surf.fill((20, 20, 30, 220))
        surface.blit(card_surf, card_rect.topleft)

        border_color = (255, 230, 100) if is_hover else GOLDEN
        pygame.draw.rect(surface, border_color, card_rect, 2, border_radius=6)

        icon_x = card_rect.x + (CARD_W - ICON_SIZE) // 2
        icon_y = card_rect.y + 18
        pygame.draw.rect(surface, choice["color"], (icon_x, icon_y, ICON_SIZE, ICON_SIZE), border_radius=8)

        name_y = icon_y + ICON_SIZE + 14
        for line in choice["name"].split("\n"):
            name_surf = self._name_font.render(line, True, WHITE)
            nx = card_rect.x + (CARD_W - name_surf.get_width()) // 2
            surface.blit(name_surf, (nx, name_y))
            name_y += name_surf.get_height() + 2

        desc_y = name_y + 10
        for line in choice["desc"].split("\n"):
            desc_surf = self._desc_font.render(line, True, (200, 200, 200))
            dx = card_rect.x + (CARD_W - desc_surf.get_width()) // 2
            surface.blit(desc_surf, (dx, desc_y))
            desc_y += desc_surf.get_height() + 2

        btn_rect = self._btn_rects[index]
        btn_adjusted = pygame.Rect(btn_rect.x, btn_rect.y + y_off, btn_rect.w, btn_rect.h)
        btn_color = (80, 60, 10) if is_hover else (50, 40, 10)
        pygame.draw.rect(surface, btn_color, btn_adjusted, border_radius=4)
        pygame.draw.rect(surface, GOLDEN, btn_adjusted, 2, border_radius=4)
        btn_text = self._btn_font.render("Choose", True, GOLDEN)
        bx = btn_adjusted.x + (BTN_W - btn_text.get_width()) // 2
        by = btn_adjusted.y + (BTN_H - btn_text.get_height()) // 2
        surface.blit(btn_text, (bx, by))
