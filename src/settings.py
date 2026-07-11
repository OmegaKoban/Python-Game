"""
Настройки игры: размеры окна, карты, тайлов, путей к ассетам,
а также параметры боевой системы (игрок, враги, снаряды, волны).
Меняй эти значения под свои ассеты — не нужно лезть в остальной код.
"""

import os


# ---------- Пути ----------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Положи сюда свою картинку клетки карты (один тайл).
TILE_IMAGE_PATH = os.path.join(ASSETS_DIR, "tiles", "tile.jpeg")

# Спрайт персонажа для состояния покоя (idle). Одиночный кадр или спрайт-лист.
PLAYER_IDLE_IMAGE_PATH = os.path.join(ASSETS_DIR, "player", "Warrior_Idle.png")
PLAYER_IDLE_FRAME_COUNT = 8

# Спрайт персонажа для состояния движения (walk).
PLAYER_WALK_IMAGE_PATH = os.path.join(ASSETS_DIR, "player", "Warrior_Run.png")
PLAYER_WALK_FRAME_COUNT = 6

# Два спрайт-листа атаки (покадрово, как idle/walk). Они чередуются по очереди:
# attack1 -> attack2 -> attack1 -> ...
PLAYER_ATTACK1_IMAGE_PATH = os.path.join(ASSETS_DIR, "player", "Warrior_Attack1.png")
PLAYER_ATTACK1_FRAME_COUNT = 4

PLAYER_ATTACK2_IMAGE_PATH = os.path.join(ASSETS_DIR, "player", "Warrior_Attack2.png")
PLAYER_ATTACK2_FRAME_COUNT = 4

# Скорость смены кадров обычной анимации (idle/walk), кадров в секунду.
PLAYER_ANIMATION_SPEED = 8
# Скорость смены кадров анимации атаки (отдельно, чтобы удар был резче).
PLAYER_ATTACK_ANIMATION_SPEED = 14

# ---------- Окно ----------
# Режимы: "fullscreen" | "borderless" | "window"
# На macOS "borderless" (NOFRAME) не скрывает системный menu bar (Wi-Fi, время и т.д.)
# — используй "fullscreen" для полного захвата экрана.
SCREEN_MODE = "fullscreen"
SCREEN_WIDTH = 960   # используется только при SCREEN_MODE = "window"
SCREEN_HEIGHT = 640
FPS = 60
WINDOW_TITLE = "Auto Arsenal"

# ---------- Меню (главный экран) ----------
# Папка с ассетами меню.
MENU_DIR = os.path.join(ASSETS_DIR, "menu")
# Фон-подложка (небо), на котором летят облака.
MENU_BACKGROUND_PATH = os.path.join(MENU_DIR, "background.png")
# Панель-свиток, на которой лежат пункты меню.
MENU_PANEL_PATH = os.path.join(MENU_DIR, "panel.png")
# Шаблон пути к спрайтам облаков (6 штук: cloud_1.png ... cloud_6.png).
MENU_CLOUD_PATH_TMPL = os.path.join(MENU_DIR, "cloud_{}.png")
MENU_CLOUD_COUNT = 6

# Направление движения облаков: "right" (слева направо) или "left".
MENU_CLOUD_DIRECTION = "right"
# Диапазон скоростей облаков (пиксели/сек) — берётся случайно из [min, max].
# Разные скорости дают лёгкий эффект параллакса и живость.
MENU_CLOUD_SPEED_RANGE = (14, 46)
# Диапазон масштаба облаков (доля от исходного размера).
MENU_CLOUD_SCALE_RANGE = (0.55, 1.15)
# Прозрачность облаков (0..255). Чуть приглушаем, чтобы не спорили с фоном.
MENU_CLOUD_ALPHA = 235

# Ширина панели-свитка как доля от ширины экрана.
MENU_PANEL_WIDTH_RATIO = 0.48
# Высота панели-свитка как доля от высоты экрана (для вертикального свитка).
MENU_PANEL_HEIGHT_RATIO = 0.7
# Смещение центра панели по вертикали (доля высоты экрана; 0.5 = центр).
MENU_PANEL_CENTER_Y_RATIO = 0.5

