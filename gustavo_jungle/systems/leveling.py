import time
from entities.xp_orb import XpOrb


class LevelingSystem:

    def __init__(self):
        self.total_enemies_killed = 0
        self.total_xp_earned = 0
        self.start_time = time.time()

    def on_enemy_killed(self, enemy, player, xp_orb_group, asset_gen):
        self.total_enemies_killed += 1
        orb = XpOrb(enemy.pos, enemy.xp_value, asset_gen)
        xp_orb_group.add(orb)

    def get_stats(self) -> dict:
        return {
            "enemies_killed": self.total_enemies_killed,
            "xp_earned": self.total_xp_earned,
            "time_survived": time.time() - self.start_time,
        }
