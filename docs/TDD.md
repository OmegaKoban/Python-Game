---
tags: [геймдев, TDD, технический-документ, архитектура, Python, Pygame]
date_created: 2026-07-02
type: project
---

# Technical Design Document: Auto Arsenal

**Команда:** Корлович Илья, Безмен Максим  
**Дата:** 2026-07-09  
**Версия:** 0.2  
**Статус:** 🟢 Прототип готов

> TDD описывает техническую реализацию проекта. Обновляй документ при изменении архитектуры.

---

## 1. Структура проекта

### 1.1 Файловая структура (плоская архитектура)

```
Python-Game/
├── 📄 main.py                    # Точка входа, игровой цикл, FSM состояний
├── 📄 records.json               # Сохранённые рекорды (создаётся автоматически)
│
├── 📁 src/                       # Исходный код
│   ├── __init__.py
│   ├── settings.py               # Все константы и настройки игры
│   │
│   ├── 📁 core/                  # Базовые классы
│   │   ├── entity.py             # AnimatedEntity (база для игрока/врагов)
│   │   ├── camera.py             # Камера с зумом
│   │   └── tilemap.py            # Карта арены
│   │
│   ├── 📁 entities/              # Игровые сущности
│   │   ├── player.py             # Персонаж игрока
│   │   ├── enemy.py              # Враги с типами
│   │   └── projectile.py         # Снаряды игрока
│   │
│   ├── 📁 systems/               # Игровые системы
│   │   ├── abilities.py          # Менеджер способностей
│   │   ├── pickups.py            # Дропы с магнитом
│   │   └── wave_manager.py       # Управление волнами
│   │
│   ├── 📁 ui/                    # Интерфейс
│   │   ├── hud.py                # HUD (HP, XP, счёт)
│   │   ├── menu.py               # Главное меню
│   │   └── records.py            # Работа с рекордами
│   │
│   └── 📁 utils/                 # Вспомогательные модули
│       └── (пусто)
│
├── 📁 assets/                    # Графические ассеты
│   ├── player/                   # Спрайты игрока (4 анимации)
│   ├── enemy/                    # Спрайты врагов (6 типов × 4 анимации)
│   ├── effects/                  # Эффекты (снаряды, heal)
│   ├── tiles/                    # Тайлы карты
│   └── menu/                     # Ассеты меню (фон, панель, облака, шрифты)
│
└── 📁 docs/                      # Документация
    ├── GDD.md                    # Game Design Document
    ├── TDD.md                    # Technical Design Document (этот файл)
    ├── Концепт-документ.md       # Концепция проекта
    └── ui_*.jpg                  # Скриншоты
```

### 1.2 Почему плоская структура?


- ✅ Проект небольшого размера (~15 модулей)
- ✅ Учебный прототип, не требует пакетной установки
- ✅ Быстрый старт: `python main.py`
- ✅ Простая навигация по коду

---

## 2. Диаграмма классов (UML)

### 2.1 Иерархия наследования

```
pygame.sprite.Sprite
    │
    └── AnimatedEntity                 # Базовый класс с анимациями
            │
            ├── Player                 # Персонаж игрока
            │       ├── handle_input()
            │       ├── auto_attack()
            │       └── abilities: AbilityManager
            │
            └── Enemy                  # Враги
                    ├── type: str (slime1..3, orc1..3)
                    ├── state: str (run, attack, hurt, death)
                    └── roll_drops()

Отдельные классы (не наследуют Sprite):
    ├── Projectile                     # Снаряды
    ├── Pickup                         # Дропы (XP, heal)
    ├── AbilityManager                 # Система способностей
    ├── WaveManager                    # Управление волнами
    ├── Camera                         # Камера с зумом
    └── TileMap                        # Карта арены
```

### 2.2 Базовый класс `AnimatedEntity`

**Файл:** `src/entity.py`

| Атрибут | Тип | Описание |
|---------|-----|----------|
| `size` | `tuple[int, int]` | Размер спрайта (ширина, высота) |
| `pos` | `pygame.Vector2` | Позиция в мировых координатах |
| `hp` | `int` | Текущее здоровье |
| `max_hp` | `int` | Максимальное здоровье |
| `is_alive` | `bool` | Флаг жизни |
| `animations` | `dict[str, list[Surface]]` | Словарь анимаций по состояниям |
| `state` | `str` | Текущее состояние анимации |
| `frame_index` | `float` | Индекс текущего кадра |
| `animation_speed` | `float` | Скорость анимации (кадров/сек) |
| `facing_right` | `bool` | Направление взгляда |
| `hitbox` | `pygame.Rect` | Реальный хитбокс для коллизий |

