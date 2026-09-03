"""
Тесты общих настроек игры.
Проверяют корректность базовых параметров, констант и конфигурации.
"""

import unittest
import sys
import os

# Добавляем корневую папку проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import settings


class TestDisplaySettings(unittest.TestCase):
    """Тесты настроек дисплея"""
    
    def test_fps_reasonable(self):
        """Проверка, что FPS разумный"""
        self.assertGreater(settings.FPS, 30, "FPS не должен быть слишком низким")
        self.assertLess(settings.FPS, 240, "FPS не должен быть чрезмерно высоким")
    
    def test_tile_size_positive(self):
        """Проверка, что размер тайла положительный"""
        self.assertGreater(settings.TILE_SIZE, 0, "Размер тайла должен быть положительным")


class TestMapSettings(unittest.TestCase):
    """Тесты настроек карты"""
    
    def test_collision_zones_defined(self):
        """Проверка, что зоны коллизий определены"""
        self.assertIsNotNone(settings.COLLISION_ZONES, "Зоны коллизий должны быть определены")
        self.assertIsInstance(settings.COLLISION_ZONES, list, "Зоны коллизий должны быть списком")
        self.assertGreater(len(settings.COLLISION_ZONES), 0, "Должна быть хотя бы одна зона")
    
    def test_collision_zones_valid_format(self):
        """Проверка формата зон коллизий"""
        for i, zone in enumerate(settings.COLLISION_ZONES):
            self.assertIsInstance(zone, (list, tuple), 
                                f"Зона {i} должна быть списком или кортежем")
            self.assertEqual(len(zone), 4, 
                           f"Зона {i} должна содержать 4 координаты (x1, y1, x2, y2)")
            
            x1, y1, x2, y2 = zone
            self.assertLess(x1, x2, f"Зона {i}: x1 должен быть меньше x2")
            self.assertLess(y1, y2, f"Зона {i}: y1 должен быть меньше y2")


class TestColorSettings(unittest.TestCase):
    """Тесты настроек цветов"""
    
    def test_colors_are_valid_rgb(self):
        """Проверка, что цвета имеют правильный RGB формат"""
        colors_to_test = []
        
        # Собираем все цвета из настроек
        if hasattr(settings, 'COLOR_BLACK'):
            colors_to_test.append(('BLACK', settings.COLOR_BLACK))
        if hasattr(settings, 'COLOR_WHITE'):
            colors_to_test.append(('WHITE', settings.COLOR_WHITE))
        if hasattr(settings, 'COLOR_RED'):
            colors_to_test.append(('RED', settings.COLOR_RED))
        if hasattr(settings, 'COLOR_GREEN'):
            colors_to_test.append(('GREEN', settings.COLOR_GREEN))
        if hasattr(settings, 'COLOR_BLUE'):
            colors_to_test.append(('BLUE', settings.COLOR_BLUE))
        
        for color_name, color in colors_to_test:
            self.assertIsInstance(color, tuple, f"{color_name} должен быть кортежем")
            self.assertEqual(len(color), 3, f"{color_name} должен иметь 3 компонента")
            
            for i, component in enumerate(color):
                self.assertIsInstance(component, int, 
                                    f"{color_name} компонент {i} должен быть int")
                self.assertGreaterEqual(component, 0, 
                                       f"{color_name} компонент {i} >= 0")
                self.assertLessEqual(component, 255, 
                                    f"{color_name} компонент {i} <= 255")
    
    def test_black_and_white_correct(self):
        """Проверка правильности определения чёрного и белого"""
        if hasattr(settings, 'COLOR_BLACK'):
            self.assertEqual(settings.COLOR_BLACK, (0, 0, 0), "Чёрный должен быть (0, 0, 0)")
        
        if hasattr(settings, 'COLOR_WHITE'):
            self.assertEqual(settings.COLOR_WHITE, (255, 255, 255), 
                           "Белый должен быть (255, 255, 255)")


class TestGameBalanceSettings(unittest.TestCase):
    """Тесты настроек баланса игры"""
    
    def test_difficulty_curve_reasonable(self):
        """Проверка, что кривая сложности разумная"""
        # Проверяем соотношение характеристик игрока и врагов
        player_hp = settings.PLAYER_MAX_HP
        player_damage = settings.PLAYER_ATTACK_DAMAGE
        
        # Базовый слайм
        slime1 = settings.ENEMY_TYPES['slime1']
        
        # Игрок должен выдерживать несколько ударов
        hits_to_kill_player = player_hp / slime1['damage']
        self.assertGreater(hits_to_kill_player, 3,
                          "Игрок должен выдерживать хотя бы 3 удара слайма")
        
        # Игрок должен убивать слайма за разумное количество ударов
        hits_to_kill_slime = slime1['hp'] / player_damage
        self.assertLess(hits_to_kill_slime, 10,
                       "Слайм не должен требовать слишком много ударов")
    
    def test_movement_speed_balance(self):
        """Проверка баланса скорости движения"""
        player_speed = settings.PLAYER_SPEED
        
        # Проверяем скорости врагов
        for enemy_type, enemy_data in settings.ENEMY_TYPES.items():
            enemy_speed = enemy_data['speed']
            
            # Враги не должны быть намного быстрее игрока
            self.assertLess(enemy_speed, player_speed * 1.5,
                           f"{enemy_type} не должен быть слишком быстрым")
            
            # Но должны двигаться достаточно быстро
            self.assertGreater(enemy_speed, player_speed * 0.3,
                             f"{enemy_type} не должен быть слишком медленным")


