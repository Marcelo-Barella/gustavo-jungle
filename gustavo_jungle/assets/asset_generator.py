import math
import pygame
from settings import (
    TILE_SIZE, JUNGLE_GREEN, DARK_GREEN, BROWN, GOLDEN,
    RIVER_BLUE, WHITE, BLACK, TAN, LIGHT_GREEN, RED,
)

_cache: dict[str, list[pygame.Surface]] = {}


def _get(key: str, builder):
    if key not in _cache:
        _cache[key] = builder()
    return _cache[key]


def _tint_red(surf: pygame.Surface) -> pygame.Surface:
    copy = surf.copy()
    overlay = pygame.Surface(copy.get_size(), pygame.SRCALPHA)
    overlay.fill((255, 0, 0, 100))
    copy.blit(overlay, (0, 0))
    return copy


class AssetGenerator:

    # ------------------------------------------------------------------
    # Gustavo (Player) ~32x40
    # ------------------------------------------------------------------

    def _build_gustavo_base(self, w=32, h=40, squish=0, arm_extend=False):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        skin = (255, 218, 185)
        glasses = (60, 60, 60)
        shirt = (34, 139, 34)
        shorts = (139, 90, 43)
        shoe = (80, 50, 20)

        body_y = 14 + squish
        body_h = 16 - squish
        pygame.draw.ellipse(surf, shirt, (6, body_y, 20, body_h))

        head_r = 8
        head_cx, head_cy = 16, 10
        pygame.draw.circle(surf, skin, (head_cx, head_cy), head_r)

        pygame.draw.circle(surf, glasses, (12, 9), 3, 1)
        pygame.draw.circle(surf, glasses, (20, 9), 3, 1)
        pygame.draw.line(surf, glasses, (15, 9), (17, 9), 1)

        shorts_y = body_y + body_h - 2
        pygame.draw.rect(surf, shorts, (8, shorts_y, 16, 6))

        foot_y = shorts_y + 6
        pygame.draw.ellipse(surf, shoe, (8, foot_y, 7, 4))
        pygame.draw.ellipse(surf, shoe, (17, foot_y, 7, 4))

        if arm_extend:
            pygame.draw.line(surf, skin, (26, body_y + 4), (31, body_y + 2), 3)

        return surf

    def get_player_sprites(self) -> dict[str, list[pygame.Surface]]:
        def build():
            idle1 = self._build_gustavo_base()
            idle2 = self._build_gustavo_base(squish=2)
            walk_frames = []
            for i in range(4):
                f = self._build_gustavo_base()
                ox = (i % 2) * 2 - 1
                shifted = pygame.Surface(f.get_size(), pygame.SRCALPHA)
                shifted.blit(f, (ox, 0))
                walk_frames.append(shifted)
            attack = self._build_gustavo_base(arm_extend=True)
            hurt = _tint_red(idle1)
            return {
                "idle": [idle1, idle2],
                "walk": walk_frames,
                "attack": [attack],
                "hurt": [hurt],
            }
        return _get("player", build)

    # ------------------------------------------------------------------
    # Panther ~40x24
    # ------------------------------------------------------------------

    def get_panther_sprites(self) -> dict[str, list[pygame.Surface]]:
        def _base(w=40, h=24, stretch=0):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            body_color = (30, 30, 30)
            pygame.draw.ellipse(surf, body_color, (2 - stretch, 6, 32 + stretch, 14))
            pygame.draw.circle(surf, (255, 255, 0), (6, 10), 2)
            pygame.draw.circle(surf, (255, 255, 0), (6, 14), 2)
            pygame.draw.line(surf, body_color, (34, 12), (38, 8), 2)
            return surf

        def build():
            idle = _base()
            w1 = _base()
            w2_surf = pygame.Surface((40, 24), pygame.SRCALPHA)
            w2_surf.blit(_base(), (0, 1))
            lunge = _base(stretch=4)
            hurt = _tint_red(idle)
            return {
                "idle": [idle],
                "walk": [w1, w2_surf],
                "lunge": [lunge],
                "hurt": [hurt],
            }
        return _get("panther", build)

    # ------------------------------------------------------------------
    # Lion ~48x36
    # ------------------------------------------------------------------

    def get_lion_sprites(self) -> dict[str, list[pygame.Surface]]:
        def _base(w=48, h=36, lean=False):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            body = (210, 180, 100)
            mane = (139, 90, 43)
            pygame.draw.ellipse(surf, body, (6, 10, 36, 22))
            pygame.draw.circle(surf, mane, (12, 16), 10)
            pygame.draw.circle(surf, body, (10, 14), 6)
            pygame.draw.circle(surf, BLACK, (8, 13), 2)
            pygame.draw.circle(surf, BLACK, (13, 13), 2)
            if lean:
                pygame.draw.ellipse(surf, body, (2, 12, 38, 20))
            return surf

        def build():
            idle = _base()
            w1 = _base()
            w2 = pygame.Surface((48, 36), pygame.SRCALPHA)
            w2.blit(_base(), (0, 1))
            charge = _base(lean=True)
            hurt = _tint_red(idle)
            return {
                "idle": [idle],
                "walk": [w1, w2],
                "charge": [charge],
                "hurt": [hurt],
            }
        return _get("lion", build)

    # ------------------------------------------------------------------
    # Snake ~30x12
    # ------------------------------------------------------------------

    def get_snake_sprites(self) -> dict[str, list[pygame.Surface]]:
        def _body(w=30, h=12, phase=0.0, bite=False):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            color = (34, 180, 34)
            pts = []
            for x in range(4, 26):
                y = int(h // 2 + math.sin(x * 0.5 + phase) * 3)
                pts.append((x, y))
            if len(pts) > 1:
                pygame.draw.lines(surf, color, False, pts, 3)
            head_x = 4 if not bite else 2
            pygame.draw.polygon(surf, color, [(head_x, h // 2 - 3), (head_x, h // 2 + 3), (head_x - 3, h // 2)])
            tongue_x = head_x - 3
            pygame.draw.line(surf, RED, (tongue_x, h // 2), (tongue_x - 4, h // 2 - 1), 1)
            pygame.draw.line(surf, RED, (tongue_x, h // 2), (tongue_x - 4, h // 2 + 1), 1)
            return surf

        def build():
            idle = _body(phase=0.0)
            s1 = _body(phase=0.0)
            s2 = _body(phase=math.pi)
            bite = _body(bite=True)
            hurt = _tint_red(idle)
            return {
                "idle": [idle],
                "slither": [s1, s2],
                "bite": [bite],
                "hurt": [hurt],
            }
        return _get("snake", build)

    # ------------------------------------------------------------------
    # Gorilla ~52x48
    # ------------------------------------------------------------------

    def get_gorilla_sprites(self) -> dict[str, list[pygame.Surface]]:
        def _base(w=52, h=48, arms_up=False, arm_offset=0):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            body = (60, 40, 30)
            pygame.draw.ellipse(surf, body, (8, 12, 36, 30))
            pygame.draw.circle(surf, body, (26, 10), 8)
            pygame.draw.circle(surf, BLACK, (23, 9), 2)
            pygame.draw.circle(surf, BLACK, (29, 9), 2)
            if arms_up:
                pygame.draw.line(surf, body, (8, 18), (2, 4), 6)
                pygame.draw.line(surf, body, (44, 18), (50, 4), 6)
            else:
                ay = 18 + arm_offset
                pygame.draw.line(surf, body, (8, ay), (2, ay + 16), 6)
                pygame.draw.line(surf, body, (44, ay), (50, ay + 16), 6)
            return surf

        def build():
            idle = _base()
            w1 = _base(arm_offset=0)
            w2 = _base(arm_offset=3)
            slam = _base(arms_up=True)
            hurt = _tint_red(idle)
            return {
                "idle": [idle],
                "walk": [w1, w2],
                "slam": [slam],
                "hurt": [hurt],
            }
        return _get("gorilla", build)

    # ------------------------------------------------------------------
    # Tiles (TILE_SIZE x TILE_SIZE)
    # ------------------------------------------------------------------

    def get_tile(self, tile_type: str) -> pygame.Surface:
        key = f"tile_{tile_type}"
        def build():
            s = pygame.Surface((TILE_SIZE, TILE_SIZE))
            if tile_type == "grass":
                s.fill(JUNGLE_GREEN)
                for i in range(8):
                    x = (i * 17 + 5) % TILE_SIZE
                    y = (i * 23 + 3) % TILE_SIZE
                    pygame.draw.circle(s, DARK_GREEN, (x, y), 2)
            elif tile_type == "tree":
                s.fill(JUNGLE_GREEN)
                cx, cy = TILE_SIZE // 2, TILE_SIZE // 2
                pygame.draw.rect(s, BROWN, (cx - 4, cy + 6, 8, 20))
                pygame.draw.circle(s, DARK_GREEN, (cx, cy - 2), 20)
            elif tile_type == "water":
                s.fill(RIVER_BLUE)
                for i in range(3):
                    y = 15 + i * 18
                    pts = [(0, y)]
                    for x in range(0, TILE_SIZE, 8):
                        pts.append((x, y + int(math.sin(x * 0.3 + i) * 3)))
                    pts.append((TILE_SIZE, y))
                    if len(pts) > 1:
                        pygame.draw.lines(s, (100, 200, 255), False, pts, 1)
            elif tile_type == "path":
                s.fill(TAN)
                for i in range(5):
                    x = (i * 19 + 7) % TILE_SIZE
                    y = (i * 13 + 11) % TILE_SIZE
                    pygame.draw.circle(s, (190, 160, 120), (x, y), 2)
            elif tile_type == "bush":
                s.fill(JUNGLE_GREEN)
                pygame.draw.ellipse(s, LIGHT_GREEN, (4, 4, TILE_SIZE - 8, TILE_SIZE - 8))
                for i in range(6):
                    x = (i * 13 + 8) % (TILE_SIZE - 8) + 4
                    y = (i * 17 + 6) % (TILE_SIZE - 8) + 4
                    pygame.draw.circle(s, DARK_GREEN, (x, y), 4)
            else:
                s.fill(JUNGLE_GREEN)
            return [s]
        return _get(key, build)[0]

    # ------------------------------------------------------------------
    # Effects
    # ------------------------------------------------------------------

    def get_xp_orb(self) -> pygame.Surface:
        def build():
            s = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(s, GOLDEN, (5, 5), 5)
            pygame.draw.circle(s, WHITE, (5, 5), 2)
            return [s]
        return _get("xp_orb", build)[0]

    def get_powerup_icon(self, kind: str) -> pygame.Surface:
        key = f"powerup_{kind}"
        def build():
            s = pygame.Surface((16, 16), pygame.SRCALPHA)
            if kind == "speed":
                pygame.draw.circle(s, (64, 164, 223), (8, 8), 7)
            elif kind == "regen":
                pygame.draw.rect(s, LIGHT_GREEN, (5, 2, 6, 12))
                pygame.draw.rect(s, LIGHT_GREEN, (2, 5, 12, 6))
            elif kind == "double_xp":
                pts = []
                for i in range(5):
                    angle = math.radians(i * 72 - 90)
                    pts.append((8 + int(7 * math.cos(angle)), 8 + int(7 * math.sin(angle))))
                    angle2 = math.radians(i * 72 - 90 + 36)
                    pts.append((8 + int(3 * math.cos(angle2)), 8 + int(3 * math.sin(angle2))))
                pygame.draw.polygon(s, GOLDEN, pts)
            return [s]
        return _get(key, build)[0]

    def get_skill_icon(self, skill: str) -> pygame.Surface:
        key = f"skill_{skill}"
        def build():
            s = pygame.Surface((20, 20), pygame.SRCALPHA)
            if skill == "vine_whip":
                pygame.draw.arc(s, JUNGLE_GREEN, (2, 2, 16, 16), 0.5, 2.5, 3)
            elif skill == "rock_throw":
                pygame.draw.circle(s, BROWN, (10, 10), 8)
            elif skill == "jungle_roar":
                pygame.draw.circle(s, GOLDEN, (10, 10), 8, 2)
            elif skill == "dash":
                pygame.draw.polygon(s, (64, 164, 223), [(2, 14), (10, 2), (18, 14)])
            return [s]
        return _get(key, build)[0]
