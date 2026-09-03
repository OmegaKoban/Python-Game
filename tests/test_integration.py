"""
Интеграционные тесты игровых систем.
Проверяют взаимодействие между различными компонентами игры.
"""

import unittest
import sys
import os

# Добавляем корневую папку проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import settings


class TestPlayerEnemyBalance(unittest.TestCase):
    """Тесты баланса между игроком и врагами"""
    
    def test_player_can_survive_early_waves(self):
        """Проверка, что игрок может пережить начальные волны"""
        player_hp = settings.PLAYER_MAX_HP
        
        # Берём самого слабого врага
        weakest_enemy = min(settings.ENEMY_TYPES.values(), key=lambda x: x['damage'])
        enemy_damage = weakest_enemy['damage']
        
        # Количество врагов в первой волне
        first_wave_count = settings.WAVE_BASE_ENEMY_COUNT
        
        # Игрок должен выдержать хотя бы несколько атак первой волны
        hits_to_kill = player_hp / enemy_damage
        
        self.assertGreater(hits_to_kill, first_wave_count * 0.5,
                          "Игрок должен выдерживать хотя бы половину атак первой волны")
    
    def test_player_can_kill_enemies_in_reasonable_time(self):
        """Проверка, что игрок может убивать врагов за разумное время"""
        player_damage = settings.PLAYER_ATTACK_DAMAGE
        attack_interval = settings.PLAYER_ATTACK_INTERVAL
        
        # DPS игрока
        player_dps = player_damage / attack_interval
        
        # Проверяем на базовом враге
        base_enemy = settings.ENEMY_TYPES['slime1']
        enemy_hp = base_enemy['hp']
        
        time_to_kill = enemy_hp / player_dps
        
        # Убийство не должно занимать слишком долго
        self.assertLess(time_to_kill, 5.0,
                       "Базовый враг должен умирать меньше чем за 5 секунд")
        
        # Но и не мгновенно
        self.assertGreater(time_to_kill, 0.5,
                          "Базовый враг не должен умирать мгновенно")
    
    def test_enemy_progression_matches_player_progression(self):
        """Проверка, что усиление врагов соответствует усилению игрока"""
        # Рост HP врагов за волну
        enemy_hp_growth = getattr(settings, 'WAVE_HP_SCALING', 0.1)
        
        # Рост урона игрока за уровень
        player_damage_growth = settings.UPGRADE_ATTACK_DAMAGE_MULT
        
        # Усиление игрока должно быть сопоставимо с усилением врагов
        # Иначе игра станет либо слишком лёгкой, либо невозможной
        self.assertLess(abs(enemy_hp_growth - player_damage_growth), 0.3,
                       "Прогрессия врагов и игрока должна быть сбалансирована")


class TestLevelingProgression(unittest.TestCase):
    """Тесты прогрессии уровней"""
    
    def test_leveling_speed_reasonable(self):
        """Проверка, что скорость получения уровней разумная"""
        # XP за убийство базового врага
        base_xp = settings.ENEMY_XP_REWARD['slime1']
        
        # XP для первого уровня
        level_1_threshold = settings.XP_BASE
        
        # Количество убийств для первого уровня
        kills_for_level = level_1_threshold / base_xp
        
        self.assertGreater(kills_for_level, 3,
                          "Первый уровень не должен даваться слишком быстро")
        self.assertLess(kills_for_level, 30,
                       "Первый уровень не должен требовать слишком много убийств")
    
    def test_xp_scaling_with_wave_scaling(self):
        """Проверка, что масштабирование XP соответствует волнам"""
        # Враги в поздних волнах сильнее, но дают больше XP
        slime1_xp = settings.ENEMY_XP_REWARD['slime1']
        slime3_xp = settings.ENEMY_XP_REWARD['slime3']
        
        slime1_hp = settings.ENEMY_TYPES['slime1']['hp']
        slime3_hp = settings.ENEMY_TYPES['slime3']['hp']
        
        # XP за единицу HP должен быть примерно одинаковым
        xp_per_hp_1 = slime1_xp / slime1_hp
        xp_per_hp_3 = slime3_xp / slime3_hp
        
        ratio = xp_per_hp_3 / xp_per_hp_1
        
        # Соотношение должно быть разумным (более сильные враги могут давать чуть больше)
        self.assertGreater(ratio, 0.5,
                          "Более сильные враги не должны быть слишком невыгодными")
        self.assertLess(ratio, 3.0,
                       "Более сильные враги не должны быть чрезмерно выгодными")