| Метод | Возврат | Описание |
|-------|---------|----------|
| `load_frames(path, count, size)` | `list[Surface] \| None` | Загрузка спрайт-листа |
| `set_state(state)` | `None` | Смена состояния анимации |
| `animate(dt, loop)` | `bool` | Проигрывание анимации, возврат True если закончилась |
| `take_damage(amount)` | `bool` | Получение урона, возврат True при смерти |
| `init_hitbox(scale)` | `None` | Инициализация хитбокса |
| `sync_hitbox()` | `None` | Синхронизация хитбокса с rect |



> **Архитектурное решение:** Все анимированные сущности наследуют `AnimatedEntity` вместо прямого наследования `pygame.sprite.Sprite`. Это даёт единую систему загрузки спрайт-листов, автоматическое переключение кадров и отражение по горизонтали без дублирования кода.

### 2.3 Класс `Player`

**Файл:** `src/player.py`

**Дополнительные атрибуты:**

| Атрибут | Тип | Описание |
|---------|-----|----------|
| `speed` | `float` | Скорость движения (220 px/с) |
| `attack_timer` | `float` | Таймер до следующей атаки |
| `attack_interval` | `float` | Интервал между атаками (0.9 с) |
| `attack_target` | `Enemy \| None` | Цель текущей атаки |
| `is_attacking` | `bool` | Флаг анимации атаки |
| `pending_projectiles` | `list[Projectile]` | Буфер снарядов для main.py |
| `level` | `int` | Текущий уровень игрока |
| `xp` | `int` | Накопленный опыт |
| `xp_to_next` | `int` | Опыт до следующего уровня |
| `pending_levelups` | `int` | Количество нерастраченных level-up |
| `damage_mult` | `float` | Множитель урона (от пассивок) |
| `abilities` | `AbilityManager` | Менеджер активных способностей |
| `invuln_timer` | `float` | Таймер неуязвимости после урона |

**Ключевые методы:**

| Метод | Описание |
|-------|----------|
| `handle_input()` | Чтение WASD/стрелок, возврат вектора направления |
| `update(dt, tilemap, enemies)` | Движение, автоатака, анимация, способности |
| `_find_nearest_enemy(enemies)` | Поиск ближайшего врага в радиусе 500 px |
| `_start_attack(target)` | Запуск анимации атаки |
| `_deal_attack(target)` | Создание снаряда или прямой урон |
| `add_xp(amount)` | Добавление опыта, проверка level-up |
| `heal(amount)` | Восстановление HP |
| `roll_upgrade_choices()` | Генерация 3 случайных усилений |
| `apply_upgrade(choice)` | Применение выбранного усиления |

### 2.4 Класс `Enemy`

**Файл:** `src/enemy.py`

**Атрибуты:**

| Атрибут | Тип | Описание |
|---------|-----|----------|
| `enemy_type` | `str` | Тип врага (slime1..3, orc1..3) |
| `cfg` | `dict` | Конфиг типа из settings.ENEMY_TYPES |
| `speed` | `float` | Скорость преследования (85–130 px/с) |
| `damage` | `int` | Урон при контакте (8–24) |
| `attack_cooldown` | `float` | Таймер до следующего урона |
| `state` | `str` | Состояние: run/attack/hurt/death |
| `dying` | `bool` | Флаг анимации смерти |
| `death_timer` | `float` | Таймер смерти (макс. 1.5 с) |
| `should_remove` | `bool` | Флаг для удаления из main.py |
| `attack_hit_done` | `bool` | Урон в текущей атаке нанесён |

**Ключевые методы:**

| Метод | Описание |
|-------|----------|
| `update(dt, player, tilemap)` | Преследование игрока, атака при контакте, анимация |
| `take_damage(amount)` | Урон, запуск hurt или death |
| `roll_drops()` | Генерация дропов: XP (всегда), heal (8% шанс) |
| `render(surface, camera)` | Отрисовка + полоска HP |



### 2.5 Система способностей

**Файлы:** `src/abilities.py`

**Класс `AbilityManager`:**

