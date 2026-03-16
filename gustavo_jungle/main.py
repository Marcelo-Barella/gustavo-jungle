import sys
import time
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
from ui.hud import HUD

try:
    from ui.menus import MainMenu, PauseMenu, GameOverScreen
except ImportError:
    class MainMenu:
        def __init__(self): pass
        def draw(self, surface): pass
        def handle_event(self, event): return None

    class PauseMenu:
        def __init__(self): pass
        def draw(self, surface): pass
        def handle_event(self, event): return None

    class GameOverScreen:
        def __init__(self): pass
        def draw(self, surface, stats_dict=None): pass
        def handle_event(self, event): return None

try:
    from ui.level_up_screen import LevelUpScreen
except ImportError:
    class LevelUpScreen:
        def __init__(self):
            self.active = False
        def show(self, player, on_choose_callback=None): self.active = True
        def handle_event(self, event): self.active = False; return False
        def draw(self, surface): pass
        def update(self, dt): pass
        def apply_choice(self, player, choice): pass

try:
    from ui.settings_screen import SettingsScreen
except ImportError:
    class SettingsScreen:
        def __init__(self):
            self.active = False
        def show(self): self.active = True
        def hide(self): self.active = False
        def handle_event(self, event): return None
        def update(self, dt): pass
        def draw(self, surface): pass
        def get_volumes(self): return {"master": 1.0, "sfx": 1.0, "music": 1.0}
        def is_fullscreen(self): return False

try:
    from ui.minimap import Minimap
except ImportError:
    class Minimap:
        def __init__(self, **kwargs): pass
        def generate_terrain_surface(self, grid): pass
        def draw(self, surface, player_pos, enemies, camera_offset): pass
        def update(self, dt): pass

try:
    from ui.transitions import FadeTransition
except ImportError:
    class FadeTransition:
        def __init__(self):
            self.is_done = True
        def fade_in(self): self.is_done = True
        def fade_out(self): self.is_done = True
        def update(self, dt): pass
        def draw(self, surface): pass

try:
    from ui.high_scores_screen import HighScoresScreen
except ImportError:
    class HighScoresScreen:
        def __init__(self, save_manager=None):
            self.active = False
        def show(self, current_score=None): self.active = True
        def handle_event(self, event): return None
        def draw(self, surface): pass

try:
    from systems.sound_manager import SoundManager
except ImportError:
    class SoundManager:
        def __init__(self): pass
        def play(self, sound_name): pass
        def set_master_volume(self, vol): pass
        def set_sfx_volume(self, vol): pass
        def set_music_volume(self, vol): pass
        def play_ambient(self): pass
        def stop_ambient(self): pass
        def play_boss_music(self): pass
        def stop_all(self): pass

try:
    from systems.save_manager import SaveManager
