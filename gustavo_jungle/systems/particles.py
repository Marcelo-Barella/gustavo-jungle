import math
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


class FlashCircle(pygame.sprite.Sprite):

    def __init__(self, pos, color, max_radius, lifetime):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.color = color
        self.max_radius = max_radius
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.radius = 1.0
        size = max_radius * 2 + 4
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
            return
        progress = 1.0 - (self.lifetime / self.max_lifetime)
        self.radius = self.max_radius * progress
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def draw(self, surface: pygame.Surface, camera_offset: tuple[float, float]):
        if self.lifetime <= 0:
            return
        alpha = max(0, int(255 * (self.lifetime / self.max_lifetime)))
        sx = self.pos.x - camera_offset[0]
        sy = self.pos.y - camera_offset[1]
        r = max(1, int(self.radius))
        circle_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        c = (*self.color[:3], alpha)
        pygame.draw.circle(circle_surf, c, (r, r), r, 2)
        surface.blit(circle_surf, (sx - r, sy - r))


class SparkParticle(pygame.sprite.Sprite):

    def __init__(self, pos, vel, color, lifetime):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.length = max(6, int(self.vel.length() * 3))
        self.image = pygame.Surface((self.length, 4), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def update(self, dt):
        self.pos += self.vel * dt * 60
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def draw(self, surface: pygame.Surface, camera_offset: tuple[float, float]):
        if self.lifetime <= 0:
            return
        alpha = max(0, int(255 * (self.lifetime / self.max_lifetime)))
        sx = self.pos.x - camera_offset[0]
        sy = self.pos.y - camera_offset[1]
        if self.vel.length_squared() > 0:
            direction = self.vel.normalize()
        else:
            direction = pygame.math.Vector2(1, 0)
        end = pygame.math.Vector2(sx, sy) + direction * self.length
        c = (*self.color[:3], alpha)
        pygame.draw.line(surface, c, (sx, sy), (end.x, end.y), 2)


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

    def emit_death_burst(self, pos, color, group):
        count = random.randint(15, 25)
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(1.5, 4.0)
            vel = pygame.math.Vector2(speed, 0).rotate_rad(angle)
            lifetime = random.uniform(0.4, 1.0)
            p = Particle(pos, vel, color, lifetime)
            group.add(p)
        flash = FlashCircle(pos, color, max_radius=40, lifetime=0.3)
        group.add(flash)

    def emit_hit_spark(self, pos, direction, group):
        count = random.randint(5, 8)
        if isinstance(direction, pygame.math.Vector2) and direction.length_squared() > 0:
            base_angle = math.atan2(direction.y, direction.x)
        else:
            base_angle = random.uniform(0, math.tau)
        for _ in range(count):
            angle = base_angle + random.uniform(-0.4, 0.4)
            speed = random.uniform(2.0, 5.0)
            vel = pygame.math.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
            color = random.choice([(255, 255, 255), (255, 255, 100), (255, 220, 50)])
            p = SparkParticle(pos, vel, color, lifetime=0.2)
            group.add(p)

    def emit_level_up(self, pos, group):
        for i in range(30):
            angle = (math.tau / 30) * i
            speed = random.uniform(1.5, 3.0)
            vel = pygame.math.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
            color = (255, 215, 0)
            p = Particle(pos, vel, color, lifetime=1.0)
            group.add(p)
        for _ in range(10):
            offset_x = random.uniform(-20, 20)
            vel = pygame.math.Vector2(random.uniform(-0.3, 0.3), random.uniform(-2.0, -0.8))
            sparkle_pos = (pos[0] + offset_x, pos[1])
            color = random.choice([(255, 215, 0), (255, 235, 80), (255, 200, 50)])
            p = SparkParticle(sparkle_pos, vel, color, lifetime=1.0)
            group.add(p)

    def emit_heal(self, pos, group):
        offsets = [
            (0, -8), (0, -4), (0, 0), (0, 4), (0, 8),
            (-8, 0), (-4, 0), (4, 0), (8, 0),
        ]
        for ox, oy in offsets:
            p_pos = (pos[0] + ox, pos[1] + oy)
            vel = pygame.math.Vector2(random.uniform(-0.2, 0.2), random.uniform(-1.5, -0.5))
            color = random.choice([(0, 200, 0), (50, 220, 50), (100, 255, 100)])
            p = Particle(p_pos, vel, color, lifetime=random.uniform(0.5, 0.9))
            group.add(p)
