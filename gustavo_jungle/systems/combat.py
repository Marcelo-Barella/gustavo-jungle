import math
import random
import pygame
from settings import (
    MELEE_RANGE, MELEE_ARC_DURATION, DAMAGE_TEXT_DURATION,
    DAMAGE_TEXT_RISE_SPEED, WHITE, GOLDEN,
)


class DamageText(pygame.sprite.Sprite):

    def __init__(self, pos, amount: int, is_crit: bool = False):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.timer = DAMAGE_TEXT_DURATION
        self.is_crit = is_crit
        self.alpha = 255
        self._font = None
        self.amount = amount

    def _ensure_font(self):
        if self._font is None:
            size = 24 if self.is_crit else 18
            self._font = pygame.font.SysFont(None, size)

    def update(self, dt):
        self.pos.y -= DAMAGE_TEXT_RISE_SPEED * dt * 60
        self.timer -= dt
        self.alpha = max(0, int(255 * (self.timer / DAMAGE_TEXT_DURATION)))
        if self.timer <= 0:
            self.kill()

    def draw(self, surface: pygame.Surface, camera_offset: tuple[float, float]):
        self._ensure_font()
        color = GOLDEN if self.is_crit else WHITE
        text_surf = self._font.render(str(self.amount), True, color)
        text_surf.set_alpha(self.alpha)
        surface.blit(text_surf,
                     (self.pos.x - camera_offset[0] - text_surf.get_width() // 2,
                      self.pos.y - camera_offset[1] - text_surf.get_height() // 2))


class CombatSystem:

    def __init__(self):
        self.melee_cooldown = 0.0

    def process_player_attack(self, player, enemies, dt) -> list[tuple]:
        self.melee_cooldown = max(0.0, self.melee_cooldown - dt)
        if self.melee_cooldown > 0:
            return []

        mouse_buttons = pygame.mouse.get_pressed()
        if not mouse_buttons[0]:
            return []

        self.melee_cooldown = MELEE_ARC_DURATION
        hits = []
        facing = player.facing_direction
        for enemy in enemies:
            if not enemy.is_alive:
                continue
            diff = enemy.pos - player.pos
            dist = diff.length()
            if dist > MELEE_RANGE:
                continue
            if dist > 0:
                angle = math.acos(max(-1, min(1, facing.dot(diff.normalize()))))
                if angle > math.pi / 3:
                    continue
            luck_bonus = random.uniform(0, player.luck / 100)
            damage = player.attack * (1 + luck_bonus)
            is_crit = luck_bonus / (player.luck / 100) > 0.8 if player.luck > 0 else False
            if is_crit:
                damage *= 2
            damage = int(damage)
            actual = enemy.take_damage(damage)
            hits.append((enemy, actual, is_crit))
        if hits:
            player.animation_state = "attack"
            player.animation_frame = 0
        return hits

    def process_enemy_attacks(self, enemies, player, dt) -> list[int]:
        damages = []
        for enemy in enemies:
            if not enemy.is_alive:
                continue
            if enemy.state != "attack" and not getattr(enemy, 'lunging', False) \
               and not getattr(enemy, 'charging', False) \
               and enemy.state != "bite" and enemy.state != "slam" \
               and enemy.state != "lunge" and enemy.state != "charge":
                continue
            diff = player.pos - enemy.pos
            dist = diff.length()
            if dist > enemy.attack_range:
                continue
            if enemy.attack_cooldown > 0:
                continue
            actual = player.take_damage(enemy.attack)
            if actual > 0:
                damages.append(actual)
                enemy.attack_cooldown = 1.0
                direction = diff.normalize() if dist > 0 else pygame.math.Vector2(1, 0)
                self.apply_knockback(player, direction, 3.0)
        return damages

    def check_projectile_hits(self, projectiles, enemies) -> list[tuple]:
        hits = []
        for proj in list(projectiles):
            for enemy in enemies:
                if not enemy.is_alive:
                    continue
                dist = (proj.pos - enemy.pos).length()
                if dist < 20:
                    actual = enemy.take_damage(proj.damage)
                    hits.append((enemy, actual, False))
                    proj.kill()
                    break
        return hits

    @staticmethod
    def apply_knockback(entity, direction, force):
        if direction.length_squared() > 0:
            entity.pos += direction.normalize() * force