except ImportError:
    class SaveManager:
        def __init__(self): pass
        def compute_score(self, level, waves, kills, time_survived): return level * 100 + waves * 50 + kills * 10
        def save_high_score(self, score_data): pass
        def get_high_scores(self): return []
        def save_settings(self, settings): pass
        def load_settings(self): return {}


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

        self.sound_manager = SoundManager()
        self.save_manager = SaveManager()

        saved_settings = self.save_manager.load_settings()
        if saved_settings:
            self.sound_manager.set_master_volume(saved_settings.get("master", 1.0))
            self.sound_manager.set_sfx_volume(saved_settings.get("sfx", 1.0))
            self.sound_manager.set_music_volume(saved_settings.get("music", 1.0))

        self.main_menu = MainMenu()
        self.pause_menu = PauseMenu()
        self.game_over_screen = GameOverScreen()
        self.level_up_screen = LevelUpScreen()
        self.settings_screen = SettingsScreen()
        self.high_scores_screen = HighScoresScreen(self.save_manager)
        self.minimap = Minimap(map_width=MAP_WIDTH, map_height=MAP_HEIGHT)
        self.minimap.generate_terrain_surface(self.map_manager.grid)
        self.transition = FadeTransition()

        self._init_groups()

        spawn = (MAP_WIDTH // 2, MAP_HEIGHT // 2)
        self.player = Player(spawn, self.asset_gen)
        self.player.unlocked_skills = ["vine_whip"]
        self.all_sprites.add(self.player)

        self.combat_system = CombatSystem()
        self.leveling_system = LevelingSystem()
        self.wave_spawner = WaveSpawner()
        self.skill_system = SkillSystem()
        self.powerup_system = PowerupSystem()
        self.particle_system = ParticleSystem()
        self.hud = HUD()

        self.game_state = "main_menu"
        self._previous_state = "main_menu"
        self.running = True
        self.xp_multiplier = 1.0
        self._game_over_stats = None

    def _init_groups(self):
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.xp_orbs = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.powerup_drops = pygame.sprite.Group()
        self.damage_texts = pygame.sprite.Group()

    def _start_new_game(self):
        self._init_groups()

        spawn = (MAP_WIDTH // 2, MAP_HEIGHT // 2)
        self.player = Player(spawn, self.asset_gen)
        self.player.unlocked_skills = ["vine_whip"]
        self.all_sprites.add(self.player)

        self.combat_system = CombatSystem()
        self.leveling_system = LevelingSystem()
        self.wave_spawner = WaveSpawner()
        self.skill_system = SkillSystem()
        self.powerup_system = PowerupSystem()
        self.xp_multiplier = 1.0
        self._game_over_stats = None

        self.wave_spawner.start()
        self.game_state = "playing"

        self.transition.fade_in()
        self.sound_manager.play_ambient()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if self.game_state == "main_menu":
                self._handle_main_menu_event(event)
            elif self.game_state in ("settings_from_menu", "settings_from_pause"):
                self._handle_settings_event(event)
            elif self.game_state == "playing":
                self._handle_playing_event(event)
            elif self.game_state == "paused":
                self._handle_paused_event(event)
            elif self.game_state == "level_up":
                self._handle_level_up_event(event)
            elif self.game_state == "game_over":
                self._handle_game_over_event(event)
            elif self.game_state == "high_scores":
                self._handle_high_scores_event(event)

        if self.game_state == "playing":
            keys = pygame.key.get_pressed()
            mouse_pos = pygame.mouse.get_pos()
            self.player.handle_input(keys, mouse_pos, self.camera.get_offset())

    def _handle_main_menu_event(self, event):
        result = self.main_menu.handle_event(event)
        if result == "start":
            self._start_new_game()
        elif result == "settings":
            self._previous_state = "main_menu"
            self.game_state = "settings_from_menu"
            self.settings_screen.show()
        elif result == "quit":
            self.running = False
        elif result == "high_scores":
            self.game_state = "high_scores"
            self.high_scores_screen.show()

    def _handle_settings_event(self, event):
        result = self.settings_screen.handle_event(event)
        if result == "back":
            volumes = self.settings_screen.get_volumes()
            self.sound_manager.set_master_volume(volumes.get("master", 1.0))
            self.sound_manager.set_sfx_volume(volumes.get("sfx", 1.0))
            self.sound_manager.set_music_volume(volumes.get("music", 1.0))
            self.save_manager.save_settings(volumes)
            self.settings_screen.hide()
            if self.game_state == "settings_from_menu":
                self.game_state = "main_menu"
            else:
                self.game_state = "paused"

    def _handle_playing_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game_state = "paused"
                return
            skill_name = SKILL_KEYS.get(event.key)
            if skill_name:
                hits = self.skill_system.use_skill(
                    skill_name, self.player, self.enemies,
                    self.projectiles, self.particles, self.asset_gen
                )
                if hits or skill_name in self.player.unlocked_skills:
                    sound_key = f"skill_{skill_name}"
                    self.sound_manager.play(sound_key)
                self._spawn_damage_texts(hits)

    def _handle_paused_event(self, event):
        result = self.pause_menu.handle_event(event)
        if result == "resume":
            self.game_state = "playing"
        elif result == "settings":
            self._previous_state = "paused"
            self.game_state = "settings_from_pause"
            self.settings_screen.show()
        elif result == "quit_to_menu":
            self.sound_manager.stop_all()
            self.game_state = "main_menu"

    def _handle_level_up_event(self, event):
        result = self.level_up_screen.handle_event(event)
        if not self.level_up_screen.active:
            self.game_state = "playing"

    def _handle_game_over_event(self, event):
        result = self.game_over_screen.handle_event(event)
        if result == "restart":
            self._start_new_game()
        elif result == "main_menu":
            self.sound_manager.stop_all()
            self.game_state = "main_menu"

    def _handle_high_scores_event(self, event):
        result = self.high_scores_screen.handle_event(event)
        if result == "back":
            self.game_state = "main_menu"

    def update(self, dt: float):
        self.transition.update(dt)

        if self.game_state == "level_up":
            self.level_up_screen.update(dt)
            return

        if self.game_state in ("settings_from_menu", "settings_from_pause"):
            self.settings_screen.update(dt)
            return

        if self.game_state != "playing":
            return

        self.wave_spawner.update(dt, self.player, self.enemies, self.asset_gen)

        if hasattr(self.wave_spawner, 'is_boss_wave') and self.wave_spawner.is_boss_wave:
            if hasattr(self.wave_spawner, 'boss_active') and self.wave_spawner.boss_active:
                self.sound_manager.play("boss_spawn")

        melee_hits = self.combat_system.process_player_attack(self.player, self.enemies, dt)
        self._spawn_damage_texts(melee_hits)
        for hit in melee_hits:
            enemy, damage, is_crit = hit
            self.sound_manager.play("hit_enemy")
            if hasattr(self.particle_system, 'emit_hit_spark'):
                direction = (enemy.pos - self.player.pos)
                if direction.length_squared() > 0:
                    direction = direction.normalize()
                self.particle_system.emit_hit_spark(enemy.pos, direction, self.particles)

        enemy_damages = self.combat_system.process_enemy_attacks(self.enemies, self.player, dt)
        for dmg in enemy_damages:
            dt_sprite = DamageText(self.player.pos.copy(), dmg, False)
            self.damage_texts.add(dt_sprite)
            self.sound_manager.play("hit_player")
            if hasattr(self.camera, 'shake'):
                self.camera.shake(3, 0.2)

        proj_hits = self.combat_system.check_projectile_hits(self.projectiles, self.enemies)
        self._spawn_damage_texts(proj_hits)
        for hit in proj_hits:
            enemy, damage, is_crit = hit
            self.sound_manager.play("hit_enemy")

        dash_hits = self.skill_system.update(dt, self.player, self.enemies)
        self._spawn_damage_texts(dash_hits)

        self.player.update(dt)
        if hasattr(self.camera, 'shake'):
            self.camera.update(self.player.pos, dt)
        else:
            self.camera.update(self.player.pos)

        for enemy in self.enemies:
            enemy.update(dt, self.player.pos)
            if hasattr(enemy, 'is_boss') and enemy.is_boss:
                if hasattr(enemy, 'try_roar') and hasattr(self.camera, 'shake'):
                    pass

        for proj in self.projectiles:
            proj.update(dt)

        for orb in list(self.xp_orbs):
            orb.update(dt, self.player.pos)
            if orb.collected:
                xp_amount = int(orb.value * self.xp_multiplier)
                self.leveling_system.total_xp_earned += xp_amount
                self.sound_manager.play("xp_pickup")
                leveled = self.player.gain_xp(xp_amount)
                orb.kill()
                if leveled:
                    self._on_level_up()

        for p in self.particles:
            p.update(dt)

        for pu in list(self.powerup_drops):
            pu.update(dt)
            dist = (pu.pos - self.player.pos).length()
            if dist < 25:
                self.powerup_system.activate(pu.kind, self.player)
                self.sound_manager.play("powerup_collect")
                pu.kill()

        for dt_sprite in self.damage_texts:
            dt_sprite.update(dt)

        dead_enemies = [e for e in self.enemies if not e.is_alive]
        for enemy in dead_enemies:
            self.leveling_system.on_enemy_killed(enemy, self.player, self.xp_orbs, self.asset_gen)
            self.powerup_system.try_drop(enemy.pos, self.asset_gen, self.powerup_drops)
            self.sound_manager.play("enemy_death")
            if hasattr(self.particle_system, 'emit_death_burst'):
                color = getattr(enemy, 'color', (200, 50, 50))
                self.particle_system.emit_death_burst(enemy.pos, color, self.particles)
            if hasattr(enemy, 'is_boss') and enemy.is_boss:
                if hasattr(self.camera, 'shake'):
                    self.camera.shake(8, 0.4)
            self.enemies.remove(enemy)

        self.xp_multiplier = self.powerup_system.update(dt, self.player)
        if self.xp_multiplier < 1.0:
            self.xp_multiplier = 1.0

        self.minimap.update(dt)

        if hasattr(self.hud, 'kill_count'):
            self.hud.kill_count = self.leveling_system.total_enemies_killed

        if self.player.hp <= 0:
            self._on_game_over()

    def _on_level_up(self):
        self.sound_manager.play("level_up")
        if hasattr(self.particle_system, 'emit_level_up'):
            self.particle_system.emit_level_up(self.player.pos, self.particles)
        self.level_up_screen.show(self.player, self._on_level_up_choice)
        self.game_state = "level_up"

    def _on_level_up_choice(self, *args):
        self.game_state = "playing"

    def _on_game_over(self):
        self.sound_manager.play("game_over")
        self.sound_manager.stop_ambient()
        stats = self.leveling_system.get_stats()
        score = self.save_manager.compute_score(
            self.player.level,
            self.wave_spawner.current_wave_number,
            stats["enemies_killed"],
            stats["time_survived"],
        )
        score_data = {
            "player_name": "Gustavo",
            "level": self.player.level,
            "waves_survived": self.wave_spawner.current_wave_number,
            "enemies_killed": stats["enemies_killed"],
            "time_survived": stats["time_survived"],
            "total_xp": stats["xp_earned"],
            "score": score,
        }
        self.save_manager.save_high_score(score_data)
        self._game_over_stats = {
            "level": self.player.level,
            "enemies_killed": stats["enemies_killed"],
            "waves": self.wave_spawner.current_wave_number,
            "time_survived": stats["time_survived"],
            "xp_earned": stats["xp_earned"],
            "score": score,
        }
        self.game_state = "game_over"

    def _spawn_damage_texts(self, hits: list[tuple]):
        for hit in hits:
            enemy, damage, is_crit = hit
            dt_sprite = DamageText(enemy.pos.copy(), damage, is_crit)
            self.damage_texts.add(dt_sprite)

    def draw(self):
        self.screen.fill((0, 0, 0))

        if self.game_state == "main_menu":
            self.main_menu.draw(self.screen)
        elif self.game_state == "high_scores":
            self.high_scores_screen.draw(self.screen)
        elif self.game_state in ("playing", "paused", "level_up", "game_over",
                                  "settings_from_pause"):
            self._draw_world()
            self.hud.draw(self.screen, self.player, self.wave_spawner, self.powerup_system)
            if hasattr(self.hud, 'draw_enemy_hp_bars'):
                self.hud.draw_enemy_hp_bars(self.screen, self.enemies, self.camera.get_offset())
            self.minimap.draw(self.screen, self.player.pos, self.enemies, self.camera.get_offset())

            if self.game_state == "paused":
                self.pause_menu.draw(self.screen)
            elif self.game_state == "level_up":
                self.level_up_screen.draw(self.screen)
            elif self.game_state == "game_over":
                self.game_over_screen.draw(self.screen, self._game_over_stats)
            elif self.game_state == "settings_from_pause":
                self.settings_screen.draw(self.screen)
        elif self.game_state == "settings_from_menu":
            self.main_menu.draw(self.screen)
            self.settings_screen.draw(self.screen)

        self.transition.draw(self.screen)
        pygame.display.flip()

    def _draw_world(self):
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

        for p in self.particles:
            if hasattr(p, 'draw'):
                p.draw(self.screen, offset)
            else:
                self.screen.blit(p.image,
                                 (p.rect.centerx - offset[0], p.rect.centery - offset[1]))

        for dt_sprite in self.damage_texts:
            if hasattr(dt_sprite, 'draw'):
                dt_sprite.draw(self.screen, offset)


if __name__ == "__main__":
    game = Game()
    game.run()
