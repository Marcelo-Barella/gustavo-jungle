SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
TILE_SIZE = 64

MAP_WIDTH = 3200
MAP_HEIGHT = 3200
MAP_COLS = MAP_WIDTH // TILE_SIZE
MAP_ROWS = MAP_HEIGHT // TILE_SIZE

JUNGLE_GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
BROWN = (139, 90, 43)
GOLDEN = (255, 215, 0)
RIVER_BLUE = (64, 164, 223)
SKY_BLUE = (135, 206, 235)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 20, 20)
LIGHT_GREEN = (144, 238, 144)
TAN = (210, 180, 140)

BASE_HP = 100
BASE_ATTACK = 10
BASE_DEFENSE = 5
BASE_SPEED = 3.0
BASE_LUCK = 5

STAT_GROWTH_RATE = 0.1

PANTHER_STATS = dict(hp=30, attack=8, defense=2, speed=2.5, xp=15, min_level=1)
LION_STATS = dict(hp=80, attack=20, defense=8, speed=1.2, xp=40, min_level=3)
SNAKE_STATS = dict(hp=20, attack=5, defense=1, speed=2.0, xp=10, min_level=2, poison_dps=2, poison_duration=3.0)
GORILLA_STATS = dict(hp=150, attack=25, defense=12, speed=0.8, xp=80, min_level=5, slam_radius=80)

XP_BASE = 100
XP_EXPONENT = 1.5

MAX_LEVEL = 50

WAVE_BASE_ENEMIES = 2
WAVE_DELAY = 3.0

ORB_COLLECT_RADIUS = 80
ORB_DRIFT_SPEED = 4.0
ORB_LIFETIME = 15.0

INVINCIBILITY_DURATION = 0.5

MELEE_ARC_DURATION = 0.2
MELEE_RANGE = 50

VINE_WHIP = dict(damage_mult=1.5, cooldown=4.0, range=70)
ROCK_THROW = dict(damage_mult=2.0, cooldown=3.0, speed=8, range=300)
JUNGLE_ROAR = dict(damage_mult=1.0, cooldown=8.0, radius=150, stun_duration=1.0)
DASH_ATTACK = dict(damage_mult=2.5, cooldown=6.0, distance=200, duration=0.3)
NATURE_SHIELD = dict(damage_reduction=0.5, duration=5.0, cooldown=20.0)
SUMMON_VINES = dict(damage_per_sec=5, slow_factor=0.5, radius=80, duration=8.0, cooldown=25.0)

SKILL_UNLOCK_LEVELS = {
    1: "vine_whip",
    3: "rock_throw",
    6: "jungle_roar",
    10: "dash",
    15: "nature_shield",
    20: "summon_vines",
}

SKILL_NAMES = {
    "vine_whip": "Vine Whip",
    "rock_throw": "Rock Throw",
    "jungle_roar": "Jungle Roar",
    "dash": "Dash",
    "nature_shield": "Nature Shield",
    "summon_vines": "Summon Vines",
}

SKILL_DESCRIPTIONS = {
    "vine_whip": "Whip enemies in a frontal arc dealing 1.5x damage.",
    "rock_throw": "Hurl a rock projectile dealing 2x damage.",
    "jungle_roar": "AoE roar that damages and stuns nearby enemies.",
    "dash": "Dash forward dealing 2.5x damage to enemies in path.",
    "nature_shield": "Gain 50% damage reduction for 5 seconds.",
    "summon_vines": "Create a vine trap that slows and damages enemies for 8s.",
}

STAT_UPGRADES = {
    "hp": {"amount": 15, "attr": "_base_hp", "label": "Max HP", "color": (100, 200, 100), "desc": "Increases maximum health points"},
    "attack": {"amount": 3, "attr": "_base_attack", "label": "Attack", "color": (220, 60, 60), "desc": "Increases attack power"},
    "defense": {"amount": 2, "attr": "_base_defense", "label": "Defense", "color": (60, 120, 220), "desc": "Reduces incoming damage"},
    "speed": {"amount": 0.3, "attr": "_base_speed", "label": "Speed", "color": (230, 230, 60), "desc": "Move faster through the jungle"},
    "luck": {"amount": 3, "attr": "_base_luck", "label": "Luck", "color": (180, 80, 220), "desc": "Increases critical hit chance"},
}

SPEED_BOOST = dict(multiplier=1.4, duration=15.0)
HEALTH_REGEN = dict(hps=2.0, duration=20.0)
DOUBLE_XP = dict(multiplier=2.0, duration=30.0)

POWERUP_DROP_CHANCE = 0.10

HP_BAR_WIDTH = 200
HP_BAR_HEIGHT = 20
XP_BAR_WIDTH = 200
XP_BAR_HEIGHT = 14
MINIMAP_SIZE = 150

SCREEN_SHAKE_INTENSITY = 5
SCREEN_SHAKE_DURATION = 0.3

DAMAGE_TEXT_DURATION = 0.8
DAMAGE_TEXT_RISE_SPEED = 1.5