| Атрибут | Тип | Описание |
|---------|-----|----------|
| `levels` | `dict[str, int]` | ID способности → текущий уровень (1..8) |
| `timers` | `dict[str, float]` | ID → накопленное время до следующего срабатывания |
| `effects` | `list[Effect]` | Список активных визуальных эффектов |

| Метод | Описание |
|-------|----------|
| `add_or_upgrade(ability_id)` | Даёт новую способность или повышает уровень |
| `update(dt, player, enemies, tilemap)` | Тикает кулдауны, запускает способности, обновляет эффекты |
| `render(surface, camera)` | Рендер всех эффектов |
| `available_ability_upgrades()` | Список способностей для меню level-up |

**Типы эффектов:**

| Класс | Описание |
|-------|----------|
| `FlyingProjectile` | Летящий снаряд (fireball) или снаряд с взрывом (fireball_aoe) |
| `AuraTick` | Кольцо-вспышка ауры (визуал) |
| `LightningStrike` | Луч молнии от неба к цели (визуал) |
| `Meteor` | Падающий метеорит с тенью-маркером |

### 2.6 Управление волнами

**Файл:** `src/wave_manager.py`

**Класс `WaveManager`:**

| Атрибут | Тип | Описание |
|---------|-----|----------|
| `wave_number` | `int` | Номер текущей волны |
| `wave_timer` | `float` | Таймер до следующей волны |
| `spawn_queue` | `list[str]` | Очередь типов врагов для спавна |
| `spawn_timer` | `float` | Таймер до следующего спавна (0.35 с) |

| Метод | Описание |
|-------|----------|
| `update(dt, player, enemies)` | Тикает таймеры, спавнит волны |
| `_spawn_wave()` | Генерация состава волны по весам типов |
| `_spawn_enemy(etype, player)` | Спавн врага за границами камеры |

**Алгоритм взвешивания:**
```python
# Вес типа = base_weight + (wave - unlock_wave) * weight_growth
# Но не меньше min_weight для старых типов
weight = max(
    MIN_WEIGHT,
    BASE_WEIGHT + (wave_number - unlock_wave) * WEIGHT_GROWTH
)
```

---

## 3. Игровой цикл и машина состояний

### 3.1 FSM состояний

```
STATE_MENU ──[play]──► STATE_PLAYING ──[hp≤0]──► (save record)
    │                         │
    │                         ├─[Esc]──► STATE_PAUSED ──[Esc/P]──► STATE_PLAYING
    │                         │                └─[Q]──► STATE_MENU
    │                         │
    │                         └─[level up]──► (level_up_active=True)
    │
    ├─[settings]──► STATE_SETTINGS ──[back]──► STATE_MENU
    │
    └─[records]───► STATE_RECORDS ──[back]───► STATE_MENU
```



### 3.2 Псевдокод `main.py`

```python
# Инициализация
pygame.init()
screen = create_screen()  # Определяет режим (fullscreen/borderless/window)
clock = pygame.time.Clock()

menu = Menu(screen)
game = None
state = STATE_MENU

# Главный цикл
while running:
    dt = clock.tick(FPS) / 1000  # секунды
    
    # 1. Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Делегирование событий текущему состоянию
        if state == STATE_MENU:
            choice = menu.handle_event(event)
            if choice == "play":
                game = Game(screen)
                state = STATE_PLAYING
        
        elif state == STATE_PLAYING:
            if game.level_up_active:
                # Обработка выбора усиления
                handle_levelup_input(event, game)
            else:
                # Обычное управление
                handle_game_input(event, game)
    
    # 2. Обновление состояния
    if state == STATE_PLAYING:
        game.update(dt)
        if game.game_over and not record_saved:
            add_record(player_name, kills, wave)
            record_saved = True
    
    # 3. Рендеринг
    game.render()
    
    # 4. Применение яркости (оверлей)
    apply_brightness_overlay(screen)
    
    pygame.display.flip()
```

### 3.3 Цикл обновления `Game.update(dt)`

