import math
import random
import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    JUNGLE_GREEN, DARK_GREEN, GOLDEN, WHITE, BLACK, RED, LIGHT_GREEN,
)


class MenuButton:

    def __init__(self, text, x, y, width, height, font, color=WHITE, hover_color=GOLDEN):
        self.text = text
        self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.is_selected = False

    def draw(self, surface):
        color = self.hover_color if (self.is_hovered or self.is_selected) else self.color
        if self.is_hovered or self.is_selected:
            border_rect = self.rect.inflate(4, 4)
            pygame.draw.rect(surface, GOLDEN, border_rect, 2, border_radius=6)
        bg_alpha = 80 if (self.is_hovered or self.is_selected) else 40
        bg = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        bg.fill((255, 255, 255, bg_alpha))
        surface.blit(bg, self.rect.topleft)
        txt = self.font.render(self.text, True, color)
        tx = self.rect.centerx - txt.get_width() // 2
        ty = self.rect.centery - txt.get_height() // 2
        surface.blit(txt, (tx, ty))

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered


class MainMenu:

    def __init__(self):
        self.title_font = pygame.font.SysFont(None, 72)
        self.subtitle_font = pygame.font.SysFont(None, 32)
        self.button_font = pygame.font.SysFont(None, 42)
        self.time = 0.0
        self.selected_index = 0
        self.buttons = [
            MenuButton("New Game", SCREEN_WIDTH // 2, 420, 260, 50, self.button_font),
            MenuButton("Settings", SCREEN_WIDTH // 2, 490, 260, 50, self.button_font),
            MenuButton("Quit", SCREEN_WIDTH // 2, 560, 260, 50, self.button_font),
        ]
        self.actions = ["new_game", "settings", "quit"]
        self.buttons[self.selected_index].is_selected = True
        self._vines = self._generate_vines()
        self._leaves = self._generate_leaves()

    def _generate_vines(self):
        vines = []
        for _ in range(12):
            x = random.randint(0, SCREEN_WIDTH)
            length = random.randint(150, 500)
            width = random.randint(2, 5)
            sway = random.uniform(0.3, 1.2)
            phase = random.uniform(0, math.pi * 2)
            vines.append((x, length, width, sway, phase))
        return vines

    def _generate_leaves(self):
        leaves = []
        for _ in range(30):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            size = random.randint(6, 18)
            speed = random.uniform(0.2, 0.8)
            phase = random.uniform(0, math.pi * 2)
            shade = (
                random.randint(20, 60),
                random.randint(100, 180),
                random.randint(20, 60),
            )
            leaves.append((x, y, size, speed, phase, shade))
        return leaves

    def _draw_background(self, surface):
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(0 * (1 - t) + 0 * t)
            g = int(40 * (1 - t) + 0 * t)
            b = int(20 * (1 - t) + 0 * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        for x, length, width, sway, phase in self._vines:
            points = []
            for i in range(0, length, 4):
                ox = x + math.sin(i * 0.02 + self.time * sway + phase) * 15
                points.append((ox, i))
            if len(points) > 1:
                pygame.draw.lines(surface, DARK_GREEN, False, points, width)

        for lx, ly, size, speed, phase, shade in self._leaves:
            ox = lx + math.sin(self.time * speed + phase) * 10
            oy = ly + math.cos(self.time * speed * 0.7 + phase) * 5
            points = [
                (ox, oy - size),
                (ox + size * 0.6, oy),
                (ox, oy + size * 0.3),
                (ox - size * 0.6, oy),
            ]
            pygame.draw.polygon(surface, shade, points)

    def draw(self, surface):
        self.time += 1 / 60.0
        self._draw_background(surface)

        pulse = 0.5 + 0.5 * math.sin(self.time * 2)
        title_color = (
            int(34 + pulse * 30),
            int(139 + pulse * 40),
            int(34 + pulse * 30),
        )
        title = self.title_font.render("GUSTAVO IN THE JUNGLE", True, title_color)
        shadow = self.title_font.render("GUSTAVO IN THE JUNGLE", True, (0, 0, 0))
        tx = SCREEN_WIDTH // 2 - title.get_width() // 2
        ty = 180
        surface.blit(shadow, (tx + 3, ty + 3))
        surface.blit(title, (tx, ty))

        sub_pulse = 0.6 + 0.4 * math.sin(self.time * 3)
        sub_color = (
            int(200 * sub_pulse),
            int(215 * sub_pulse),
            int(100 * sub_pulse),
        )
        subtitle = self.subtitle_font.render("A Top-Down Jungle Adventure", True, sub_color)
        sx = SCREEN_WIDTH // 2 - subtitle.get_width() // 2
        surface.blit(subtitle, (sx, ty + 70))

        mouse_pos = pygame.mouse.get_pos()
        any_hovered = False
        for i, btn in enumerate(self.buttons):
            if btn.check_hover(mouse_pos):
                if not btn.is_selected:
                    self._select(i)
                any_hovered = True
            btn.draw(surface)

    def _select(self, index):
        self.buttons[self.selected_index].is_selected = False
        self.selected_index = index
        self.buttons[self.selected_index].is_selected = True

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self._select((self.selected_index - 1) % len(self.buttons))
                return None
            elif event.key == pygame.K_DOWN:
                self._select((self.selected_index + 1) % len(self.buttons))
                return None
            elif event.key == pygame.K_RETURN:
                return self.actions[self.selected_index]
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.buttons):
                if btn.rect.collidepoint(event.pos):
                    return self.actions[i]
        return None


class PauseMenu:

    def __init__(self):
        self.title_font = pygame.font.SysFont(None, 64)
        self.button_font = pygame.font.SysFont(None, 38)
        self.selected_index = 0
        self.buttons = [
            MenuButton("Resume", SCREEN_WIDTH // 2, 360, 260, 50, self.button_font),
            MenuButton("Restart", SCREEN_WIDTH // 2, 430, 260, 50, self.button_font),
            MenuButton("Quit to Menu", SCREEN_WIDTH // 2, 500, 260, 50, self.button_font),
        ]
        self.actions = ["resume", "restart", "quit_to_menu"]
        self.buttons[self.selected_index].is_selected = True
        self.overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 150))

    def draw(self, surface):
        surface.blit(self.overlay, (0, 0))
        title = self.title_font.render("PAUSED", True, WHITE)
        tx = SCREEN_WIDTH // 2 - title.get_width() // 2
        surface.blit(title, (tx, 240))

        mouse_pos = pygame.mouse.get_pos()
        for i, btn in enumerate(self.buttons):
            if btn.check_hover(mouse_pos):
                if not btn.is_selected:
                    self._select(i)
            btn.draw(surface)

    def _select(self, index):
        self.buttons[self.selected_index].is_selected = False
        self.selected_index = index
        self.buttons[self.selected_index].is_selected = True

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "resume"
            elif event.key == pygame.K_UP:
                self._select((self.selected_index - 1) % len(self.buttons))
                return None
            elif event.key == pygame.K_DOWN:
                self._select((self.selected_index + 1) % len(self.buttons))
                return None
            elif event.key == pygame.K_RETURN:
                return self.actions[self.selected_index]
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.buttons):
                if btn.rect.collidepoint(event.pos):
                    return self.actions[i]
        return None


class GameOverScreen:

    def __init__(self):
        self.title_font = pygame.font.SysFont(None, 72)
        self.stats_font = pygame.font.SysFont(None, 30)
        self.button_font = pygame.font.SysFont(None, 38)
        self.selected_index = 0
        self.buttons = [
            MenuButton("Try Again", SCREEN_WIDTH // 2, 560, 260, 50, self.button_font),
            MenuButton("Main Menu", SCREEN_WIDTH // 2, 630, 260, 50, self.button_font),
        ]
        self.actions = ["try_again", "main_menu"]
        self.buttons[self.selected_index].is_selected = True
        self.time = 0.0
        self.fade_alpha = 0
        self.overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    def reset(self):
        self.time = 0.0
        self.fade_alpha = 0
        self.selected_index = 0
        for btn in self.buttons:
            btn.is_selected = False
        self.buttons[0].is_selected = True

    def draw(self, surface, stats):
        self.time += 1 / 60.0

        self.fade_alpha = min(180, self.fade_alpha + 4)
        self.overlay.fill((0, 0, 0, self.fade_alpha))
        surface.blit(self.overlay, (0, 0))

        pulse = 0.6 + 0.4 * math.sin(self.time * 4)
        glow_r = int(220 * pulse)
        glow_color = (glow_r, 20, 20)

        shadow = self.title_font.render("GAME OVER", True, (80, 0, 0))
        title = self.title_font.render("GAME OVER", True, glow_color)
        tx = SCREEN_WIDTH // 2 - title.get_width() // 2
        ty = 180
        for dx in (-2, 0, 2):
            for dy in (-2, 0, 2):
                if dx != 0 or dy != 0:
                    surface.blit(shadow, (tx + dx, ty + dy))
        surface.blit(title, (tx, ty))

        level = stats.get("level", 1)
        enemies_killed = stats.get("enemies_killed", 0)
        wave = stats.get("wave", 1)
        time_survived = stats.get("time_survived", 0)
        xp_earned = stats.get("xp_earned", 0)

        minutes = int(time_survived) // 60
        seconds = int(time_survived) % 60
        time_str = f"{minutes}:{seconds:02d}"

        stat_lines = [
            f"Level Reached: {level}",
            f"Enemies Killed: {enemies_killed}",
            f"Waves Survived: {wave}",
            f"Time Survived: {time_str}",
            f"Total XP Earned: {xp_earned}",
        ]
        sy = 290
        for line in stat_lines:
            txt = self.stats_font.render(line, True, WHITE)
            surface.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, sy))
            sy += 38

        mouse_pos = pygame.mouse.get_pos()
        for i, btn in enumerate(self.buttons):
            if btn.check_hover(mouse_pos):
                if not btn.is_selected:
                    self._select(i)
            btn.draw(surface)

    def _select(self, index):
        self.buttons[self.selected_index].is_selected = False
        self.selected_index = index
        self.buttons[self.selected_index].is_selected = True

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self._select((self.selected_index - 1) % len(self.buttons))
                return None
            elif event.key == pygame.K_DOWN:
                self._select((self.selected_index + 1) % len(self.buttons))
                return None
            elif event.key == pygame.K_RETURN:
                return self.actions[self.selected_index]
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.buttons):
                if btn.rect.collidepoint(event.pos):
                    return self.actions[i]
        return None
