import math
import random
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, GOLDEN, DARK_GREEN, RED, LIGHT_GREEN
from assets.asset_generator import AssetGenerator


class Button:

    def __init__(self, x, y, width, height, text, font_size=32):
        self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        self.text = text
        self.font = pygame.font.SysFont(None, font_size)
        self.base_color = (0, 100, 0)
        self.hover_color = (0, 140, 0)
        self.click_color = (0, 70, 0)
        self.text_color = WHITE
        self.hovered = False
        self.pressed = False
        self.scale = 1.0
        self.target_scale = 1.0

    def update(self, dt):
        mx, my = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mx, my)
        self.target_scale = 1.05 if self.hovered else 1.0
        self.scale += (self.target_scale - self.scale) * min(dt * 12, 1.0)

    def draw(self, surface):
        w = int(self.rect.width * self.scale)
        h = int(self.rect.height * self.scale)
        draw_rect = pygame.Rect(0, 0, w, h)
        draw_rect.center = self.rect.center

        if self.pressed:
            color = self.click_color
        elif self.hovered:
            color = self.hover_color
        else:
            color = self.base_color

        btn_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(btn_surf, color, (0, 0, w, h), border_radius=10)
        pygame.draw.rect(btn_surf, (0, 180, 0), (0, 0, w, h), 2, border_radius=10)

        txt = self.font.render(self.text, True, self.text_color)
        txt_rect = txt.get_rect(center=(w // 2, h // 2))
        btn_surf.blit(txt, txt_rect)
        surface.blit(btn_surf, draw_rect.topleft)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_pressed = self.pressed
            self.pressed = False
            if was_pressed and self.rect.collidepoint(event.pos):
                return True
        return False


class _Leaf:

    def __init__(self):
        self.x = random.uniform(0, SCREEN_WIDTH)
        self.y = random.uniform(-SCREEN_HEIGHT, SCREEN_HEIGHT)
        self.vx = random.uniform(-15, -5)
        self.vy = random.uniform(10, 30)
        self.size = random.randint(3, 7)
        self.angle = random.uniform(0, math.pi * 2)
        self.spin = random.uniform(-2, 2)
        g = random.randint(80, 160)
        self.color = (0, g, 0)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle += self.spin * dt
        if self.y > SCREEN_HEIGHT + 10 or self.x < -20:
            self.x = random.uniform(0, SCREEN_WIDTH + 40)
            self.y = random.uniform(-40, -10)

    def draw(self, surface):
        s = self.size
        pts = [
            (self.x + math.cos(self.angle) * s, self.y + math.sin(self.angle) * s),
            (self.x + math.cos(self.angle + 1.2) * s * 0.5, self.y + math.sin(self.angle + 1.2) * s * 0.5),
            (self.x + math.cos(self.angle + math.pi) * s, self.y + math.sin(self.angle + math.pi) * s),
            (self.x + math.cos(self.angle - 1.2) * s * 0.5, self.y + math.sin(self.angle - 1.2) * s * 0.5),
        ]
        pygame.draw.polygon(surface, self.color, pts)


class MainMenu:

    def __init__(self):
        self.title_font = pygame.font.SysFont(None, 72)
        self.leaves = [_Leaf() for _ in range(50)]
        self.parallax_offset = 0.0

        cx = SCREEN_WIDTH // 2
        btn_w, btn_h = 240, 50
        base_y = SCREEN_HEIGHT // 2 - 10
        self.buttons = {
            "start": Button(cx, base_y, btn_w, btn_h, "Start Game"),
            "settings": Button(cx, base_y + 70, btn_w, btn_h, "Settings"),
            "quit": Button(cx, base_y + 140, btn_w, btn_h, "Quit"),
        }

        self.asset_gen = AssetGenerator()
        sprites = self.asset_gen.get_player_sprites()
        self.gustavo_frames = sprites["idle"]
        self.gustavo_frame_idx = 0
        self.gustavo_timer = 0.0
        self.time = 0.0

    def update(self, dt):
        self.time += dt
        self.parallax_offset += dt * 8
        for leaf in self.leaves:
            leaf.update(dt)
        for btn in self.buttons.values():
            btn.update(dt)
        self.gustavo_timer += dt
        if self.gustavo_timer >= 0.5:
            self.gustavo_timer -= 0.5
            self.gustavo_frame_idx = (self.gustavo_frame_idx + 1) % len(self.gustavo_frames)

    def _draw_background(self, surface):
        surface.fill((0, 40, 0))

        for i in range(3):
            speed = (i + 1) * 0.3
            offset = self.parallax_offset * speed
            alpha = 20 + i * 15
            layer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            for j in range(6):
                x = ((j * 200 + int(offset)) % (SCREEN_WIDTH + 200)) - 100
                y = SCREEN_HEIGHT - 80 - i * 60
                g = 30 + i * 20
                pygame.draw.ellipse(layer, (0, g, 0, alpha), (x, y, 180, 120))
            surface.blit(layer, (0, 0))

    def _draw_vine_border(self, surface):
        c = (0, 90, 0)
        t = self.time
        for i in range(0, SCREEN_WIDTH, 12):
            y_off = int(math.sin(i * 0.05 + t) * 6)
            pygame.draw.circle(surface, c, (i, 8 + y_off), 5)
            pygame.draw.circle(surface, c, (i, SCREEN_HEIGHT - 8 - y_off), 5)
        for i in range(0, SCREEN_HEIGHT, 12):
            x_off = int(math.sin(i * 0.05 + t * 0.8) * 6)
            pygame.draw.circle(surface, c, (8 + x_off, i), 5)
            pygame.draw.circle(surface, c, (SCREEN_WIDTH - 8 - x_off, i), 5)

        leaf_c = (0, 120, 0)
        for i in range(0, SCREEN_WIDTH, 60):
            y_off = int(math.sin(i * 0.05 + t) * 6)
            pygame.draw.polygon(surface, leaf_c, [
                (i, 8 + y_off),
                (i - 8, 18 + y_off),
                (i + 8, 18 + y_off),
            ])

    def _draw_title(self, surface):
        text = "GUSTAVO IN THE JUNGLE"
        outline_color = (60, 30, 0)
        title_color = (255, 215, 0)
        rendered = self.title_font.render(text, True, title_color)
        outline = self.title_font.render(text, True, outline_color)
        cx = SCREEN_WIDTH // 2 - rendered.get_width() // 2
        cy = 100
        for dx in (-2, 0, 2):
            for dy in (-2, 0, 2):
                if dx != 0 or dy != 0:
                    surface.blit(outline, (cx + dx, cy + dy))
        surface.blit(rendered, (cx, cy))

    def draw(self, surface):
        self._draw_background(surface)
        for leaf in self.leaves:
            leaf.draw(surface)
        self._draw_vine_border(surface)
        self._draw_title(surface)

        for btn in self.buttons.values():
            btn.draw(surface)

        frame = self.gustavo_frames[self.gustavo_frame_idx]
        scaled = pygame.transform.scale(frame, (frame.get_width() * 3, frame.get_height() * 3))
        bob = int(math.sin(self.time * 2) * 4)
        gx = SCREEN_WIDTH // 2 - scaled.get_width() // 2
        gy = SCREEN_HEIGHT - scaled.get_height() - 40 + bob
        surface.blit(scaled, (gx, gy))

    def handle_event(self, event):
        for key, btn in self.buttons.items():
            if btn.handle_event(event):
                return key
        return None


class PauseMenu:

    def __init__(self):
        self.title_font = pygame.font.SysFont(None, 64)
        self.shadow_font = pygame.font.SysFont(None, 64)

        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        btn_w, btn_h = 220, 44
        self.buttons = {
            "resume": Button(cx, cy, btn_w, btn_h, "Resume", 28),
            "settings": Button(cx, cy + 60, btn_w, btn_h, "Settings", 28),
            "quit_to_menu": Button(cx, cy + 120, btn_w, btn_h, "Quit to Menu", 28),
        }

        self.overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 160))

    def update(self, dt):
        for btn in self.buttons.values():
            btn.update(dt)

    def draw(self, surface):
        surface.blit(self.overlay, (0, 0))

        title_text = "PAUSED"
        shadow = self.shadow_font.render(title_text, True, (40, 40, 40))
        title = self.title_font.render(title_text, True, WHITE)
        tx = SCREEN_WIDTH // 2 - title.get_width() // 2
        ty = SCREEN_HEIGHT // 2 - 120
        surface.blit(shadow, (tx + 3, ty + 3))
        surface.blit(title, (tx, ty))

        for btn in self.buttons.values():
            btn.draw(surface)

    def handle_event(self, event):
        for key, btn in self.buttons.items():
            if btn.handle_event(event):
                return key
        return None


