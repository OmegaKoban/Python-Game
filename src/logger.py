"""
Система логирования для игры Auto Arsenal.

Уровни (от тихого к громкому):
  DEBUG    — детали работы (урон, попадания, позиции)
  INFO     — важные события (волны, level-up, пикапы, старт/конец игры)
  WARNING  — потенциальные проблемы (ассет не загрузился → заглушка)
  ERROR    — ошибки, которые не роняют игру (не сохранился рекорд)
  CRITICAL — фатальные ошибки (игра может упасть)

В файл пишется всё начиная с DEBUG.
В консоль пишется всё начиная с DEBUG (с цветами по уровню).

Использование:
    from src.logger import get_logger
    logger = get_logger()

    logger.debug("pos={}".format(pos))
    logger.info("Игра началась")
    logger.warning("Спрайт не найден: {}".format(path))
    logger.error("Не удалось сохранить рекорд")
    logger.critical("Критический сбой инициализации")

    # Готовые хелперы для типовых событий:
    logger.asset(path, loaded=False)          # WARNING / DEBUG о загрузке ассета
    logger.wave_start(number, count)          # INFO о начале волны
    logger.wave_end(number)                   # INFO о конце волны
    logger.combat(msg)                        # DEBUG боевого события
    logger.levelup(level)                     # INFO о повышении уровня
    logger.pickup(kind, value)                # DEBUG о подборе предмета
    logger.game_over(kills, waves)            # INFO об окончании игры
    logger.perf(metric, value)                # DEBUG метрики производительности
"""

import logging
import os
import sys
from datetime import datetime


# ── ANSI-коды цветов для консольного вывода ──────────────────────────────────
_RESET  = "\033[0m"
_GREY   = "\033[90m"
_CYAN   = "\033[96m"
_YELLOW = "\033[93m"
_RED    = "\033[91m"
_BOLD_RED = "\033[1;91m"

_LEVEL_COLORS = {
    logging.DEBUG:    _GREY,
    logging.INFO:     _CYAN,
    logging.WARNING:  _YELLOW,
    logging.ERROR:    _RED,
    logging.CRITICAL: _BOLD_RED,
}

# Метки категорий — видны в файле и консоли
_CAT_ASSET  = "ASSET"
_CAT_WAVE   = "WAVE"
_CAT_COMBAT = "COMBAT"
_CAT_LEVEL  = "LEVELUP"
_CAT_PICKUP = "PICKUP"
_CAT_GAME   = "GAME"
_CAT_PERF   = "PERF"


class _ColorFormatter(logging.Formatter):
    """Форматтер с ANSI-цветами по уровню (только для консоли)."""

    def format(self, record):
        color = _LEVEL_COLORS.get(record.levelno, _RESET)
        record.levelname = f"{color}{record.levelname:<8}{_RESET}"
        return super().format(record)


