import math
import random
import pygame
from settings import MAP_WIDTH, MAP_HEIGHT


class Enemy(pygame.sprite.Sprite):

    def __init__(self, pos, stats_dict: dict, asset_gen):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(0, 0)
        self.hp = stats_dict["hp"]
        self.max_hp = stats_dict["hp"]
        self.attack = stats_dict["attack"]
        self.defense = stats_dict["defense"]
        self.speed = stats_dict["speed"]
        self.xp_value = stats_dict["xp"]
        self.state = "idle"
        self.state_timer = 0.0
        self.attack_cooldown = 0.0
        self.detection_range = 200
        self.attack_range = 40
        self.sprites: dict[str, list[pygame.Surface]] = {}
        self.animation_frame = 0
        self.animation_timer = 0.0
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    @property
    def is_alive(self) -> bool:
        return self.hp > 0 and self.state != "dead"

    def update(self, dt: float, player_pos: pygame.math.Vector2):
        if not self.is_alive:
            return

        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.state_timer = max(0.0, self.state_timer - dt)

        diff = player_pos - self.pos
        dist = diff.length()

        if self.state == "hurt" and self.state_timer > 0:
            pass
        elif dist <= self.attack_range and self.attack_cooldown <= 0:
            self._do_attack(diff, dist)
        elif dist <= self.detection_range:
            self.state = "chase"
            if dist > 0:
                self.vel = diff.normalize() * self.speed
        else:
            self.state = "idle"
            self.vel = pygame.math.Vector2(0, 0)

        self.pos += self.vel * dt * 60
        self.pos.x = max(0, min(MAP_WIDTH, self.pos.x))
        self.pos.y = max(0, min(MAP_HEIGHT, self.pos.y))

        self._animate(dt)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def _do_attack(self, diff, dist):
        self.state = "attack"
        self.vel = pygame.math.Vector2(0, 0)

    def _animate(self, dt: float):
        self.animation_timer += dt
        if self.animation_timer >= 0.15:
            self.animation_timer = 0.0
            state_key = self.state
            if state_key == "chase":
                state_key = "walk"
            frames = self.sprites.get(state_key, self.sprites.get("idle", [self.image]))
            self.animation_frame = (self.animation_frame + 1) % len(frames)
            self.image = frames[self.animation_frame]

    def take_damage(self, amount: int) -> int:
        actual = max(1, amount - self.defense)
        self.hp -= actual
        if self.hp <= 0:
            self.state = "dead"
        else:
            self.state = "hurt"
            self.state_timer = 0.2
            self.vel = pygame.math.Vector2(0, 0)
        return actual

    def draw(self, surface: pygame.Surface, camera_offset: tuple[float, float]):
        if self.state == "dead":
            return
        surface.blit(self.image,
                      (self.pos.x - camera_offset[0] - self.image.get_width() // 2,
                       self.pos.y - camera_offset[1] - self.image.get_height() // 2))


class Panther(Enemy):

    def __init__(self, pos, asset_gen):
        from settings import PANTHER_STATS
        super().__init__(pos, PANTHER_STATS, asset_gen)
        self.sprites = asset_gen.get_panther_sprites()
        self.image = self.sprites["idle"][0]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.detection_range = 250
        self.attack_range = 120
        self.lunge_cooldown = 0.0
        self.lunging = False
        self.lunge_timer = 0.0

    def update(self, dt: float, player_pos: pygame.math.Vector2):
        if not self.is_alive:
            return
        self.lunge_cooldown = max(0.0, self.lunge_cooldown - dt)
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)

        if self.lunging:
            self.lunge_timer -= dt
            if self.lunge_timer <= 0:
                self.lunging = False
                self.vel = pygame.math.Vector2(0, 0)
            self.pos += self.vel * dt * 60
        else:
            diff = player_pos - self.pos
            dist = diff.length()
            if self.state == "hurt" and self.state_timer > 0:
                self.state_timer -= dt
            elif dist <= self.attack_range and self.lunge_cooldown <= 0 and dist > 0:
                self.lunging = True
                self.lunge_timer = 0.3
                self.lunge_cooldown = 2.0
                self.vel = diff.normalize() * self.speed * 4
                self.state = "lunge"
            elif dist <= self.detection_range and dist > 0:
                self.state = "chase"
                self.vel = diff.normalize() * self.speed * 0.5
                self.pos += self.vel * dt * 60
            else:
                self.state = "idle"
                self.vel = pygame.math.Vector2(0, 0)

        self.pos.x = max(0, min(MAP_WIDTH, self.pos.x))
        self.pos.y = max(0, min(MAP_HEIGHT, self.pos.y))
        self._animate(dt)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def _animate(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= 0.15:
            self.animation_timer = 0.0
            key = "walk" if self.state == "chase" else self.state
            if key == "lunge":
                key = "lunge"
            frames = self.sprites.get(key, self.sprites["idle"])
            self.animation_frame = (self.animation_frame + 1) % len(frames)
            self.image = frames[self.animation_frame]


class Lion(Enemy):

    def __init__(self, pos, asset_gen):
        from settings import LION_STATS
        super().__init__(pos, LION_STATS, asset_gen)
        self.sprites = asset_gen.get_lion_sprites()
        self.image = self.sprites["idle"][0]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.detection_range = 200
        self.attack_range = 80
        self.charge_cooldown = 0.0
        self.charging = False
        self.charge_timer = 0.0

    def update(self, dt: float, player_pos: pygame.math.Vector2):
        if not self.is_alive:
            return
        self.charge_cooldown = max(0.0, self.charge_cooldown - dt)
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)

        if self.charging:
            self.charge_timer -= dt
            if self.charge_timer <= 0:
                self.charging = False
                self.vel = pygame.math.Vector2(0, 0)
            self.pos += self.vel * dt * 60
        else:
            diff = player_pos - self.pos
            dist = diff.length()
            if self.state == "hurt" and self.state_timer > 0:
                self.state_timer -= dt
            elif dist <= self.attack_range and self.charge_cooldown <= 0 and dist > 0:
                self.charging = True
                self.charge_timer = 0.5
                self.charge_cooldown = 3.0
                self.vel = diff.normalize() * self.speed * 3
                self.state = "charge"
            elif dist <= self.detection_range and dist > 0:
                self.state = "chase"
                self.vel = diff.normalize() * self.speed
                self.pos += self.vel * dt * 60
            else:
                self.state = "idle"
                self.vel = pygame.math.Vector2(0, 0)

        self.pos.x = max(0, min(MAP_WIDTH, self.pos.x))
        self.pos.y = max(0, min(MAP_HEIGHT, self.pos.y))
        self._animate(dt)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))