# Заголовок игры на панели.
MENU_TITLE = "AUTO ARSENAL"
# Пункты меню (id, подпись). Обрабатываются в main.py.
MENU_ITEMS = [
    ("play", "Играть"),
    ("settings", "Настройки"),
    ("records", "Рекорды"),
    ("quit", "Выход"),
]

# Цвета текста меню (в тон пергаменту — тёмно-коричневый).
MENU_TITLE_COLOR = (74, 47, 24)
MENU_ITEM_COLOR = (92, 62, 34)
MENU_ITEM_HOVER_COLOR = (150, 92, 30)
MENU_TITLE_FONT_SIZE = 32
MENU_ITEM_FONT_SIZE = 24
# Цвет неба-заглушки, если фон не загрузился.
MENU_FALLBACK_SKY = (128, 116, 168)

# ---------- Настройки (экран настроек) ----------
SETTINGS_TITLE = "НАСТРОЙКИ"
SETTINGS_PLAYER_NAME = "Игрок"   # имя игрока
SETTINGS_BRIGHTNESS = 1.0         # яркость игры (0.2 — 1.0)
SETTINGS_VOLUME = 0.5             # громкость (0.0 — 1.0)
TILE_SIZE = 3000

# Карта фиксированного размера — сколько тайлов по ширине и высоте.
# Размер подобран так, чтобы враги с краёв успевали набегать на игрока.
MAP_WIDTH_TILES = 1
MAP_HEIGHT_TILES = 1

# Зоны коллизий (домики, препятствия)
# Формат: (x1, y1, x2, y2) где (x1,y1) — левый верхний угол, (x2,y2) — правый нижний
# Используй find_collision_zones.py чтобы найти координаты
COLLISION_ZONES = [
    # Дом 1
    (1270, 1322, 1643, 1494),
    # Дом 2
    (1439, 1193, 1489, 1313),
    # Дом 3
    (1680, 1515, 1770, 1605),
    # Дом 4
    (2391, 2345, 2416, 2435),
    # Дом 5
    (2686, 2348, 2721, 2431),
    # Дом 6
    (2883, 2563, 2962, 2643),
    # Дом 7
    (271, 1360, 396, 1490),
    # Дом 8 (труба дома 7)
    (328, 1235, 338, 1330),
]

# Запасные цвета, если ассеты не загрузятся.
FALLBACK_TILE_COLOR = (40, 44, 52)
FALLBACK_PLAYER_COLOR = (233, 69, 96)

# ---------- Игрок ----------
PLAYER_SPEED = 220  # пикселей в секунду

# Размер персонажа как доля от размера клетки (TILE_SIZE).
PLAYER_SCALE = 0.25/4.0
PLAYER_SIZE = (int(TILE_SIZE * PLAYER_SCALE), int(TILE_SIZE * PLAYER_SCALE))

# Здоровье игрока.
PLAYER_MAX_HP = 100

# Хитбокс игрока как доля от размера спрайта (ширина, высота). Спрайты обычно
# имеют прозрачные поля вокруг тела, поэтому хитбокс делают меньше картинки.
# 1.0 = во весь спрайт, 0.5 = половина. По нему считается урон от врагов.
PLAYER_HITBOX_SCALE = (0.4, 0.6)

# Неуязвимость после получения урона (секунды) — чтобы не сливали за кадр.
PLAYER_INVULN_TIME = 0.6

# --- Боевая система игрока (автоатака) ---
# Как часто игрок атакует (секунды). Меньше = чаще.
PLAYER_ATTACK_INTERVAL = 0.9
# Радиус, в котором игрок автоматически бьёт ближайшего врага (пиксели).
PLAYER_ATTACK_RANGE = 500
# Урон одной атаки.
PLAYER_ATTACK_DAMAGE = 34

