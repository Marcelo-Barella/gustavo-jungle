import pygame


class PowerupDrop(pygame.sprite.Sprite):

    def __init__(self, pos, kind, asset_gen):
        super().__init__()
        self.kind = kind
        self.pos = pygame.math.Vector2(pos)
        self.lifetime = 15.0
        self.image = asset_gen.get_powerup_icon(kind)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()


class PowerupSystem:

    def __init__(self):
        self.active_buffs: list = []

    def update(self, dt, player):
        pass

    def apply_powerup(self, kind, player):
        pass

    def try_drop(self, pos, asset_gen, group):
        pass