```python
def update(self, dt):
    if self.game_over or self.level_up_active:
        return
    
    # 1. Игрок
    self.player.update(dt, self.tilemap, self.enemies)
    self.projectiles.extend(self.player.collect_projectiles())
    
    # 2. Волны врагов
    self.wave_manager.update(dt, self.player, self.enemies)
    
    # 3. Враги
    for enemy in self.enemies:
        enemy.update(dt, self.player, self.tilemap)
    
    # 4. Снаряды
    for proj in self.projectiles:
        proj.update(dt, self.enemies, self.tilemap)
    
    # 5. Удаление мёртвых врагов + создание дропов
    for enemy in list(self.enemies):
        if not enemy.is_alive:
            self.kills += 1
            for kind, value, pos in enemy.roll_drops():
                self.pickups.append(Pickup(pos, kind, value))
            self.enemies.remove(enemy)
    
    # 6. Дропы (магнит + подбор)
    for pickup in self.pickups:
        if pickup.update(dt, self.player):
            if pickup.kind == "xp":
                self.player.add_xp(pickup.value)
            elif pickup.kind == "heal":
                self.player.heal(pickup.value)
    self.pickups = [p for p in self.pickups if p.alive]
    
    # 7. Убираем отработавшие снаряды
    self.projectiles = [p for p in self.projectiles if p.alive]
    
    # 8. Камера
    self.camera.update(self.player.rect)
    
    # 9. Проверка поражения и level-up
    if not self.player.is_alive:
        self.game_over = True
    
    if self.player.pending_levelups > 0:
        self._open_level_up()
```

---

## 4. Формат данных и настройки

### 4.1 `settings.py` — все константы

```python
# Пути к ассетам
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
TILE_IMAGE_PATH = os.path.join(ASSETS_DIR, "tiles", "tile.jpeg")
# ... (все пути к спрайтам)

# Экран
SCREEN_MODE = "fullscreen"  # fullscreen | borderless | window
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
FPS = 60

# Игрок
PLAYER_SPEED = 220
PLAYER_MAX_HP = 100
PLAYER_ATTACK_DAMAGE = 34
PLAYER_ATTACK_INTERVAL = 0.9
PLAYER_ATTACK_RANGE = 500
# ...

# Враги
ENEMY_TYPES = {
    "slime1": {
        "dir": "slime1",
        "frames": {"run": 8, "attack": 10, "hurt": 5, "death": 10},
        "hp": 30, "speed": 110, "damage": 8,
        "scale": 0.9, "hitbox_scale": (0.5, 0.5)
    },
    # ... остальные 5 типов
}

# Волны
WAVE_START_DELAY = 2.0
WAVE_INTERVAL = 6.0
WAVE_BASE_ENEMY_COUNT = 5
WAVE_ENEMY_GROWTH = 3
WAVE_SPAWN_INTERVAL = 0.35

# Опыт
XP_BASE = 5
XP_GROWTH = 1.35
XP_FLAT_ADD = 3

# Способности
ABILITIES = {
    "fireball": {
        "name": "Огненная пуля",
        "kind": "projectile",
        "cooldown": 0.9,
        "damage": 20,
        # ...
    },
    # ... остальные 4 способности
}
```



### 4.2 `records.json` — формат сохранений

```json
{
  "records": [
    {
      "player": "Игрок",
      "kills": 42,
      "wave": 8,
      "date": "2026-07-09 15:30:45"
    }
  ]
}
```

**Модуль:** `src/records.py`

| Функция | Описание |
|---------|----------|
| `load_records()` | Загрузка из JSON, создание файла если отсутствует |
| `add_record(player, kills, wave)` | Добавление нового рекорда с текущей датой |
| `get_top_records(n)` | Получение топ-N рекордов по убийствам |

---

## 5. Алгоритмы и механики

### 5.1 Система опыта и уровней

**Формула порога:**
```python
def _xp_threshold(level: int) -> int:
    base = XP_BASE * (XP_GROWTH ** (level - 1))
    return int(round(base + XP_FLAT_ADD * (level - 1)))

# Примеры:
# Ур.1→2: 5 XP
# Ур.2→3: 9 XP
# Ур.3→4: 15 XP
# Ур.4→5: 23 XP
```

**Добавление опыта:**
```python
def add_xp(self, amount: int):
    self.xp += amount
    while self.xp >= self.xp_to_next:
        self.xp -= self.xp_to_next
        self.level += 1
        self.pending_levelups += 1
        self.xp_to_next = self._xp_threshold(self.level)
```

### 5.2 Магнитный подбор дропов

**Класс `Pickup` (src/pickups.py):**