# --- Снаряды игрока ---
# Тип боя: "melee" — урон по площади вокруг игрока в момент атаки;
#          "ranged" — выпускает снаряд в сторону ближайшего врага.
PLAYER_COMBAT_MODE = "ranged"
PROJECTILE_SPEED = 520          # скорость снаряда, пиксели/сек
PROJECTILE_RADIUS = 10          # радиус снаряда-заглушки (если нет ассета)
PROJECTILE_LIFETIME = 1.5       # сколько секунд живёт снаряд
PROJECTILE_COLOR = (255, 214, 90)

# --- Ассет снаряда (анимированный спрайт-лист, кадры в один ряд) ---
# Путь к спрайт-листу эффекта снаряда. None -> рисуется заглушка-кружок.
PROJECTILE_IMAGE_PATH = os.path.join(ASSETS_DIR, "effects", "projectile.png")
PROJECTILE_FRAME_COUNT = 14              # кадров в спрайт-листе (1 = статичная картинка)
PROJECTILE_ANIMATION_SPEED = 14        # скорость анимации снаряда, кадров/сек
PROJECTILE_SIZE = (96, 96)             # размер снаряда на экране (пиксели)
# Поворачивать спрайт по направлению полёта. Ассет должен быть нарисован "носом" вправо.
PROJECTILE_ROTATE_TO_DIRECTION = True
# Радиус попадания снаряда (пиксели). Не зависит от размера картинки,
# чтобы прозрачные поля спрайта не мешали регистрации удара.
PROJECTILE_HIT_RADIUS = 14

# ---------- Враги ----------
# Ассет врага. Реализован так же, как игрок (спрайт-листы). Пока None -> заглушка.
ENEMY_IDLE_IMAGE_PATH = None
ENEMY_IDLE_FRAME_COUNT = 1
ENEMY_WALK_IMAGE_PATH = None
ENEMY_WALK_FRAME_COUNT = 1
ENEMY_ANIMATION_SPEED = 8

# Размер врага как доля от клетки.
ENEMY_SCALE = 0.35/4.0
ENEMY_SIZE = (int(TILE_SIZE * ENEMY_SCALE), int(TILE_SIZE * ENEMY_SCALE))

ENEMY_SPEED = 90            # пиксели/сек — медленнее игрока, чтобы можно было кайтить
ENEMY_MAX_HP = 50
ENEMY_DAMAGE = 12           # урон игроку при касании
ENEMY_ATTACK_COOLDOWN = 0.8 # как часто враг может нанести урон при контакте (сек)

# Хитбокс врага как доля от размера спрайта (ширина, высота). Урон игроку
# наносится только при пересечении хитбоксов, а не прозрачных полей спрайтов.
ENEMY_HITBOX_SCALE = (0.5, 0.6)

# Цвет заглушки врага и его полоски здоровья.
FALLBACK_ENEMY_COLOR = (120, 200, 120)
ENEMY_HP_BAR_BG = (50, 20, 20)
ENEMY_HP_BAR_FG = (220, 70, 70)

# ---------- Волны ----------
# Пауза перед первой волной (сек).
WAVE_START_DELAY = 2.0
# Пауза между волнами (сек).
WAVE_INTERVAL = 6.0
# Сколько врагов в первой волне.
WAVE_BASE_ENEMY_COUNT = 5
# На сколько врагов растёт каждая следующая волна.
WAVE_ENEMY_GROWTH = 3
# Интервал между спавном отдельных врагов внутри волны (сек).
WAVE_SPAWN_INTERVAL = 0.35
# Насколько усиливается HP врагов с каждой волной (множитель на номер волны).
WAVE_HP_SCALING = 0.15

# ---------- Опыт, уровни и прокачка ----------
# Прогрессивная шкала опыта: сколько XP нужно на каждый следующий уровень.
# Порог уровня N = XP_BASE * (XP_GROWTH ** (N - 1)) + XP_FLAT_ADD*(N-1).
XP_BASE = 5              # XP для перехода с 1 на 2 уровень
XP_GROWTH = 1.35         # во сколько раз растёт порог каждый уровень
XP_FLAT_ADD = 3          # плюс фиксированная прибавка к порогу на каждом уровне

