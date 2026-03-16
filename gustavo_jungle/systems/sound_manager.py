import array
import math
import random

import numpy as np
import pygame


class SoundManager:
    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self._master_volume = 0.7
        self._sfx_volume = 0.7
        self._music_volume = 0.5
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._ambient_channel: pygame.mixer.Channel = pygame.mixer.Channel(7)
        self._ambient_sound: pygame.mixer.Sound | None = None
        self._boss_ambient_sound: pygame.mixer.Sound | None = None
        self._generate_all()

    def _generate_all(self):
        self._sounds["hit_enemy"] = self._gen_hit_enemy()
        self._sounds["hit_player"] = self._gen_hit_player()
        self._sounds["skill_vine_whip"] = self._gen_skill_vine_whip()
        self._sounds["skill_rock_throw"] = self._gen_skill_rock_throw()
        self._sounds["skill_jungle_roar"] = self._gen_skill_jungle_roar()
        self._sounds["skill_dash"] = self._gen_skill_dash()
        self._sounds["enemy_death"] = self._gen_enemy_death()
        self._sounds["level_up"] = self._gen_level_up()
        self._sounds["xp_pickup"] = self._gen_xp_pickup()
        self._sounds["menu_hover"] = self._gen_menu_hover()
        self._sounds["menu_click"] = self._gen_menu_click()
        self._sounds["boss_spawn"] = self._gen_boss_spawn()
        self._sounds["powerup_collect"] = self._gen_powerup_collect()
        self._sounds["game_over"] = self._gen_game_over()
        self._ambient_sound = self._gen_ambient()
        self._boss_ambient_sound = self._gen_boss_ambient()

    @staticmethod
    def _make_sound(samples: array.array) -> pygame.mixer.Sound:
        stereo = np.column_stack([
            np.frombuffer(samples, dtype=np.int16),
            np.frombuffer(samples, dtype=np.int16),
        ])
        return pygame.sndarray.make_sound(stereo)

    @staticmethod
    def _clamp(value: int) -> int:
        return max(-32767, min(32767, value))

    def _gen_hit_enemy(self) -> pygame.mixer.Sound:
        rate = 44100
        duration = 0.1
        n = int(rate * duration)
        buf = array.array("h", [0] * n)
        for i in range(n):
            t = i / rate
            decay = 1.0 - (i / n)
            period = rate / 200
            val = 20000 * decay * (1 if (i % int(period)) < int(period / 2) else -1)
            buf[i] = self._clamp(int(val))
        return self._make_sound(buf)

    def _gen_hit_player(self) -> pygame.mixer.Sound:
        rate = 44100
        duration = 0.15
        n = int(rate * duration)
        buf = array.array("h", [0] * n)
        for i in range(n):
            t = i / rate
            decay = 1.0 - (i / n)
            sine = math.sin(2 * math.pi * 150 * t)
            noise = random.uniform(-1, 1) * 0.3
            val = 18000 * decay * (sine + noise)
            buf[i] = self._clamp(int(val))
        return self._make_sound(buf)

    def _gen_skill_vine_whip(self) -> pygame.mixer.Sound:
        rate = 44100
        duration = 0.2
        n = int(rate * duration)
        buf = array.array("h", [0] * n)
        for i in range(n):
            progress = i / n
            decay = 1.0 - progress
            freq = 4000 * (1.0 - progress) + 200 * progress
            noise = random.uniform(-1, 1)
            filtered = noise * math.sin(2 * math.pi * freq * (i / rate))
            buf[i] = self._clamp(int(15000 * decay * filtered))
        return self._make_sound(buf)

    def _gen_skill_rock_throw(self) -> pygame.mixer.Sound:
        rate = 44100
        duration = 0.15
        n = int(rate * duration)
        buf = array.array("h", [0] * n)
        for i in range(n):
            t = i / rate
            decay = 1.0 - (i / n)
            sine = math.sin(2 * math.pi * 80 * t)
            noise = random.uniform(-1, 1) * 0.4
            buf[i] = self._clamp(int(20000 * decay * (sine + noise)))
        return self._make_sound(buf)

    def _gen_skill_jungle_roar(self) -> pygame.mixer.Sound:
        rate = 44100
        duration = 0.5
        n = int(rate * duration)
        buf = array.array("h", [0] * n)
        for i in range(n):
            t = i / rate
            env = math.sin(math.pi * i / n)
            am = 0.5 + 0.5 * math.sin(2 * math.pi * 8 * t)
            sine = math.sin(2 * math.pi * 60 * t)
            buf[i] = self._clamp(int(22000 * env * am * sine))
        return self._make_sound(buf)

    def _gen_skill_dash(self) -> pygame.mixer.Sound:
        rate = 44100
        duration = 0.3
        n = int(rate * duration)
        buf = array.array("h", [0] * n)
        for i in range(n):
            progress = i / n
            decay = 1.0 - progress
            freq = 2000 * (1.0 - progress) + 100 * progress
            noise = random.uniform(-1, 1)
            swept = noise * math.sin(2 * math.pi * freq * (i / rate))
            buf[i] = self._clamp(int(16000 * decay * swept))
        return self._make_sound(buf)

    def _gen_enemy_death(self) -> pygame.mixer.Sound:
        rate = 44100
        duration = 0.15
        n = int(rate * duration)
        buf = array.array("h", [0] * n)
        for i in range(n):
            t = i / rate
            progress = i / n
            decay = 1.0 - progress
            freq = 400 - 300 * progress
            buf[i] = self._clamp(int(18000 * decay * math.sin(2 * math.pi * freq * t)))
        return self._make_sound(buf)

    def _gen_level_up(self) -> pygame.mixer.Sound:
        rate = 44100
        duration = 0.5
        n = int(rate * duration)
        buf = array.array("h", [0] * n)
        freqs = [400, 500, 600]
        seg = n // len(freqs)
        for i in range(n):
            t = i / rate
            idx = min(i // seg, len(freqs) - 1)
            local_progress = (i - idx * seg) / seg if seg > 0 else 0
            env = 1.0 - local_progress
            buf[i] = self._clamp(int(16000 * env * math.sin(2 * math.pi * freqs[idx] * t)))
        return self._make_sound(buf)

    def _gen_xp_pickup(self) -> pygame.mixer.Sound:
        rate = 44100
        duration = 0.08
        n = int(rate * duration)
        buf = array.array("h", [0] * n)
        for i in range(n):
            t = i / rate
            decay = 1.0 - (i / n)
            buf[i] = self._clamp(int(14000 * decay * math.sin(2 * math.pi * 800 * t)))
        return self._make_sound(buf)

    def _gen_menu_hover(self) -> pygame.mixer.Sound:
        rate = 44100
        duration = 0.05
        n = int(rate * duration)
        buf = array.array("h", [0] * n)
        for i in range(n):
            t = i / rate
            decay = 1.0 - (i / n)
            buf[i] = self._clamp(int(10000 * decay * math.sin(2 * math.pi * 600 * t)))
        return self._make_sound(buf)

    def _gen_menu_click(self) -> pygame.mixer.Sound:
        rate = 44100
        duration = 0.08
        n = int(rate * duration)
        buf = array.array("h", [0] * n)
        for i in range(n):
            t = i / rate
            decay = 1.0 - (i / n)
            buf[i] = self._clamp(int(12000 * decay * math.sin(2 * math.pi * 400 * t)))
        return self._make_sound(buf)

    def _gen_boss_spawn(self) -> pygame.mixer.Sound:
        rate = 44100
        duration = 0.8
        n = int(rate * duration)
        buf = array.array("h", [0] * n)
        for i in range(n):
            t = i / rate
            env = math.sin(math.pi * i / n)
            layer1 = math.sin(2 * math.pi * 40 * t)
            layer2 = math.sin(2 * math.pi * 55 * t) * 0.7
            layer3 = math.sin(2 * math.pi * 30 * t) * 0.5
            buf[i] = self._clamp(int(20000 * env * (layer1 + layer2 + layer3) / 2.2))
        return self._make_sound(buf)

    def _gen_powerup_collect(self) -> pygame.mixer.Sound:
        rate = 44100
        duration = 0.2
        n = int(rate * duration)
        buf = array.array("h", [0] * n)
        for i in range(n):
            t = i / rate
            progress = i / n
            decay = 1.0 - progress
            freq = 300 + 600 * progress
            buf[i] = self._clamp(int(14000 * decay * math.sin(2 * math.pi * freq * t)))
        return self._make_sound(buf)

    def _gen_game_over(self) -> pygame.mixer.Sound:
        rate = 44100
        duration = 0.6
        n = int(rate * duration)
        buf = array.array("h", [0] * n)
        for i in range(n):
            t = i / rate
            progress = i / n
            env = 1.0 - progress
            freq = 500 - 300 * progress
            buf[i] = self._clamp(int(18000 * env * math.sin(2 * math.pi * freq * t)))
        return self._make_sound(buf)

    def _gen_ambient(self) -> pygame.mixer.Sound:
        rate = 44100
        duration = 3.0
        n = int(rate * duration)
        buf = array.array("h", [0] * n)
        for i in range(n):
            t = i / rate
            hum = math.sin(2 * math.pi * 80 * t) * 0.3
            hum2 = math.sin(2 * math.pi * 120 * t) * 0.15
            sweep = 0.0
            cycle = (t % 1.5) / 1.5
            if cycle < 0.3:
                sweep_freq = 200 + 400 * (cycle / 0.3)
                sweep = math.sin(2 * math.pi * sweep_freq * t) * 0.2 * (1.0 - cycle / 0.3)
            buf[i] = self._clamp(int(8000 * (hum + hum2 + sweep)))
        return self._make_sound(buf)

    def _gen_boss_ambient(self) -> pygame.mixer.Sound:
        rate = 44100
        duration = 3.0
        n = int(rate * duration)
        buf = array.array("h", [0] * n)
        for i in range(n):
            t = i / rate
            base = math.sin(2 * math.pi * 50 * t) * 0.4
            pulse = math.sin(2 * math.pi * 2 * t)
            rumble = math.sin(2 * math.pi * 35 * t) * 0.3 * (0.5 + 0.5 * pulse)
            high = math.sin(2 * math.pi * 200 * t) * 0.1 * max(0, math.sin(2 * math.pi * 0.5 * t))
            buf[i] = self._clamp(int(10000 * (base + rumble + high)))
        return self._make_sound(buf)

    def play(self, sound_name: str):
        sound = self._sounds.get(sound_name)
        if sound is None:
            return
        sound.set_volume(self._sfx_volume * self._master_volume)
        sound.play()

    def set_master_volume(self, vol: float):
        self._master_volume = max(0.0, min(1.0, vol))

    def set_sfx_volume(self, vol: float):
        self._sfx_volume = max(0.0, min(1.0, vol))

    def set_music_volume(self, vol: float):
        self._music_volume = max(0.0, min(1.0, vol))

    def play_ambient(self):
        if self._ambient_sound is None:
            return
        self._ambient_sound.set_volume(self._music_volume * self._master_volume)
        self._ambient_channel.play(self._ambient_sound, loops=-1)

    def stop_ambient(self):
        self._ambient_channel.stop()

    def play_boss_music(self):
        if self._boss_ambient_sound is None:
            return
        self._ambient_channel.stop()
        self._boss_ambient_sound.set_volume(self._music_volume * self._master_volume)
        self._ambient_channel.play(self._boss_ambient_sound, loops=-1)

    def stop_all(self):
        pygame.mixer.stop()
