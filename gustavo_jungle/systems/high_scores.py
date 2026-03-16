import json
from pathlib import Path
from datetime import datetime


MAX_ENTRIES = 10


class HighScoreManager:

    def __init__(self):
        self._dir = Path.home() / ".gustavo_jungle"
        self._path = self._dir / "highscores.json"
        self._scores: list[dict] = []
        self.load()

    def load(self):
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    self._scores = json.load(f)
                if not isinstance(self._scores, list):
                    self._scores = []
                self._scores = self._scores[:MAX_ENTRIES]
            except (json.JSONDecodeError, OSError):
                self._scores = []
        else:
            self._scores = []

    def save(self):
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._scores, f, indent=2)
        except OSError:
            pass

    @staticmethod
    def calculate_score(enemies_killed: int, waves_completed: int, level: int, time_survived: float) -> int:
        time_bonus = max(0, int(time_survived * 2))
        return (enemies_killed * 10) + (waves_completed * 100) + (level * 50) + time_bonus

    def add_score(self, stats: dict) -> int | None:
        entry = {
            "name": stats.get("name", "Player"),
            "score": int(stats.get("score", 0)),
            "level": int(stats.get("level", 1)),
            "waves": int(stats.get("waves", 0)),
            "enemies_killed": int(stats.get("enemies_killed", 0)),
            "time": float(stats.get("time", 0.0)),
            "difficulty": stats.get("difficulty", "normal"),
            "date": stats.get("date", datetime.now().strftime("%Y-%m-%d")),
        }
        self._scores.append(entry)
        self._scores.sort(key=lambda e: e["score"], reverse=True)
        rank = None
        for i, e in enumerate(self._scores):
            if e is entry:
                rank = i + 1
                break
        self._scores = self._scores[:MAX_ENTRIES]
        if rank is not None and rank <= MAX_ENTRIES:
            self.save()
            return rank
        self.save()
        return None

    def get_scores(self) -> list[dict]:
        return list(self._scores)
