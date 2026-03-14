import pygame


class SpawnerSystem:

    def __init__(self, asset_gen):
        self.asset_gen = asset_gen
        self.wave = 0
        self.wave_timer = 0.0

    def update(self, dt, player, enemies_group):
        pass

    def spawn_wave(self, player, enemies_group):
        pass