class TestWaveProgression(unittest.TestCase):
    """Тесты прогрессии волн"""
    
    def test_enemy_spawn_rate_manageable(self):
        """Проверка, что скорость спавна врагов управляемая"""
        base_enemy_count = settings.WAVE_BASE_ENEMY_COUNT
        spawn_interval = settings.WAVE_SPAWN_INTERVAL
        
        # Время спавна всех врагов волны
        total_spawn_time = base_enemy_count * spawn_interval
        
        # Не должны все спавниться мгновенно
        self.assertGreater(total_spawn_time, 1.0,
                          "Враги не должны спавниться все мгновенно")
        
        # Но и не слишком долго
        wave_interval = settings.WAVE_INTERVAL
        self.assertLess(total_spawn_time, wave_interval * 0.7,
                       "Спавн врагов не должен занимать большую часть волны")
    
    def test_wave_difficulty_increases(self):
        """Проверка, что сложность волн растёт"""
        wave_1_enemies = settings.WAVE_BASE_ENEMY_COUNT
        wave_10_enemies = wave_1_enemies + settings.WAVE_ENEMY_GROWTH * 9
        
        self.assertGreater(wave_10_enemies, wave_1_enemies * 1.5,
                          "В 10-й волне должно быть значительно больше врагов")
        
        # Но не должно быть экспоненциального роста
        self.assertLess(wave_10_enemies, wave_1_enemies * 10,
                       "Рост количества врагов не должен быть слишком быстрым")


class TestAbilitySystem(unittest.TestCase):
    """Тесты системы способностей и их взаимодействия"""
    
    def test_abilities_complement_base_attack(self):
        """Проверка, что способности дополняют базовую атаку"""
        base_dps = settings.PLAYER_ATTACK_DAMAGE / settings.PLAYER_ATTACK_INTERVAL
        
        # Проверяем DPS способностей
        for ability_id, ability_data in settings.ABILITIES.items():
            ability_damage = ability_data['damage']
            ability_cooldown = ability_data['cooldown']
            
            ability_dps = ability_damage / ability_cooldown
            
            # Способности должны добавлять значимый урон, но не затмевать базовую атаку
            self.assertGreater(ability_dps, base_dps * 0.1,
                             f"{ability_id} должна добавлять хотя бы 10% от базового DPS")
            
            # На первом уровне способность не должна быть сильнее базовой атаки в разы
            self.assertLess(ability_dps, base_dps * 5,
                           f"{ability_id} не должна быть слишком сильной на первом уровне")
    
    def test_ability_max_levels_reasonable(self):
        """Проверка, что максимальные уровни способностей достижимы"""
        max_player_level = 20  # Предполагаемый максимальный уровень игрока
        
        total_max_ability_levels = sum(
            ability_data['max_level'] 
            for ability_data in settings.ABILITIES.values()
        )
        
        # Количество выборов при прокачке
        available_upgrades = max_player_level - 1  # -1 потому что первый уровень стартовый
        
        # Невозможно прокачать все способности до максимума
        # Это создаёт выбор и реиграбельность
        self.assertGreater(total_max_ability_levels, available_upgrades,
                          "Должен быть выбор при прокачке способностей")


