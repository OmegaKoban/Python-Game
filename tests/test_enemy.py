"""
Тесты системы врагов.
Проверяют настройки врагов, систему волн и прогрессию сложности.
"""

import unittest
import sys
import os

# Добавляем корневую папку проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import settings


class TestEnemyTypes(unittest.TestCase):
    """Тесты типов врагов"""
    
    def test_all_enemy_types_have_required_fields(self):
        """Проверка, что у всех типов врагов есть необходимые поля"""
        required_fields = ['dir', 'frames', 'hp', 'speed', 'damage', 'scale', 'hitbox_scale']
        
        for enemy_type, enemy_data in settings.ENEMY_TYPES.items():
            for field in required_fields:
                self.assertIn(field, enemy_data,
                            f"Тип врага {enemy_type} должен иметь поле '{field}'")
    
    def test_enemy_hp_positive(self):
        """Проверка, что HP врагов положительное"""
        for enemy_type, enemy_data in settings.ENEMY_TYPES.items():
            self.assertGreater(enemy_data['hp'], 0,
                             f"HP {enemy_type} должно быть положительным")
    
    def test_enemy_speed_positive(self):
        """Проверка, что скорость врагов положительная"""
        for enemy_type, enemy_data in settings.ENEMY_TYPES.items():
            self.assertGreater(enemy_data['speed'], 0,
                             f"Скорость {enemy_type} должна быть положительной")
    
    def test_enemy_damage_positive(self):
        """Проверка, что урон врагов положительный"""
        for enemy_type, enemy_data in settings.ENEMY_TYPES.items():
            self.assertGreater(enemy_data['damage'], 0,
                             f"Урон {enemy_type} должен быть положительным")
    
    def test_enemy_scale_reasonable(self):
        """Проверка, что масштаб врагов разумный"""
        for enemy_type, enemy_data in settings.ENEMY_TYPES.items():
            scale = enemy_data['scale']
            self.assertGreater(scale, 0.1,
                             f"Масштаб {enemy_type} не должен быть слишком маленьким")
            self.assertLess(scale, 5.0,
                           f"Масштаб {enemy_type} не должен быть слишком большим")
    
    def test_stronger_enemies_have_more_hp(self):
        """Проверка прогрессии HP: slime1 < slime2 < slime3"""
        slime1_hp = settings.ENEMY_TYPES['slime1']['hp']
        slime2_hp = settings.ENEMY_TYPES['slime2']['hp']
        slime3_hp = settings.ENEMY_TYPES['slime3']['hp']
        
        self.assertLess(slime1_hp, slime2_hp,
                       "Слайм 2 должен иметь больше HP чем слайм 1")
        self.assertLess(slime2_hp, slime3_hp,
                       "Слайм 3 должен иметь больше HP чем слайм 2")
    
    def test_enemy_animations_have_frames(self):
        """Проверка, что у врагов есть кадры анимаций"""
        required_anims = ['run', 'attack', 'hurt', 'death']
        
        for enemy_type, enemy_data in settings.ENEMY_TYPES.items():
            frames = enemy_data['frames']
            for anim in required_anims:
                self.assertIn(anim, frames,
                            f"{enemy_type} должен иметь анимацию '{anim}'")
                self.assertGreater(frames[anim], 0,
                                 f"{enemy_type}.{anim} должна иметь > 0 кадров")


class TestWaveSystem(unittest.TestCase):
    """Тесты системы волн"""
    
    def test_wave_delays_positive(self):
        """Проверка, что задержки волн положительные"""
        self.assertGreater(settings.WAVE_START_DELAY, 0,
                          "Задержка старта должна быть положительной")
        self.assertGreater(settings.WAVE_INTERVAL, 0,
                          "Интервал между волнами должен быть положительным")
    
    def test_wave_enemy_count_grows(self):
        """Проверка, что количество врагов растёт с волнами"""
        wave_1_count = settings.WAVE_BASE_ENEMY_COUNT
        wave_5_count = wave_1_count + settings.WAVE_ENEMY_GROWTH * 4
        
        self.assertGreater(wave_5_count, wave_1_count,
                          "В 5-й волне должно быть больше врагов чем в 1-й")
    
    def test_wave_spawn_interval_reasonable(self):
        """Проверка, что интервал спавна разумный"""
        self.assertGreater(settings.WAVE_SPAWN_INTERVAL, 0.1,
                          "Интервал спавна не должен быть слишком маленьким")
        self.assertLess(settings.WAVE_SPAWN_INTERVAL, 5.0,
                       "Интервал спавна не должен быть слишком большим")
    
    def test_wave_hp_scaling_reasonable(self):
        """Проверка, что масштабирование HP разумное"""
        self.assertGreaterEqual(settings.WAVE_HP_SCALING, 0,
                               "Масштабирование HP не должно быть отрицательным")
        self.assertLess(settings.WAVE_HP_SCALING, 1.0,
                       "Масштабирование HP не должно быть слишком большим")


