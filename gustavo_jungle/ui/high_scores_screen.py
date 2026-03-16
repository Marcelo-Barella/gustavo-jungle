import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, GOLDEN, WHITE, BLACK


class HighScoresScreen:

    PANEL_W = 700
    PANEL_H = 520
    BORDER_COLOR = GOLDEN
    BG_COLOR = (20, 20, 30)
    OVERLAY_ALPHA = 180
    ROW_EVEN = (30, 30, 45)
    ROW_ODD = (40, 40, 55)
    HIGHLIGHT_COLOR = (80, 70, 20)
    HEADER_COLOR = GOLDEN
    TEXT_COLOR = WHITE
    BACK_NORMAL = (60, 60, 80)
    BACK_HOVER = (80, 80, 110)
    COLUMNS = ["Rank", "Player", "Level", "Waves", "Kills", "Time", "Score"]
    COL_WIDTHS = [50, 110, 60, 60, 60, 70, 90]

    def __init__(self, save_manager):
        self.save_manager = save_manager
        self.active = False
        self._current_score: int | None = None
        self._back_rect = pygame.Rect(0, 0, 120, 40)
        self._font_title = None
        self._font_header = None
        self._font_row = None
        self._font_btn = None
        self._initialized = False

    def _ensure_fonts(self):
        if self._initialized:
            return
        self._font_title = pygame.font.SysFont(None, 48)
        self._font_header = pygame.font.SysFont(None, 24)
        self._font_row = pygame.font.SysFont(None, 22)
        self._font_btn = pygame.font.SysFont(None, 28)
        self._initialized = True

    def show(self, current_score=None):
        self.active = True
        self._current_score = current_score

    def handle_event(self, event) -> str | None:
        if not self.active:
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._back_rect.collidepoint(event.pos):
                self.active = False
                return "back"
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_BACKSPACE):
                self.active = False
                return "back"
        return None

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return
        self._ensure_fonts()

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, self.OVERLAY_ALPHA))
        surface.blit(overlay, (0, 0))

        px = (SCREEN_WIDTH - self.PANEL_W) // 2
        py = (SCREEN_HEIGHT - self.PANEL_H) // 2
        panel_rect = pygame.Rect(px, py, self.PANEL_W, self.PANEL_H)
        pygame.draw.rect(surface, self.BG_COLOR, panel_rect)
        pygame.draw.rect(surface, self.BORDER_COLOR, panel_rect, 3)

        title = self._font_title.render("HIGH SCORES", True, GOLDEN)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, py + 15))

        header_y = py + 70
        table_x = px + 20
        total_w = sum(self.COL_WIDTHS)
        start_x = table_x + (self.PANEL_W - 40 - total_w) // 2

        cx = start_x
        for col, w in zip(self.COLUMNS, self.COL_WIDTHS):
            txt = self._font_header.render(col, True, self.HEADER_COLOR)
            surface.blit(txt, (cx, header_y))
            cx += w

        pygame.draw.line(surface, self.BORDER_COLOR,
                         (start_x, header_y + 24),
                         (start_x + total_w, header_y + 24), 1)

        scores = self.save_manager.get_high_scores()
        row_h = 32
        row_y = header_y + 30

        for i, entry in enumerate(scores[:10]):
            is_highlight = (self._current_score is not None
                            and entry.get("score") == self._current_score)
            if is_highlight:
                bg = self.HIGHLIGHT_COLOR
            elif i % 2 == 0:
                bg = self.ROW_EVEN
            else:
                bg = self.ROW_ODD

            row_rect = pygame.Rect(start_x - 4, row_y, total_w + 8, row_h)
            pygame.draw.rect(surface, bg, row_rect)

            time_val = entry.get("time_survived", 0)
            mins = int(time_val) // 60
            secs = int(time_val) % 60
            time_str = f"{mins}:{secs:02d}"

            cells = [
                str(i + 1),
                str(entry.get("player_name", "---"))[:10],
                str(entry.get("level", 0)),
                str(entry.get("waves_survived", 0)),
                str(entry.get("enemies_killed", 0)),
                time_str,
                str(entry.get("score", 0)),
            ]

            color = GOLDEN if is_highlight else self.TEXT_COLOR
            cx = start_x
            for cell, w in zip(cells, self.COL_WIDTHS):
                txt = self._font_row.render(cell, True, color)
                surface.blit(txt, (cx, row_y + 6))
                cx += w

            row_y += row_h

        btn_x = SCREEN_WIDTH // 2 - 60
        btn_y = py + self.PANEL_H - 55
        self._back_rect = pygame.Rect(btn_x, btn_y, 120, 40)

        mouse_pos = pygame.mouse.get_pos()
        hover = self._back_rect.collidepoint(mouse_pos)
        btn_color = self.BACK_HOVER if hover else self.BACK_NORMAL
        pygame.draw.rect(surface, btn_color, self._back_rect, border_radius=6)
        pygame.draw.rect(surface, self.BORDER_COLOR, self._back_rect, 2, border_radius=6)

        btn_txt = self._font_btn.render("Back", True, WHITE)
        surface.blit(btn_txt, (
            self._back_rect.centerx - btn_txt.get_width() // 2,
            self._back_rect.centery - btn_txt.get_height() // 2,
        ))