class TestResourceManagement(unittest.TestCase):
    """Тесты управления ресурсами"""
    
    def test_xp_economy_progression(self):
        """Проверка экономики опыта"""
        # XP за первую волну
        wave_1_enemies = settings.WAVE_BASE_ENEMY_COUNT
        xp_per_enemy = settings.ENEMY_XP_REWARD['slime1']
        wave_1_xp = wave_1_enemies * xp_per_enemy
        
        # XP для первого уровня
        level_1_threshold = settings.XP_BASE
        
        # Первый уровень должен быть достижим за 1-3 волны
        waves_for_level = level_1_threshold / wave_1_xp
        
        self.assertGreater(waves_for_level, 0.5,
                          "Первый уровень не должен даваться за полволны")
        self.assertLess(waves_for_level, 5,
                       "Первый уровень должен быть достижим за несколько волн")


class TestGamePacing(unittest.TestCase):
    """Тесты темпа игры"""
    
    def test_early_game_not_too_slow(self):
        """Проверка, что начало игры не слишком медленное"""
        # Задержка до первой волны
        start_delay = settings.WAVE_START_DELAY
        
        # Не должна быть слишком долгой
        self.assertLess(start_delay, 10.0,
                       "Задержка до первой волны не должна быть слишком большой")
        
        # Но должна дать время осмотреться
        self.assertGreater(start_delay, 1.0,
                          "Должно быть время на ознакомление с управлением")


class TestUserExperience(unittest.TestCase):
    """Тесты пользовательского опыта"""
    
    def test_invulnerability_prevents_instant_death(self):
        """Проверка, что неуязвимость предотвращает мгновенную смерть"""
        invuln_time = settings.PLAYER_INVULN_TIME
        enemy_attack_interval = 1.0  # Примерный интервал атаки врагов
        
        # Неуязвимость должна длиться дольше одной атаки
        self.assertGreater(invuln_time, enemy_attack_interval * 0.5,
                          "Неуязвимость должна давать время на реакцию")
    
    def test_visual_feedback_timing(self):
        """Проверка таймингов визуальной обратной связи"""
        # Время анимации смерти врагов
        death_time = settings.ENEMY_DEATH_MAX_TIME
        
        # Должно быть заметным, но не затягивать игру
        self.assertGreater(death_time, 0.2,
                          "Анимация смерти должна быть заметной")
        self.assertLess(death_time, 3.0,
                       "Анимация смерти не должна затягивать игру")


class TestEdgeCases(unittest.TestCase):
    """Тесты граничных случаев"""
    
    def test_zero_hp_scenarios(self):
        """Проверка обработки нулевого HP"""
        # HP никогда не должно быть нулевым или отрицательным в начале
        self.assertGreater(settings.PLAYER_MAX_HP, 0)
        
        for enemy_type, enemy_data in settings.ENEMY_TYPES.items():
            self.assertGreater(enemy_data['hp'], 0,
                             f"{enemy_type} должен иметь положительное HP")
    
    def test_extreme_level_values(self):
        """Проверка экстремальных значений уровней"""
        # Проверяем формулу XP на высоких уровнях
        def calculate_xp_threshold(level):
            return int(settings.XP_BASE * (settings.XP_GROWTH ** (level - 1)) + 
                      settings.XP_FLAT_ADD * (level - 1))
        
        # На уровне 100 не должно быть переполнения
        try:
            xp_100 = calculate_xp_threshold(100)
            self.assertIsInstance(xp_100, int)
            self.assertGreater(xp_100, 0)
        except OverflowError:
            self.fail("Формула XP вызывает переполнение на высоких уровнях")
    
    def test_max_enemies_on_screen(self):
        """Проверка максимального количества врагов"""
        # Максимальное количество врагов в поздней волне
        wave_50_enemies = settings.WAVE_BASE_ENEMY_COUNT + settings.WAVE_ENEMY_GROWTH * 49
        
        # Не должно быть слишком много для производительности
        self.assertLess(wave_50_enemies, 500,
                       "Количество врагов не должно быть чрезмерным для производительности")


if __name__ == '__main__':
    unittest.main()