class GameLogger:
    """
    Singleton-логгер игры.

    Один файловый хендлер (DEBUG+, без цветов) и один консольный
    хендлер (DEBUG+, с ANSI-цветами).
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # ── Папка и файл лога ────────────────────────────────────────────────
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._log_file = os.path.join(log_dir, f"game_{timestamp}.log")

        # ── Корневой логгер ──────────────────────────────────────────────────
        self._log = logging.getLogger("AutoArsenal")
        self._log.setLevel(logging.DEBUG)
        # Не пробрасываем в root-логгер Python — избегаем дублей.
        self._log.propagate = False

        # ── Формат файла ─────────────────────────────────────────────────────
        _file_fmt = logging.Formatter(
            "%(asctime)s  %(levelname)-8s  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = logging.FileHandler(self._log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(_file_fmt)
        self._log.addHandler(file_handler)

        # ── Формат консоли (цвета) ───────────────────────────────────────────
        # Цвета поддерживаются в обычных терминалах; в Windows IDE может не работать.
        _supports_color = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
        if _supports_color:
            _con_fmt = _ColorFormatter(
                "%(asctime)s  %(levelname)s  %(message)s",
                datefmt="%H:%M:%S",
            )
        else:
            _con_fmt = logging.Formatter(
                "%(asctime)s  %(levelname)-8s  %(message)s",
                datefmt="%H:%M:%S",
            )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(_con_fmt)
        self._log.addHandler(console_handler)

        # ── Стартовый баннер ─────────────────────────────────────────────────
        sep = "─" * 60
        self._log.info(sep)
        self._log.info("Auto Arsenal — система логирования запущена")
        self._log.info("Лог-файл : %s", self._log_file)
        self._log.info(
            "Уровни   : DEBUG | INFO | WARNING | ERROR | CRITICAL"
        )
        self._log.info(sep)

    # ── Базовые методы ───────────────────────────────────────────────────────

    def debug(self, message: str) -> None:
        """Детали работы: координаты, значения урона, флаги."""
        self._log.debug(message)

    def info(self, message: str) -> None:
        """Важные события: начало игры, волны, level-up."""
        self._log.info(message)

    def warning(self, message: str) -> None:
        """Потенциальные проблемы: ассет не найден, заглушка заменяет спрайт."""
        self._log.warning(message)

    def error(self, message: str) -> None:
        """Ошибки, не роняющие игру: сбой записи рекорда, I/O."""
        self._log.error(message)

    def critical(self, message: str) -> None:
        """Фатальные ошибки: игра может упасть."""
        self._log.critical(message)

    # ── Хелперы для типовых игровых событий ─────────────────────────────────

    def asset(self, path: str, loaded: bool) -> None:
        """
        Событие загрузки ассета.
        loaded=True  → DEBUG  «загружен»
        loaded=False → WARNING «не найден, используется заглушка»
        """
        if loaded:
            self._log.debug("[%s] Загружен: %s", _CAT_ASSET, path)
        else:
            self._log.warning(
                "[%s] Не найден, используется заглушка: %s", _CAT_ASSET, path
            )

    def wave_start(self, number: int, enemy_count: int) -> None:
        """INFO о начале волны."""
        self._log.info(
            "[%s] ── Волна %d начата, врагов: %d ──",
            _CAT_WAVE, number, enemy_count,
        )

    def wave_end(self, number: int) -> None:
        """INFO о конце волны."""
        self._log.info("[%s] Волна %d завершена", _CAT_WAVE, number)

    def wave_fallback_spawn(self, enemy_type: str) -> None:
        """WARNING: не нашлась валидная позиция спавна — помещён в центр."""
        self._log.warning(
            "[%s] Не найдена валидная позиция спавна для %s — помещён в центр карты",
            _CAT_WAVE, enemy_type,
        )

    def combat(self, message: str) -> None:
        """DEBUG для боевых событий (урон, попадание, смерть врага)."""
        self._log.debug("[%s] %s", _CAT_COMBAT, message)

    def levelup(self, level: int) -> None:
        """INFO о повышении уровня игрока."""
        self._log.info("[%s] Игрок достиг уровня %d", _CAT_LEVEL, level)

    def pickup(self, kind: str, value) -> None:
        """DEBUG о подборе предмета."""
        self._log.debug("[%s] Подобран %s (значение: %s)", _CAT_PICKUP, kind, value)

    def game_over(self, kills: int, waves: int) -> None:
        """INFO об окончании игры."""
        self._log.info(
            "[%s] Игра окончена — убито врагов: %d, пройдено волн: %d",
            _CAT_GAME, kills, waves,
        )

    def perf(self, metric: str, value) -> None:
        """DEBUG для метрик производительности."""
        self._log.debug("[%s] %s = %s", _CAT_PERF, metric, value)


# ── Глобальный доступ ─────────────────────────────────────────────────────────

_logger: GameLogger | None = None


def get_logger() -> GameLogger:
    """Возвращает единственный экземпляр GameLogger (создаёт при первом вызове)."""
    global _logger
    if _logger is None:
        _logger = GameLogger()
    return _logger
