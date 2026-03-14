import random
import math
import pygame
from settings import WAVE_BASE_ENEMIES, WAVE_DELAY, MAP_WIDTH, MAP_HEIGHT
from entities.enemy import Panther, Lion, Snake, Gorilla


class WaveSpawner:

    def __init__(self):
        self.current_wave = 0
        self.wave_timer = 0.0
        self.wave_active = False
        self.enemies_in_wave = 0
        self.waiting = False

    def start(self):
        self.waiting = True
        self.wave_timer = 2.0

    @property
    def current_wave_number(self) -> int:
        return self.current_wave

    def update(self, dt, player, enemy_group, asset_gen):
        if self.waiting:
            self.wave_timer -= dt
            if self.wave_timer <= 0:
                self.waiting = False
                self.spawn_wave(player, enemy_group, asset_gen)
        elif self.wave_active:
            alive = sum(1 for e in enemy_group if e.is_alive)
            if alive == 0:
                self.waiting = True
                self.wave_timer = WAVE_DELAY

    def spawn_wave(self, player, enemy_group, asset_gen):
        self.current_wave += 1
        n = self.current_wave
        to_spawn = []

        panther_count = WAVE_BASE_ENEMIES + n
        for _ in range(panther_count):
            pos = self._edge_pos(player.pos)
            to_spawn.append(Panther(pos, asset_gen))

        lion_count = n // 3 if player.level >= 3 else 0
        for _ in range(lion_count):
            pos = self._edge_pos(player.pos)
            to_spawn.append(Lion(pos, asset_gen))

        snake_count = n // 4 if player.level >= 2 else 0
        for _ in range(snake_count):
            pos = self._edge_pos(player.pos)
            to_spawn.append(Snake(pos, asset_gen))

        gorilla_count = n // 6 if player.level >= 5 else 0
        for _ in range(gorilla_count):
            pos = self._edge_pos(player.pos)
            to_spawn.append(Gorilla(pos, asset_gen))

        for e in to_spawn:
            enemy_group.add(e)

        self.wave_active = True
        self.enemies_in_wave = len(to_spawn)

    @staticmethod
    def _edge_pos(player_pos: pygame.math.Vector2) -> tuple[float, float]:
        margin = 50
        for _ in range(50):
            edge = random.randint(0, 3)
            if edge == 0:
                x = random.uniform(margin, MAP_WIDTH - margin)
                y = margin
            elif edge == 1:
                x = random.uniform(margin, MAP_WIDTH - margin)
                y = MAP_HEIGHT - margin
            elif edge == 2:
                x = margin
                y = random.uniform(margin, MAP_HEIGHT - margin)
            else:
                x = MAP_WIDTH - margin
                y = random.uniform(margin, MAP_HEIGHT - margin)
            dist = math.hypot(x - player_pos.x, y - player_pos.y)
            if dist >= 400:
                return (x, y)
        return (margin, margin)
