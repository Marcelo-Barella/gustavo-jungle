import sys
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, MAP_WIDTH, MAP_HEIGHT
from assets.asset_generator import AssetGenerator
from entities.player import Player
from systems.map_manager import MapManager, Camera
from ui.hud import HUD


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

        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.xp_orbs = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.powerup_drops = pygame.sprite.Group()

        self.all_sprites.add(self.player)

        self.hud = HUD()
        self.game_state = "playing"
        self.running = True

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
            keys = pygame.key.get_pressed()
            mouse_pos = pygame.mouse.get_pos()
            self.player.handle_input(keys, mouse_pos, self.camera.get_offset())

    def update(self, dt: float):
        self.player.update(dt)
        self.camera.update(self.player.pos)

        for enemy in self.enemies:
            enemy.update(dt, self.player.pos)
        for proj in self.projectiles:
            proj.update(dt)
        for orb in self.xp_orbs:
            orb.update(dt)
        for p in self.particles:
            p.update(dt)
        for pu in self.powerup_drops:
            pu.update(dt)

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

        for p in self.particles:
            if hasattr(p, 'draw'):
                p.draw(self.screen, offset)
            else:
                self.screen.blit(p.image,
                                 (p.rect.centerx - offset[0], p.rect.centery - offset[1]))

        self.hud.draw(self.screen, self.player)
        pygame.display.flip()


if __name__ == "__main__":
    game = Game()
    game.run()
