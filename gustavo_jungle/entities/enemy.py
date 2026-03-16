import random
import pygame
from settings import MAP_WIDTH, MAP_HEIGHT


class Enemy(pygame.sprite.Sprite):

    def __init__(self, pos, stats_dict: dict, asset_gen):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.spawn_pos = pygame.math.Vector2(pos)
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

        self.enable_patrol = True
        self.enable_flee = True
        self.enable_group_aggro = True
        self.enable_dodge = True

        self._patrol_target: pygame.math.Vector2 | None = None
        self._patrol_wait = 0.0
        self._patrol_radius = 100
        self._flee_decided = False
        self._will_flee = False
        self._dodge_timer = 0.0
        self._aware_of_player = False

    @property
    def is_alive(self) -> bool:
        return self.hp > 0 and self.state != "dead"

    def _patrol_update(self, dt: float):
        if self._patrol_wait > 0:
            self._patrol_wait -= dt
            self.vel = pygame.math.Vector2(0, 0)
            return

        if self._patrol_target is None:
            angle = random.uniform(0, 6.2832)
            dist = random.uniform(20, self._patrol_radius)
            self._patrol_target = self.spawn_pos + pygame.math.Vector2(
                dist * pygame.math.Vector2(1, 0).rotate_rad(angle).x,
                dist * pygame.math.Vector2(1, 0).rotate_rad(angle).y,
            )

        diff = self._patrol_target - self.pos
        if diff.length() < 5:
            self._patrol_target = None
            self._patrol_wait = random.uniform(1.0, 3.0)
            self.vel = pygame.math.Vector2(0, 0)
        else:
            self.vel = diff.normalize() * self.speed * 0.3

    def _flee_update(self, dt: float, player_pos: pygame.math.Vector2):
        diff = self.pos - player_pos
        if diff.length() > 0:
            self.vel = diff.normalize() * self.speed * 1.2
        else:
            self.vel = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * self.speed

    def _check_flee(self) -> bool:
        if not self.enable_flee:
            return False
        if self.hp > self.max_hp * 0.2:
            self._flee_decided = False
            self._will_flee = False
            return False
        if not self._flee_decided:
            self._flee_decided = True
            self._will_flee = random.random() < 0.5
        return self._will_flee

    def _dodge_update(self, dt: float, player_pos: pygame.math.Vector2):
        if not self.enable_dodge:
            return
        self._dodge_timer += dt
        if self._dodge_timer >= 1.0:
            self._dodge_timer = 0.0
            if random.random() < 0.10:
                diff = player_pos - self.pos
                if diff.length() > 0:
                    perp = pygame.math.Vector2(-diff.y, diff.x).normalize()
                    if random.random() < 0.5:
                        perp = -perp
                    self.pos += perp * 20

    def notify_aggro(self):
        self._aware_of_player = True

    def update(self, dt: float, player_pos: pygame.math.Vector2):
        if not self.is_alive:
            return

        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.state_timer = max(0.0, self.state_timer - dt)

        diff = player_pos - self.pos
        dist = diff.length()

        if self.state == "hurt" and self.state_timer > 0:
            pass
        elif self._check_flee():
            self.state = "chase"
            self._flee_update(dt, player_pos)
        elif dist <= self.attack_range and self.attack_cooldown <= 0:
            self._do_attack(diff, dist)
        elif dist <= self.detection_range or self._aware_of_player:
            self._aware_of_player = True
            self.state = "chase"
            if dist > 0:
                self.vel = diff.normalize() * self.speed
            self._dodge_update(dt, player_pos)
        else:
            self.state = "idle"
            if self.enable_patrol:
                self._patrol_update(dt)
            else:
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

        if self._check_flee():
            self._flee_update(dt, player_pos)
            self.state = "chase"
            self.pos += self.vel * dt * 60
        elif self.lunging:
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
            elif dist <= self.detection_range or self._aware_of_player and dist > 0:
                self._aware_of_player = True
                self.state = "chase"
                if dist > 0:
                    self.vel = diff.normalize() * self.speed * 0.5
                self.pos += self.vel * dt * 60
                self._dodge_update(dt, player_pos)
            else:
                self.state = "idle"
                if self.enable_patrol:
                    self._patrol_update(dt)
                    self.pos += self.vel * dt * 60
                else:
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

        if self._check_flee():
            self._flee_update(dt, player_pos)
            self.state = "chase"
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
            elif dist <= self.attack_range and self.charge_cooldown <= 0 and dist > 0:
                self.charging = True
                self.charge_timer = 0.5
                self.charge_cooldown = 3.0
                self.vel = diff.normalize() * self.speed * 3
                self.state = "charge"
            elif dist <= self.detection_range or self._aware_of_player and dist > 0:
                self._aware_of_player = True
                self.state = "chase"
                if dist > 0:
                    self.vel = diff.normalize() * self.speed
                self.pos += self.vel * dt * 60
                self._dodge_update(dt, player_pos)
            else:
                self.state = "idle"
                if self.enable_patrol:
                    self._patrol_update(dt)
                    self.pos += self.vel * dt * 60
                else:
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

        if self._check_flee():
            self._flee_update(dt, player_pos)
            self.state = "chase"
            self.pos += self.vel * dt * 60
        elif self.state == "hurt" and self.state_timer > 0:
            self.state_timer -= dt
        elif dist <= self.attack_range and self.bite_cooldown <= 0:
            self.state = "bite"
            self.bite_cooldown = 1.5
            self.vel = pygame.math.Vector2(0, 0)
        elif dist <= self.detection_range or self._aware_of_player and dist > 0:
            self._aware_of_player = True
            self.state = "chase"
            if dist > 0:
                self.vel = diff.normalize() * self.speed
            self.pos += self.vel * dt * 60
        else:
            self.state = "idle"
            if self.enable_patrol:
                self._patrol_update(dt)
                self.pos += self.vel * dt * 60
            else:
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

        if self._check_flee():
            self._flee_update(dt, player_pos)
            self.state = "chase"
            self.pos += self.vel * dt * 60
        elif self.slamming:
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
            elif dist <= self.detection_range or self._aware_of_player and dist > 0:
                self._aware_of_player = True
                self.state = "chase"
                if dist > 0:
                    self.vel = diff.normalize() * self.speed
                self.pos += self.vel * dt * 60
                self._dodge_update(dt, player_pos)
            else:
                self.state = "idle"
                if self.enable_patrol:
                    self._patrol_update(dt)
                    self.pos += self.vel * dt * 60
                else:
                    self.vel = pygame.math.Vector2(0, 0)

        self.pos.x = max(0, min(MAP_WIDTH, self.pos.x))
        self.pos.y = max(0, min(MAP_HEIGHT, self.pos.y))
        self._animate(dt)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))


