import json
import os
import tempfile


class SaveManager:

    DEFAULT_SETTINGS = {
        "master_volume": 0.7,
        "sfx_volume": 0.7,
        "music_volume": 0.5,
        "fullscreen": False,
    }

    def __init__(self):
        self.save_dir = os.path.expanduser("~/.gustavo_jungle/")
        os.makedirs(self.save_dir, exist_ok=True)
        self._highscores_path = os.path.join(self.save_dir, "highscores.json")
        self._settings_path = os.path.join(self.save_dir, "settings.json")
        self._high_scores: list[dict] = self._load_json(self._highscores_path, [])

    def _load_json(self, path: str, default):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return default

    def _atomic_write(self, path: str, data) -> None:
        dir_name = os.path.dirname(path)
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    @staticmethod
    def compute_score(level: int, waves: int, kills: int, time_survived: float) -> int:
        return (level * 1000) + (waves * 500) + (kills * 50) + int(time_survived * 10)

    def save_high_score(self, score_data: dict) -> None:
        self._high_scores.append(score_data)
        self._high_scores.sort(key=lambda s: s.get("score", 0), reverse=True)
        self._high_scores = self._high_scores[:10]
        self._atomic_write(self._highscores_path, self._high_scores)

    def get_high_scores(self) -> list[dict]:
        return list(self._high_scores)

    def save_settings(self, settings: dict) -> None:
        self._atomic_write(self._settings_path, settings)

    def load_settings(self) -> dict:
        loaded = self._load_json(self._settings_path, {})
        result = dict(self.DEFAULT_SETTINGS)
        result.update(loaded)
        return result
