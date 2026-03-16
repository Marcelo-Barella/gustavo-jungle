import pygame


class StatusEffect:

    def __init__(self, effect_type: str, duration: float, intensity: float, source=None):
        self.effect_type = effect_type
        self.duration = duration
        self.intensity = intensity
        self.source = source
        self.elapsed = 0.0

    @property
    def expired(self) -> bool:
        return self.elapsed >= self.duration


class StatusEffectManager:

    TINT_COLORS = {
        "poison": (0, 200, 0, 80),
        "slow": (0, 0, 200, 80),
        "stun": (255, 255, 0, 80),
        "burn": (255, 100, 0, 80),
    }

    ICON_COLORS = {
        "poison": (0, 180, 0),
        "slow": (80, 80, 255),
        "stun": (255, 255, 0),
        "burn": (255, 80, 0),
    }

    def __init__(self):
        self._effects: dict[int, list[StatusEffect]] = {}
        self._original_speeds: dict[int, float] = {}

    def apply(self, entity, effect_type: str, duration: float, intensity: float, source=None):
        eid = id(entity)
        if eid not in self._effects:
            self._effects[eid] = []

        for eff in self._effects[eid]:
            if eff.effect_type == effect_type and eff.source is not None and eff.source is source:
                eff.duration = duration
                eff.elapsed = 0.0
                eff.intensity = intensity
                return

        effect = StatusEffect(effect_type, duration, intensity, source)
        self._effects[eid] = self._effects.get(eid, [])
        self._effects[eid].append(effect)

        if effect_type == "slow" and eid not in self._original_speeds:
            self._original_speeds[eid] = entity.speed

        if effect_type == "stun" and eid not in self._original_speeds:
            self._original_speeds[eid] = entity.speed

    def update(self, dt: float, entities):
        to_remove_ids = []
        for eid, effects in self._effects.items():
            entity = None
            for e in entities:
                if id(e) == eid:
                    entity = e
                    break
            if entity is None:
                to_remove_ids.append(eid)
                continue

            has_slow = False
            has_stun = False
            max_slow_intensity = 0.0

            expired_indices = []
            for i, eff in enumerate(effects):
                eff.elapsed += dt
                if eff.expired:
                    expired_indices.append(i)
                    continue

                if eff.effect_type == "poison":
                    dmg = eff.intensity * dt
                    entity.hp -= dmg
                    if hasattr(entity, 'max_hp') and entity.hp <= 0:
                        entity.hp = 0
                        if hasattr(entity, 'state'):
                            entity.state = "dead"
                elif eff.effect_type == "burn":
                    dmg = eff.intensity * dt
                    entity.hp -= dmg
                    if hasattr(entity, 'max_hp') and entity.hp <= 0:
                        entity.hp = 0
                        if hasattr(entity, 'state'):
                            entity.state = "dead"
                elif eff.effect_type == "slow":
                    has_slow = True
                    max_slow_intensity = max(max_slow_intensity, eff.intensity)
                elif eff.effect_type == "stun":
                    has_stun = True

            for i in reversed(expired_indices):
                effects.pop(i)

            if eid in self._original_speeds:
                if has_stun:
                    entity.speed = 0
                elif has_slow:
                    entity.speed = self._original_speeds[eid] * (1.0 - max_slow_intensity)
                else:
                    entity.speed = self._original_speeds[eid]
                    if not any(e.effect_type in ("slow", "stun") for e in effects):
                        del self._original_speeds[eid]

            if not effects:
                to_remove_ids.append(eid)

        for eid in to_remove_ids:
            self._effects.pop(eid, None)
            self._original_speeds.pop(eid, None)

    def get_effects(self, entity) -> list[StatusEffect]:
        return self._effects.get(id(entity), [])

    def has_effect(self, entity, effect_type: str) -> bool:
        for eff in self._effects.get(id(entity), []):
            if eff.effect_type == effect_type and not eff.expired:
                return True
        return False

    def clear(self, entity):
        eid = id(entity)
        if eid in self._original_speeds:
            for e_candidate in [entity]:
                if id(e_candidate) == eid:
                    e_candidate.speed = self._original_speeds[eid]
        self._effects.pop(eid, None)
        self._original_speeds.pop(eid, None)

    def draw_effects(self, surface: pygame.Surface, entity, camera_offset: tuple[float, float]):
        effects = self.get_effects(entity)
        if not effects:
            return

        active_types = set()
        for eff in effects:
            if not eff.expired:
                active_types.add(eff.effect_type)

        for etype in active_types:
            tint_color = self.TINT_COLORS.get(etype)
            if tint_color:
                overlay = pygame.Surface(entity.image.get_size(), pygame.SRCALPHA)
                overlay.fill(tint_color)
                sx = entity.pos.x - camera_offset[0] - entity.image.get_width() // 2
                sy = entity.pos.y - camera_offset[1] - entity.image.get_height() // 2
                surface.blit(overlay, (sx, sy))

        icon_x = entity.pos.x - camera_offset[0] - len(active_types) * 5
        icon_y = entity.pos.y - camera_offset[1] - entity.image.get_height() // 2 - 10
        for etype in sorted(active_types):
            color = self.ICON_COLORS.get(etype, (255, 255, 255))
            pygame.draw.circle(surface, color, (int(icon_x), int(icon_y)), 4)
            pygame.draw.circle(surface, (0, 0, 0), (int(icon_x), int(icon_y)), 4, 1)
            icon_x += 10
