"""
Тесты игрока и его систем.
Проверяют характеристики игрока, систему здоровья, опыта и уровней.
"""

import unittest
import pygame
import sys
import os

# Добавляем корневую папку проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import settings


class TestPlayerSettings(unittest.TestCase):
    """Тесты настроек игрока"""
    
    def test_player_has_positive_speed(self):
        """Проверка, что скорость игрока положительная"""
        self.assertGreater(settings.PLAYER_SPEED, 0,
                          "Скорость игрока должна быть положительной")
    
    def test_player_has_positive_health(self):
        """Проверка, что здоровье игрока положительное"""
        self.assertGreater(settings.PLAYER_MAX_HP, 0,
                          "Максимальное здоровье должно быть положительным")
    
    def test_player_attack_interval_positive(self):
        """Проверка, что интервал атаки положительный"""
        self.assertGreater(settings.PLAYER_ATTACK_INTERVAL, 0,
                          "Интервал атаки должен быть положительным")
    
    def test_player_attack_range_positive(self):
        """Проверка, что радиус атаки положительный"""
        self.assertGreater(settings.PLAYER_ATTACK_RANGE, 0,
                          "Радиус атаки должен быть положительным")
    
    def test_player_attack_damage_positive(self):
        """Проверка, что урон игрока положительный"""
        self.assertGreater(settings.PLAYER_ATTACK_DAMAGE, 0,
                          "Урон атаки должен быть положительным")
    
    def test_invulnerability_time_reasonable(self):
        """Проверка, что время неуязвимости разумное"""
        self.assertGreater(settings.PLAYER_INVULN_TIME, 0,
                          "Время неуязвимости должно быть положительным")
        self.assertLess(settings.PLAYER_INVULN_TIME, 5,
                       "Время неуязвимости не должно быть слишком большим")


class TestExperienceSystem(unittest.TestCase):
    """Тесты системы опыта"""
    
    def test_xp_formula_grows(self):
        """Проверка, что порог опыта растёт с уровнем"""
        def calculate_xp_threshold(level):
            return int(settings.XP_BASE * (settings.XP_GROWTH ** (level - 1)) + 
                      settings.XP_FLAT_ADD * (level - 1))
        
        threshold_1 = calculate_xp_threshold(1)
        threshold_2 = calculate_xp_threshold(2)
        threshold_5 = calculate_xp_threshold(5)
        
        self.assertLess(threshold_1, threshold_2,
                       "Порог 2-го уровня должен быть выше 1-го")
        self.assertLess(threshold_2, threshold_5,
                       "Порог 5-го уровня должен быть выше 2-го")
    
    def test_enemy_xp_rewards_positive(self):
        """Проверка, что награды за врагов положительные"""
        for enemy_type, xp in settings.ENEMY_XP_REWARD.items():
            self.assertGreater(xp, 0,
                             f"XP за {enemy_type} должен быть положительным")
    
    def test_stronger_enemies_give_more_xp(self):
        """Проверка, что сильные враги дают больше опыта"""
        slime1_xp = settings.ENEMY_XP_REWARD.get("slime1", 0)
        slime3_xp = settings.ENEMY_XP_REWARD.get("slime3", 0)
        
        self.assertLess(slime1_xp, slime3_xp,
                       "Слайм 3 уровня должен давать больше XP чем слайм 1")


class TestAbilitySystem(unittest.TestCase):
    """Тесты системы способностей"""
    
    def test_all_abilities_have_required_fields(self):
        """Проверка, что у всех способностей есть необходимые поля"""
        required_fields = ['name', 'desc', 'kind', 'max_level', 'cooldown', 'damage']
        
        for ability_id, ability_data in settings.ABILITIES.items():
            for field in required_fields:
                self.assertIn(field, ability_data,
                            f"Способность {ability_id} должна иметь поле '{field}'")
    
    def test_ability_cooldowns_positive(self):
        """Проверка, что кулдауны способностей положительные"""
        for ability_id, ability_data in settings.ABILITIES.items():
            self.assertGreater(ability_data['cooldown'], 0,
                             f"Кулдаун {ability_id} должен быть положительным")
    
    def test_ability_damage_positive(self):
        """Проверка, что урон способностей положительный"""
        for ability_id, ability_data in settings.ABILITIES.items():
            self.assertGreater(ability_data['damage'], 0,
                             f"Урон {ability_id} должен быть положительным")
    
    def test_ability_max_level_reasonable(self):
        """Проверка, что максимальный уровень способностей разумный"""
        for ability_id, ability_data in settings.ABILITIES.items():
            max_level = ability_data['max_level']
            self.assertGreaterEqual(max_level, 1,
                                   f"Макс. уровень {ability_id} должен быть >= 1")
            self.assertLessEqual(max_level, 20,
                                f"Макс. уровень {ability_id} не должен быть слишком большим")


class TestUpgradeSystem(unittest.TestCase):
    """Тесты системы улучшений"""
    
    def test_upgrade_multipliers_positive(self):
        """Проверка, что множители улучшений положительные"""
        self.assertGreater(settings.UPGRADE_ATTACK_DAMAGE_MULT, 0,
                          "Множитель урона должен быть положительным")
        self.assertGreater(settings.UPGRADE_ATTACK_SPEED_MULT, 0,
                          "Множитель скорости должен быть положительным")
        self.assertGreater(settings.UPGRADE_MAX_HP_ADD, 0,
                          "Прибавка HP должна быть положительной")
    
    def test_upgrade_multipliers_reasonable(self):
        """Проверка, что множители улучшений не слишком большие"""
        self.assertLess(settings.UPGRADE_ATTACK_DAMAGE_MULT, 1.0,
                       "Множитель урона не должен быть >= 100%")
        self.assertLess(settings.UPGRADE_ATTACK_SPEED_MULT, 0.5,
                       "Множитель скорости атаки не должен быть слишком большим")


if __name__ == '__main__':
    unittest.main()