# Сколько опыта даёт враг каждого типа (при смерти). Сильные типы — больше XP.
ENEMY_XP_REWARD = {
    "slime1": 1, "slime2": 2, "slime3": 4,
    "orc1": 2, "orc2": 4, "orc3": 7,
}
ENEMY_XP_DEFAULT = 1     # если тип не найден в таблице

# --- Дропы (выпадают из врага при смерти) ---
HEAL_DROP_CHANCE = 0.08          # шанс выпадения хилки (0..1), 0.08 = 8%
HEAL_DROP_AMOUNT = 25            # сколько HP восстанавливает одна хилка

# --- Подбор (магнит) ---
PICKUP_MAGNET_RADIUS = 160       # радиус, где дроп начинает притягиваться
PICKUP_COLLECT_RADIUS = 34       # радиус сбора
PICKUP_MAGNET_SPEED = 420        # скорость притягивания (пиксели/сек)
PICKUP_SIZE = 36                # размер иконки дропа (пиксели) — запасной, если тип не найден
XP_PICKUP_SIZE = 22             # размер иконки опыта (пиксели)
HEAL_PICKUP_SIZE = 50           # размер иконки хилки (пиксели)
PICKUP_LIFETIME = 25.0           # через сколько секунд несобранный дроп исчезает

# Цвета-заглушки дропов (пока нет спрайтов).
XP_PICKUP_COLOR = (90, 200, 255)     # опыт — голубой кристалл
HEAL_PICKUP_COLOR = (90, 230, 120)   # хилка — зелёный крест
# Пути к спрайтам дропов. None -> рисуется фигура-заглушка.
XP_PICKUP_IMAGE_PATH = None
HEAL_PICKUP_IMAGE_PATH = os.path.join(ASSETS_DIR, "effects", "heal.png")

# ---------- Улучшения при повышении уровня ----------
LEVELUP_CHOICES = 3

UPGRADE_ATTACK_DAMAGE_MULT = 0.10   # +10% к силе атаки
UPGRADE_ATTACK_SPEED_MULT = 0.07    # +7% к скорости атаки (уменьшает интервал)
UPGRADE_MAX_HP_ADD = 20             # +20 к максимальному здоровью (и текущему)
PLAYER_ATTACK_INTERVAL_MIN = 0.15   # минимальный интервал атаки (не уйдёт в 0)

# Список пассивных улучшений (id, подпись, описание).
UPGRADES_PASSIVE = [
    ("dmg",   "Сила атаки +10%",   "Увеличивает урон всех атак"),
    ("aspd",  "Скорость атаки +7%", "Атаки происходят чаще"),
    ("hp",    "Здоровье +20",      "Увеличивает максимум здоровья и лечит"),
]

# ---------- Активные способности ----------
# Модель как в Vampire Survivors: повторный выбор = +1 уровень способности.
ABILITY_START = "fireball"   # способность, выдаваемая изначально (огненная пуля)