class Parrot(Enemy):

    def __init__(self, pos, asset_gen):
        from settings import PARROT_STATS
        super().__init__(pos, PARROT_STATS, asset_gen)
        self.sprites = asset_gen.get_parrot_sprites()
        self.image = self.sprites["idle"][0]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.detection_range = 300
        self.attack_range = 200
        self.preferred_min_dist = 150
        self.preferred_max_dist = 200
        self.flee_dist = 100
        self.fire_cooldown = 0.0
        self.fire_interval = 2.5
        self.pending_projectile = None
        self.enable_flee = False

    def update(self, dt: float, player_pos: pygame.math.Vector2):
        if not self.is_alive:
            return
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.state_timer = max(0.0, self.state_timer - dt)
        self.fire_cooldown = max(0.0, self.fire_cooldown - dt)
        self.pending_projectile = None

        diff = player_pos - self.pos
        dist = diff.length()

        if self.state == "hurt" and self.state_timer > 0:
            pass
        elif dist < self.flee_dist and dist > 0:
            self.state = "chase"
            self.vel = -diff.normalize() * self.speed * 2.0
        elif dist <= self.detection_range or self._aware_of_player:
            self._aware_of_player = True
            if dist < self.preferred_min_dist and dist > 0:
                self.vel = -diff.normalize() * self.speed
                self.state = "chase"
            elif dist > self.preferred_max_dist and dist > 0:
                self.vel = diff.normalize() * self.speed
                self.state = "chase"
            else:
                perp = pygame.math.Vector2(-diff.y, diff.x)
                if perp.length() > 0:
                    self.vel = perp.normalize() * self.speed * 0.5
                else:
                    self.vel = pygame.math.Vector2(0, 0)
                self.state = "idle"

            if self.fire_cooldown <= 0 and dist <= self.attack_range and dist > 0:
                self.fire_cooldown = self.fire_interval
                self.state = "attack"
                direction = diff.normalize()
                self.pending_projectile = {
                    "pos": self.pos.copy(),
                    "direction": direction,
                    "speed": 6,
                    "damage": self.attack,
                    "lifetime": 250 / (6 * 60),
                    "color": (200, 50, 50),
                    "size": 4,
                }
        else:
            self.state = "idle"
            if self.enable_patrol:
                self._patrol_update(dt)
            else:
                self.vel = pygame.math.Vector2(0, 0)

        self.pos += self.vel * dt * 60
        self.pos.x = max(0, min(MAP_WIDTH, self.pos.x))
        self.pos.y = max(0, min(MAP_HEIGHT, self.pos.y))
        self._animate(dt)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def _animate(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= 0.12:
            self.animation_timer = 0.0
            key = "fly" if self.state == "chase" else self.state
            frames = self.sprites.get(key, self.sprites["idle"])
            self.animation_frame = (self.animation_frame + 1) % len(frames)
            self.image = frames[self.animation_frame]


class PoisonFrog(Enemy):

    def __init__(self, pos, asset_gen):
        from settings import POISON_FROG_STATS
        super().__init__(pos, POISON_FROG_STATS, asset_gen)
        self.sprites = asset_gen.get_poison_frog_sprites()
        self.image = self.sprites["idle"][0]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.detection_range = 180
        self.attack_range = 25
        self.hop_timer = 0.0
        self.hop_phase = "wait"
        self.hop_wait_duration = 1.0
        self.hop_move_duration = 0.2
        self.poison_dps = POISON_FROG_STATS.get("poison_dps", 2)
        self.poison_duration = POISON_FROG_STATS.get("poison_duration", 5.0)
        self.contact_cooldown = 0.0
        self.enable_flee = False

    def update(self, dt: float, player_pos: pygame.math.Vector2):
        if not self.is_alive:
            return
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.state_timer = max(0.0, self.state_timer - dt)
        self.contact_cooldown = max(0.0, self.contact_cooldown - dt)

        diff = player_pos - self.pos
        dist = diff.length()

        if self.state == "hurt" and self.state_timer > 0:
            pass
        elif (dist <= self.detection_range or self._aware_of_player) and dist > 0:
            self._aware_of_player = True
            self.hop_timer += dt
            if self.hop_phase == "wait":
                self.state = "idle"
                self.vel = pygame.math.Vector2(0, 0)
                if self.hop_timer >= self.hop_wait_duration:
                    self.hop_timer = 0.0
                    self.hop_phase = "hop"
                    self.vel = diff.normalize() * self.speed * 2.5
                    self.state = "hop"
            elif self.hop_phase == "hop":
                if self.hop_timer >= self.hop_move_duration:
                    self.hop_timer = 0.0
                    self.hop_phase = "wait"
                    self.vel = pygame.math.Vector2(0, 0)
                    self.state = "idle"
        else:
            self.state = "idle"
            if self.enable_patrol:
                self._patrol_update(dt)
            else:
                self.vel = pygame.math.Vector2(0, 0)

        if dist <= self.attack_range and self.contact_cooldown <= 0:
            self.state = "attack"
            self.contact_cooldown = 1.0

        self.pos += self.vel * dt * 60
        self.pos.x = max(0, min(MAP_WIDTH, self.pos.x))
        self.pos.y = max(0, min(MAP_HEIGHT, self.pos.y))
        self._animate(dt)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def _animate(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= 0.15:
            self.animation_timer = 0.0
            key = self.state
            if key == "chase":
                key = "hop"
            frames = self.sprites.get(key, self.sprites["idle"])
            self.animation_frame = (self.animation_frame + 1) % len(frames)
            self.image = frames[self.animation_frame]
