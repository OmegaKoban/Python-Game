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
SCREEN_MODE = "borderless"
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
MENU_PANEL_WIDTH_RATIO = 0.4
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

# ---------- Тайлы и карта ----------
TILE_SIZE = 3000

# Карта фиксированного размера — сколько тайлов по ширине и высоте.
# Размер подобран так, чтобы враги с краёв успевали набегать на игрока.
MAP_WIDTH_TILES = 1
MAP_HEIGHT_TILES = 1

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

# ---------- Камера ----------
CAMERA_ZOOM = 0.9

# ---------- Отладка ----------
# Показать хитбоксы (красные рамки) поверх спрайтов — удобно подбирать
# *_HITBOX_SCALE под конкретные ассеты. Выключи, когда настроишь.
DEBUG_HITBOXES = False

# ---------- Прочее ----------
BACKGROUND_COLOR = (20, 20, 30)

# HUD
HUD_FONT_SIZE = 22
HUD_TEXT_COLOR = (235, 235, 245)
PLAYER_HP_BAR_BG = (60, 20, 25)
PLAYER_HP_BAR_FG = (70, 210, 120)
