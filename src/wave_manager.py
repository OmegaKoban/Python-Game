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

    def _hp_multiplier(self):
        return 1.0 + self.wave_number * settings.WAVE_HP_SCALING

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
                pos = self._random_edge_position(player.pos)
                enemies_group.add(Enemy(pos, hp_multiplier=self._hp_multiplier()))
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
