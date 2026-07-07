"""
Главное меню Auto Arsenal.

Экран меню:
    - фон-подложка (небо) — растягивается на весь экран;
    - 6 спрайтов облаков, которые летят за панелью по фону (зацикленно,
      с разными скоростями/высотами/масштабами — лёгкий параллакс);
    - панель-свиток по центру с заголовком игры и пунктами меню;
    - навигация мышью (наведение + клик) и клавиатурой (стрелки/W/S + Enter).

Меню не знает, что делать при выборе пункта — оно лишь возвращает id
выбранного пункта ("play" / "quit" / ...). Реакцию задаёт main.py.
"""

import os
import random

import pygame

from src import settings


def _load_image(path, alpha=True):
    """Грузит картинку. Возвращает None, если файла нет или не читается."""
    if not path or not os.path.exists(path):
        return None
    try:
        img = pygame.image.load(path)
        return img.convert_alpha() if alpha else img.convert()
    except pygame.error:
        return None


class Cloud:
    """Одно облако: летит по горизонтали и зацикливается за краями экрана."""

    def __init__(self, image, screen_w, screen_h, direction, spawn_offscreen=False):
        self.base_image = image
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.direction = 1 if direction == "right" else -1

        self._randomize(spawn_offscreen)

    def _randomize(self, spawn_offscreen):
        # Масштаб.
        smin, smax = settings.MENU_CLOUD_SCALE_RANGE
        scale = random.uniform(smin, smax)
        w = max(1, int(self.base_image.get_width() * scale))
        h = max(1, int(self.base_image.get_height() * scale))
        self.image = pygame.transform.smoothscale(self.base_image, (w, h))
        if settings.MENU_CLOUD_ALPHA < 255:
            self.image.set_alpha(settings.MENU_CLOUD_ALPHA)
        self.w, self.h = w, h

        # Скорость (пиксели/сек).
        vmin, vmax = settings.MENU_CLOUD_SPEED_RANGE
        self.speed = random.uniform(vmin, vmax)

        # Вертикальная позиция — по всей высоте, чтобы облака шли на разных ярусах.
        self.y = random.uniform(-self.h * 0.3, self.screen_h - self.h * 0.5)

        # Горизонтальная позиция.
        if spawn_offscreen:
            # Появляется за краем (для плавного «влёта» после ухода).
            self.x = -self.w if self.direction > 0 else self.screen_w
        else:
            # Стартовая раскладка — разбросаны по всему экрану.
            self.x = random.uniform(-self.w, self.screen_w)

    def update(self, dt):
        self.x += self.direction * self.speed * dt
        # Зацикливание: ушло за край — перезапускаем с новыми параметрами.
        if self.direction > 0 and self.x > self.screen_w:
            self._randomize(spawn_offscreen=True)
        elif self.direction < 0 and self.x + self.w < 0:
            self._randomize(spawn_offscreen=True)

    def render(self, surface):
        surface.blit(self.image, (int(self.x), int(self.y)))


