import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT


SECTION_AUDIO = 0
SECTION_DISPLAY = 1
SECTION_GAMEPLAY = 2
SECTION_CONTROLS = 3
SECTION_NAMES = ["Audio", "Display", "Gameplay", "Controls"]

BG_COLOR = (20, 20, 30, 220)
PANEL_COLOR = (35, 35, 50)
TAB_COLOR = (50, 50, 70)
TAB_ACTIVE_COLOR = (80, 140, 80)
TEXT_COLOR = (230, 230, 230)
LABEL_COLOR = (180, 180, 200)
SLIDER_TRACK_COLOR = (60, 60, 80)
SLIDER_FILL_COLOR = (80, 180, 80)
SLIDER_HANDLE_COLOR = (220, 220, 220)
TOGGLE_ON_COLOR = (80, 180, 80)
TOGGLE_OFF_COLOR = (100, 60, 60)
BUTTON_COLOR = (60, 60, 80)
BUTTON_HOVER_COLOR = (80, 80, 110)
HIGHLIGHT_COLOR = (255, 215, 0)
REBIND_COLOR = (200, 60, 60)


class SettingsScreen:

    def __init__(self, config_manager):
        self.config = config_manager
        self.active_section = SECTION_AUDIO
        self.font = None
        self.title_font = None
        self.small_font = None
        self.waiting_for_key = None
        self.dragging_slider = None
        self._sliders = {}
        self._toggles = {}
        self._difficulty_rects = {}
        self._keybind_rects = {}
        self._tab_rects = []
        self._back_rect = pygame.Rect(0, 0, 0, 0)

    def _ensure_fonts(self):
        if self.font is None:
            self.font = pygame.font.SysFont(None, 26)
        if self.title_font is None:
            self.title_font = pygame.font.SysFont(None, 36)
        if self.small_font is None:
            self.small_font = pygame.font.SysFont(None, 22)

    def handle_event(self, event) -> str | None:
        if self.waiting_for_key is not None:
            if event.type == pygame.KEYDOWN:
                bindings = dict(self.config.get("key_bindings"))
                bindings[self.waiting_for_key] = event.key
                self.config.set("key_bindings", bindings)
                self.waiting_for_key = None
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for i, rect in enumerate(self._tab_rects):
                if rect.collidepoint(pos):
                    self.active_section = i
                    return None
            if self._back_rect.collidepoint(pos):
                return "back"
            self._handle_section_click(pos)

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_slider = None

        if event.type == pygame.MOUSEMOTION:
            if self.dragging_slider is not None:
                self._handle_slider_drag(event.pos)

        return None

    def _handle_section_click(self, pos):
        if self.active_section == SECTION_AUDIO:
            for key, (rect, _) in self._sliders.items():
                if rect.collidepoint(pos):
                    self.dragging_slider = key
                    self._handle_slider_drag(pos)
                    return
        elif self.active_section == SECTION_DISPLAY:
            for key, rect in self._toggles.items():
                if rect.collidepoint(pos):
                    self.config.set(key, not self.config.get(key))
                    return
        elif self.active_section == SECTION_GAMEPLAY:
            for diff, rect in self._difficulty_rects.items():
                if rect.collidepoint(pos):
                    self.config.set("difficulty", diff)
                    return
        elif self.active_section == SECTION_CONTROLS:
            for action, rect in self._keybind_rects.items():
                if rect.collidepoint(pos):
                    self.waiting_for_key = action
                    return

    def _handle_slider_drag(self, pos):
        if self.dragging_slider is None:
            return
        if self.dragging_slider not in self._sliders:
            return
        rect, _ = self._sliders[self.dragging_slider]
        ratio = (pos[0] - rect.x) / max(1, rect.width)
        ratio = max(0.0, min(1.0, ratio))
        self.config.set(self.dragging_slider, round(ratio, 2))

    def draw(self, surface):
        self._ensure_fonts()

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(BG_COLOR)
        surface.blit(overlay, (0, 0))

        panel_w, panel_h = 700, 500
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        pygame.draw.rect(surface, PANEL_COLOR, (panel_x, panel_y, panel_w, panel_h), border_radius=8)
        pygame.draw.rect(surface, (80, 80, 100), (panel_x, panel_y, panel_w, panel_h), 2, border_radius=8)

        title = self.title_font.render("Settings", True, TEXT_COLOR)
        surface.blit(title, (panel_x + panel_w // 2 - title.get_width() // 2, panel_y + 12))

        tab_y = panel_y + 50
        tab_w = panel_w // len(SECTION_NAMES)
        self._tab_rects = []
        for i, name in enumerate(SECTION_NAMES):
            tx = panel_x + i * tab_w
            rect = pygame.Rect(tx, tab_y, tab_w, 32)
            self._tab_rects.append(rect)
            color = TAB_ACTIVE_COLOR if i == self.active_section else TAB_COLOR
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, (80, 80, 100), rect, 1)
            txt = self.font.render(name, True, TEXT_COLOR)
            surface.blit(txt, (tx + tab_w // 2 - txt.get_width() // 2, tab_y + 6))

        content_y = tab_y + 42
        content_area = pygame.Rect(panel_x + 20, content_y, panel_w - 40, panel_h - (content_y - panel_y) - 60)

        if self.active_section == SECTION_AUDIO:
            self._draw_audio(surface, content_area)
        elif self.active_section == SECTION_DISPLAY:
            self._draw_display(surface, content_area)
        elif self.active_section == SECTION_GAMEPLAY:
            self._draw_gameplay(surface, content_area)
        elif self.active_section == SECTION_CONTROLS:
            self._draw_controls(surface, content_area)

        back_w, back_h = 100, 36
        self._back_rect = pygame.Rect(
            panel_x + panel_w // 2 - back_w // 2,
            panel_y + panel_h - 50,
            back_w, back_h
        )
        mouse_pos = pygame.mouse.get_pos()
        bc = BUTTON_HOVER_COLOR if self._back_rect.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(surface, bc, self._back_rect, border_radius=4)
        pygame.draw.rect(surface, (80, 80, 100), self._back_rect, 1, border_radius=4)
        bt = self.font.render("Back", True, TEXT_COLOR)
        surface.blit(bt, (self._back_rect.centerx - bt.get_width() // 2,
                          self._back_rect.centery - bt.get_height() // 2))

    def _draw_slider(self, surface, x, y, w, key, label):
        txt = self.font.render(label, True, LABEL_COLOR)
        surface.blit(txt, (x, y))

        track_x = x + 200
        track_w = w - 260
        track_rect = pygame.Rect(track_x, y + 4, track_w, 16)
        self._sliders[key] = (track_rect, label)

        pygame.draw.rect(surface, SLIDER_TRACK_COLOR, track_rect, border_radius=4)
        val = self.config.get(key)
        fill_w = int(track_w * val)
        pygame.draw.rect(surface, SLIDER_FILL_COLOR, (track_x, y + 4, fill_w, 16), border_radius=4)

        handle_x = track_x + fill_w - 6
        pygame.draw.rect(surface, SLIDER_HANDLE_COLOR, (handle_x, y + 1, 12, 22), border_radius=3)

        val_txt = self.small_font.render(f"{int(val * 100)}%", True, TEXT_COLOR)
        surface.blit(val_txt, (track_x + track_w + 10, y + 2))

    def _draw_toggle(self, surface, x, y, key, label):
        txt = self.font.render(label, True, LABEL_COLOR)
        surface.blit(txt, (x, y))

        box_x = x + 280
        box_rect = pygame.Rect(box_x, y + 2, 20, 20)
        self._toggles[key] = box_rect

        val = self.config.get(key)
        color = TOGGLE_ON_COLOR if val else TOGGLE_OFF_COLOR
        pygame.draw.rect(surface, color, box_rect, border_radius=3)
        pygame.draw.rect(surface, (120, 120, 140), box_rect, 1, border_radius=3)
        if val:
            check = self.small_font.render("X", True, TEXT_COLOR)
            surface.blit(check, (box_x + 4, y + 2))

        state_txt = self.small_font.render("On" if val else "Off", True, TEXT_COLOR)
        surface.blit(state_txt, (box_x + 28, y + 2))

    def _draw_audio(self, surface, area):
        self._sliders = {}
        y = area.y + 10
        self._draw_slider(surface, area.x, y, area.width, "master_volume", "Master Volume")
        y += 50
        self._draw_slider(surface, area.x, y, area.width, "sfx_volume", "SFX Volume")
        y += 50
        self._draw_slider(surface, area.x, y, area.width, "music_volume", "Music Volume")

    def _draw_display(self, surface, area):
        self._toggles = {}
        y = area.y + 10
        self._draw_toggle(surface, area.x, y, "fullscreen", "Fullscreen")
        y += 40
        self._draw_toggle(surface, area.x, y, "show_fps", "Show FPS")
        y += 40
        self._draw_toggle(surface, area.x, y, "show_damage_numbers", "Show Damage Numbers")

    def _draw_gameplay(self, surface, area):
        self._difficulty_rects = {}
        y = area.y + 10
        lbl = self.font.render("Difficulty", True, LABEL_COLOR)
        surface.blit(lbl, (area.x, y))

        current = self.config.get("difficulty")
        bx = area.x + 160
        for diff in ("easy", "normal", "hard"):
            w, h = 100, 32
            rect = pygame.Rect(bx, y, w, h)
            self._difficulty_rects[diff] = rect
            is_selected = diff == current
            color = TAB_ACTIVE_COLOR if is_selected else BUTTON_COLOR
            pygame.draw.rect(surface, color, rect, border_radius=4)
            pygame.draw.rect(surface, (80, 80, 100), rect, 1, border_radius=4)
            txt = self.font.render(diff.title(), True, TEXT_COLOR)
            surface.blit(txt, (rect.centerx - txt.get_width() // 2,
                               rect.centery - txt.get_height() // 2))
            bx += w + 12

        y += 60
        info_lines = {
            "easy": "Enemy HP x0.7, Enemy ATK x0.7, XP gain x1.3",
            "normal": "All multipliers x1.0 (default)",
            "hard": "Enemy HP x1.5, Enemy ATK x1.3, XP gain x0.8",
        }
        info = self.small_font.render(info_lines.get(current, ""), True, LABEL_COLOR)
        surface.blit(info, (area.x, y))

    def _draw_controls(self, surface, area):
        self._keybind_rects = {}
        bindings = self.config.get("key_bindings")
        y = area.y + 4
        col_w = area.width // 2
        items = list(bindings.items())
        for i, (action, key_val) in enumerate(items):
            col = i % 2
            row = i // 2
            cx = area.x + col * col_w
            cy = y + row * 36

            label = action.replace("_", " ").title()
            txt = self.small_font.render(f"{label}:", True, LABEL_COLOR)
            surface.blit(txt, (cx, cy + 4))

            btn_x = cx + 130
            btn_rect = pygame.Rect(btn_x, cy, 100, 28)
            self._keybind_rects[action] = btn_rect

            if self.waiting_for_key == action:
                pygame.draw.rect(surface, REBIND_COLOR, btn_rect, border_radius=3)
                key_txt = self.small_font.render("Press key...", True, TEXT_COLOR)
            else:
                pygame.draw.rect(surface, BUTTON_COLOR, btn_rect, border_radius=3)
                key_name = pygame.key.name(key_val)
                key_txt = self.small_font.render(key_name, True, TEXT_COLOR)

            pygame.draw.rect(surface, (80, 80, 100), btn_rect, 1, border_radius=3)
            surface.blit(key_txt, (btn_rect.x + 6, btn_rect.y + 4))
