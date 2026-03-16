import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT


class SettingsScreen:

    PANEL_W = 500
    PANEL_H = 500
    SLIDER_W = 200
    SLIDER_H = 8
    HANDLE_R = 10
    BG_COLOR = (20, 20, 20, 220)
    BORDER_COLOR = (255, 215, 0)
    TITLE_COLOR = (255, 255, 255)
    SECTION_COLOR = (255, 215, 0)
    TEXT_COLOR = (220, 220, 220)
    TRACK_COLOR = (80, 80, 80)
    HANDLE_COLOR = (255, 255, 255)
    HOVER_COLOR = (255, 235, 100)
    BTN_COLOR = (50, 50, 50)
    BTN_HOVER_COLOR = (80, 80, 80)
    CHECK_COLOR = (255, 215, 0)

    def __init__(self):
        self.active = False
        self.master_volume = 0.7
        self.sfx_volume = 0.7
        self.music_volume = 0.7
        self.fullscreen = False
        self._dragging = None
        self._font = None
        self._small_font = None
        self._title_font = None
        self._panel_rect = None
        self._slider_rects = {}
        self._back_rect = None
        self._fs_rect = None
        self._hover_back = False
        self._hover_fs = False
        self._hover_sliders = {}

    def _ensure_fonts(self):
        if self._font is None:
            self._font = pygame.font.SysFont(None, 24)
        if self._small_font is None:
            self._small_font = pygame.font.SysFont(None, 20)
        if self._title_font is None:
            self._title_font = pygame.font.SysFont(None, 36)

    def _build_layout(self):
        px = (SCREEN_WIDTH - self.PANEL_W) // 2
        py = (SCREEN_HEIGHT - self.PANEL_H) // 2
        self._panel_rect = pygame.Rect(px, py, self.PANEL_W, self.PANEL_H)

        slider_x = px + 230
        base_y = py + 70
        gap = 40

        self._slider_rects = {
            "master": pygame.Rect(slider_x, base_y, self.SLIDER_W, self.SLIDER_H),
            "sfx": pygame.Rect(slider_x, base_y + gap, self.SLIDER_W, self.SLIDER_H),
            "music": pygame.Rect(slider_x, base_y + gap * 2, self.SLIDER_W, self.SLIDER_H),
        }

        fs_y = base_y + gap * 3 + 10
        self._fs_rect = pygame.Rect(px + 30, fs_y, 20, 20)

        self._back_rect = pygame.Rect(
            px + (self.PANEL_W - 120) // 2,
            py + self.PANEL_H - 50,
            120,
            36,
        )

    def show(self):
        self.active = True

    def hide(self):
        self.active = False

    def _volume_for(self, name):
        return getattr(self, f"{name}_volume")

    def _set_volume_for(self, name, val):
        setattr(self, f"{name}_volume", max(0.0, min(1.0, val)))

    def _handle_pos_to_value(self, name, mx):
        r = self._slider_rects[name]
        return max(0.0, min(1.0, (mx - r.x) / r.width))

    def handle_event(self, event):
        if not self.active:
            return None
        self._ensure_fonts()
        if self._panel_rect is None:
            self._build_layout()

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self._hover_back = self._back_rect.collidepoint(mx, my)
            self._hover_fs = self._fs_rect.collidepoint(mx, my)
            for name, rect in self._slider_rects.items():
                val = self._volume_for(name)
                hx = rect.x + int(val * rect.width)
                hy = rect.y + rect.height // 2
                self._hover_sliders[name] = (mx - hx) ** 2 + (my - hy) ** 2 <= (self.HANDLE_R + 4) ** 2

            if self._dragging is not None:
                self._set_volume_for(self._dragging, self._handle_pos_to_value(self._dragging, mx))

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for name, rect in self._slider_rects.items():
                val = self._volume_for(name)
                hx = rect.x + int(val * rect.width)
                hy = rect.y + rect.height // 2
                if (mx - hx) ** 2 + (my - hy) ** 2 <= (self.HANDLE_R + 4) ** 2:
                    self._dragging = name
                    return None
                expanded = rect.inflate(0, 20)
                if expanded.collidepoint(mx, my):
                    self._dragging = name
                    self._set_volume_for(name, self._handle_pos_to_value(name, mx))
                    return None

            if self._fs_rect.collidepoint(mx, my):
                self.fullscreen = not self.fullscreen
                return None

            if self._back_rect.collidepoint(mx, my):
                return "back"

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = None

        return None

    def update(self, dt):
        pass

    def draw(self, surface):
        if not self.active:
            return
        self._ensure_fonts()
        if self._panel_rect is None:
            self._build_layout()

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        pr = self._panel_rect
        panel = pygame.Surface((pr.width, pr.height), pygame.SRCALPHA)
        panel.fill(self.BG_COLOR)
        surface.blit(panel, pr.topleft)
        pygame.draw.rect(surface, self.BORDER_COLOR, pr, 2)

        title = self._title_font.render("SETTINGS", True, self.TITLE_COLOR)
        surface.blit(title, (pr.centerx - title.get_width() // 2, pr.y + 18))

        self._draw_sliders(surface)
        self._draw_fullscreen_toggle(surface)
        self._draw_controls_ref(surface)
        self._draw_back_button(surface)

    def _draw_sliders(self, surface):
        labels = {"master": "Master Volume", "sfx": "SFX Volume", "music": "Music Volume"}
        pr = self._panel_rect
        section = self._font.render("Volume", True, self.SECTION_COLOR)
        surface.blit(section, (pr.x + 30, pr.y + 52))

        for name in ("master", "sfx", "music"):
            rect = self._slider_rects[name]
            label = self._small_font.render(labels[name], True, self.TEXT_COLOR)
            surface.blit(label, (pr.x + 30, rect.y - 4))

            pygame.draw.rect(surface, self.TRACK_COLOR, rect)

            val = self._volume_for(name)
            hx = rect.x + int(val * rect.width)
            hy = rect.y + rect.height // 2

            filled = pygame.Rect(rect.x, rect.y, hx - rect.x, rect.height)
            pygame.draw.rect(surface, self.BORDER_COLOR, filled)

            color = self.HOVER_COLOR if self._hover_sliders.get(name) or self._dragging == name else self.HANDLE_COLOR
            pygame.draw.circle(surface, color, (hx, hy), self.HANDLE_R)

            pct = self._small_font.render(f"{int(val * 100)}%", True, self.TEXT_COLOR)
            surface.blit(pct, (rect.right + 12, rect.y - 4))

    def _draw_fullscreen_toggle(self, surface):
        pr = self._panel_rect
        r = self._fs_rect
        section = self._font.render("Display", True, self.SECTION_COLOR)
        surface.blit(section, (pr.x + 30, r.y - 24))

        border_color = self.HOVER_COLOR if self._hover_fs else self.TEXT_COLOR
        pygame.draw.rect(surface, border_color, r, 2)
        if self.fullscreen:
            inner = r.inflate(-6, -6)
            pygame.draw.rect(surface, self.CHECK_COLOR, inner)

        label = self._small_font.render("Fullscreen", True, self.TEXT_COLOR)
        surface.blit(label, (r.right + 10, r.y + 1))

    def _draw_controls_ref(self, surface):
        pr = self._panel_rect
        cy = self._fs_rect.bottom + 30
        section = self._font.render("Controls", True, self.SECTION_COLOR)
        surface.blit(section, (pr.x + 30, cy))
        cy += 26

        controls = [
            "WASD = Move",
            "LClick = Attack",
            "1-4 = Skills",
            "ESC = Pause",
        ]
        for line in controls:
            txt = self._small_font.render(line, True, self.TEXT_COLOR)
            surface.blit(txt, (pr.x + 40, cy))
            cy += 22

    def _draw_back_button(self, surface):
        r = self._back_rect
        color = self.BTN_HOVER_COLOR if self._hover_back else self.BTN_COLOR
        pygame.draw.rect(surface, color, r)
        pygame.draw.rect(surface, self.BORDER_COLOR, r, 2)
        label = self._font.render("Back", True, self.TITLE_COLOR)
        surface.blit(label, (r.centerx - label.get_width() // 2, r.centery - label.get_height() // 2))

    def get_volumes(self):
        return {
            "master": self.master_volume,
            "sfx": self.sfx_volume,
            "music": self.music_volume,
        }

    def is_fullscreen(self):
        return self.fullscreen
