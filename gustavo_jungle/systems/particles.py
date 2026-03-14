import random
import pygame


class Particle(pygame.sprite.Sprite):

    def __init__(self, pos, vel, color, lifetime):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.image = pygame.Surface((4, 4), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (2, 2), 2)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def update(self, dt):
        self.pos += self.vel * dt * 60
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def draw(self, surface: pygame.Surface, camera_offset: tuple[float, float]):
        alpha = max(0, int(255 * (self.lifetime / self.max_lifetime)))
        img = self.image.copy()
        img.set_alpha(alpha)
        surface.blit(img,
                     (self.pos.x - camera_offset[0] - 2,
                      self.pos.y - camera_offset[1] - 2))


class ParticleSystem:

    def __init__(self):
        pass

    def emit(self, pos, color, count, group):
        for _ in range(count):
            angle = random.uniform(0, 6.283)
            speed = random.uniform(0.5, 2.0)
            vel = pygame.math.Vector2(speed, 0).rotate_rad(angle)
            lifetime = random.uniform(0.3, 0.8)
            p = Particle(pos, vel, color, lifetime)
            group.add(p)
