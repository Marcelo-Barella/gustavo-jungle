import math
import pygame
from settings import VINE_WHIP, ROCK_THROW, JUNGLE_ROAR, DASH_ATTACK, BROWN, GOLDEN
from entities.projectile import Projectile


class SkillVisual(pygame.sprite.Sprite):

    def __init__(self, pos, kind: str, radius: float, duration: float, color: tuple):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.kind = kind
        self.radius = radius
        self.max_radius = radius
        self.timer = duration
        self.duration = duration
        self.color = color
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            self.kill()
            return
        progress = 1.0 - (self.timer / self.duration)
        if self.kind == "roar":
            self.radius = self.max_radius * progress

    def draw(self, surface: pygame.Surface, camera_offset: tuple[float, float]):
        alpha = max(0, int(255 * (self.timer / self.duration)))
        cx = int(self.pos.x - camera_offset[0])
        cy = int(self.pos.y - camera_offset[1])
        r = max(1, int(self.radius))
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        c = (*self.color[:3], alpha)
        pygame.draw.circle(s, c, (r, r), r, 3)
        surface.blit(s, (cx - r, cy - r))


class DashTrail(pygame.sprite.Sprite):

    def __init__(self, pos, image: pygame.Surface, alpha: int):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.image = image.copy()
        self.image.set_alpha(alpha)
        self.timer = 0.3
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            self.kill()

    def draw(self, surface: pygame.Surface, camera_offset: tuple[float, float]):
        alpha = max(0, int(100 * (self.timer / 0.3)))
        img = self.image.copy()
        img.set_alpha(alpha)
        surface.blit(img,
                     (self.pos.x - camera_offset[0] - img.get_width() // 2,
                      self.pos.y - camera_offset[1] - img.get_height() // 2))


class SkillSystem:

    def __init__(self):
        self.skills = {
            "vine_whip": VINE_WHIP,
            "rock_throw": ROCK_THROW,
            "jungle_roar": JUNGLE_ROAR,
            "dash": DASH_ATTACK,
        }
        self.dash_state = None

    def use_skill(self, skill_name, player, enemies, projectile_group, particles_group, asset_gen) -> list[tuple]:
        if skill_name not in player.unlocked_skills:
            return []
        if player.skill_cooldowns.get(skill_name, 0) > 0:
            return []

        conf = self.skills[skill_name]
        player.skill_cooldowns[skill_name] = conf["cooldown"]
        hits = []

        if skill_name == "vine_whip":
            hits = self._vine_whip(player, enemies, conf, particles_group)
        elif skill_name == "rock_throw":
            self._rock_throw(player, conf, projectile_group)
        elif skill_name == "jungle_roar":
            hits = self._jungle_roar(player, enemies, conf, particles_group)
        elif skill_name == "dash":
            self._dash_start(player, enemies, conf, particles_group)

        return hits

    def update(self, dt, player, enemies):
        hits = []
        if self.dash_state is not None:
            hits = self._dash_update(dt, player, enemies)
        return hits

    def _vine_whip(self, player, enemies, conf, particles_group) -> list[tuple]:
        hits = []
        facing = player.facing_direction
        for enemy in enemies:
            if not enemy.is_alive:
                continue
            diff = enemy.pos - player.pos
            dist = diff.length()
            if dist > conf["range"]:
                continue
            if dist > 0:
                angle = math.acos(max(-1, min(1, facing.dot(diff.normalize()))))
                if angle > math.pi / 4:
                    continue
            damage = int(player.attack * conf["damage_mult"])
            actual = enemy.take_damage(damage)
            hits.append((enemy, actual, False))
        vis = SkillVisual(player.pos + facing * 30, "whip", conf["range"], 0.3, (34, 180, 34))
        particles_group.add(vis)
        return hits

    def _rock_throw(self, player, conf, projectile_group):
        mouse_pos = pygame.mouse.get_pos()
        from systems.map_manager import Camera
        offset = pygame.math.Vector2(0, 0)
        direction = player.facing_direction
        damage = int(player.attack * conf["damage_mult"])
        lifetime = conf["range"] / max(1, conf["speed"] * 60)
        proj = Projectile(player.pos, direction, conf["speed"], damage, lifetime, BROWN, size=10)
        projectile_group.add(proj)

    def _jungle_roar(self, player, enemies, conf, particles_group) -> list[tuple]:
        hits = []
        for enemy in enemies:
            if not enemy.is_alive:
                continue
            dist = (enemy.pos - player.pos).length()
            if dist > conf["radius"]:
                continue
            damage = int(player.attack * conf["damage_mult"])
            actual = enemy.take_damage(damage)
            enemy.state = "hurt"
            enemy.state_timer = conf["stun_duration"]
            enemy.vel = pygame.math.Vector2(0, 0)
            hits.append((enemy, actual, False))
        vis = SkillVisual(player.pos, "roar", conf["radius"], 0.5, GOLDEN)
        particles_group.add(vis)
        return hits

    def _dash_start(self, player, enemies, conf, particles_group):
        direction = player.facing_direction.copy()
        if direction.length_squared() == 0:
            direction = pygame.math.Vector2(1, 0)
        self.dash_state = {
            "start_pos": player.pos.copy(),
            "direction": direction.normalize(),
            "distance": conf["distance"],
            "duration": conf["duration"],
            "timer": conf["duration"],
            "damage_mult": conf["damage_mult"],
            "hit_enemies": set(),
            "particles_group": particles_group,
            "trail_interval": conf["duration"] / 4,
            "trail_timer": 0,
        }
        player.is_invincible = True
        player.invincibility_timer = conf["duration"] + 0.1

    def _dash_update(self, dt, player, enemies) -> list[tuple]:
        ds = self.dash_state
        ds["timer"] -= dt
        hits = []

        progress = 1.0 - (ds["timer"] / ds["duration"])
        target = ds["start_pos"] + ds["direction"] * ds["distance"] * progress
        player.pos = target.copy()

        ds["trail_timer"] += dt
        if ds["trail_timer"] >= ds["trail_interval"]:
            ds["trail_timer"] = 0
            trail = DashTrail(player.pos, player.image, 80)
            ds["particles_group"].add(trail)

        for enemy in enemies:
            if not enemy.is_alive:
                continue
            if id(enemy) in ds["hit_enemies"]:
                continue
            dist = (enemy.pos - player.pos).length()
            if dist < 40:
                damage = int(player.attack * ds["damage_mult"])
                actual = enemy.take_damage(damage)
                ds["hit_enemies"].add(id(enemy))
                hits.append((enemy, actual, False))

        if ds["timer"] <= 0:
            self.dash_state = None

        return hits
