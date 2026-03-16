import numpy as np
import pygame


SAMPLE_RATE = 44100
CHANNELS = 2


def _envelope(length: int, attack: int = 0, decay: int = 0, sustain_level: float = 1.0, release: int = 0) -> np.ndarray:
    env = np.ones(length, dtype=np.float64)
    if attack > 0:
        env[:attack] = np.linspace(0, 1, attack)
    sustain_start = attack + decay
    if decay > 0:
        env[attack:sustain_start] = np.linspace(1, sustain_level, decay)
    if sustain_start < length:
        env[sustain_start:] = sustain_level
    if release > 0:
        release_start = max(0, length - release)
        env[release_start:] *= np.linspace(1, 0, length - release_start)
    return env


def _sine(freq: float, duration: float, volume: float = 0.5) -> np.ndarray:
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    return np.sin(2 * np.pi * freq * t) * volume


def _square(freq: float, duration: float, volume: float = 0.3) -> np.ndarray:
    return np.sign(_sine(freq, duration, volume))


def _noise(duration: float, volume: float = 0.3) -> np.ndarray:
    n = int(SAMPLE_RATE * duration)
    return (np.random.uniform(-1, 1, n) * volume).astype(np.float64)


def _to_stereo_int16(mono: np.ndarray) -> np.ndarray:
    mono = np.clip(mono, -1, 1)
    pcm = (mono * 32767).astype(np.int16)
    return np.column_stack((pcm, pcm))


def _make_sound(mono: np.ndarray) -> pygame.mixer.Sound:
    stereo = _to_stereo_int16(mono)
    return pygame.sndarray.make_sound(stereo)


def _gen_melee_hit() -> pygame.mixer.Sound:
    dur = 0.15
    n = int(SAMPLE_RATE * dur)
    wave = _sine(300, dur, 0.6) + _noise(dur, 0.15)
    env = _envelope(n, attack=int(n * 0.02), release=int(n * 0.6))
    return _make_sound(wave[:n] * env)


def _gen_enemy_hit() -> pygame.mixer.Sound:
    dur = 0.15
    n = int(SAMPLE_RATE * dur)
    wave = _sine(400, dur, 0.5) + _noise(dur, 0.12)
    env = _envelope(n, attack=int(n * 0.02), release=int(n * 0.6))
    return _make_sound(wave[:n] * env)


def _gen_enemy_death() -> pygame.mixer.Sound:
    dur = 0.3
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    freq = np.linspace(400, 100, n)
    wave = np.sin(2 * np.pi * freq * t) * 0.5 + _noise(dur, 0.15)
    env = _envelope(n, attack=int(n * 0.02), release=int(n * 0.5))
    return _make_sound(wave[:n] * env)


def _gen_player_hurt() -> pygame.mixer.Sound:
    dur = 0.2
    n = int(SAMPLE_RATE * dur)
    wave = _sine(120, dur, 0.6) + _noise(dur, 0.2)
    env = _envelope(n, attack=int(n * 0.05), release=int(n * 0.5))
    return _make_sound(wave[:n] * env)


def _gen_level_up() -> pygame.mixer.Sound:
    dur = 0.5
    tone_dur = dur / 3
    tones = []
    for freq in [440, 554, 659]:
        tones.append(_sine(freq, tone_dur, 0.5))
    wave = np.concatenate(tones)
    n = len(wave)
    env = _envelope(n, attack=int(n * 0.05), release=int(n * 0.3))
    return _make_sound(wave * env)


def _gen_xp_collect() -> pygame.mixer.Sound:
    dur = 0.1
    n = int(SAMPLE_RATE * dur)
    wave = _sine(1200, dur, 0.4)
    env = _envelope(n, attack=int(n * 0.05), release=int(n * 0.5))
    return _make_sound(wave[:n] * env)


