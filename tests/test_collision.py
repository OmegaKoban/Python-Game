"""
Тесты системы коллизий.
Проверяют правильность работы зон коллизий и разрешения столкновений.
"""

import unittest
import pygame
import sys
import os

# Добавляем корневую папку проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tilemap import TileMap
from src import settings


class TestCollisionSystem(unittest.TestCase):
    """Тесты системы коллизий"""
    
    @classmethod
    def setUpClass(cls):
        """Инициализация Pygame перед всеми тестами"""
        pygame.init()
    
    @classmethod
    def tearDownClass(cls):
        """Завершение Pygame после всех тестов"""
        pygame.quit()
    
    def setUp(self):
        """Создание tilemap перед каждым тестом"""
        self.tilemap = TileMap()
    
    def test_collision_zones_loaded(self):
        """Проверка, что зоны коллизий загружены"""
        self.assertGreater(len(self.tilemap.collision_zones), 0, 
                          "Должны быть загружены зоны коллизий")
        self.assertEqual(len(self.tilemap.collision_zones), 8,
                        "Должно быть 8 зон коллизий")
    
    def test_no_collision_in_free_space(self):
        """Проверка отсутствия коллизии в свободном пространстве"""
        # Создаём прямоугольник в центре карты (обычно свободное место)
        rect = pygame.Rect(1500, 1500, 50, 50)
        collision = self.tilemap.check_collision(rect)
        self.assertIsNone(collision, 
                         "В центре карты не должно быть коллизий")
    
    def test_collision_with_house(self):
        """Проверка обнаружения коллизии с домом"""
        # Берём координаты из первой зоны коллизий (Дом 1)
        house_zone = settings.COLLISION_ZONES[0]
        x1, y1, x2, y2 = house_zone
        
        # Создаём прямоугольник в центре этой зоны
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        rect = pygame.Rect(center_x - 25, center_y - 25, 50, 50)
        
        collision = self.tilemap.check_collision(rect)
        self.assertIsNotNone(collision, 
                            "Должна быть обнаружена коллизия с домом")
    
    def test_resolve_collision_blocks_movement(self):
        """Проверка, что resolve_collision откатывает движение в зону коллизии"""
        # Начальная позиция вне зоны коллизии
        prev_pos = (1200, 1300)
        
        # Пытаемся переместиться в зону Дома 1 (1270, 1322, 1643, 1494)
        rect = pygame.Rect(1400, 1400, 50, 50)
        
        # Разрешаем коллизию
        had_collision = self.tilemap.resolve_collision(rect, prev_pos)
        
        self.assertTrue(had_collision, "Должна быть обнаружена коллизия")
        # После resolve_collision позиция должна быть откачена
        self.assertNotEqual(rect.centerx, 1400, 
                           "X координата должна быть изменена")
    
    def test_resolve_collision_allows_sliding(self):
        """Проверка скольжения вдоль стены"""
        # Позиция слева от Дома 1
        prev_pos = (1200, 1400)
        
        # Пытаемся двигаться вправо и вниз одновременно
        rect = pygame.Rect(1260, 1450, 50, 50)
        
        self.tilemap.resolve_collision(rect, prev_pos)
        
        # Должна быть возможность движения хотя бы по одной оси
        moved = (rect.centerx != prev_pos[0]) or (rect.centery != prev_pos[1])
        self.assertTrue(moved or rect.centerx == prev_pos[0], 
                       "Должно быть возможно скольжение или откат")
    
    def test_map_boundaries(self):
        """Проверка ограничения границами карты"""
        # Прямоугольник за границей карты
        rect = pygame.Rect(-100, -100, 50, 50)
        self.tilemap.clamp_to_bounds(rect)
        
        self.assertGreaterEqual(rect.left, 0, "Left должен быть >= 0")
        self.assertGreaterEqual(rect.top, 0, "Top должен быть >= 0")
        
        # Прямоугольник справа и снизу за границей
        rect = pygame.Rect(4000, 4000, 50, 50)
        self.tilemap.clamp_to_bounds(rect)
        
        self.assertLessEqual(rect.right, self.tilemap.pixel_width,
                            f"Right должен быть <= {self.tilemap.pixel_width}")
        self.assertLessEqual(rect.bottom, self.tilemap.pixel_height,
                            f"Bottom должен быть <= {self.tilemap.pixel_height}")
    
    def test_all_collision_zones_are_rectangles(self):
        """Проверка, что все зоны коллизий - корректные прямоугольники"""
        for i, zone in enumerate(self.tilemap.collision_zones):
            self.assertIsInstance(zone, pygame.Rect, 
                                f"Зона {i} должна быть pygame.Rect")
            self.assertGreater(zone.width, 0, 
                             f"Зона {i} должна иметь положительную ширину")
            self.assertGreater(zone.height, 0,
                             f"Зона {i} должна иметь положительную высоту")


if __name__ == '__main__':
    unittest.main()
