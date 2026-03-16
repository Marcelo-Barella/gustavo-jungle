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

    def _resolve_tree_collision(self, collision_rects, old_pos):
        if not collision_rects:
            return
        body = pygame.Rect(self.pos.x - 10, self.pos.y - 10, 20, 20)
        for cr in collision_rects:
            if body.colliderect(cr):
                move_dir = self.pos - old_pos
                if move_dir.length_squared() > 0:
                    perp = pygame.math.Vector2(-move_dir.y, move_dir.x)
                    test_pos = old_pos + perp.normalize() * move_dir.length()
                    test_body = pygame.Rect(test_pos.x - 10, test_pos.y - 10, 20, 20)
                    blocked = False
                    for cr2 in collision_rects:
                        if test_body.colliderect(cr2):
                            blocked = True
                            break
                    if not blocked:
                        self.pos.x = test_pos.x
                        self.pos.y = test_pos.y
                        return
                self.pos.x = old_pos.x
                self.pos.y = old_pos.y
                return

    def update(self, dt: float, player_pos: pygame.math.Vector2,
               collision_rects=None):
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

        old_pos = pygame.math.Vector2(self.pos)
        self.pos += self.vel * dt * 60
        self._resolve_tree_collision(collision_rects, old_pos)
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

    def update(self, dt: float, player_pos: pygame.math.Vector2,
               collision_rects=None):
        if not self.is_alive:
            return
        self.lunge_cooldown = max(0.0, self.lunge_cooldown - dt)
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)

        old_pos = pygame.math.Vector2(self.pos)
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

        self._resolve_tree_collision(collision_rects, old_pos)
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

    def update(self, dt: float, player_pos: pygame.math.Vector2,
               collision_rects=None):
        if not self.is_alive:
            return
        self.charge_cooldown = max(0.0, self.charge_cooldown - dt)
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)

        old_pos = pygame.math.Vector2(self.pos)
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

        self._resolve_tree_collision(collision_rects, old_pos)
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

    def update(self, dt: float, player_pos: pygame.math.Vector2,
               collision_rects=None):
        if not self.is_alive:
            return
        self.bite_cooldown = max(0.0, self.bite_cooldown - dt)
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)

        old_pos = pygame.math.Vector2(self.pos)
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

        self._resolve_tree_collision(collision_rects, old_pos)
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

    def update(self, dt: float, player_pos: pygame.math.Vector2,
               collision_rects=None):
        if not self.is_alive:
            return
        self.slam_cooldown = max(0.0, self.slam_cooldown - dt)
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)

        old_pos = pygame.math.Vector2(self.pos)
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

        self._resolve_tree_collision(collision_rects, old_pos)
        self.pos.x = max(0, min(MAP_WIDTH, self.pos.x))
        self.pos.y = max(0, min(MAP_HEIGHT, self.pos.y))
        self._animate(dt)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