class TestEnemyUnlockSystem(unittest.TestCase):
    """Тесты системы разблокировки врагов"""
    
    def test_all_enemy_types_have_unlock_wave(self):
        """Проверка, что для всех типов врагов задана волна разблокировки"""
        for enemy_type in settings.ENEMY_TYPES.keys():
            self.assertIn(enemy_type, settings.ENEMY_TYPE_UNLOCK_WAVE,
                         f"{enemy_type} должен иметь волну разблокировки")
    
    def test_unlock_waves_are_positive(self):
        """Проверка, что волны разблокировки положительные"""
        for enemy_type, unlock_wave in settings.ENEMY_TYPE_UNLOCK_WAVE.items():
            self.assertGreater(unlock_wave, 0,
                             f"Волна разблокировки {enemy_type} должна быть > 0")
    
    def test_stronger_enemies_unlock_later(self):
        """Проверка, что сильные враги разблокируются позже"""
        slime1_wave = settings.ENEMY_TYPE_UNLOCK_WAVE['slime1']
        slime2_wave = settings.ENEMY_TYPE_UNLOCK_WAVE['slime2']
        slime3_wave = settings.ENEMY_TYPE_UNLOCK_WAVE['slime3']
        
        self.assertLessEqual(slime1_wave, slime2_wave,
                            "Слайм 2 должен разблокироваться не раньше слайма 1")
        self.assertLessEqual(slime2_wave, slime3_wave,
                            "Слайм 3 должен разблокироваться не раньше слайма 2")
    
    def test_weight_system_parameters_reasonable(self):
        """Проверка, что параметры системы весов разумные"""
        self.assertGreater(settings.ENEMY_TYPE_BASE_WEIGHT, 0,
                          "Базовый вес должен быть положительным")
        self.assertGreater(settings.ENEMY_TYPE_WEIGHT_GROWTH, 0,
                          "Рост веса должен быть положительным")
        self.assertGreaterEqual(settings.ENEMY_TYPE_MIN_WEIGHT, 0,
                               "Минимальный вес не должен быть отрицательным")


class TestEnemyProgression(unittest.TestCase):
    """Тесты прогрессии характеристик врагов"""
    
    def test_stat_growth_positive(self):
        """Проверка, что рост характеристик положительный"""
        self.assertGreaterEqual(settings.ENEMY_STAT_HP_GROWTH, 0,
                               "Рост HP не должен быть отрицательным")
        self.assertGreaterEqual(settings.ENEMY_STAT_DAMAGE_GROWTH, 0,
                               "Рост урона не должен быть отрицательным")
    
    def test_stat_growth_reasonable(self):
        """Проверка, что рост характеристик не слишком большой"""
        self.assertLess(settings.ENEMY_STAT_HP_GROWTH, 0.5,
                       "Рост HP не должен быть слишком большим (> 50% за волну)")
        self.assertLess(settings.ENEMY_STAT_DAMAGE_GROWTH, 0.5,
                       "Рост урона не должен быть слишком большим (> 50% за волну)")
    
    def test_death_animation_time_reasonable(self):
        """Проверка, что время анимации смерти разумное"""
        self.assertGreater(settings.ENEMY_DEATH_MAX_TIME, 0,
                          "Время анимации смерти должно быть положительным")
        self.assertLess(settings.ENEMY_DEATH_MAX_TIME, 5.0,
                       "Время анимации смерти не должно быть слишком большим")


if __name__ == '__main__':
    unittest.main()