```python
def update(self, dt, player):
    self.lifetime -= dt
    if self.lifetime <= 0:
        self.alive = False
        return False
    
    to_player = player.pos - self.pos
    dist = to_player.length()
    
    # Сбор
    if dist <= PICKUP_COLLECT_RADIUS:
        self.alive = False
        return True
    
    # Магнит
    if self.magnetized or dist <= PICKUP_MAGNET_RADIUS:
        self.magnetized = True
        self.current_speed += PICKUP_MAGNET_SPEED * dt * 2
        if dist > 0:
            self.pos += to_player.normalize() * min(self.current_speed * dt, dist)
    else:
        # Покачивание на месте
        self._bob += dt * 3
        self.pos.y += math.sin(self._bob) * 6 * dt
    
    self.rect.center = (round(self.pos.x), round(self.pos.y))
    return False
```

### 5.3 Коллизии

| Пара | Метод | Описание |
|------|-------|----------|
| Снаряды ↔ Враги | `Rect.colliderect` | Попадание по хитбоксу врага |
| Игрок ↔ Враги | `Rect.colliderect` | Контакт хитбоксов для урона |
| Игрок ↔ Дропы | Расстояние между pos | Магнит и подбор по дистанции |
| Способности ↔ Враги | `distance_squared` | Радиус действия AOE/lightning |

> **Важно:** Используем хитбоксы (меньше rect), чтобы прозрачные поля спрайтов не влияли на коллизии.

### 5.4 Спавн врагов за камерой

```python
def _spawn_enemy(self, etype, player):
    # Случайная сторона: 0=верх, 1=право, 2=низ, 3=лево
    side = random.randint(0, 3)
    margin = 100  # за границей экрана
    
    if side == 0:  # верх
        x = random.uniform(0, tilemap.pixel_width)
        y = player.pos.y - camera.viewport_h // 2 - margin
    elif side == 1:  # право
        x = player.pos.x + camera.viewport_w // 2 + margin
        y = random.uniform(0, tilemap.pixel_height)
    # ... аналогично для низ и лево
    
    enemies.add(Enemy((x, y), etype, self.wave_number))
```

### 5.5 Система весов для спавна

```python
def _calculate_weights(self, wave_number):
    weights = {}
    for etype, unlock_wave in ENEMY_TYPE_UNLOCK_WAVE.items():
        if wave_number >= unlock_wave:
            steps = wave_number - unlock_wave
            w = ENEMY_TYPE_BASE_WEIGHT + steps * ENEMY_TYPE_WEIGHT_GROWTH
            weights[etype] = max(ENEMY_TYPE_MIN_WEIGHT, w)
    return weights

# Выбор по весам:
types = list(weights.keys())
vals = list(weights.values())
chosen = random.choices(types, weights=vals, k=count)
```

---

## 6. Рендеринг и камера

### 6.1 Двухэтапный рендер

```python
def render(self):
    # 1. Рендер мира в промежуточный surface (размер видимой области)
    self.view_surface.fill(BACKGROUND_COLOR)
    
    self.tilemap.render(self.view_surface, self.camera.offset)
    
    # Дропы → Снаряды → Враги → Игрок → Эффекты способностей
    for pickup in self.pickups:
        pickup.render(self.view_surface, self.camera)
    
    for proj in self.projectiles:
        proj.render(self.view_surface, self.camera)
    
    for enemy in self.enemies:
        enemy.render(self.view_surface, self.camera)
    
    # Игрок с миганием при неуязвимости
    if not (self.player.invuln_timer > 0 and int(self.player.invuln_timer * 20) % 2):
        self.view_surface.blit(self.player.image, 
                               self.camera.apply(self.player.rect))
    
    self.player.abilities.render(self.view_surface, self.camera)
    
    # 2. Масштабирование на весь экран (зум)
    scaled = pygame.transform.scale(self.view_surface, 
                                     (SCREEN_WIDTH, SCREEN_HEIGHT))
    self.screen.blit(scaled, (0, 0))
    
    # 3. HUD поверх (не масштабируется)
    self.hud.render(self.screen, self.player, self.wave_manager, self.kills)
```

### 6.2 Камера с зумом

**Класс `Camera` (src/camera.py):**

```python
class Camera:
    def __init__(self, tilemap):
        self.zoom = CAMERA_ZOOM
        self.viewport_w = int(SCREEN_WIDTH / self.zoom)
        self.viewport_h = int(SCREEN_HEIGHT / self.zoom)
        self.offset = pygame.Vector2(0, 0)
    
    def update(self, target_rect):
        # Центрируем на цели
        self.offset.x = target_rect.centerx - self.viewport_w // 2
        self.offset.y = target_rect.centery - self.viewport_h // 2
        
        # Ограничиваем границами карты
        self.offset.x = max(0, min(self.offset.x, 
                                   tilemap.pixel_width - self.viewport_w))
        self.offset.y = max(0, min(self.offset.y, 
                                   tilemap.pixel_height - self.viewport_h))
    
    def apply(self, rect):
        return rect.move(-self.offset.x, -self.offset.y)
    
    def apply_point(self, point):
        return (point[0] - self.offset.x, point[1] - self.offset.y)
```