ABILITIES = {
    "fireball": {
        "name": "Огненная пуля", "desc": "Вылетает в ближайшего врага",
        "kind": "projectile", "max_level": 8,
        "cooldown": 0.9, "cooldown_mult": 0.92,
        "damage": 20, "damage_add": 8,
        "radius": 0, "radius_add": 0, "speed": 520,
        "color": (255, 150, 60), "image_path": None,
    },
    "aura": {
        "name": "Огненная аура", "desc": "Урон по области вокруг игрока",
        "kind": "aura", "max_level": 8,
        "cooldown": 0.5, "cooldown_mult": 0.95,
        "damage": 8, "damage_add": 4,
        "radius": 120, "radius_add": 16,
        "color": (255, 120, 40), "image_path": None,
    },
    "lightning": {
        "name": "Атака молнией", "desc": "Сама бьёт по ближайшему врагу",
        "kind": "lightning", "max_level": 8,
        "cooldown": 1.4, "cooldown_mult": 0.9,
        "damage": 30, "damage_add": 12,
        "radius": 500, "radius_add": 40,
        "color": (120, 200, 255), "image_path": None,
    },
    "fireball_aoe": {
        "name": "Фаербол", "desc": "Взрыв по области в ближайшем враге",
        "kind": "fireball_aoe", "max_level": 8,
        "cooldown": 2.2, "cooldown_mult": 0.9,
        "damage": 40, "damage_add": 16,
        "radius": 90, "radius_add": 12, "speed": 380,
        "color": (255, 90, 30), "image_path": None,
    },
    "meteor": {
        "name": "Метеорит", "desc": "Падает в случайное место, урон по области",
        "kind": "meteor", "max_level": 8,
        "cooldown": 3.0, "cooldown_mult": 0.9,
        "damage": 60, "damage_add": 24,
        "radius": 130, "radius_add": 16, "fall_time": 0.8,
        "color": (255, 70, 20), "image_path": None,
    },
}

ABILITY_ORDER = ["fireball", "aura", "lightning", "fireball_aoe", "meteor"]

# ---------- Камера ----------
CAMERA_ZOOM = 0.9

# ---------- Отладка ----------
# Показать хитбоксы (красные рамки) поверх спрайтов — удобно подбирать
# *_HITBOX_SCALE под конкретные ассеты. Выключи, когда настроишь.
DEBUG_HITBOXES = False

# Показать зоны коллизий (синие рамки) поверх домиков.
DEBUG_COLLISION_ZONES = False

# ---------- Прочее ----------
BACKGROUND_COLOR = (20, 20, 30)

# HUD
HUD_FONT_SIZE = 22
HUD_HP_FONT_SIZE = 20   # шрифт текста "HP: X / Y" на полоске здоровья
HUD_TEXT_COLOR = (235, 235, 245)
PLAYER_HP_BAR_BG = (60, 20, 25)
PLAYER_HP_BAR_FG = (70, 210, 120)

# ---------- Типы врагов (тиры) ----------
# Папка с ассетами врагов. Спрайты каждого типа лежат в своей подпапке:
#   assets/enemy/<имя_типа>/{run,attack,hurt,death}.png
# Каждый файл — спрайт-лист (кадры в один горизонтальный ряд).
ENEMY_DIR = os.path.join(ASSETS_DIR, "enemy")

# Размер врага на экране задаём в ПИКСЕЛЯХ (базовый), а не от TILE_SIZE —
# так размер не зависит от размера карты. У каждого типа свой множитель "scale".
ENEMY_BASE_SIZE = 192

# Скорость анимаций врагов по состояниям (кадров/сек).
ENEMY_ANIM_SPEED = {"run": 12, "attack": 14, "hurt": 14, "death": 12}

