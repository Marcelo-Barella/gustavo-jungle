import sys
import random
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, MAP_WIDTH, MAP_HEIGHT
from assets.asset_generator import AssetGenerator
from entities.player import Player
from systems.map_manager import MapManager, Camera
from systems.combat import CombatSystem, DamageText
from systems.leveling import LevelingSystem
from systems.spawner import WaveSpawner
from systems.skills import SkillSystem
from systems.powerups import PowerupSystem
from systems.particles import ParticleSystem
from systems.status_effects import StatusEffectManager
from entities.enemy import Parrot, PoisonFrog, Snake
from entities.projectile import Projectile
from ui.hud import HUD


SKILL_KEYS = {
    pygame.K_1: "vine_whip",
    pygame.K_2: "rock_throw",
    pygame.K_3: "jungle_roar",
    pygame.K_4: "dash",
}


class Game:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Gustavo in the Jungle")
        self.clock = pygame.time.Clock()

        self.asset_gen = AssetGenerator()
        self.map_manager = MapManager(self.asset_gen)
        self.camera = Camera()

        spawn = (MAP_WIDTH // 2, MAP_HEIGHT // 2)
        self.player = Player(spawn, self.asset_gen)
        self.player.unlocked_skills = ["vine_whip", "rock_throw", "jungle_roar", "dash"]

        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.xp_orbs = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.powerup_drops = pygame.sprite.Group()
        self.damage_texts = pygame.sprite.Group()

        self.all_sprites.add(self.player)

        self.combat_system = CombatSystem()
        self.leveling_system = LevelingSystem()
        self.wave_spawner = WaveSpawner()
        self.skill_system = SkillSystem()
        self.powerup_system = PowerupSystem()
        self.particle_system = ParticleSystem()
        self.status_effect_manager = StatusEffectManager()

        self.hud = HUD()
        self.game_state = "playing"
        self.running = True
        self.xp_multiplier = 1.0

        self.wave_spawner.start()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)
            self.handle_events()
            if self.game_state == "playing":
                self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if self.game_state == "playing":
                    skill_name = SKILL_KEYS.get(event.key)
                    if skill_name:
                        hits = self.skill_system.use_skill(
                            skill_name, self.player, self.enemies,
                            self.projectiles, self.particles, self.asset_gen
                        )
                        self._spawn_damage_texts(hits)

        if self.game_state == "playing":
            keys = pygame.key.get_pressed()
            mouse_pos = pygame.mouse.get_pos()
            self.player.handle_input(keys, mouse_pos, self.camera.get_offset())

    def update(self, dt: float):
        self.wave_spawner.update(dt, self.player, self.enemies, self.asset_gen)

        melee_hits = self.combat_system.process_player_attack(self.player, self.enemies, dt)
        self._spawn_damage_texts(melee_hits)

        enemy_damages = self.combat_system.process_enemy_attacks(self.enemies, self.player, dt)
        for dmg in enemy_damages:
            dt_sprite = DamageText(self.player.pos.copy(), dmg, False)
            self.damage_texts.add(dt_sprite)

        player_projectiles = pygame.sprite.Group(
            *[p for p in self.projectiles if not getattr(p, '_from_enemy', False)]
        )
        proj_hits = self.combat_system.check_projectile_hits(player_projectiles, self.enemies)
        self._spawn_damage_texts(proj_hits)

        self._check_enemy_projectile_hits()

        dash_hits = self.skill_system.update(dt, self.player, self.enemies)
        self._spawn_damage_texts(dash_hits)

        self.player.update(dt)
        self.camera.update(self.player.pos)

        for enemy in self.enemies:
            enemy.update(dt, self.player.pos)
            if isinstance(enemy, Parrot) and enemy.pending_projectile is not None:
                pd = enemy.pending_projectile
                proj = Projectile(
                    pd["pos"], pd["direction"], pd["speed"],
                    pd["damage"], pd["lifetime"], pd["color"], pd["size"],
                )
                proj._from_enemy = True
                self.projectiles.add(proj)
                enemy.pending_projectile = None

        self._handle_group_aggro()
        self._handle_contact_effects(dt)

        for proj in self.projectiles:
            proj.update(dt)

        for orb in list(self.xp_orbs):
            orb.update(dt, self.player.pos)
            if orb.collected:
                xp_amount = int(orb.value * self.xp_multiplier)
                self.leveling_system.total_xp_earned += xp_amount
                leveled = self.player.gain_xp(xp_amount)
                orb.kill()
                if leveled:
                    self._auto_level_up()

        for p in self.particles:
            p.update(dt)

        for pu in list(self.powerup_drops):
            pu.update(dt)
            dist = (pu.pos - self.player.pos).length()
            if dist < 25:
                self.powerup_system.activate(pu.kind, self.player)
                pu.kill()

        for dt_sprite in self.damage_texts:
            dt_sprite.update(dt)

        all_entities = [self.player] + list(self.enemies)
        self.status_effect_manager.update(dt, all_entities)

        dead_enemies = [e for e in self.enemies if not e.is_alive]
        for enemy in dead_enemies:
            self.status_effect_manager.clear(enemy)
            self.leveling_system.on_enemy_killed(enemy, self.player, self.xp_orbs, self.asset_gen)
            self.powerup_system.try_drop(enemy.pos, self.asset_gen, self.powerup_drops)
            self.enemies.remove(enemy)

        self.xp_multiplier = self.powerup_system.update(dt, self.player)
        if self.xp_multiplier < 1.0:
            self.xp_multiplier = 1.0

        if self.player.hp <= 0:
            self.game_state = "game_over"

    def _spawn_damage_texts(self, hits: list[tuple]):
        for hit in hits:
            enemy, damage, is_crit = hit
            dt_sprite = DamageText(enemy.pos.copy(), damage, is_crit)
            self.damage_texts.add(dt_sprite)

    def _handle_group_aggro(self):
        aware_positions = []
        for enemy in self.enemies:
            if not enemy.is_alive:
                continue
            if enemy._aware_of_player:
                aware_positions.append(enemy.pos)
        for enemy in self.enemies:
            if not enemy.is_alive or enemy._aware_of_player:
                continue
            if not enemy.enable_group_aggro:
                continue
            for ap in aware_positions:
                if (enemy.pos - ap).length() <= 150:
                    enemy.notify_aggro()
                    break

    def _handle_contact_effects(self, dt: float):
        for enemy in self.enemies:
            if not enemy.is_alive:
                continue
            dist = (enemy.pos - self.player.pos).length()
            if isinstance(enemy, Snake) and enemy.state == "bite" and dist <= enemy.attack_range + 10:
                self.status_effect_manager.apply(
                    self.player, "poison", enemy.poison_duration, enemy.poison_dps, source=enemy,
                )
            elif isinstance(enemy, PoisonFrog) and enemy.contact_cooldown > 0.9 and dist <= enemy.attack_range + 10:
                self.status_effect_manager.apply(
                    self.player, "poison", enemy.poison_duration, enemy.poison_dps, source=enemy,
                )

    def _check_enemy_projectile_hits(self):
        hits = []
        for proj in list(self.projectiles):
            if not hasattr(proj, '_from_enemy'):
                continue
            dist = (proj.pos - self.player.pos).length()
            if dist < 20:
                actual = self.player.take_damage(proj.damage)
                if actual > 0:
                    dt_sprite = DamageText(self.player.pos.copy(), actual, False)
                    self.damage_texts.add(dt_sprite)
                proj.kill()
        return hits

    def _auto_level_up(self):
        stat = random.choice(["hp", "attack", "defense", "speed", "luck"])
        if stat == "hp":
            self.player._base_hp += 10
        elif stat == "attack":
            self.player._base_attack += 2
        elif stat == "defense":
            self.player._base_defense += 1
        elif stat == "speed":
            self.player._base_speed += 0.2
        elif stat == "luck":
            self.player._base_luck += 2
        self.player._recalc_stats()

    def draw(self):
        self.screen.fill((0, 0, 0))
        offset = self.camera.get_offset()
        self.map_manager.draw(self.screen, offset)

        sprites_to_draw = []
        sprites_to_draw.append(self.player)
        for e in self.enemies:
            sprites_to_draw.append(e)
        for p in self.projectiles:
            sprites_to_draw.append(p)
        for o in self.xp_orbs:
            sprites_to_draw.append(o)
        for pu in self.powerup_drops:
            sprites_to_draw.append(pu)

        sprites_to_draw.sort(key=lambda s: s.pos.y if hasattr(s, 'pos') else s.rect.centery)

        for sprite in sprites_to_draw:
            if hasattr(sprite, 'draw'):
                sprite.draw(self.screen, offset)

        for e in self.enemies:
            if e.is_alive:
                self.status_effect_manager.draw_effects(self.screen, e, offset)
        self.status_effect_manager.draw_effects(self.screen, self.player, offset)

        for p in self.particles:
            if hasattr(p, 'draw'):
                p.draw(self.screen, offset)
            else:
                self.screen.blit(p.image,
                                 (p.rect.centerx - offset[0], p.rect.centery - offset[1]))

        for dt_sprite in self.damage_texts:
            if hasattr(dt_sprite, 'draw'):
                dt_sprite.draw(self.screen, offset)

        self.hud.draw(self.screen, self.player, self.wave_spawner, self.powerup_system)

        if self.game_state == "game_over":
            self._draw_game_over()

        pygame.display.flip()

    def _draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        font = pygame.font.SysFont(None, 64)
        text = font.render("GAME OVER", True, (220, 20, 20))
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2,
                                SCREEN_HEIGHT // 2 - text.get_height() // 2))
        stats = self.leveling_system.get_stats()
        small = pygame.font.SysFont(None, 28)
        info = small.render(
            f"Level {self.player.level} | Killed {stats['enemies_killed']} | "
            f"Wave {self.wave_spawner.current_wave_number}",
            True, (255, 255, 255))
        self.screen.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2,
                                SCREEN_HEIGHT // 2 + 40))


if __name__ == "__main__":
    game = Game()
    game.run()
