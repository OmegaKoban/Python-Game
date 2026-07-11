"""
Запуск всех тестов игры Auto Arsenal.
Выполняет все тесты и выводит отчёт о результатах.
"""

import unittest
import sys
import os

# Добавляем корневую папку проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_all_tests():
    """Запускает все тесты и возвращает результат"""
    # Создаём загрузчик тестов
    loader = unittest.TestLoader()
    
    # Находим все тесты в текущей папке
    test_dir = os.path.dirname(__file__)
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # Создаём runner с подробным выводом
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Запускаем тесты
    print("=" * 70)
    print("Запуск тестов Auto Arsenal")
    print("=" * 70)
    
    result = runner.run(suite)
    
    # Выводим итоги
    print("\n" + "=" * 70)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 70)
    print(f"Всего тестов выполнено: {result.testsRun}")
    print(f"Успешно: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Провалено: {len(result.failures)}")
    print(f"Ошибок: {len(result.errors)}")
    print(f"Пропущено: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return 0
    else:
        print("\n❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
