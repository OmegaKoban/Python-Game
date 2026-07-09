"""
Карта фиксированного размера, собранная из повторяющихся клеток (тайлов).
Один загруженный тайл используется для заполнения всей сетки карты.
"""

import pygame

from src import settings


class TileMap:
    def __init__(self):
        self.tile_size = settings.TILE_SIZE
        self.width_tiles = settings.MAP_WIDTH_TILES
        self.height_tiles = settings.MAP_HEIGHT_TILES

        self.pixel_width = self.width_tiles * self.tile_size
        self.pixel_height = self.height_tiles * self.tile_size

        self.tile_image = self._load_tile_image()
        
        # Зоны коллизий (домики и препятствия)
        self.collision_zones = self._load_collision_zones()

    def _load_tile_image(self):
        """
        Загружает картинку клетки карты. Если файл не квадратный — вырезается по
        центру до квадрата, чтобы избежать искажения. Если файла нет — заглушка.
        """
        try:
            image = pygame.image.load(settings.TILE_IMAGE_PATH).convert_alpha()
            image = self._crop_to_square(image)
            image = pygame.transform.scale(image, (self.tile_size, self.tile_size))
            return image
        except (pygame.error, FileNotFoundError):
            placeholder = pygame.Surface((self.tile_size, self.tile_size))
            placeholder.fill(settings.FALLBACK_TILE_COLOR)
            pygame.draw.rect(placeholder, (60, 64, 72), placeholder.get_rect(), width=1)
            return placeholder

    @staticmethod
    def _crop_to_square(image):
        """Обрезает изображение по центру до квадрата по меньшей стороне."""
        width, height = image.get_size()
        if width == height:
            return image

        side = min(width, height)
        x = (width - side) // 2
        y = (height - side) // 2
        crop_rect = pygame.Rect(x, y, side, side)
        return image.subsurface(crop_rect).copy()

    def render(self, surface, camera_offset=(0, 0)):
        """Отрисовывает всю сетку карты с учётом смещения камеры."""
        offset_x, offset_y = camera_offset

        for row in range(self.height_tiles):
            for col in range(self.width_tiles):
                x = col * self.tile_size - offset_x
                y = row * self.tile_size - offset_y

                # Culling: не рисуем тайлы вне экрана.
                if x + self.tile_size < 0 or x > surface.get_width():
                    continue
                if y + self.tile_size < 0 or y > surface.get_height():
                    continue

                surface.blit(self.tile_image, (x, y))

    def clamp_to_bounds(self, rect):
        """Ограничивает прямоугольник (например, игрока) границами карты."""
        rect.left = max(rect.left, 0)
        rect.top = max(rect.top, 0)
        rect.right = min(rect.right, self.pixel_width)
        rect.bottom = min(rect.bottom, self.pixel_height)
        return rect
    
    def _load_collision_zones(self):
        """Загружает зоны коллизий из settings. Возвращает список pygame.Rect."""
        zones = []
        if hasattr(settings, 'COLLISION_ZONES'):
            for x1, y1, x2, y2 in settings.COLLISION_ZONES:
                width = x2 - x1
                height = y2 - y1
                zones.append(pygame.Rect(x1, y1, width, height))
        return zones
    
    def check_collision(self, rect):
        """
        Проверяет столкновение rect с зонами коллизий.
        Возвращает None если коллизии нет, иначе pygame.Rect зоны.
        """
        for zone in self.collision_zones:
            if rect.colliderect(zone):
                return zone
        return None
    
    def resolve_collision(self, rect, prev_pos):
        """
        Разрешает коллизию с попыткой скольжения вдоль стены.
        
        Args:
            rect: текущий прямоугольник сущности
            prev_pos: предыдущая позиция (x, y) перед движением
        
        Returns:
            bool: True если была коллизия, False иначе
        """
        collision = self.check_collision(rect)
        if not collision:
            return False
        
        # Есть коллизия - пробуем скольжение
        # Сохраняем желаемую позицию
        desired_x = rect.centerx
        desired_y = rect.centery
        
        # Пробуем движение только по X
        rect.centerx = desired_x
        rect.centery = int(prev_pos[1])
        if not self.check_collision(rect):
            return True  # Движение по X успешно
        
        # Пробуем движение только по Y
        rect.centerx = int(prev_pos[0])
        rect.centery = desired_y
        if not self.check_collision(rect):
            return True  # Движение по Y успешно
        
        # Ни X, ни Y не работают - полный откат
        rect.centerx = int(prev_pos[0])
        rect.centery = int(prev_pos[1])
        return True