def _gen_skill_vine_whip() -> pygame.mixer.Sound:
    dur = 0.2
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    freq = np.linspace(800, 200, n)
    wave = _noise(dur, 0.35) * np.sin(2 * np.pi * freq * t)
    env = _envelope(n, attack=int(n * 0.1), release=int(n * 0.4))
    return _make_sound(wave[:n] * env)


def _gen_skill_rock_throw() -> pygame.mixer.Sound:
    dur = 0.15
    n = int(SAMPLE_RATE * dur)
    wave = _sine(200, dur, 0.5) + _noise(dur, 0.2)
    env = _envelope(n, attack=int(n * 0.05), release=int(n * 0.5))
    return _make_sound(wave[:n] * env)


def _gen_skill_jungle_roar() -> pygame.mixer.Sound:
    dur = 0.4
    n = int(SAMPLE_RATE * dur)
    wave = _sine(60, dur, 0.5) + _sine(90, dur, 0.3) + _noise(dur, 0.15)
    env = _envelope(n, attack=int(n * 0.4), decay=int(n * 0.1), sustain_level=0.8, release=int(n * 0.3))
    return _make_sound(wave[:n] * env)


def _gen_skill_dash() -> pygame.mixer.Sound:
    dur = 0.2
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    freq = np.linspace(400, 1200, n)
    wave = _noise(dur, 0.3) * np.sin(2 * np.pi * freq * t)
    env = _envelope(n, attack=int(n * 0.05), release=int(n * 0.5))
    return _make_sound(wave[:n] * env)


def _gen_powerup_collect() -> pygame.mixer.Sound:
    dur = 0.3
    half = dur / 2
    wave = np.concatenate([_sine(600, half, 0.5), _sine(900, half, 0.5)])
    n = len(wave)
    env = _envelope(n, attack=int(n * 0.05), release=int(n * 0.3))
    return _make_sound(wave * env)


def _gen_menu_hover() -> pygame.mixer.Sound:
    dur = 0.05
    n = int(SAMPLE_RATE * dur)
    wave = _sine(800, dur, 0.25)
    env = _envelope(n, attack=int(n * 0.1), release=int(n * 0.5))
    return _make_sound(wave[:n] * env)


def _gen_menu_select() -> pygame.mixer.Sound:
    dur = 0.15
    n = int(SAMPLE_RATE * dur)
    wave = _sine(600, dur, 0.4) + _sine(900, dur, 0.2)
    env = _envelope(n, attack=int(n * 0.05), release=int(n * 0.4))
    return _make_sound(wave[:n] * env)


def _gen_wave_start() -> pygame.mixer.Sound:
    dur = 0.5
    n = int(SAMPLE_RATE * dur)
    wave = _sine(150, dur, 0.5) + _sine(300, dur, 0.3) + _noise(dur, 0.1)
    env = _envelope(n, attack=int(n * 0.1), decay=int(n * 0.1), sustain_level=0.7, release=int(n * 0.4))
    return _make_sound(wave[:n] * env)


def _gen_game_over() -> pygame.mixer.Sound:
    dur = 1.0
    tone_dur = dur / 4
    tones = []
    for freq in [440, 370, 330, 220]:
        tones.append(_sine(freq, tone_dur, 0.5))
    wave = np.concatenate(tones)
    n = len(wave)
    env = _envelope(n, attack=int(n * 0.02), release=int(n * 0.3))
    return _make_sound(wave * env)


_SFX_GENERATORS = {
    "melee_hit": _gen_melee_hit,
    "enemy_hit": _gen_enemy_hit,
    "enemy_death": _gen_enemy_death,
    "player_hurt": _gen_player_hurt,
    "level_up": _gen_level_up,
    "xp_collect": _gen_xp_collect,
    "skill_vine_whip": _gen_skill_vine_whip,
    "skill_rock_throw": _gen_skill_rock_throw,
    "skill_jungle_roar": _gen_skill_jungle_roar,
    "skill_dash": _gen_skill_dash,
    "powerup_collect": _gen_powerup_collect,
    "menu_hover": _gen_menu_hover,
    "menu_select": _gen_menu_select,
    "wave_start": _gen_wave_start,
    "game_over": _gen_game_over,
}


