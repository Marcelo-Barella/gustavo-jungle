import math
import pygame
from settings import (
    VINE_WHIP, ROCK_THROW, JUNGLE_ROAR, DASH_ATTACK,
    NATURE_SHIELD, SUMMON_VINES,
    BROWN, GOLDEN, SCREEN_WIDTH, SCREEN_HEIGHT,
)
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


class NatureShieldVisual(pygame.sprite.Sprite):

    def __init__(self, player, duration):
        super().__init__()
        self.player = player
        self.timer = duration
        self.duration = duration
        self.pos = player.pos.copy()
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def update(self, dt):
        self.timer -= dt
        self.pos = self.player.pos.copy()
        if self.timer <= 0:
            self.kill()

    def draw(self, surface: pygame.Surface, camera_offset: tuple[float, float]):
        alpha = max(30, int(100 * (self.timer / self.duration)))
        pulse = 1.0 + 0.1 * math.sin(self.timer * 6)
        cx = int(self.pos.x - camera_offset[0])
        cy = int(self.pos.y - camera_offset[1])
        r = int(28 * pulse)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (60, 220, 60, alpha), (r, r), r, 3)
        pygame.draw.circle(s, (120, 255, 120, alpha // 3), (r, r), r)
        surface.blit(s, (cx - r, cy - r))


class VineTrapZone(pygame.sprite.Sprite):

    def __init__(self, pos, conf):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.radius = conf["radius"]
        self.damage_per_sec = conf["damage_per_sec"]
        self.slow_factor = conf["slow_factor"]
        self.timer = conf["duration"]
        self.duration = conf["duration"]
        self.damage_tick = 0.0
        self.color = (34, 180, 34)
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            self.kill()

    def process_enemies(self, dt, enemies):
        if self.timer <= 0:
            return []
        self.damage_tick += dt
        hits = []
        if self.damage_tick >= 1.0:
            self.damage_tick -= 1.0
            for enemy in enemies:
                if not enemy.is_alive:
                    continue
                dist = (enemy.pos - self.pos).length()
                if dist <= self.radius:
                    actual = enemy.take_damage(self.damage_per_sec)
                    hits.append((enemy, actual, False))
        for enemy in enemies:
            if not enemy.is_alive:
                continue
            dist = (enemy.pos - self.pos).length()
            if dist <= self.radius:
                enemy.vel *= self.slow_factor
        return hits

    def draw(self, surface: pygame.Surface, camera_offset: tuple[float, float]):
        alpha = max(30, int(120 * (self.timer / self.duration)))
        cx = int(self.pos.x - camera_offset[0])
        cy = int(self.pos.y - camera_offset[1])
        r = int(self.radius)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha // 2), (r, r), r)
        pygame.draw.circle(s, (*self.color, min(255, alpha + 50)), (r, r), r, 2)
        tendril_count = 8
        for i in range(tendril_count):
            angle = (2 * math.pi / tendril_count) * i + self.timer * 0.5
            ex = r + int(math.cos(angle) * r * 0.7)
            ey = r + int(math.sin(angle) * r * 0.7)
            pygame.draw.line(s, (*self.color, min(255, alpha + 30)), (r, r), (ex, ey), 2)
        surface.blit(s, (cx - r, cy - r))


class SkillSystem:

    def __init__(self):
        self.skills = {
            "vine_whip": VINE_WHIP,
            "rock_throw": ROCK_THROW,
            "jungle_roar": JUNGLE_ROAR,
            "dash": DASH_ATTACK,
            "nature_shield": NATURE_SHIELD,
            "summon_vines": SUMMON_VINES,
        }
        self.dash_state = None
        self.vine_traps: list[VineTrapZone] = []

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
        elif skill_name == "nature_shield":
            self._nature_shield(player, conf, particles_group)
        elif skill_name == "summon_vines":
            self._summon_vines(player, conf, particles_group)

        return hits

    def update(self, dt, player, enemies):
        hits = []
        if self.dash_state is not None:
            hits = self._dash_update(dt, player, enemies)
        return hits

    def update_vine_traps(self, dt, enemies):
        hits = []
        for trap in list(self.vine_traps):
            if trap.timer <= 0:
                self.vine_traps.remove(trap)
                continue
            trap_hits = trap.process_enemies(dt, enemies)
            hits.extend(trap_hits)
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

    def _nature_shield(self, player, conf, particles_group):
        player.shield_timer = conf["duration"]
        player.damage_reduction = conf["damage_reduction"]
        vis = NatureShieldVisual(player, conf["duration"])
        particles_group.add(vis)

    def _summon_vines(self, player, conf, particles_group):
        mouse_pos = pygame.mouse.get_pos()
        camera_offset = (
            player.pos.x - SCREEN_WIDTH / 2,
            player.pos.y - SCREEN_HEIGHT / 2,
        )
        world_pos = (
            mouse_pos[0] + camera_offset[0],
            mouse_pos[1] + camera_offset[1],
        )
        trap = VineTrapZone(world_pos, conf)
        self.vine_traps.append(trap)
        particles_group.add(trap)