class Snake(Enemy):

    def __init__(self, pos, asset_gen):
        from settings import SNAKE_STATS
        super().__init__(pos, SNAKE_STATS, asset_gen)
        self.sprites = asset_gen.get_snake_sprites()
        self.image = self.sprites["idle"][0]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.detection_range = 180
        self.attack_range = 30
        self.bite_cooldown = 0.0
        self.poison_dps = SNAKE_STATS.get("poison_dps", 2)
        self.poison_duration = SNAKE_STATS.get("poison_duration", 3.0)

    def update(self, dt: float, player_pos: pygame.math.Vector2):
        if not self.is_alive:
            return
        self.bite_cooldown = max(0.0, self.bite_cooldown - dt)
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)

        diff = player_pos - self.pos
        dist = diff.length()
        if self.state == "hurt" and self.state_timer > 0:
            self.state_timer -= dt
        elif dist <= self.attack_range and self.bite_cooldown <= 0:
            self.state = "bite"
            self.bite_cooldown = 1.5
            self.vel = pygame.math.Vector2(0, 0)
        elif dist <= self.detection_range and dist > 0:
            self.state = "chase"
            self.vel = diff.normalize() * self.speed
            self.pos += self.vel * dt * 60
        else:
            self.state = "idle"
            self.vel = pygame.math.Vector2(0, 0)

        self.pos.x = max(0, min(MAP_WIDTH, self.pos.x))
        self.pos.y = max(0, min(MAP_HEIGHT, self.pos.y))
        self._animate(dt)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def _animate(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= 0.15:
            self.animation_timer = 0.0
            key = "slither" if self.state == "chase" else self.state
            frames = self.sprites.get(key, self.sprites["idle"])
            self.animation_frame = (self.animation_frame + 1) % len(frames)
            self.image = frames[self.animation_frame]


class Gorilla(Enemy):

    def __init__(self, pos, asset_gen):
        from settings import GORILLA_STATS
        super().__init__(pos, GORILLA_STATS, asset_gen)
        self.sprites = asset_gen.get_gorilla_sprites()
        self.image = self.sprites["idle"][0]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.detection_range = 200
        self.slam_radius = GORILLA_STATS.get("slam_radius", 80)
        self.attack_range = self.slam_radius
        self.slam_cooldown = 0.0
        self.slamming = False
        self.slam_timer = 0.0
        self.slam_windup = 0.0

    def update(self, dt: float, player_pos: pygame.math.Vector2):
        if not self.is_alive:
            return
        self.slam_cooldown = max(0.0, self.slam_cooldown - dt)
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)

        if self.slamming:
            self.slam_timer -= dt
            if self.slam_timer <= 0:
                self.slamming = False
                self.vel = pygame.math.Vector2(0, 0)
        else:
            diff = player_pos - self.pos
            dist = diff.length()
            if self.state == "hurt" and self.state_timer > 0:
                self.state_timer -= dt
            elif dist <= self.slam_radius and self.slam_cooldown <= 0:
                self.slamming = True
                self.slam_timer = 0.5
                self.slam_cooldown = 4.0
                self.state = "slam"
                self.vel = pygame.math.Vector2(0, 0)
            elif dist <= self.detection_range and dist > 0:
                self.state = "chase"
                self.vel = diff.normalize() * self.speed
                self.pos += self.vel * dt * 60
            else:
                self.state = "idle"
                self.vel = pygame.math.Vector2(0, 0)

        self.pos.x = max(0, min(MAP_WIDTH, self.pos.x))
        self.pos.y = max(0, min(MAP_HEIGHT, self.pos.y))
        self._animate(dt)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))


