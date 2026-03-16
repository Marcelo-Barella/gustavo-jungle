import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT


BG_COLOR = (20, 20, 30, 220)
PANEL_COLOR = (35, 35, 50)
TEXT_COLOR = (230, 230, 230)
HEADER_COLOR = (255, 215, 0)
ROW_EVEN_COLOR = (40, 40, 55)
ROW_ODD_COLOR = (50, 50, 65)
HIGHLIGHT_COLOR = (80, 140, 80)
BUTTON_COLOR = (60, 60, 80)
BUTTON_HOVER_COLOR = (80, 80, 110)
LABEL_COLOR = (180, 180, 200)


class HighScoresScreen:

    def __init__(self, high_score_manager):
        self.hsm = high_score_manager
        self.font = None
        self.title_font = None
        self.small_font = None
        self._back_rect = pygame.Rect(0, 0, 0, 0)
        self.highlight_rank = None

    def _ensure_fonts(self):
        if self.font is None:
            self.font = pygame.font.SysFont(None, 24)
        if self.title_font is None:
            self.title_font = pygame.font.SysFont(None, 36)
        if self.small_font is None:
            self.small_font = pygame.font.SysFont(None, 20)

    def handle_event(self, event) -> str | None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._back_rect.collidepoint(event.pos):
                return "back"
        return None

    def draw(self, surface):
        self._ensure_fonts()

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(BG_COLOR)
        surface.blit(overlay, (0, 0))

        panel_w, panel_h = 800, 520
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        pygame.draw.rect(surface, PANEL_COLOR, (panel_x, panel_y, panel_w, panel_h), border_radius=8)
        pygame.draw.rect(surface, (80, 80, 100), (panel_x, panel_y, panel_w, panel_h), 2, border_radius=8)

        title = self.title_font.render("High Scores", True, HEADER_COLOR)
        surface.blit(title, (panel_x + panel_w // 2 - title.get_width() // 2, panel_y + 12))

        columns = ["#", "Score", "Lvl", "Waves", "Kills", "Time", "Diff", "Date"]
        col_widths = [40, 90, 50, 60, 60, 70, 70, 100]
        header_y = panel_y + 55
        cx = panel_x + 30

        for i, col in enumerate(columns):
            txt = self.font.render(col, True, HEADER_COLOR)
            surface.blit(txt, (cx, header_y))
            cx += col_widths[i] + 15

        pygame.draw.line(surface, (80, 80, 100),
                         (panel_x + 20, header_y + 26),
                         (panel_x + panel_w - 20, header_y + 26))

        scores = self.hsm.get_scores()
        row_y = header_y + 34
        row_h = 32

        if not scores:
            empty_txt = self.font.render("No high scores yet. Play a game!", True, LABEL_COLOR)
            surface.blit(empty_txt, (panel_x + panel_w // 2 - empty_txt.get_width() // 2, row_y + 40))
        else:
            for idx, entry in enumerate(scores[:10]):
                rank = idx + 1
                ry = row_y + idx * row_h

                if self.highlight_rank is not None and rank == self.highlight_rank:
                    bg_color = HIGHLIGHT_COLOR
                elif idx % 2 == 0:
                    bg_color = ROW_EVEN_COLOR
                else:
                    bg_color = ROW_ODD_COLOR

                pygame.draw.rect(surface, bg_color,
                                 (panel_x + 20, ry, panel_w - 40, row_h - 2),
                                 border_radius=3)

                time_val = entry.get("time", 0)
                mins = int(time_val) // 60
                secs = int(time_val) % 60
                time_str = f"{mins}:{secs:02d}"

                values = [
                    str(rank),
                    str(entry.get("score", 0)),
                    str(entry.get("level", 1)),
                    str(entry.get("waves", 0)),
                    str(entry.get("enemies_killed", 0)),
                    time_str,
                    entry.get("difficulty", "normal").title(),
                    entry.get("date", ""),
                ]

                cx = panel_x + 30
                text_color = (20, 20, 20) if (self.highlight_rank and rank == self.highlight_rank) else TEXT_COLOR
                for i, val in enumerate(values):
                    txt = self.small_font.render(val, True, text_color)
                    surface.blit(txt, (cx, ry + 6))
                    cx += col_widths[i] + 15

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
