import math
import random
import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, STAT_GROWTH_RATE,
    SKILL_UNLOCK_LEVELS, SKILL_NAMES, SKILL_DESCRIPTIONS,
    STAT_UPGRADES, GOLDEN, WHITE, BLACK,
)


CARD_WIDTH = 240
CARD_HEIGHT = 330
CARD_GAP = 40
CARD_Y = 180
FLASH_DURATION = 0.5


class LevelUpScreen:

    def __init__(self):
        self.active = False
        self.choices = []
        self.selected = -1
        self.hovered = -1
        self.state = "choosing"
        self.flash_timer = 0.0
        self.glow_timer = 0.0
        self.player_level = 1
        self.card_rects: list[pygame.Rect] = []
        self.particles: list[dict] = []
        self._title_font = None
        self._level_font = None
        self._card_font = None
        self._desc_font = None
        self._hint_font = None

    def _ensure_fonts(self):
        if self._title_font is None:
            self._title_font = pygame.font.SysFont(None, 64)
            self._level_font = pygame.font.SysFont(None, 36)
            self._card_font = pygame.font.SysFont(None, 28)
            self._desc_font = pygame.font.SysFont(None, 22)
            self._hint_font = pygame.font.SysFont(None, 24)

    def show(self, player):
        self._ensure_fonts()
        self.active = True
        self.choices = self._generate_choices(player)
        self.selected = -1
        self.hovered = -1
        self.state = "choosing"
        self.flash_timer = 0.0
        self.glow_timer = 0.0
        self.player_level = player.level
        self.particles = []
        self._compute_card_rects()

    def _compute_card_rects(self):
        count = len(self.choices)
        total_w = count * CARD_WIDTH + (count - 1) * CARD_GAP
        start_x = (SCREEN_WIDTH - total_w) // 2
        self.card_rects = []
        for i in range(count):
            x = start_x + i * (CARD_WIDTH + CARD_GAP)
            self.card_rects.append(pygame.Rect(x, CARD_Y, CARD_WIDTH, CARD_HEIGHT))

    def _generate_choices(self, player):
        choices = []
        skill_to_unlock = None
        for level in sorted(SKILL_UNLOCK_LEVELS.keys()):
            skill = SKILL_UNLOCK_LEVELS[level]
            if level <= player.level and skill not in player.unlocked_skills:
                skill_to_unlock = skill
                break

        if skill_to_unlock:
            choices.append({
                "type": "skill",
                "key": skill_to_unlock,
                "label": SKILL_NAMES.get(skill_to_unlock, skill_to_unlock.replace("_", " ").title()),
                "description": SKILL_DESCRIPTIONS.get(skill_to_unlock, ""),
                "color": (255, 215, 0),
            })

        stat_keys = list(STAT_UPGRADES.keys())
        random.shuffle(stat_keys)
        mult = 1 + STAT_GROWTH_RATE * (player.level - 1)

        for stat_key in stat_keys:
            if len(choices) >= 3:
                break
            info = STAT_UPGRADES[stat_key]
            base_val = getattr(player, info["attr"])
            amount = info["amount"]
            if stat_key == "speed":
                current_eff = base_val * mult
                new_eff = (base_val + amount) * mult
                current_display = f"{current_eff:.1f}"
                new_display = f"{new_eff:.1f}"
            else:
                current_eff = int(base_val * mult)
                new_eff = int((base_val + amount) * mult)
                current_display = str(current_eff)
                new_display = str(new_eff)

            choices.append({
                "type": "stat",
                "key": stat_key,
                "attr": info["attr"],
                "amount": amount,
                "label": info["label"],
                "current": current_display,
                "new": new_display,
                "description": info["desc"],
                "color": info["color"],
            })

        return choices

    def get_choices(self, player):
        return self._generate_choices(player)

    def handle_event(self, event):
        if not self.active or self.state != "choosing":
            return

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.hovered = -1
            for i, rect in enumerate(self.card_rects):
                if rect.collidepoint(mx, my):
                    self.hovered = i
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for i, rect in enumerate(self.card_rects):
                if rect.collidepoint(mx, my):
                    self._confirm_selection(i)
                    break

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1 and len(self.choices) >= 1:
                self._confirm_selection(0)
            elif event.key == pygame.K_2 and len(self.choices) >= 2:
                self._confirm_selection(1)
            elif event.key == pygame.K_3 and len(self.choices) >= 3:
                self._confirm_selection(2)

    def _confirm_selection(self, index):
        self.selected = index
        self.state = "flash"
        self.flash_timer = FLASH_DURATION
        self._spawn_particles(index)

    def _spawn_particles(self, card_index):
        cx = self.card_rects[card_index].centerx
        cy = self.card_rects[card_index].centery
        color = self.choices[card_index]["color"]
        for _ in range(40):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            self.particles.append({
                "x": float(cx),
                "y": float(cy),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": random.uniform(0.3, 0.7),
                "max_life": random.uniform(0.3, 0.7),
                "color": color,
                "size": random.randint(3, 8),
            })

    def update(self, dt):
        self.glow_timer += dt
        if self.state == "flash":
            self.flash_timer -= dt
        for p in self.particles:
            p["x"] += p["vx"] * dt * 60
            p["y"] += p["vy"] * dt * 60
            p["vy"] += 0.15
            p["life"] -= dt
        self.particles = [p for p in self.particles if p["life"] > 0]

    @property
    def is_done(self):
        return self.state == "flash" and self.flash_timer <= 0

    def apply_choice(self, player, choice_index=None):
        idx = choice_index if choice_index is not None else self.selected
        if idx < 0 or idx >= len(self.choices):
            self.active = False
            return
        choice = self.choices[idx]
        if choice["type"] == "stat":
            current = getattr(player, choice["attr"])
            setattr(player, choice["attr"], current + choice["amount"])
            player._recalc_stats()
        elif choice["type"] == "skill":
            if choice["key"] not in player.unlocked_skills:
                player.unlocked_skills.append(choice["key"])
        self.active = False

    def draw(self, surface):
        if not self.active:
            return
        self._ensure_fonts()

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        self._draw_title(surface)
        self._draw_cards(surface)
        self._draw_particles(surface)
        self._draw_hint(surface)

        if self.state == "flash" and self.flash_timer > FLASH_DURATION * 0.6:
            fade = (self.flash_timer - FLASH_DURATION * 0.6) / (FLASH_DURATION * 0.4)
            alpha = int(180 * fade)
            flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((255, 255, 255, alpha))
            surface.blit(flash_surf, (0, 0))

    def _draw_title(self, surface):
        t = math.sin(self.glow_timer * 3) * 0.5 + 0.5
        r = int(255 * (0.8 + 0.2 * t))
        g = int(215 * (0.7 + 0.3 * t))
        b = int(50 * t)

        glow_scale = 1.0 + 0.05 * math.sin(self.glow_timer * 3)
        glow_size = int(68 * glow_scale)
        glow_font = pygame.font.SysFont(None, glow_size)
        glow_text = glow_font.render("LEVEL UP!", True, (255, 220, 80))
        glow_alpha = int(60 + 40 * math.sin(self.glow_timer * 3))
        glow_text.set_alpha(glow_alpha)
        glow_x = SCREEN_WIDTH // 2 - glow_text.get_width() // 2
        glow_y = 40 - (glow_text.get_height() - self._title_font.get_height()) // 2
        surface.blit(glow_text, (glow_x, glow_y))

        title = self._title_font.render("LEVEL UP!", True, (r, g, b))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

        level_text = self._level_font.render(f"Level {self.player_level}", True, WHITE)
        surface.blit(level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2, 110))

    def _draw_cards(self, surface):
        for i, choice in enumerate(self.choices):
            rect = self.card_rects[i]
            is_hovered = (i == self.hovered and self.state == "choosing")
            is_selected = (i == self.selected)
            self._draw_single_card(surface, rect, choice, i, is_hovered, is_selected)

    def _draw_single_card(self, surface, rect, choice, index, is_hovered, is_selected):
        card_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        card_surf.fill((20, 20, 30, 220))

        border_color = choice["color"]
        border_width = 3
        if is_selected:
            border_color = GOLDEN
            border_width = 4
        elif is_hovered:
            border_width = 3
            glow_surf = pygame.Surface((rect.width + 12, rect.height + 12), pygame.SRCALPHA)
            glow_alpha = int(40 + 20 * math.sin(self.glow_timer * 4))
            glow_surf.fill((*border_color[:3], glow_alpha))
            surface.blit(glow_surf, (rect.x - 6, rect.y - 6))

        pygame.draw.rect(card_surf, border_color, (0, 0, rect.width, rect.height), border_width, border_radius=8)

        self._draw_icon(card_surf, choice, rect.width)

        key_label = self._card_font.render(f"[{index + 1}]", True, (180, 180, 180))
        card_surf.blit(key_label, (rect.width // 2 - key_label.get_width() // 2, 10))

        label_text = self._card_font.render(choice["label"], True, WHITE)
        card_surf.blit(label_text, (rect.width // 2 - label_text.get_width() // 2, 130))

        if choice["type"] == "stat":
            val_str = f"{choice['current']} -> {choice['new']}"
            val_text = self._card_font.render(val_str, True, choice["color"])
            card_surf.blit(val_text, (rect.width // 2 - val_text.get_width() // 2, 165))

            amount = choice["amount"]
            if isinstance(amount, float):
                bonus_str = f"+{amount:.1f}"
            else:
                bonus_str = f"+{amount}"
            bonus_text = self._desc_font.render(bonus_str, True, (180, 255, 180))
            card_surf.blit(bonus_text, (rect.width // 2 - bonus_text.get_width() // 2, 200))
        else:
            skill_label = self._card_font.render("NEW SKILL!", True, GOLDEN)
            card_surf.blit(skill_label, (rect.width // 2 - skill_label.get_width() // 2, 165))

        desc = choice.get("description", "")
        self._draw_wrapped_text(card_surf, desc, rect.width // 2, 235, rect.width - 24)

        surface.blit(card_surf, (rect.x, rect.y))

    def _draw_icon(self, card_surf, choice, card_width):
        cx = card_width // 2
        cy = 80
        color = choice["color"]
        icon_key = choice.get("key", "")

        if choice["type"] == "skill":
            pygame.draw.circle(card_surf, (*color, 60), (cx, cy), 32)
            pygame.draw.circle(card_surf, color, (cx, cy), 32, 3)
            star_points = []
            for k in range(10):
                angle = -math.pi / 2 + k * math.pi / 5
                r = 20 if k % 2 == 0 else 10
                star_points.append((cx + int(math.cos(angle) * r), cy + int(math.sin(angle) * r)))
            pygame.draw.polygon(card_surf, color, star_points)
        elif icon_key == "hp":
            pygame.draw.circle(card_surf, (*color, 60), (cx, cy), 28)
            pygame.draw.rect(card_surf, color, (cx - 4, cy - 16, 8, 32))
            pygame.draw.rect(card_surf, color, (cx - 16, cy - 4, 32, 8))
        elif icon_key == "attack":
            pygame.draw.circle(card_surf, (*color, 60), (cx, cy), 28)
            pts = [(cx, cy - 20), (cx + 14, cy + 14), (cx - 14, cy + 14)]
            pygame.draw.polygon(card_surf, color, pts)
        elif icon_key == "defense":
            pygame.draw.circle(card_surf, (*color, 60), (cx, cy), 28)
            shield = [(cx, cy - 22), (cx + 18, cy - 10), (cx + 14, cy + 12), (cx, cy + 22), (cx - 14, cy + 12), (cx - 18, cy - 10)]
            pygame.draw.polygon(card_surf, color, shield, 3)
        elif icon_key == "speed":
            pygame.draw.circle(card_surf, (*color, 60), (cx, cy), 28)
            bolt = [(cx - 4, cy - 20), (cx + 10, cy - 4), (cx + 2, cy - 4), (cx + 4, cy + 20), (cx - 10, cy + 4), (cx - 2, cy + 4)]
            pygame.draw.polygon(card_surf, color, bolt)
        elif icon_key == "luck":
            pygame.draw.circle(card_surf, (*color, 60), (cx, cy), 28)
            star_points = []
            for k in range(10):
                angle = -math.pi / 2 + k * math.pi / 5
                r = 18 if k % 2 == 0 else 8
                star_points.append((cx + int(math.cos(angle) * r), cy + int(math.sin(angle) * r)))
            pygame.draw.polygon(card_surf, color, star_points)

    def _draw_wrapped_text(self, surf, text, cx, y, max_width):
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            tw = self._desc_font.size(test)[0]
            if tw > max_width and current:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)

        for line in lines:
            rendered = self._desc_font.render(line, True, (200, 200, 200))
            surf.blit(rendered, (cx - rendered.get_width() // 2, y))
            y += rendered.get_height() + 2

    def _draw_particles(self, surface):
        for p in self.particles:
            alpha = max(0, int(255 * (p["life"] / p["max_life"])))
            size = max(1, int(p["size"] * (p["life"] / p["max_life"])))
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p["color"][:3], alpha), (size, size), size)
            surface.blit(s, (int(p["x"]) - size, int(p["y"]) - size))

    def _draw_hint(self, surface):
        if self.state != "choosing":
            return
        hint = self._hint_font.render("Click a card or press 1 / 2 / 3 to choose", True, (160, 160, 160))
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 60))