class GameOverScreen:

    def __init__(self):
        self.title_font = pygame.font.SysFont(None, 80)
        self.stats_font = pygame.font.SysFont(None, 28)
        self.label_font = pygame.font.SysFont(None, 32)
        self.time = 0.0

        cx = SCREEN_WIDTH // 2
        btn_y = SCREEN_HEIGHT // 2 + 180
        btn_w, btn_h = 200, 44
        self.buttons = {
            "restart": Button(cx - 120, btn_y, btn_w, btn_h, "Play Again", 28),
            "main_menu": Button(cx + 120, btn_y, btn_w, btn_h, "Main Menu", 28),
        }

        self.overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.overlay.fill((60, 0, 0, 180))

    def update(self, dt):
        self.time += dt
        for btn in self.buttons.values():
            btn.update(dt)

    def _draw_title(self, surface):
        pulse = int((math.sin(self.time * 3) * 0.3 + 0.7) * 255)
        pulse = max(60, min(255, pulse))
        title_color = (pulse, 20, 20)
        text = self.title_font.render("GAME OVER", True, title_color)
        tx = SCREEN_WIDTH // 2 - text.get_width() // 2
        ty = SCREEN_HEIGHT // 2 - 200
        surface.blit(text, (tx, ty))

    def _draw_stats(self, surface, stats_dict):
        panel_w, panel_h = 340, 210
        px = SCREEN_WIDTH // 2 - panel_w // 2
        py = SCREEN_HEIGHT // 2 - 100

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (0, 0, 0, 140), (0, 0, panel_w, panel_h), border_radius=8)
        pygame.draw.rect(panel, (180, 40, 40), (0, 0, panel_w, panel_h), 2, border_radius=8)
        surface.blit(panel, (px, py))

        lines = [
            ("Level Reached", str(stats_dict.get("level", 0))),
            ("Enemies Killed", str(stats_dict.get("enemies_killed", 0))),
            ("Waves Survived", str(stats_dict.get("waves", 0))),
            ("Time Survived", f"{stats_dict.get('time_survived', 0):.1f}s"),
            ("Total XP Earned", str(stats_dict.get("xp_earned", 0))),
        ]

        y = py + 15
        for label, value in lines:
            label_surf = self.stats_font.render(label, True, (200, 200, 200))
            value_surf = self.stats_font.render(value, True, GOLDEN)
            surface.blit(label_surf, (px + 20, y))
            surface.blit(value_surf, (px + panel_w - 20 - value_surf.get_width(), y))
            y += 38

    def draw(self, surface, stats_dict):
        surface.blit(self.overlay, (0, 0))
        self._draw_title(surface)
        self._draw_stats(surface, stats_dict)
        for btn in self.buttons.values():
            btn.draw(surface)

    def handle_event(self, event):
        for key, btn in self.buttons.items():
            if btn.handle_event(event):
                return key
        return None