def _gen_music_loop() -> pygame.mixer.Sound:
    dur = 10.0
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)

    drone = np.sin(2 * np.pi * 80 * t) * 0.12 + np.sin(2 * np.pi * 120 * t) * 0.06

    beat_interval = int(SAMPLE_RATE * 0.5)
    percussion = np.zeros(n, dtype=np.float64)
    hit_len = int(SAMPLE_RATE * 0.04)
    hit = _noise(0.04, 0.3) * _envelope(hit_len, attack=2, release=int(hit_len * 0.7))
    for i in range(0, n, beat_interval):
        end = min(i + hit_len, n)
        percussion[i:end] += hit[:end - i]

    chirps = np.zeros(n, dtype=np.float64)
    rng = np.random.RandomState(42)
    chirp_times = rng.uniform(0, dur - 0.15, 8)
    for ct in chirp_times:
        start = int(ct * SAMPLE_RATE)
        cdur = 0.12
        cn = int(SAMPLE_RATE * cdur)
        ct_arr = np.linspace(0, cdur, cn, endpoint=False)
        freq = np.linspace(rng.uniform(1500, 2500), rng.uniform(800, 1200), cn)
        chirp = np.sin(2 * np.pi * freq * ct_arr) * 0.08
        chirp *= _envelope(cn, attack=int(cn * 0.1), release=int(cn * 0.5))
        end = min(start + cn, n)
        chirps[start:end] += chirp[:end - start]

    mix = drone + percussion + chirps

    fade = int(SAMPLE_RATE * 0.05)
    mix[:fade] *= np.linspace(0, 1, fade)
    mix[-fade:] *= np.linspace(1, 0, fade)

    return _make_sound(mix)


class SoundManager:

    def __init__(self):
        self.enabled = False
        self._sfx_cache: dict[str, pygame.mixer.Sound] = {}
        self._music_sound: pygame.mixer.Sound | None = None
        self._music_channel: pygame.mixer.Channel | None = None
        self._master_vol = 0.7
        self._sfx_vol = 0.8
        self._music_vol = 0.4

        try:
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=CHANNELS, buffer=1024)
            pygame.mixer.set_num_channels(16)
            self.enabled = True
        except Exception:
            return

        self._generate_all_sfx()
        self._generate_music()

    def _generate_all_sfx(self):
        for name, gen in _SFX_GENERATORS.items():
            try:
                self._sfx_cache[name] = gen()
            except Exception:
                pass

    def _generate_music(self):
        try:
            self._music_sound = _gen_music_loop()
        except Exception:
            pass

    def play_sfx(self, name: str):
        if not self.enabled:
            return
        snd = self._sfx_cache.get(name)
        if snd is None:
            return
        snd.set_volume(self._master_vol * self._sfx_vol)
        snd.play()

    def play_music(self, track_name: str = "jungle"):
        if not self.enabled or self._music_sound is None:
            return
        self._music_channel = pygame.mixer.Channel(15)
        self._music_sound.set_volume(self._master_vol * self._music_vol)
        self._music_channel.play(self._music_sound, loops=-1)

    def stop_music(self):
        if self._music_channel is not None:
            self._music_channel.stop()
            self._music_channel = None

    def set_volume(self, master: float = -1, sfx: float = -1, music: float = -1):
        if master >= 0:
            self._master_vol = max(0.0, min(1.0, master))
        if sfx >= 0:
            self._sfx_vol = max(0.0, min(1.0, sfx))
        if music >= 0:
            self._music_vol = max(0.0, min(1.0, music))
        if self._music_channel is not None and self._music_sound is not None:
            self._music_sound.set_volume(self._master_vol * self._music_vol)