class JungleKingLion(Enemy):

    def __init__(self, pos, asset_gen):
        from settings import JUNGLE_KING_STATS
        super().__init__(pos, JUNGLE_KING_STATS, asset_gen)
        self.is_boss = True
        self.sprites = asset_gen.get_jungle_king_sprites()
        self.image = self.sprites["idle"][0]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.detection_range = 300
        self.attack_range = 150
        self.charge_cooldown = 0.0
        self.charging = False
        self.charge_timer = 0.0
        self.ground_pound_cooldown = 0.0
        self.ground_pounding = False
        self.ground_pound_timer = 0.0
        self.ground_pound_windup = JUNGLE_KING_STATS["ground_pound_windup"]
        self.ground_pound_radius = JUNGLE_KING_STATS["ground_pound_radius"]
        self.roar_cooldown = 0.0
        self.roar_interval = JUNGLE_KING_STATS["roar_cooldown"]
        self.roar_speed_buff = JUNGLE_KING_STATS["roar_speed_buff"]
        self.roar_buff_duration = JUNGLE_KING_STATS["roar_buff_duration"]
        self.roar_active = False
        self.roar_timer = 0.0
        self.nearby_enemies: list = []

    def update(self, dt: float, player_pos: pygame.math.Vector2):
        if not self.is_alive:
            return
        self.charge_cooldown = max(0.0, self.charge_cooldown - dt)
        self.ground_pound_cooldown = max(0.0, self.ground_pound_cooldown - dt)
        self.roar_cooldown = max(0.0, self.roar_cooldown - dt)
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)

        if self.roar_active:
            self.roar_timer -= dt
            if self.roar_timer <= 0:
                self.roar_active = False
                for e in self.nearby_enemies:
                    if hasattr(e, '_original_speed'):
                        e.speed = e._original_speed
                        del e._original_speed
                self.nearby_enemies = []

        if self.ground_pounding:
            self.ground_pound_timer -= dt
            if self.ground_pound_timer <= 0:
                self.ground_pounding = False
                self.vel = pygame.math.Vector2(0, 0)
            self.pos += self.vel * dt * 60
        elif self.charging:
            self.charge_timer -= dt
            if self.charge_timer <= 0:
                self.charging = False
                self.vel = pygame.math.Vector2(0, 0)
            self.pos += self.vel * dt * 60
        else:
            diff = player_pos - self.pos
            dist = diff.length()
            if self.state == "hurt" and self.state_timer > 0:
                self.state_timer -= dt
            elif dist <= self.ground_pound_radius and self.ground_pound_cooldown <= 0:
                self.ground_pounding = True
                self.ground_pound_timer = self.ground_pound_windup
                self.ground_pound_cooldown = 5.0
                self.state = "ground_pound"
                self.vel = pygame.math.Vector2(0, 0)
            elif dist <= self.attack_range and self.charge_cooldown <= 0 and dist > 0:
                self.charging = True
                self.charge_timer = 0.4
                self.charge_cooldown = 2.5
                self.vel = diff.normalize() * self.speed * 4
                self.state = "charge"
            elif dist <= self.detection_range and dist > 0:
                self.state = "chase"
                self.vel = diff.normalize() * self.speed
                self.pos += self.vel * dt * 60
            else:
                self.state = "idle"
                self.vel = pygame.math.Vector2(0, 0)

        self.pos.x = max(0, min(MAP_WIDTH, self.pos.x))
        self.pos.y = max(0, min(MAP_HEIGHT, self.pos.y))
        self._animate(dt)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def try_roar(self, enemy_group):
        if self.roar_cooldown > 0 or not self.is_alive:
            return
        self.roar_cooldown = self.roar_interval
        self.roar_active = True
        self.roar_timer = self.roar_buff_duration
        self.nearby_enemies = []
        for e in enemy_group:
            if e is self or not e.is_alive:
                continue
            dist = (e.pos - self.pos).length()
            if dist <= self.detection_range:
                if not hasattr(e, '_original_speed'):
                    e._original_speed = e.speed
                e.speed = e._original_speed * (1.0 + self.roar_speed_buff)
                self.nearby_enemies.append(e)

    def _animate(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= 0.15:
            self.animation_timer = 0.0
            key = "walk" if self.state == "chase" else self.state
            frames = self.sprites.get(key, self.sprites["idle"])
            self.animation_frame = (self.animation_frame + 1) % len(frames)
            self.image = frames[self.animation_frame]


class AncientGorilla(Enemy):

    def __init__(self, pos, asset_gen):
        from settings import ANCIENT_GORILLA_STATS
        super().__init__(pos, ANCIENT_GORILLA_STATS, asset_gen)
        self.is_boss = True
        self.sprites = asset_gen.get_ancient_gorilla_sprites()
        self.image = self.sprites["idle"][0]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.detection_range = 250
        self.attack_range = 100
        self.slam_radius = ANCIENT_GORILLA_STATS["slam_radius"]
        self.slam_cooldown = 0.0
        self.slamming = False
        self.slam_timer = 0.0
        self.slam_count = 0
        self.rock_toss_cooldown = 0.0
        self.rock_toss_speed = ANCIENT_GORILLA_STATS["rock_toss_speed"]
        self.rock_toss_range = ANCIENT_GORILLA_STATS["rock_toss_range"]
        self.enrage_threshold = ANCIENT_GORILLA_STATS["enrage_threshold"]
        self.enrage_attack_mult = ANCIENT_GORILLA_STATS["enrage_attack_mult"]
        self.enrage_speed_mult = ANCIENT_GORILLA_STATS["enrage_speed_mult"]
        self.enraged = False
        self._base_attack = self.attack
        self._base_speed = self.speed

    def update(self, dt: float, player_pos: pygame.math.Vector2):
        if not self.is_alive:
            return
        self.slam_cooldown = max(0.0, self.slam_cooldown - dt)
        self.rock_toss_cooldown = max(0.0, self.rock_toss_cooldown - dt)
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)

        if not self.enraged and self.hp <= self.max_hp * self.enrage_threshold:
            self.enraged = True
            self.attack = int(self._base_attack * self.enrage_attack_mult)
            self.speed = self._base_speed * self.enrage_speed_mult

        if self.slamming:
            self.slam_timer -= dt
            if self.slam_timer <= 0:
                self.slam_count -= 1
                if self.slam_count > 0:
                    self.slam_timer = 0.4
                else:
                    self.slamming = False
                    self.vel = pygame.math.Vector2(0, 0)
        else:
            diff = player_pos - self.pos
            dist = diff.length()
            if self.state == "hurt" and self.state_timer > 0:
                self.state_timer -= dt
            elif dist <= self.slam_radius and self.slam_cooldown <= 0:
                self.slamming = True
                self.slam_count = 2
                self.slam_timer = 0.5
                self.slam_cooldown = 4.0
                self.state = "slam"
                self.vel = pygame.math.Vector2(0, 0)
            elif dist <= self.rock_toss_range and self.rock_toss_cooldown <= 0 and dist > self.slam_radius:
                self.state = "attack"
                self.rock_toss_cooldown = 3.0
                self.vel = pygame.math.Vector2(0, 0)
            elif dist <= self.detection_range and dist > 0:
                self.state = "chase"
                self.vel = diff.normalize() * self.speed
                self.pos += self.vel * dt * 60
            else:
                self.state = "idle"
                self.vel = pygame.math.Vector2(0, 0)

        self.pos.x = max(0, min(MAP_WIDTH, self.pos.x))
        self.pos.y = max(0, min(MAP_HEIGHT, self.pos.y))
        self._animate(dt)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def _animate(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= 0.15:
            self.animation_timer = 0.0
            key = "walk" if self.state == "chase" else self.state
            if key == "attack":
                key = "slam"
            frames = self.sprites.get(key, self.sprites["idle"])
            self.animation_frame = (self.animation_frame + 1) % len(frames)
            self.image = frames[self.animation_frame]


class VenomQueen(Enemy):

    def __init__(self, pos, asset_gen):
        from settings import VENOM_QUEEN_STATS
        super().__init__(pos, VENOM_QUEEN_STATS, asset_gen)
        self.is_boss = True
        self.sprites = asset_gen.get_venom_queen_sprites()
        self.image = self.sprites["idle"][0]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.detection_range = 280
        self.attack_range = 50
        self.poison_spray_range = VENOM_QUEEN_STATS["poison_spray_range"]
        self.constrict_range = VENOM_QUEEN_STATS["constrict_range"]
        self.constrict_dps = VENOM_QUEEN_STATS["constrict_dps"]
        self.spray_cooldown = 0.0
        self.constricting = False
        self.constrict_timer = 0.0
        self.summon_cooldown = VENOM_QUEEN_STATS["summon_cooldown"]
        self.summon_interval = VENOM_QUEEN_STATS["summon_cooldown"]
        self.summon_count_min = VENOM_QUEEN_STATS["summon_count_min"]
        self.summon_count_max = VENOM_QUEEN_STATS["summon_count_max"]
        self.pending_summon = False
        self._asset_gen = asset_gen

    def update(self, dt: float, player_pos: pygame.math.Vector2):
        if not self.is_alive:
            return
        self.spray_cooldown = max(0.0, self.spray_cooldown - dt)
        self.summon_cooldown = max(0.0, self.summon_cooldown - dt)
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)

        if self.summon_cooldown <= 0:
            self.pending_summon = True
            self.summon_cooldown = self.summon_interval

        diff = player_pos - self.pos
        dist = diff.length()

        if self.constricting:
            self.constrict_timer -= dt
            if self.constrict_timer <= 0 or dist > self.constrict_range * 1.5:
                self.constricting = False
                self.vel = pygame.math.Vector2(0, 0)
        elif self.state == "hurt" and self.state_timer > 0:
            self.state_timer -= dt
        elif dist <= self.constrict_range:
            self.constricting = True
            self.constrict_timer = 2.0
            self.state = "attack"
            self.vel = pygame.math.Vector2(0, 0)
        elif dist <= self.poison_spray_range and self.spray_cooldown <= 0:
            self.state = "spray"
            self.spray_cooldown = 3.0
            self.vel = pygame.math.Vector2(0, 0)
        elif dist <= self.detection_range and dist > 0:
            self.state = "chase"
            self.vel = diff.normalize() * self.speed
            self.pos += self.vel * dt * 60
        else:
            self.state = "idle"
            self.vel = pygame.math.Vector2(0, 0)

        self.pos.x = max(0, min(MAP_WIDTH, self.pos.x))
        self.pos.y = max(0, min(MAP_HEIGHT, self.pos.y))
        self._animate(dt)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def try_summon(self, enemy_group):
        if not self.pending_summon or not self.is_alive:
            return
        self.pending_summon = False
        count = random.randint(self.summon_count_min, self.summon_count_max)
        for _ in range(count):
            offset = pygame.math.Vector2(
                random.uniform(-60, 60),
                random.uniform(-60, 60),
            )
            spawn_pos = self.pos + offset
            spawn_pos.x = max(0, min(MAP_WIDTH, spawn_pos.x))
            spawn_pos.y = max(0, min(MAP_HEIGHT, spawn_pos.y))
            snake = Snake((spawn_pos.x, spawn_pos.y), self._asset_gen)
            enemy_group.add(snake)

    def _animate(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= 0.15:
            self.animation_timer = 0.0
            key = self.state
            if key == "chase":
                key = "slither"
            if key == "attack":
                key = "idle"
            frames = self.sprites.get(key, self.sprites["idle"])
            self.animation_frame = (self.animation_frame + 1) % len(frames)
            self.image = frames[self.animation_frame]
