"""
Снаряд автоатаки игрока. Летит по прямой в сторону цели (направление
фиксируется в момент выстрела), наносит урон первому задетому врагу и исчезает.

Визуал: анимированный спрайт-лист (кадры в один горизонтальный ряд), который
проигрывается по кругу и, при желании, поворачивается по направлению полёта.
Если ассета нет — рисуется заглушка-кружок. Ассет настраивается в settings.py:
PROJECTILE_IMAGE_PATH / PROJECTILE_FRAME_COUNT / PROJECTILE_SIZE и др.
"""

import pygame

from src import settings


class Projectile(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos, damage):
        super().__init__()
        self.pos = pygame.Vector2(start_pos)
        self.damage = damage
        self.lifetime = settings.PROJECTILE_LIFETIME
        self.alive = True

        # Направление к цели (нормализованное). Если цель совпадает с точкой
        # старта — летим вправо, чтобы не делить на ноль.
        direction = pygame.Vector2(target_pos) - self.pos
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        direction = direction.normalize()
        self.velocity = direction * settings.PROJECTILE_SPEED

        # Угол поворота спрайта по направлению полёта.
        # Важно: в pygame экранная ось Y направлена вниз, а transform.rotate
        # вращает против часовой стрелки в математической системе (Y вверх).
        # Поэтому инвертируем Y, чтобы спрайт смотрел туда, куда летит.
        # Спрайт должен быть нарисован "носом" вправо (0°).
        self.angle = pygame.Vector2(1, 0).angle_to(pygame.Vector2(direction.x, -direction.y))

        # Радиус попадания — отдельно от размера картинки (см. settings).
        self.hit_radius = settings.PROJECTILE_HIT_RADIUS

        # Кадры анимации + fallback-кружок.
        self.frames = self._load_frames()
        self.frame_index = 0
        self.anim_timer = 0.0

        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))

    def _load_frames(self):
        """Загружает спрайт-лист снаряда и режет на кадры. Fallback — кружок."""
        if settings.PROJECTILE_IMAGE_PATH:
            try:
                sheet = pygame.image.load(settings.PROJECTILE_IMAGE_PATH).convert_alpha()
                count = max(1, settings.PROJECTILE_FRAME_COUNT)
                frame_w = sheet.get_width() // count
                frame_h = sheet.get_height()
                frames = []
                for i in range(count):
                    frame_rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
                    frame = sheet.subsurface(frame_rect).copy()
                    frame = pygame.transform.scale(frame, settings.PROJECTILE_SIZE)
                    frames.append(frame)
                return frames
            except (pygame.error, FileNotFoundError):
                pass

        # Fallback: кружок-заглушка.
        r = settings.PROJECTILE_RADIUS
        surface = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(surface, settings.PROJECTILE_COLOR, (r, r), r)
        return [surface]

    def _current_frame(self):
        """Текущий кадр анимации с поворотом по направлению полёта (если включено)."""
        frame = self.frames[self.frame_index % len(self.frames)]
        if settings.PROJECTILE_ROTATE_TO_DIRECTION and len(self.frames) >= 1:
            frame = pygame.transform.rotate(frame, self.angle)
        return frame

    def update(self, dt, enemies, tilemap):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
            return

        # Анимация кадров (крутится по кругу, пока снаряд летит).
        if len(self.frames) > 1:
            self.anim_timer += dt
            if self.anim_timer >= 1 / settings.PROJECTILE_ANIMATION_SPEED:
                self.anim_timer = 0.0
                self.frame_index = (self.frame_index + 1) % len(self.frames)

        # Движение.
        self.pos += self.velocity * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        # Вышел за пределы карты — убираем.
        if (self.pos.x < 0 or self.pos.x > tilemap.pixel_width or
                self.pos.y < 0 or self.pos.y > tilemap.pixel_height):
            self.alive = False
            return

        # Попадание: проверяем пересечение с хитбоксом врага (а не со всем
        # спрайтом). Сам снаряд — кружок радиусом hit_radius вокруг своего центра.
        proj_hitbox = pygame.Rect(0, 0, self.hit_radius * 2, self.hit_radius * 2)
        proj_hitbox.center = (round(self.pos.x), round(self.pos.y))
        for enemy in enemies:
            if not enemy.is_alive:
                continue
            if proj_hitbox.colliderect(enemy.hitbox):
                enemy.take_damage(self.damage)
                self.alive = False
                return

    def render(self, surface, camera):
        # Поворот меняет размер surface — центрируем кадр относительно позиции.
        frame = self._current_frame()
        screen_center = camera.apply(self.rect).center
        draw_rect = frame.get_rect(center=screen_center)
        surface.blit(frame, draw_rect)
