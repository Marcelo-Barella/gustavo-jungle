import random
import math
import pygame
from settings import (
    POWERUP_DROP_CHANCE, SPEED_BOOST, HEALTH_REGEN, DOUBLE_XP,
)


class PowerupDrop(pygame.sprite.Sprite):

    def __init__(self, pos, kind: str, asset_gen):
        super().__init__()
        self.kind = kind
        self.pos = pygame.math.Vector2(pos)
        self.lifetime = 15.0
        self.image = asset_gen.get_powerup_icon(self._icon_key())
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.bob_timer = 0.0
        self.base_y = self.pos.y

    def _icon_key(self) -> str:
        mapping = {"speed_boost": "speed", "health_regen": "regen", "double_xp": "double_xp"}
        return mapping.get(self.kind, self.kind)

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
            return
        self.bob_timer += dt
        self.pos.y = self.base_y + math.sin(self.bob_timer * 3) * 3
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def draw(self, surface: pygame.Surface, camera_offset: tuple[float, float]):
        surface.blit(self.image,
                     (self.pos.x - camera_offset[0] - self.image.get_width() // 2,
                      self.pos.y - camera_offset[1] - self.image.get_height() // 2))


class PowerupSystem:

    POWERUP_TYPES = ["speed_boost", "health_regen", "double_xp"]

    CONFIGS = {
        "speed_boost": SPEED_BOOST,
        "health_regen": HEALTH_REGEN,
        "double_xp": DOUBLE_XP,
    }

    def __init__(self):
        self.active_powerups: list[dict] = []
        self._original_speed: float | None = None

    def update(self, dt, player) -> float:
        xp_mult = 1.0
        expired = []
        for buff in self.active_powerups:
            buff["timer"] -= dt
            if buff["timer"] <= 0:
                expired.append(buff)
                continue
            if buff["kind"] == "health_regen":
                heal = HEALTH_REGEN["hps"] * dt
                player.hp = min(player.max_hp, player.hp + heal)
            if buff["kind"] == "double_xp":
                xp_mult = DOUBLE_XP["multiplier"]

        for buff in expired:
            self._deactivate(buff, player)
            self.active_powerups.remove(buff)

        return xp_mult

    def activate(self, powerup_type: str, player):
        conf = self.CONFIGS[powerup_type]
        for buff in self.active_powerups:
            if buff["kind"] == powerup_type:
                buff["timer"] = conf.get("duration", 15.0)
                return
        buff = {"kind": powerup_type, "timer": conf.get("duration", 15.0)}
        if powerup_type == "speed_boost":
            if self._original_speed is None:
                self._original_speed = player.speed
            player.speed *= conf["multiplier"]
        self.active_powerups.append(buff)

    def _deactivate(self, buff: dict, player):
        if buff["kind"] == "speed_boost" and self._original_speed is not None:
            player.speed = self._original_speed
            self._original_speed = None

    def get_active(self) -> list[dict]:
        return list(self.active_powerups)

    def try_drop(self, pos, asset_gen, group):
        if random.random() < POWERUP_DROP_CHANCE:
            kind = random.choice(self.POWERUP_TYPES)
            drop = PowerupDrop(pos, kind, asset_gen)
            group.add(drop)
