import sys
import random
import time
import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, MAP_WIDTH, MAP_HEIGHT,
    DIFFICULTY_MULTIPLIERS, WHITE,
)
from assets.asset_generator import AssetGenerator
from entities.player import Player
from systems.map_manager import MapManager, Camera
from systems.combat import CombatSystem, DamageText
from systems.leveling import LevelingSystem
from systems.spawner import WaveSpawner
from systems.skills import SkillSystem
from systems.powerups import PowerupSystem
from systems.particles import ParticleSystem
from systems.config_manager import ConfigManager
from systems.high_scores import HighScoreManager
from ui.hud import HUD
from ui.settings_screen import SettingsScreen
from ui.high_scores_screen import HighScoresScreen


SKILL_KEYS = {
    pygame.K_1: "vine_whip",
    pygame.K_2: "rock_throw",
    pygame.K_3: "jungle_roar",
    pygame.K_4: "dash",
}


class Game:

    def __init__(self):
        pygame.init()
        self.config_manager = ConfigManager()
        self.high_score_manager = HighScoreManager()

        flags = 0
        if self.config_manager.get("fullscreen"):
            flags = pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        pygame.display.set_caption("Gustavo in the Jungle")
        self.clock = pygame.time.Clock()

        self.asset_gen = AssetGenerator()

        self.settings_screen = SettingsScreen(self.config_manager)
        self.high_scores_screen = HighScoresScreen(self.high_score_manager)

        self.game_state = "main_menu"
        self.previous_state = None
        self.running = True
        self.score_submitted = False

        self._fps_font = None

        self._init_game_session()

    def _init_game_session(self):
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

        self.hud = HUD()
        self.xp_multiplier = 1.0
        self.score_submitted = False

    def _get_difficulty_mults(self) -> dict:
        diff = self.config_manager.get("difficulty")
        return DIFFICULTY_MULTIPLIERS.get(diff, DIFFICULTY_MULTIPLIERS["normal"])

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
                continue

            if self.game_state == "main_menu":
                self._handle_main_menu_event(event)
            elif self.game_state == "playing":
                self._handle_playing_event(event)
            elif self.game_state == "paused":
                self._handle_paused_event(event)
            elif self.game_state == "game_over":
                self._handle_game_over_event(event)
            elif self.game_state == "settings":
                result = self.settings_screen.handle_event(event)
                if result == "back":
                    self.game_state = self.previous_state or "main_menu"
            elif self.game_state == "high_scores":
                result = self.high_scores_screen.handle_event(event)
                if result == "back":
                    self.game_state = "main_menu"
                    self.high_scores_screen.highlight_rank = None

        if self.game_state == "playing":
            keys = pygame.key.get_pressed()
            mouse_pos = pygame.mouse.get_pos()
            bindings = self.config_manager.get("key_bindings")
            dx, dy = 0.0, 0.0
            if keys[bindings.get("move_up", pygame.K_w)]:
                dy -= 1
            if keys[bindings.get("move_down", pygame.K_s)]:
                dy += 1
            if keys[bindings.get("move_left", pygame.K_a)]:
                dx -= 1
            if keys[bindings.get("move_right", pygame.K_d)]:
                dx += 1
            self.player.vel = pygame.math.Vector2(dx, dy)
            if self.player.vel.length_squared() > 0:
                self.player.vel = self.player.vel.normalize() * self.player.speed
            world_mouse = pygame.math.Vector2(mouse_pos) + pygame.math.Vector2(self.camera.get_offset())
            diff = world_mouse - self.player.pos
            if diff.length_squared() > 0:
                self.player.facing_direction = diff.normalize()

    def _handle_main_menu_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_1:
                self._init_game_session()
                self.game_state = "playing"
                self.wave_spawner.start()
            elif event.key == pygame.K_2:
                self.previous_state = "main_menu"
                self.game_state = "settings"
            elif event.key == pygame.K_3:
                self.game_state = "high_scores"
            elif event.key == pygame.K_ESCAPE:
                self.running = False

    def _handle_playing_event(self, event):
        if event.type == pygame.KEYDOWN:
            pause_key = self.config_manager.get("key_bindings").get("pause", pygame.K_ESCAPE)
            if event.key == pause_key:
                self.game_state = "paused"
                return
            skill_name = SKILL_KEYS.get(event.key)
            if skill_name:
                hits = self.skill_system.use_skill(
                    skill_name, self.player, self.enemies,
                    self.projectiles, self.particles, self.asset_gen
                )
                self._spawn_damage_texts(hits)

    def _handle_paused_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_1:
                self.game_state = "playing"
            elif event.key == pygame.K_2:
                self._init_game_session()
                self.game_state = "playing"
                self.wave_spawner.start()
            elif event.key == pygame.K_3:
                self.previous_state = "paused"
                self.game_state = "settings"
            elif event.key == pygame.K_4:
                self.game_state = "main_menu"

    def _handle_game_over_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1 or event.key == pygame.K_RETURN:
                self._init_game_session()
                self.game_state = "playing"
                self.wave_spawner.start()
            elif event.key == pygame.K_2:
                self.game_state = "high_scores"
            elif event.key == pygame.K_3:
                self.game_state = "main_menu"

    def update(self, dt: float):
        self.wave_spawner.update(dt, self.player, self.enemies, self.asset_gen)

        mults = self._get_difficulty_mults()
        for enemy in self.enemies:
            if not hasattr(enemy, "_difficulty_applied"):
                enemy.max_hp = int(enemy.max_hp * mults["enemy_hp"])
                enemy.hp = enemy.max_hp
                enemy.attack = int(enemy.attack * mults["enemy_attack"])
                enemy._difficulty_applied = True

        melee_hits = self.combat_system.process_player_attack(self.player, self.enemies, dt)
        self._spawn_damage_texts(melee_hits)

        enemy_damages = self.combat_system.process_enemy_attacks(self.enemies, self.player, dt)
        for dmg in enemy_damages:
            dt_sprite = DamageText(self.player.pos.copy(), dmg, False)
            self.damage_texts.add(dt_sprite)

        proj_hits = self.combat_system.check_projectile_hits(self.projectiles, self.enemies)
        self._spawn_damage_texts(proj_hits)

        dash_hits = self.skill_system.update(dt, self.player, self.enemies)
        self._spawn_damage_texts(dash_hits)

        self.player.update(dt)
        self.camera.update(self.player.pos)

        for enemy in self.enemies:
            enemy.update(dt, self.player.pos)

        for proj in self.projectiles:
            proj.update(dt)

        xp_mult = mults["xp_gain"]
        for orb in list(self.xp_orbs):
            orb.update(dt, self.player.pos)
            if orb.collected:
                xp_amount = int(orb.value * self.xp_multiplier * xp_mult)
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

        dead_enemies = [e for e in self.enemies if not e.is_alive]
        for enemy in dead_enemies:
            self.leveling_system.on_enemy_killed(enemy, self.player, self.xp_orbs, self.asset_gen)
            self.powerup_system.try_drop(enemy.pos, self.asset_gen, self.powerup_drops)
            self.enemies.remove(enemy)

        self.xp_multiplier = self.powerup_system.update(dt, self.player)
        if self.xp_multiplier < 1.0:
            self.xp_multiplier = 1.0

        if self.player.hp <= 0:
            self.game_state = "game_over"
            self._submit_score()

    def _submit_score(self):
        if self.score_submitted:
            return
        self.score_submitted = True
        stats = self.leveling_system.get_stats()
        score = HighScoreManager.calculate_score(
            enemies_killed=stats["enemies_killed"],
            waves_completed=self.wave_spawner.current_wave_number,
            level=self.player.level,
            time_survived=stats["time_survived"],
        )
        entry = {
            "name": "Player",
            "score": score,
            "level": self.player.level,
            "waves": self.wave_spawner.current_wave_number,
            "enemies_killed": stats["enemies_killed"],
            "time": stats["time_survived"],
            "difficulty": self.config_manager.get("difficulty"),
        }
        rank = self.high_score_manager.add_score(entry)
        self.high_scores_screen.highlight_rank = rank

    def _spawn_damage_texts(self, hits: list[tuple]):
        if not self.config_manager.get("show_damage_numbers"):
            return
        for hit in hits:
            enemy, damage, is_crit = hit
            dt_sprite = DamageText(enemy.pos.copy(), damage, is_crit)
            self.damage_texts.add(dt_sprite)

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

        if self.game_state == "main_menu":
            self._draw_main_menu()
        elif self.game_state in ("playing", "paused", "game_over"):
            self._draw_game_world()
            self.hud.draw(self.screen, self.player, self.wave_spawner, self.powerup_system)
            if self.game_state == "paused":
                self._draw_pause_menu()
            elif self.game_state == "game_over":
                self._draw_game_over()
        elif self.game_state == "settings":
            if self.previous_state in ("playing", "paused"):
                self._draw_game_world()
            self.settings_screen.draw(self.screen)
        elif self.game_state == "high_scores":
            self.high_scores_screen.draw(self.screen)

        if self.config_manager.get("show_fps"):
            self._draw_fps()

        pygame.display.flip()

    def _draw_game_world(self):
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

    def _draw_main_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 30, 15, 255))
        self.screen.blit(overlay, (0, 0))

        title_font = pygame.font.SysFont(None, 64)
        title = title_font.render("Gustavo in the Jungle", True, (80, 200, 80))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 160))

        menu_font = pygame.font.SysFont(None, 32)
        items = [
            "[1 / Enter] New Game",
            "[2] Settings",
            "[3] High Scores",
            "[Esc] Quit",
        ]
        y = 320
        for item in items:
            txt = menu_font.render(item, True, (200, 200, 200))
            self.screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, y))
            y += 44

    def _draw_pause_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        title_font = pygame.font.SysFont(None, 48)
        title = title_font.render("Paused", True, (230, 230, 230))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 220))

        menu_font = pygame.font.SysFont(None, 28)
        items = [
            "[1 / Esc] Resume",
            "[2] Restart",
            "[3] Settings",
            "[4] Quit to Menu",
        ]
        y = 310
        for item in items:
            txt = menu_font.render(item, True, (200, 200, 200))
            self.screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, y))
            y += 36

    def _draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        font = pygame.font.SysFont(None, 64)
        text = font.render("GAME OVER", True, (220, 20, 20))
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2,
                                SCREEN_HEIGHT // 2 - 80))

        stats = self.leveling_system.get_stats()
        small = pygame.font.SysFont(None, 28)

        score = HighScoreManager.calculate_score(
            enemies_killed=stats["enemies_killed"],
            waves_completed=self.wave_spawner.current_wave_number,
            level=self.player.level,
            time_survived=stats["time_survived"],
        )
        score_txt = small.render(f"Score: {score}", True, (255, 215, 0))
        self.screen.blit(score_txt, (SCREEN_WIDTH // 2 - score_txt.get_width() // 2,
                                     SCREEN_HEIGHT // 2 - 30))

        info = small.render(
            f"Level {self.player.level} | Killed {stats['enemies_killed']} | "
            f"Wave {self.wave_spawner.current_wave_number}",
            True, (255, 255, 255))
        self.screen.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2,
                                SCREEN_HEIGHT // 2 + 4))

        if self.high_scores_screen.highlight_rank:
            rank_txt = small.render(
                f"New High Score! Rank #{self.high_scores_screen.highlight_rank}",
                True, (255, 215, 0))
            self.screen.blit(rank_txt, (SCREEN_WIDTH // 2 - rank_txt.get_width() // 2,
                                        SCREEN_HEIGHT // 2 + 38))

        menu_font = pygame.font.SysFont(None, 24)
        options = [
            "[1 / Enter] Try Again",
            "[2] High Scores",
            "[3] Main Menu",
        ]
        y = SCREEN_HEIGHT // 2 + 80
        for opt in options:
            txt = menu_font.render(opt, True, (180, 180, 180))
            self.screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, y))
            y += 28

    def _draw_fps(self):
        if self._fps_font is None:
            self._fps_font = pygame.font.SysFont(None, 22)
        fps_val = self.clock.get_fps()
        fps_txt = self._fps_font.render(f"FPS: {fps_val:.0f}", True, WHITE)
        self.screen.blit(fps_txt, (SCREEN_WIDTH - fps_txt.get_width() - 10, 10))


if __name__ == "__main__":
    game = Game()
    game.run()