# Описание типов врагов. Для каждого — пути к анимациям и число кадров,
# а также базовые характеристики. Урон игрока сейчас = PLAYER_ATTACK_DAMAGE (34),
# поэтому hp подобраны под нужное число ударов (комментарии рядом).
#
# frames — число кадров в каждом спрайт-листе (ОБЯЗАТЕЛЬНО точное!).
# scale  — множитель размера от ENEMY_BASE_SIZE (1.0 = 96px).
# Если файлов типа ещё нет (slime2/3, orc2/3) — игра покажет заглушку-квадрат,
# ничего не сломается. Положишь спрайты в папки — автоматически подхватятся.
ENEMY_TYPES = {
    # ---- СЛАЙМЫ ----
    "slime1": {
        "dir": "slime1",
        "frames": {"run": 8, "attack": 10, "hurt": 5, "death": 10},
        "hp": 30,        # <= 34 -> умирает с 1 удара
        "speed": 110,
        "damage": 8,
        "scale": 0.9,
        "hitbox_scale": (0.5, 0.5),
    },
    "slime2": {
        "dir": "slime2",
        "frames": {"run": 8, "attack": 11, "hurt": 5, "death": 10},
        "hp": 60,        # 2 удара
        "speed": 120,
        "damage": 12,
        "scale": 1.0,
        "hitbox_scale": (0.5, 0.5),
    },
    "slime3": {
        "dir": "slime3",
        "frames": {"run": 8, "attack": 9, "hurt": 5, "death": 10},
        "hp": 100,       # 3 удара
        "speed": 130,
        "damage": 16,
        "scale": 1.15,
        "hitbox_scale": (0.5, 0.5),
    },
    # ---- ОРКИ ----
    "orc1": {
        "dir": "orc1",
        "frames": {"run": 8, "attack": 8, "hurt": 6, "death": 1118},
        "hp": 60,        # 2 удара
        "speed": 85,
        "damage": 14,
        "scale": 1.0,
        "hitbox_scale": (0.45, 0.6),
    },
    "orc2": {
        "dir": "orc2",
        "frames": {"run": 8, "attack": 8, "hurt": 6, "death": 8},
        "hp": 100,       # 3 удара
        "speed": 90,
        "damage": 18,
        "scale": 1.1,
        "hitbox_scale": (0.45, 0.6),
    },
    "orc3": {
        "dir": "orc3",
        "frames": {"run": 8, "attack": 8, "hurt": 6, "death": 8},
        "hp": 150,       # 5 ударов
        "speed": 95,
        "damage": 24,
        "scale": 1.25,
        "hitbox_scale": (0.45, 0.6),
    },
}

# С какой волны тип начинает появляться. До этой волны тип не спавнится.
ENEMY_TYPE_UNLOCK_WAVE = {
    "slime1": 1, "orc1": 1,
    "slime2": 4, "orc2": 4,
    "slime3": 8, "orc3": 8,
}

# Доля (вес) типа в пуле спавна растёт с каждой волной после разблокировки.
# Формула веса типа: base_weight + (номер_волны - волна_разблоки) * weight_growth.
# Чем выше тир, тем быстрее растёт его доля (постепенно вытесняет слабых).
ENEMY_TYPE_BASE_WEIGHT = 10.0     # вес типа в момент разблокировки
ENEMY_TYPE_WEIGHT_GROWTH = 3.0    # на сколько растёт вес за каждую волну после разблокировки
# Ограничиваем долю самого слабого тира, чтобы он не вытеснялся полностью.
ENEMY_TYPE_MIN_WEIGHT = 4.0

# Рост характеристик от волны к волне (несильно). Множитель на номер волны.
# Итоговое hp = base_hp * (1 + (номер_волны - 1) * ENEMY_STAT_HP_GROWTH), аналогично урон.
ENEMY_STAT_HP_GROWTH = 0.06       # +6% hp за волну
ENEMY_STAT_DAMAGE_GROWTH = 0.04   # +4% урона за волну

# Сколько секунд проигрывать анимацию смерти перед удалением врага (если есть анимация).
# Защита от зависания, если анимация death не доиграла.
ENEMY_DEATH_MAX_TIME = 1.5

# ---------- Волны ----------
# Пауза перед первой волной (сек).
WAVE_START_DELAY = 2.0
# Пауза между волнами (сек).
WAVE_INTERVAL = 6.0
# Сколько врагов в первой волне.
WAVE_BASE_ENEMY_COUNT = 5
# На сколько врагов растёт каждая следующая волна.
WAVE_ENEMY_GROWTH = 3
# Интервал между спавном отдельных врагов внутри волны (сек).
WAVE_SPAWN_INTERVAL = 0.35
# Насколько усиливается HP врагов с каждой волной (множитель на номер волны).
WAVE_HP_SCALING = 0.15

# Полоса опыта (внизу экрана)
XP_BAR_BG = (30, 30, 50)
XP_BAR_FG = (120, 200, 255)
