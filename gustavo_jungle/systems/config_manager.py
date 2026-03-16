import json
from pathlib import Path
import pygame


DEFAULT_KEY_BINDINGS = {
    "move_up": pygame.K_w,
    "move_down": pygame.K_s,
    "move_left": pygame.K_a,
    "move_right": pygame.K_d,
    "skill_1": pygame.K_1,
    "skill_2": pygame.K_2,
    "skill_3": pygame.K_3,
    "skill_4": pygame.K_4,
    "skill_5": pygame.K_5,
    "skill_6": pygame.K_6,
    "interact": pygame.K_e,
    "pause": pygame.K_ESCAPE,
}

DEFAULTS = {
    "master_volume": 0.7,
    "sfx_volume": 0.8,
    "music_volume": 0.5,
    "fullscreen": False,
    "show_fps": False,
    "show_damage_numbers": True,
    "difficulty": "normal",
    "key_bindings": dict(DEFAULT_KEY_BINDINGS),
}

VALID_DIFFICULTIES = ("easy", "normal", "hard")


class ConfigManager:

    def __init__(self):
        self._dir = Path.home() / ".gustavo_jungle"
        self._path = self._dir / "config.json"
        self._data: dict = {}
        self.load()

    def load(self):
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self._data = dict(DEFAULTS)
                self._data["key_bindings"] = dict(DEFAULT_KEY_BINDINGS)
                for k, v in raw.items():
                    if k == "key_bindings" and isinstance(v, dict):
                        for action, key_val in v.items():
                            if action in DEFAULT_KEY_BINDINGS:
                                self._data["key_bindings"][action] = int(key_val)
                    elif k in DEFAULTS:
                        self._data[k] = v
                self._validate()
            except (json.JSONDecodeError, OSError):
                self._data = dict(DEFAULTS)
                self._data["key_bindings"] = dict(DEFAULT_KEY_BINDINGS)
        else:
            self._data = dict(DEFAULTS)
            self._data["key_bindings"] = dict(DEFAULT_KEY_BINDINGS)
            self.save()

    def _validate(self):
        for key in ("master_volume", "sfx_volume", "music_volume"):
            val = self._data.get(key, DEFAULTS[key])
            self._data[key] = max(0.0, min(1.0, float(val)))
        for key in ("fullscreen", "show_fps", "show_damage_numbers"):
            self._data[key] = bool(self._data.get(key, DEFAULTS[key]))
        if self._data.get("difficulty") not in VALID_DIFFICULTIES:
            self._data["difficulty"] = "normal"

    def save(self):
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except OSError:
            pass

    def get(self, key: str):
        return self._data.get(key, DEFAULTS.get(key))

    def set(self, key: str, value):
        self._data[key] = value
        self._validate()
        self.save()

    def reset_defaults(self):
        self._data = dict(DEFAULTS)
        self._data["key_bindings"] = dict(DEFAULT_KEY_BINDINGS)
        self.save()
