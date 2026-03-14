import random
import pygame
from settings import ORB_COLLECT_RADIUS, ORB_DRIFT_SPEED, ORB_LIFETIME


class XpOrb(pygame.sprite.Sprite):

    def __init__(self, pos, value: int, asset_gen):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.value = value
        self.lifetime = ORB_LIFETIME
        self.collected = False
        angle = random.uniform(0, 6.283)
        scatter = random.uniform(0.5, 1.5)
        self.vel = pygame.math.Vector2(scatter * pygame.math.Vector2(1, 0).rotate_rad(angle))
        self.image = asset_gen.get_xp_orb()
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.alpha = 255

    def update(self, dt, player_pos=None):
        self.lifetime -= dt
        self.pos += self.vel * dt * 30
        self.vel *= 0.95

        if self.lifetime <= 2.0:
            self.alpha = max(0, int(255 * (self.lifetime / 2.0)))
        if self.lifetime <= 0:
            self.kill()
            return

        if player_pos is not None:
            diff = player_pos - self.pos
            dist = diff.length()
            if dist < ORB_COLLECT_RADIUS and dist > 0:
                self.pos += diff.normalize() * ORB_DRIFT_SPEED * dt * 60
            if dist < 20:
                self.collected = True

        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def draw(self, surface: pygame.Surface, camera_offset: tuple[float, float]):
        img = self.image.copy()
        img.set_alpha(self.alpha)
        surface.blit(img,
                     (self.pos.x - camera_offset[0] - img.get_width() // 2,
                      self.pos.y - camera_offset[1] - img.get_height() // 2))
