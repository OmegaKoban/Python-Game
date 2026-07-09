"""
Дропы, выпадающие из врагов: опыт (XP) и хилки (лечат игрока).

Поведение — автоподбор-магнит (как в Vampire Survivors):
    - пока игрок далеко, дроп лежит на месте (лёгкое покачивание);
    - как только игрок входит в PICKUP_MAGNET_RADIUS — дроп летит к нему,
      ускоряясь;
    - на расстоянии PICKUP_COLLECT_RADIUS дроп считается собранным.

Визуал: пока нет спрайтов — рисуется фигура-заглушка (опыт — голубой ромб,
хилка — зелёный крест). Если в settings указан путь к спрайту и файл есть —
используется он.
"""

import math

import pygame

from src import settings


class Pickup(pygame.sprite.Sprite):
    def __init__(self, pos, kind, value):
        super().__init__()
        self.kind = kind            # "xp" | "heal"
        self.value = value          # сколько опыта / сколько HP
        self.pos = pygame.Vector2(pos)
        self.alive = True
        self.lifetime = settings.PICKUP_LIFETIME
        self.magnetized = False     # уже притягивается к игроку
        self.current_speed = settings.PICKUP_MAGNET_SPEED
        self._bob = 0.0             # фаза покачивания на месте

        self.image = self._make_image()
        self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))

    def _make_image(self):
        # Попытка загрузить спрайт из settings (если задан путь и файл есть).
        path = (settings.XP_PICKUP_IMAGE_PATH if self.kind == "xp"
                else settings.HEAL_PICKUP_IMAGE_PATH)
        s = (settings.XP_PICKUP_SIZE if self.kind == "xp"
             else settings.HEAL_PICKUP_SIZE)
        if path:
            try:
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.scale(img, (s, s))
            except (pygame.error, FileNotFoundError):
                pass
        return self._make_placeholder(s)

    def _make_placeholder(self, s=None):
        """Фигура-заглушка: опыт — ромб, хилка — крест."""
        if s is None:
            s = settings.XP_PICKUP_SIZE if self.kind == "xp" else settings.HEAL_PICKUP_SIZE
        surface = pygame.Surface((s, s), pygame.SRCALPHA)
        if self.kind == "xp":
            color = settings.XP_PICKUP_COLOR
            # Ромб (кристалл опыта).
            points = [(s // 2, 2), (s - 2, s // 2), (s // 2, s - 2), (2, s // 2)]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, width=1)
        else:
            color = settings.HEAL_PICKUP_COLOR
            # Зелёный крест (аптечка).
            t = max(3, s // 3)          # толщина креста
            o = (s - t) // 2
            pygame.draw.rect(surface, color, (o, 2, t, s - 4), border_radius=2)
            pygame.draw.rect(surface, color, (2, o, s - 4, t), border_radius=2)
            pygame.draw.rect(surface, (255, 255, 255), (o, 2, t, s - 4), width=1,
                             border_radius=2)
        return surface

    def update(self, dt, player):
        """Двигает дроп; возвращает True, если он собран (надо забрать value)."""
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
            return False

        to_player = player.pos - self.pos
        dist = to_player.length()

        if dist <= settings.PICKUP_COLLECT_RADIUS:
            # Собрали.
            self.alive = False
            return True

        if self.magnetized or dist <= settings.PICKUP_MAGNET_RADIUS:
            # Летим к игроку, ускоряясь.
            self.magnetized = True
            self.current_speed += settings.PICKUP_MAGNET_SPEED * dt * 2
            if dist > 0:
                self.pos += to_player.normalize() * min(self.current_speed * dt, dist)
        else:
            # Лежим на месте, слегка покачиваясь по вертикали.
            self._bob += dt * 3
            self.pos.y += math.sin(self._bob) * 6 * dt

        self.rect.center = (round(self.pos.x), round(self.pos.y))
        return False

    def render(self, surface, camera):
        surface.blit(self.image, camera.apply(self.rect))
