import random
import pygame
from settings import CHEST_INTERACT_RANGE


class TreasureChest(pygame.sprite.Sprite):

    REWARDS = ["xp_burst", "full_heal", "powerup"]

    def __init__(self, pos, asset_gen):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.sprites = asset_gen.get_chest_sprites()
        self.image = self.sprites["closed"]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.opened = False
        self.reward_type = random.choice(self.REWARDS)
        self.xp_value = random.randint(50, 200)

    def try_open(self, player_pos):
        if self.opened:
            return None
        dist = (player_pos - self.pos).length()
        if dist > CHEST_INTERACT_RANGE:
            return None
        self.opened = True
        self.image = self.sprites["open"]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        return self.reward_type

    def draw(self, surface, camera_offset):
        surface.blit(
            self.image,
            (self.pos.x - camera_offset[0] - self.image.get_width() // 2,
             self.pos.y - camera_offset[1] - self.image.get_height() // 2),
        )
