import pygame


class Projectile(pygame.sprite.Sprite):

    def __init__(self, pos, direction: pygame.math.Vector2, speed: float,
                 damage: int, lifetime: float, color: tuple, size: int = 6):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.vel = direction.normalize() * speed if direction.length_squared() > 0 else pygame.math.Vector2(0, 0)
        self.damage = damage
        self.lifetime = lifetime
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (size // 2, size // 2), size // 2)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def update(self, dt: float):
        self.pos += self.vel * dt * 60
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def draw(self, surface: pygame.Surface, camera_offset: tuple[float, float]):
        surface.blit(self.image,
                      (self.pos.x - camera_offset[0] - self.image.get_width() // 2,
                       self.pos.y - camera_offset[1] - self.image.get_height() // 2))
