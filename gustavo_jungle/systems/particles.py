import pygame


class Particle(pygame.sprite.Sprite):

    def __init__(self, pos, vel, color, lifetime):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.color = color
        self.lifetime = lifetime
        self.image = pygame.Surface((4, 4), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (2, 2), 2)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def update(self, dt):
        self.pos += self.vel * dt * 60
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
        self.rect.center = (int(self.pos.x), int(self.pos.y))


class ParticleSystem:

    def __init__(self):
        pass

    def emit(self, pos, color, count, group):
        pass

    def update(self, dt, group):
        pass