class TestAnimationSettings(unittest.TestCase):
    """Тесты настроек анимаций"""
    
    def test_animation_speeds_reasonable(self):
        """Проверка, что скорости анимаций разумные"""
        animation_speed = getattr(settings, 'ANIMATION_SPEED', 0.2)
        
        if hasattr(settings, 'ANIMATION_SPEED'):
            self.assertGreater(animation_speed, 0.05,
                              "Скорость анимации не должна быть слишком медленной")
            self.assertLess(animation_speed, 1.0,
                           "Скорость анимации не должна быть слишком быстрой")
    
    def test_sprite_scales_positive(self):
        """Проверка, что масштабы спрайтов положительные"""
        # Проверяем масштабы из разных систем
        for enemy_type, enemy_data in settings.ENEMY_TYPES.items():
            scale = enemy_data.get('scale', 1.0)
            self.assertGreater(scale, 0, f"Масштаб {enemy_type} должен быть положительным")


class TestPathSettings(unittest.TestCase):
    """Тесты настроек путей к ресурсам"""
    
    def test_asset_paths_defined(self):
        """Проверка, что пути к ресурсам определены"""
        # Проверяем основные пути
        if hasattr(settings, 'ASSETS_DIR'):
            self.assertIsInstance(settings.ASSETS_DIR, str, "ASSETS_DIR должен быть строкой")
            self.assertGreater(len(settings.ASSETS_DIR), 0, "ASSETS_DIR не должен быть пустым")
        
        if hasattr(settings, 'PLAYER_SPRITE_DIR'):
            self.assertIsInstance(settings.PLAYER_SPRITE_DIR, str)
        
        if hasattr(settings, 'ENEMY_SPRITE_DIR'):
            self.assertIsInstance(settings.ENEMY_SPRITE_DIR, str)


class TestTimingSettings(unittest.TestCase):
    """Тесты настроек времени и интервалов"""
    
    def test_all_time_intervals_positive(self):
        """Проверка, что все временные интервалы положительные"""
        time_settings = [
            ('PLAYER_ATTACK_INTERVAL', settings.PLAYER_ATTACK_INTERVAL),
            ('PLAYER_INVULN_TIME', settings.PLAYER_INVULN_TIME),
            ('WAVE_INTERVAL', settings.WAVE_INTERVAL),
            ('WAVE_START_DELAY', settings.WAVE_START_DELAY),
        ]
        
        for name, value in time_settings:
            self.assertGreater(value, 0, f"{name} должен быть положительным")
    
    def test_time_intervals_reasonable(self):
        """Проверка, что временные интервалы не слишком большие"""
        # Атака не должна быть слишком редкой
        self.assertLess(settings.PLAYER_ATTACK_INTERVAL, 5.0,
                       "Интервал атаки не должен быть больше 5 секунд")
        
        # Волны не должны быть слишком частыми или редкими
        self.assertGreater(settings.WAVE_INTERVAL, 5.0,
                          "Интервал между волнами должен быть хотя бы 5 секунд")
        self.assertLess(settings.WAVE_INTERVAL, 120.0,
                       "Интервал между волнами не должен быть больше 2 минут")


class TestDataIntegrity(unittest.TestCase):
    """Тесты целостности данных"""
    
    def test_no_duplicate_enemy_types(self):
        """Проверка отсутствия дублирования типов врагов"""
        enemy_types = list(settings.ENEMY_TYPES.keys())
        unique_types = set(enemy_types)
        
        self.assertEqual(len(enemy_types), len(unique_types),
                        "Не должно быть дублирующихся типов врагов")
    
    def test_no_duplicate_abilities(self):
        """Проверка отсутствия дублирования способностей"""
        ability_ids = list(settings.ABILITIES.keys())
        unique_ids = set(ability_ids)
        
        self.assertEqual(len(ability_ids), len(unique_ids),
                        "Не должно быть дублирующихся ID способностей")
    
    def test_enemy_xp_rewards_match_types(self):
        """Проверка, что награды XP соответствуют типам врагов"""
        for enemy_type in settings.ENEMY_TYPES.keys():
            self.assertIn(enemy_type, settings.ENEMY_XP_REWARD,
                         f"Для {enemy_type} должна быть определена награда XP")
    
    def test_enemy_unlock_waves_match_types(self):
        """Проверка, что волны разблокировки соответствуют типам врагов"""
        for enemy_type in settings.ENEMY_TYPES.keys():
            self.assertIn(enemy_type, settings.ENEMY_TYPE_UNLOCK_WAVE,
                         f"Для {enemy_type} должна быть определена волна разблокировки")


class TestConsistency(unittest.TestCase):
    """Тесты согласованности настроек"""
    
    def test_ability_cooldown_consistency(self):
        """Проверка согласованности кулдаунов способностей"""
        # Все способности должны иметь кулдаун
        for ability_id, ability_data in settings.ABILITIES.items():
            cooldown = ability_data.get('cooldown')
            self.assertIsNotNone(cooldown, f"{ability_id} должен иметь кулдаун")
            self.assertIsInstance(cooldown, (int, float),
                                f"{ability_id} кулдаун должен быть числом")


if __name__ == '__main__':
    unittest.main()