class Menu:
    """Экран главного меню. Управляет фоном, облаками и пунктами."""

    def __init__(self, screen):
        self.screen = screen
        self.w, self.h = screen.get_size()

        # --- Фон-подложка ---
        bg = _load_image(settings.MENU_BACKGROUND_PATH, alpha=False)
        if bg is not None:
            self.background = pygame.transform.smoothscale(bg, (self.w, self.h))
        else:
            self.background = None

        # --- Облака ---
        cloud_images = []
        for i in range(1, settings.MENU_CLOUD_COUNT + 1):
            img = _load_image(settings.MENU_CLOUD_PATH_TMPL.format(i))
            if img is not None:
                cloud_images.append(img)
        self.clouds = []
        if cloud_images:
            # Делаем чуть больше экземпляров, чем картинок, чтобы небо было живее.
            count = max(settings.MENU_CLOUD_COUNT, len(cloud_images))
            for k in range(count):
                base = cloud_images[k % len(cloud_images)]
                self.clouds.append(
                    Cloud(base, self.w, self.h, settings.MENU_CLOUD_DIRECTION)
                )

        # --- Панель-свиток ---
        panel = _load_image(settings.MENU_PANEL_PATH)
        target_w = int(self.w * settings.MENU_PANEL_WIDTH_RATIO)
        target_h = int(self.h * settings.MENU_PANEL_HEIGHT_RATIO)
        if panel is not None:
            self.panel = pygame.transform.smoothscale(panel, (target_w, target_h))
        else:
            self.panel = None

        self.panel_w, self.panel_h = target_w, target_h
        self.panel_x = (self.w - target_w) // 2
        self.panel_y = int(self.h * settings.MENU_PANEL_CENTER_Y_RATIO) - target_h // 2

        # --- Шрифты ---
        # Масштабируем шрифты под фактический размер панели, чтобы текст
        # красиво помещался в свиток при любом разрешении экрана.
        font_path = os.path.join(settings.MENU_DIR, "font.ttf")
        ref = target_w / (self.w * settings.MENU_PANEL_WIDTH_RATIO)  # ~1.0
        title_size = max(24, int(settings.MENU_TITLE_FONT_SIZE * ref))
        item_size = max(18, int(settings.MENU_ITEM_FONT_SIZE * ref))

        if os.path.exists(font_path):
            self.title_font = pygame.font.Font(font_path, title_size)
            self.item_font = pygame.font.Font(font_path, item_size)
        else:
            # Запасной вариант, если файла нет — системный.
            self.title_font = pygame.font.SysFont("georgia", title_size, bold=True)
            self.item_font = pygame.font.SysFont("georgia", item_size, bold=True)

        self.items = list(settings.MENU_ITEMS)  # [(id, label), ...]
        self.selected = 0
        self._item_rects = []  # экранные прямоугольники пунктов (для мыши)
        self._layout_items()

    def _layout_items(self):
        """Считает позиции заголовка и пунктов внутри свитка."""
        # Полезная область свитка (внутри рамки/валиков) — с отступами.
        inner_x = self.panel_x + int(self.panel_w * 0.16)
        inner_w = int(self.panel_w * 0.68)
        inner_top = self.panel_y + int(self.panel_h * 0.20)
        inner_bottom = self.panel_y + int(self.panel_h * 0.84)
        inner_cx = inner_x + inner_w // 2

        # Заголовок.
        self.title_surf = self.title_font.render(
            settings.MENU_TITLE, True, settings.MENU_TITLE_COLOR
        )
        self.title_pos = (
            inner_cx - self.title_surf.get_width() // 2,
            inner_top,
        )

        # Пункты — равномерно в нижней части полезной области.
        items_top = inner_top + self.title_surf.get_height() + int(self.panel_h * 0.08)
        n = len(self.items)
        gap = (inner_bottom - items_top) / max(1, n)
        self._item_rects = []
        for i, (_id, label) in enumerate(self.items):
            surf = self.item_font.render(label, True, settings.MENU_ITEM_COLOR)
            cy = int(items_top + gap * (i + 0.5))
            rect = surf.get_rect(center=(inner_cx, cy))
            self._item_rects.append(rect)

    # ---------- Ввод ----------
    def handle_event(self, event):
        """Обрабатывает событие. Возвращает id пункта при выборе, иначе None."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.items)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.items)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return self.items[self.selected][0]

        elif event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self._item_rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._item_rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    return self.items[i][0]

        return None

    # ---------- Обновление ----------
    def update(self, dt):
        for cloud in self.clouds:
            cloud.update(dt)

    # ---------- Отрисовка ----------
    def render(self):
        # 1. Фон.
        if self.background is not None:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(settings.MENU_FALLBACK_SKY)

        # 2. Облака (летят за панелью).
        for cloud in self.clouds:
            cloud.render(self.screen)

        # 3. Панель-свиток.
        if self.panel is not None:
            self.screen.blit(self.panel, (self.panel_x, self.panel_y))
        else:
            # Заглушка панели, если ассета нет.
            pygame.draw.rect(
                self.screen, (222, 200, 150),
                (self.panel_x, self.panel_y, self.panel_w, self.panel_h),
                border_radius=12,
            )
            pygame.draw.rect(
                self.screen, (120, 90, 50),
                (self.panel_x, self.panel_y, self.panel_w, self.panel_h),
                width=4, border_radius=12,
            )

        # 4. Заголовок.
        self.screen.blit(self.title_surf, self.title_pos)

        # 5. Пункты меню (подсветка выбранного).
        for i, (_id, label) in enumerate(self.items):
            hovered = (i == self.selected)
            base_center = self._item_rects[i].center

            surf = self.item_font.render(label, True, settings.MENU_ITEM_COLOR)

            if hovered:
                # Осветляем: добавляем белый по режиму BLEND_RGB_ADD.
                surf = surf.copy()
                surf.fill((90, 90, 60), special_flags=pygame.BLEND_RGB_ADD)
                # Лёгкое увеличение (1.12x) для «оживления».
                w, h = surf.get_size()
                surf = pygame.transform.smoothscale(surf, (int(w * 1.12), int(h * 1.12)))

            rect = surf.get_rect(center=base_center)
            self.screen.blit(surf, rect)
