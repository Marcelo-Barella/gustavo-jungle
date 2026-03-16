import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK


class FadeTransition:

    def __init__(self):
        self._surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._surface.fill(BLACK)
        self._alpha = 0
        self._target_alpha = 0
        self._duration = 0.5
        self._timer = 0.0
        self._start_alpha = 0
        self._active = False

    def fade_in(self, duration: float = 0.5):
        self._duration = duration
        self._timer = 0.0
        self._start_alpha = 255
        self._target_alpha = 0
        self._alpha = 255
        self._active = True

    def fade_out(self, duration: float = 0.5):
        self._duration = duration
        self._timer = 0.0
        self._start_alpha = 0
        self._target_alpha = 255
        self._alpha = 0
        self._active = True

    def update(self, dt: float):
        if not self._active:
            return
        self._timer += dt
        if self._timer >= self._duration:
            self._alpha = self._target_alpha
            self._active = False
            return
        progress = self._timer / self._duration
        self._alpha = int(self._start_alpha + (self._target_alpha - self._start_alpha) * progress)

    def draw(self, surface: pygame.Surface):
        if self._alpha <= 0:
            return
        self._surface.set_alpha(max(0, min(255, self._alpha)))
        surface.blit(self._surface, (0, 0))

    @property
    def is_done(self) -> bool:
        return not self._active


class CircleWipeTransition:

    def __init__(self):
        self._max_radius = int((SCREEN_WIDTH ** 2 + SCREEN_HEIGHT ** 2) ** 0.5 / 2) + 10
        self._radius = 0.0
        self._target_radius = 0.0
        self._start_radius = 0.0
        self._duration = 0.5
        self._timer = 0.0
        self._active = False
        self._center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    def wipe_open(self, duration: float = 0.5):
        self._duration = duration
        self._timer = 0.0
        self._start_radius = 0.0
        self._target_radius = float(self._max_radius)
        self._radius = 0.0
        self._active = True

    def wipe_close(self, duration: float = 0.5):
        self._duration = duration
        self._timer = 0.0
        self._start_radius = float(self._max_radius)
        self._target_radius = 0.0
        self._radius = float(self._max_radius)
        self._active = True

    def update(self, dt: float):
        if not self._active:
            return
        self._timer += dt
        if self._timer >= self._duration:
            self._radius = self._target_radius
            self._active = False
            return
        progress = self._timer / self._duration
        self._radius = self._start_radius + (self._target_radius - self._start_radius) * progress

    def draw(self, surface: pygame.Surface):
        r = max(0, int(self._radius))
        if r >= self._max_radius:
            return
        mask = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        mask.fill((0, 0, 0, 255))
        if r > 0:
            pygame.draw.circle(mask, (0, 0, 0, 0), self._center, r)
        surface.blit(mask, (0, 0))

    @property
    def is_done(self) -> bool:
        return not self._active
