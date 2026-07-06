"""
Простая камера: держит игрока по центру экрана, не выходит за пределы карты
и учитывает зум (CAMERA_ZOOM).
"""

from src import settings


class Camera:
    def __init__(self, tilemap):
        self.tilemap = tilemap
        self.offset = [0, 0]
        self.zoom = max(0.01, settings.CAMERA_ZOOM)

        # Размер видимой области мира до зума.
        self.view_width = settings.SCREEN_WIDTH / self.zoom
        self.view_height = settings.SCREEN_HEIGHT / self.zoom

    def update(self, target_rect):
        # Центрируем камеру на игроке (в координатах мира, до зума).
        x = target_rect.centerx - self.view_width / 2
        y = target_rect.centery - self.view_height / 2

        # Не даём камере уезжать за пределы карты.
        max_x = max(0, self.tilemap.pixel_width - self.view_width)
        max_y = max(0, self.tilemap.pixel_height - self.view_height)

        x = max(0, min(x, max_x))
        y = max(0, min(y, max_y))

        self.offset = [x, y]

    def apply(self, rect):
        """Возвращает координаты объекта в системе координат вьюпорта (до зума)."""
        return rect.move(-self.offset[0], -self.offset[1])

    def apply_point(self, point):
        """То же для произвольной точки (x, y)."""
        return (point[0] - self.offset[0], point[1] - self.offset[1])

    def get_view_surface_size(self):
        """Размер промежуточного surface, который потом растягивается под зум."""
        return (round(self.view_width), round(self.view_height))
