import pygame
from settings import (
    BASE_HP, BASE_ATTACK, BASE_DEFENSE, BASE_SPEED, BASE_LUCK,
    STAT_GROWTH_RATE, XP_BASE, XP_EXPONENT, MAX_LEVEL,
    MAP_WIDTH, MAP_HEIGHT, INVINCIBILITY_DURATION,
)


class Player(pygame.sprite.Sprite):

    def __init__(self, pos: tuple[float, float], asset_gen):
        super().__init__()
        self.sprites = asset_gen.get_player_sprites()
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(0, 0)

        self.level = 1
        self.current_xp = 0
        self.xp_to_next_level = XP_BASE

        self._base_hp = BASE_HP
        self._base_attack = BASE_ATTACK
        self._base_defense = BASE_DEFENSE
        self._base_speed = BASE_SPEED
        self._base_luck = BASE_LUCK
        self._recalc_stats()
        self.hp = self.max_hp

        self.facing_direction = pygame.math.Vector2(1, 0)
        self.is_invincible = False
        self.invincibility_timer = 0.0

        self.animation_state = "idle"
        self.animation_frame = 0
        self.animation_timer = 0.0

        self.unlocked_skills: list[str] = []
        self.skill_ranks: dict[str, int] = {}
        self.skill_cooldowns: dict[str, float] = {}

        self.image = self.sprites["idle"][0]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def _recalc_stats(self):
        mult = 1 + STAT_GROWTH_RATE * (self.level - 1)
        self.max_hp = int(self._base_hp * mult)
        self.attack = int(self._base_attack * mult)
        self.defense = int(self._base_defense * mult)
        self.speed = self._base_speed * mult
        self.luck = int(self._base_luck * mult)

    def handle_input(self, keys, mouse_pos, camera_offset):
        dx, dy = 0.0, 0.0
        if keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_s]:
            dy += 1
        if keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_d]:
            dx += 1
        self.vel = pygame.math.Vector2(dx, dy)
        if self.vel.length_squared() > 0:
            self.vel = self.vel.normalize() * self.speed

        world_mouse = pygame.math.Vector2(mouse_pos) + pygame.math.Vector2(camera_offset)
        diff = world_mouse - self.pos
        if diff.length_squared() > 0:
            self.facing_direction = diff.normalize()

    def update(self, dt: float):
        self.pos += self.vel * dt * 60

        self.pos.x = max(16, min(MAP_WIDTH - 16, self.pos.x))
        self.pos.y = max(20, min(MAP_HEIGHT - 20, self.pos.y))

        if self.is_invincible:
            self.invincibility_timer -= dt
            if self.invincibility_timer <= 0:
                self.is_invincible = False

        self.animation_timer += dt
        if self.animation_timer >= 0.15:
            self.animation_timer = 0.0
            frames = self.sprites.get(self.animation_state, self.sprites["idle"])
            self.animation_frame = (self.animation_frame + 1) % len(frames)

        if self.vel.length_squared() > 0.1:
            if self.animation_state != "walk":
                self.animation_state = "walk"
                self.animation_frame = 0
        else:
            if self.animation_state == "walk":
                self.animation_state = "idle"
                self.animation_frame = 0

        frames = self.sprites.get(self.animation_state, self.sprites["idle"])
        self.image = frames[self.animation_frame % len(frames)]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

        for skill, cd in list(self.skill_cooldowns.items()):
            self.skill_cooldowns[skill] = max(0.0, cd - dt)

    def take_damage(self, amount: int) -> int:
        if self.is_invincible:
            return 0
        actual = max(1, amount - self.defense)
        self.hp -= actual
        self.is_invincible = True
        self.invincibility_timer = INVINCIBILITY_DURATION
        self.animation_state = "hurt"
        self.animation_frame = 0
        return actual

    def gain_xp(self, amount: int) -> bool:
        self.current_xp += amount
        if self.current_xp >= self.xp_to_next_level and self.level < MAX_LEVEL:
            self.level_up()
            return True
        return False

    def level_up(self):
        overflow = self.current_xp - self.xp_to_next_level
        self.level += 1
        self._recalc_stats()
        self.xp_to_next_level = int(XP_BASE * (self.level ** XP_EXPONENT))
        self.current_xp = max(0, overflow)
        self.hp = min(self.max_hp, self.hp + self.max_hp // 4)

    def unlock_skill(self, skill_name: str):
        if skill_name not in self.unlocked_skills:
            self.unlocked_skills.append(skill_name)
            self.skill_ranks[skill_name] = 1

    def upgrade_skill(self, skill_name: str):
        if skill_name in self.unlocked_skills:
            self.skill_ranks[skill_name] = self.skill_ranks.get(skill_name, 1) + 1

    def draw(self, surface: pygame.Surface, camera_offset: tuple[float, float]):
        if self.is_invincible:
            if int(self.invincibility_timer * 10) % 2 == 0:
                return

        img = self.image
        if self.facing_direction.x < 0:
            img = pygame.transform.flip(img, True, False)

        surface.blit(img, (self.pos.x - camera_offset[0] - img.get_width() // 2,
                           self.pos.y - camera_offset[1] - img.get_height() // 2))
