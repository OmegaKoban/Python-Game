"""
Утилита для определения зон коллизий на карте.

Использование:
1. Запусти: python find_collision_zones.py
2. Кликай ЛКМ на углах домиков (левый верхний → правый нижний)
3. Нажми ENTER после каждого домика
4. Нажми ESC для завершения
5. Координаты сохранятся в collision_zones.txt

Управление:
- ЛКМ — добавить точку
- ENTER — завершить текущий прямоугольник
- ESC — выход и сохранение
- R — сбросить текущий прямоугольник
"""

import pygame
import sys
from src import settings

# Путь к твоей карте
MAP_IMAGE = "assets/tiles/tile.jpeg"
OUTPUT_FILE = "collision_zones.txt"

# Размер карты в игре
GAME_MAP_WIDTH = settings.TILE_SIZE * settings.MAP_WIDTH_TILES
GAME_MAP_HEIGHT = settings.TILE_SIZE * settings.MAP_HEIGHT_TILES

# Инициализация
pygame.init()

# Загрузка карты
try:
    map_img = pygame.image.load(MAP_IMAGE)
    map_rect = map_img.get_rect()
except:
    print(f"❌ Не могу загрузить {MAP_IMAGE}")
    sys.exit(1)

# Создание окна (масштабируем, если карта большая)
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Кликай на углы домиков")

# Масштаб для отображения
scale = min(WINDOW_WIDTH / map_rect.width, WINDOW_HEIGHT / map_rect.height, 1.0)
scaled_width = int(map_rect.width * scale)
scaled_height = int(map_rect.height * scale)
scaled_map = pygame.transform.scale(map_img, (scaled_width, scaled_height))

# Смещение для центрирования
offset_x = (WINDOW_WIDTH - scaled_width) // 2
offset_y = (WINDOW_HEIGHT - scaled_height) // 2

# Данные
zones = []  # Список готовых зон: [(x1, y1, x2, y2), ...]
current_points = []  # Текущие точки для нового прямоугольника

font = pygame.font.Font(None, 24)
clock = pygame.time.Clock()
running = True

def screen_to_map(screen_x, screen_y):
    """Конвертация экранных координат в координаты карты (с учётом масштаба игры)"""
    # Сначала конвертируем в координаты исходного изображения
    img_x = int((screen_x - offset_x) / scale)
    img_y = int((screen_y - offset_y) / scale)
    
    # Затем масштабируем до размеров карты в игре
    game_x = int(img_x * GAME_MAP_WIDTH / map_rect.width)
    game_y = int(img_y * GAME_MAP_HEIGHT / map_rect.height)
    
    return game_x, game_y

def map_to_screen(game_x, game_y):
    """Конвертация координат карты в экранные (для отображения)"""
    # Сначала переводим из игровых координат в координаты изображения
    img_x = game_x * map_rect.width / GAME_MAP_WIDTH
    img_y = game_y * map_rect.height / GAME_MAP_HEIGHT
    
    # Затем в экранные координаты
    screen_x = offset_x + int(img_x * scale)
    screen_y = offset_y + int(img_y * scale)
    
    return screen_x, screen_y

def save_zones():
    """Сохранение зон в файл"""
    with open(OUTPUT_FILE, "w") as f:
        f.write("# Зоны коллизий (x1, y1, x2, y2)\n")
        f.write("# Формат: левый_верхний → правый_нижний\n")
        f.write(f"# Координаты для карты {GAME_MAP_WIDTH}×{GAME_MAP_HEIGHT} пикселей\n\n")
        f.write("COLLISION_ZONES = [\n")
        for i, (x1, y1, x2, y2) in enumerate(zones, 1):
            f.write(f"    # Дом {i}\n")
            f.write(f"    ({x1}, {y1}, {x2}, {y2}),\n")
        f.write("]\n")
    print(f"\n✅ Сохранено {len(zones)} зон в {OUTPUT_FILE}")
    print(f"   Координаты для карты {GAME_MAP_WIDTH}×{GAME_MAP_HEIGHT} px")

# Главный цикл
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Сохранить и выйти
                if zones or current_points:
                    save_zones()
                running = False
            
            elif event.key == pygame.K_RETURN:
                # Завершить текущий прямоугольник
                if len(current_points) == 2:
                    x1, y1 = current_points[0]
                    x2, y2 = current_points[1]
                    # Нормализуем (x1,y1 — верхний левый, x2,y2 — нижний правый)
                    zones.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
                    print(f"✓ Добавлена зона {len(zones)}: ({x1}, {y1}) → ({x2}, {y2})")
                    current_points = []
                else:
                    print("⚠️ Нужно кликнуть 2 точки (углы прямоугольника)")
            
            elif event.key == pygame.K_r:
                # Сбросить текущие точки
                current_points = []
                print("↺ Текущий прямоугольник сброшен")
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # ЛКМ
                # Добавить точку
                map_x, map_y = screen_to_map(event.pos[0], event.pos[1])
                
                # Проверка границ
                if 0 <= map_x < GAME_MAP_WIDTH and 0 <= map_y < GAME_MAP_HEIGHT:
                    current_points.append((map_x, map_y))
                    print(f"  • Точка {len(current_points)}: ({map_x}, {map_y})")
                    
                    if len(current_points) == 2:
                        print("  → Нажми ENTER чтобы сохранить, или R чтобы сбросить")
                    
                    # Ограничиваем 2 точками
                    if len(current_points) > 2:
                        current_points = current_points[-2:]
    
    # Рендер
    screen.fill((30, 30, 30))
    screen.blit(scaled_map, (offset_x, offset_y))
    
    # Рисуем сохранённые зоны (зелёные)
    for x1, y1, x2, y2 in zones:
        scr_x1, scr_y1 = map_to_screen(x1, y1)
        scr_x2, scr_y2 = map_to_screen(x2, y2)
        rect = pygame.Rect(
            min(scr_x1, scr_x2),
            min(scr_y1, scr_y2),
            abs(scr_x2 - scr_x1),
            abs(scr_y2 - scr_y1)
        )
        pygame.draw.rect(screen, (0, 255, 0), rect, 2)
    
    # Рисуем текущие точки (красные)
    for map_x, map_y in current_points:
        screen_x, screen_y = map_to_screen(map_x, map_y)
        pygame.draw.circle(screen, (255, 0, 0), (screen_x, screen_y), 5)
    
    # Рисуем текущий прямоугольник (жёлтый)
    if len(current_points) == 2:
        x1, y1 = current_points[0]
        x2, y2 = current_points[1]
        scr_x1, scr_y1 = map_to_screen(x1, y1)
        scr_x2, scr_y2 = map_to_screen(x2, y2)
        rect = pygame.Rect(
            min(scr_x1, scr_x2),
            min(scr_y1, scr_y2),
            abs(scr_x2 - scr_x1),
            abs(scr_y2 - scr_y1)
        )
        pygame.draw.rect(screen, (255, 255, 0), rect, 2)
    
    # Инструкции
    instructions = [
        f"Карта: {GAME_MAP_WIDTH}×{GAME_MAP_HEIGHT} px | Изображение: {map_rect.width}×{map_rect.height} px",
        f"Зон: {len(zones)} | Точек: {len(current_points)}/2",
        "ЛКМ — добавить точку | ENTER — сохранить зону",
        "R — сбросить | ESC — выход",
    ]
    
    y = 10
    for text in instructions:
        surf = font.render(text, True, (255, 255, 255))
        screen.blit(surf, (10, y))
        y += 30
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
print("\n👋 Готово!")