---

## 7. Архитектурные решения

### 7.1 Почему AnimatedEntity вместо прямого Sprite?

**Проблема:** Код загрузки спрайт-листов и анимации дублировался в Player и Enemy.

**Решение:** Базовый класс `AnimatedEntity` инкапсулирует:
- Загрузку горизонтальных спрайт-листов
- Автопереключение кадров по таймеру
- Отражение по горизонтали
- Хитбоксы меньше rect

**Результат:** Player и Enemy наследуют готовую систему анимации, код не дублируется.

### 7.2 Почему снаряды через буфер pending_projectiles?

**Проблема:** Player не может напрямую добавлять в группу снарядов (она принадлежит Game).

**Решение:** Player складывает снаряды в буфер `pending_projectiles`, main.py забирает их через `collect_projectiles()`.

**Альтернатива (не выбрана):** Передавать группу снарядов в `Player.update()` — усложняет сигнатуру, нарушает инкапсуляцию.

### 7.3 Почему враги не удаляются сразу при hp≤0?

**Проблема:** Нужно проиграть анимацию смерти перед удалением.

**Решение:**
1. При `hp ≤ 0` враг переходит в состояние `death`, устанавливает `dying = True`
2. Анимация проигрывается без loop
3. После завершения анимации (или таймаута 1.5 сек) устанавливается `should_remove = True`
4. Main.py проверяет `should_remove` и удаляет врага, генерируя дропы

### 7.4 Почему level-up — это флаг в Game, а не отдельное состояние?

**Проблема:** При level-up нужно заморозить игру, но не останавливать рендер.

**Решение:** Флаг `level_up_active` в Game останавливает update, но не render. Меню рисуется поверх игровой сцены в HUD.

**Альтернатива (не выбрана):** Отдельное состояние `STATE_LEVELUP` — усложняет FSM, требует сохранения/восстановления состояния Game.

---

## 8. Тестирование

> **Примечание:** В текущей версии прототипа unit-тесты не реализованы. Тестирование проводилось вручную через игровой процесс.

### 8.1 Рекомендации для тестов

**Приоритетные области:**

| Модуль | Что тестировать |
|--------|-----------------|
| `player.py` | Формула опыта, порог уровня, накопление pending_levelups |
| `wave_manager.py` | Расчёт состава волны по весам, расписание разблокировок |
| `abilities.py` | Расчёт урона/кулдауна по уровню способности |
| `enemy.py` | Генерация дропов, шанс heal (статистически) |

**Пример теста:**

```python
def test_xp_threshold():
    player = Player((0, 0))
    assert player._xp_threshold(1) == 5
    assert player._xp_threshold(2) == 9
    assert player._xp_threshold(3) == 15

def test_level_up():
    player = Player((0, 0))
    player.add_xp(100)  # хватит на несколько уровней
    assert player.level > 1
    assert player.pending_levelups > 0
```

---

## 9. Зависимости

**Файл:** `requirements.txt`

```
pygame>=2.5.0
```

**Установка:**
```bash
pip install -r requirements.txt
```

**Системные требования:**
- Python 3.11+
- SDL2 (устанавливается с pygame)
- Поддержка OpenGL (для SCALED режима)

---

## История изменений

| Версия | Дата | Изменение |
|--------|------|-----------|
| **0.1** | 2026-07-02 | Первый черновик: базовая структура проекта |
| **0.2** | 2026-07-09 | **Полное обновление под реализованный прототип:**<br>• Документирована иерархия классов (AnimatedEntity)<br>• Добавлена система способностей (AbilityManager + 5 типов эффектов)<br>• Описана система волн с весами типов<br>• Документирован магнитный подбор дропов<br>• Добавлена секция алгоритмов (опыт, спавн, коллизии)<br>• Описан двухэтапный рендер с зумом<br>• Добавлена секция архитектурных решений<br>• Обновлена структура проекта |

---

*Предыдущий шаг:* [[GDD]]  
*Связанные темы:* [[Документация игрового проекта]], [[Архитектура игр]], [[Pygame]]
