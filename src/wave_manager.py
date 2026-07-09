"""
Менеджер волн: спавнит врагов волнами по таймеру. Каждая следующая волна
больше и сильнее предыдущей. Враги появляются по краям карты, за пределами
видимой области, и набегают на игрока.
"""

import random

import pygame

from src import settings
from src.enemy import Enemy


class WaveManager:
    def __init__(self, tilemap):
        self.tilemap = tilemap
        self.wave_number = 0
        self.state = "waiting"          # "waiting" (пауза) | "spawning" (идёт спавн)
        self.timer = settings.WAVE_START_DELAY  # обратный отсчёт до старта волны
        self.spawn_timer = 0.0
        self.to_spawn = 0               # сколько врагов осталось заспавнить в волне

    def _enemies_in_wave(self):
        return settings.WAVE_BASE_ENEMY_COUNT + self.wave_number * settings.WAVE_ENEMY_GROWTH

    def _type_weights(self):
        """
        Вес каждого разблокированного типа для текущей волны. Чем дольше тип
        разблокирован, тем больше его доля (постепенно вытесняет слабых, но
        не полностью — снизу вес ограничен ENEMY_TYPE_MIN_WEIGHT).
        Возвращает {тип: вес}. Пустой dict -> фолбэк на slime1.
        """
        weights = {}
        for etype in settings.ENEMY_TYPES:
            unlock = settings.ENEMY_TYPE_UNLOCK_WAVE.get(etype, 1)
            if self.wave_number < unlock:
                continue  # тип ещё не разблокирован
            waves_since = self.wave_number - unlock
            w = settings.ENEMY_TYPE_BASE_WEIGHT + waves_since * settings.ENEMY_TYPE_WEIGHT_GROWTH
            w = max(settings.ENEMY_TYPE_MIN_WEIGHT, w)
            weights[etype] = w
        return weights

    def _pick_enemy_type(self):
        """Случайный тип врага по весам (процентная доля от волны)."""
        weights = self._type_weights()
        if not weights:
            return "slime1"
        types = list(weights.keys())
        values = list(weights.values())
        return random.choices(types, weights=values, k=1)[0]

    def _random_edge_position(self, player_pos):
        """Точка на случайном краю карты (враги набегают снаружи)."""
        w = self.tilemap.pixel_width
        h = self.tilemap.pixel_height
        edge = random.choice(("top", "bottom", "left", "right"))
        margin = 40
        if edge == "top":
            return (random.randint(0, w), margin)
        if edge == "bottom":
            return (random.randint(0, w), h - margin)
        if edge == "left":
            return (margin, random.randint(0, h))
        return (w - margin, random.randint(0, h))

    def update(self, dt, player, enemies_group):
        """Продвигает логику волн. enemies_group — pygame.sprite.Group врагов."""
        if self.state == "waiting":
            self.timer -= dt
            if self.timer <= 0:
                # Стартуем новую волну.
                self.wave_number += 1
                self.to_spawn = self._enemies_in_wave()
                self.spawn_timer = 0.0
                self.state = "spawning"

        elif self.state == "spawning":
            self.spawn_timer -= dt
            if self.spawn_timer <= 0 and self.to_spawn > 0:
                # Пробуем найти валидную позицию спауна (не в коллизии)
                max_attempts = 10
                enemy = None
                etype = self._pick_enemy_type()
                
                for attempt in range(max_attempts):
                    pos = self._random_edge_position(player.pos)
                    test_enemy = Enemy(pos, enemy_type=etype, wave_number=self.wave_number)
                    
                    # Проверяем, не в коллизии ли
                    if not self.tilemap.check_collision(test_enemy.rect):
                        enemy = test_enemy
                        break
                
                # Если не нашли валидную позицию за 10 попыток, 
                # просто спауним в центре карты (гарантированно не в коллизии)
                if enemy is None:
                    center_x = self.tilemap.pixel_width // 2
                    center_y = self.tilemap.pixel_height // 2
                    # Спауним рядом с центром в случайном направлении
                    offset = 200
                    angle = random.uniform(0, 6.28)  # 2*pi
                    pos = (
                        center_x + int(offset * pygame.math.Vector2(1, 0).rotate_rad(angle).x),
                        center_y + int(offset * pygame.math.Vector2(1, 0).rotate_rad(angle).y)
                    )
                    enemy = Enemy(pos, enemy_type=etype, wave_number=self.wave_number)
                
                enemies_group.add(enemy)
                self.to_spawn -= 1
                self.spawn_timer = settings.WAVE_SPAWN_INTERVAL

            # Все враги волны заспавнены — ждём, пока их всех перебьют,
            # затем уходим в паузу перед следующей волной.
            if self.to_spawn <= 0 and len(enemies_group) == 0:
                self.state = "waiting"
                self.timer = settings.WAVE_INTERVAL

    @property
    def time_to_next_wave(self):
        """Сколько секунд до следующей волны (для HUD), иначе None."""
        if self.state == "waiting":
            return max(0.0, self.timer)
        return None
