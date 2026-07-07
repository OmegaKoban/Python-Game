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
        inner_top = self.panel_y + int(self.panel_h * 0.20)
        inner_bottom = self.panel_y + int(self.panel_h * 0.84)
        # Центр панели по горизонтали — для точного центрирования текста.
        inner_cx = self.panel_x + self.panel_w // 2

        # Заголовок.
        self.title_surf = self.title_font.render(
            settings.MENU_TITLE, True, settings.MENU_TITLE_COLOR
        )
        title_rect = self.title_surf.get_rect(centerx=inner_cx, top=inner_top)
        self.title_pos = title_rect.topleft

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




class SettingsMenu:
    """
    Экран настроек. Визуально идентичен главному меню.
    Строки: имя игрока, громкость, яркость, назад.
    handle_event() возвращает "back" при выходе, иначе None.
    """

    _ROWS = [
        ("name",       "Имя игрока"),
        ("volume",     "Громкость"),
        ("brightness", "Яркость"),
        ("back",       "Назад"),
    ]

    _NAME_ALLOWED = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
        "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
        "0123456789_- "
    )
    _NAME_MAX_LEN = 16

    def __init__(self, screen):
        self.screen = screen
        self.w, self.h = screen.get_size()

        bg = _load_image(settings.MENU_BACKGROUND_PATH, alpha=False)
        self.background = (
            pygame.transform.smoothscale(bg, (self.w, self.h)) if bg else None
        )

        cloud_images = []
        for i in range(1, settings.MENU_CLOUD_COUNT + 1):
            img = _load_image(settings.MENU_CLOUD_PATH_TMPL.format(i))
            if img:
                cloud_images.append(img)
        self.clouds = []
        if cloud_images:
            count = max(settings.MENU_CLOUD_COUNT, len(cloud_images))
            for k in range(count):
                base = cloud_images[k % len(cloud_images)]
                self.clouds.append(Cloud(base, self.w, self.h, settings.MENU_CLOUD_DIRECTION))

        panel = _load_image(settings.MENU_PANEL_PATH)
        target_w = int(self.w * settings.MENU_PANEL_WIDTH_RATIO)
        target_h = int(self.h * settings.MENU_PANEL_HEIGHT_RATIO)
        self.panel = (
            pygame.transform.smoothscale(panel, (target_w, target_h)) if panel else None
        )
        self.panel_w, self.panel_h = target_w, target_h
        self.panel_x = (self.w - target_w) // 2
        self.panel_y = int(self.h * settings.MENU_PANEL_CENTER_Y_RATIO) - target_h // 2

        font_path = os.path.join(settings.MENU_DIR, "font.ttf")
        ref = target_w / (self.w * settings.MENU_PANEL_WIDTH_RATIO)
        title_size = max(24, int(settings.MENU_TITLE_FONT_SIZE * ref))
        item_size  = max(16, int(settings.MENU_ITEM_FONT_SIZE * ref))
        if os.path.exists(font_path):
            self.title_font = pygame.font.Font(font_path, title_size)
            self.item_font  = pygame.font.Font(font_path, item_size)
        else:
            self.title_font = pygame.font.SysFont("georgia", title_size, bold=True)
            self.item_font  = pygame.font.SysFont("georgia", item_size,  bold=True)

        # Системный шрифт с кириллицей — только для поля ввода имени.
        self._input_font = None
        for fname in ("arialunicode", "arial", "helveticaneue", "dejavusans"):
            f = pygame.font.SysFont(fname, item_size)
            if f.render("А", True, (0, 0, 0)).get_width() > 2:
                self._input_font = f
                break
        if self._input_font is None:
            self._input_font = pygame.font.Font(None, item_size)

        self.player_name = settings.SETTINGS_PLAYER_NAME
        self.brightness  = settings.SETTINGS_BRIGHTNESS
        self.volume      = settings.SETTINGS_VOLUME

        self._typing     = False
        self._cursor_vis = True
        self._cursor_t   = 0.0

        self.selected = 0
        self._item_rects    = []
        self._arrow_l_rects = []
        self._arrow_r_rects = []
        self._layout()

    # ------------------------------------------------------------------ helpers
    def _draw_breve(self, surf, title_pos, title_surf, char_index):
        """
        Рисует краткую (дужку) над символом с индексом char_index в title_surf.
        Все символы в font.ttf равной ширины — считаем позицию через advance.
        """
        # Ширина одного символа через font metrics advance.
        metrics = self.title_font.metrics(settings.SETTINGS_TITLE)
        if char_index >= len(metrics):
            return
        # Накопленный x до нужного символа.
        x_offset = sum(m[4] for m in metrics[:char_index])  # m[4] = advance
        char_advance = metrics[char_index][4]

        # Позиция дужки: рисуем в верхней части глифа, прямо над серединой буквы.
        tx, ty = title_pos
        char_cx = tx + x_offset + char_advance // 2
        font_h  = self.title_font.get_height()

        bw = int(char_advance * 0.60)
        bh = max(5, int(font_h * 0.14))
        bx = char_cx - bw // 2
        by = ty + max(0, int(font_h * 0.02))   # самый верх глифа
        rect = pygame.Rect(bx, by, bw, bh)
        color = settings.MENU_TITLE_COLOR
        import math
        pygame.draw.arc(surf, color, rect, 0, math.pi, max(2, bh // 3))

    def _row_text(self, i):
        key, label = self._ROWS[i]
        if key == "volume":
            return f"{label}: {int(round(self.volume * 100))}%"
        if key == "brightness":
            return f"{label}: {int(round(self.brightness * 100))}%"
        if key == "name":
            return f"{label}:"
        return label

    # ------------------------------------------------------------------ layout
    def _layout(self):
        inner_top    = self.panel_y + int(self.panel_h * 0.18)
        inner_bottom = self.panel_y + int(self.panel_h * 0.86)
        inner_cx     = self.panel_x + self.panel_w // 2

        title_surf = self.title_font.render(
            settings.SETTINGS_TITLE, True, settings.MENU_TITLE_COLOR
        )
        self._title_surf = title_surf
        self._title_pos  = title_surf.get_rect(centerx=inner_cx, top=inner_top).topleft

        items_top = inner_top + title_surf.get_height() + int(self.panel_h * 0.06)
        n   = len(self._ROWS)
        gap = (inner_bottom - items_top) / max(1, n)

        self._item_rects    = []
        self._arrow_l_rects = []
        self._arrow_r_rects = []

        usable_w = int(self.panel_w * 0.65)
        usable_x = inner_cx - usable_w // 2

        for i in range(n):
            cy = int(items_top + gap * (i + 0.5))
            surf = self.item_font.render(self._row_text(i), True, settings.MENU_ITEM_COLOR)
            row_rect = pygame.Rect(usable_x, cy - surf.get_height() // 2 - 4,
                                   usable_w, surf.get_height() + 8)
            self._item_rects.append(row_rect)

            arr_size = self.item_font.get_height()
            if self._ROWS[i][0] in ("volume", "brightness"):
                l_rect = pygame.Rect(usable_x, cy - arr_size // 2, arr_size, arr_size)
                r_rect = pygame.Rect(usable_x + usable_w - arr_size, cy - arr_size // 2,
                                     arr_size, arr_size)
            else:
                l_rect = r_rect = pygame.Rect(0, 0, 0, 0)
            self._arrow_l_rects.append(l_rect)
            self._arrow_r_rects.append(r_rect)

    # ------------------------------------------------------------------ draw helpers
    def _draw_arrow(self, surface, cx, cy, size, direction, color):
        """Треугольная стрелка влево (direction=-1) или вправо (+1)."""
        h = size * 0.55
        w = size * 0.45
        if direction < 0:
            pts = [(cx + w/2, cy - h/2), (cx + w/2, cy + h/2), (cx - w/2, cy)]
        else:
            pts = [(cx - w/2, cy - h/2), (cx - w/2, cy + h/2), (cx + w/2, cy)]
        pygame.draw.polygon(surface, color, pts)

    def _draw_back_arrow(self, surface, x, cy, size, color):
        """Стрелка назад (←): линия + треугольный наконечник слева."""
        lw = int(size * 0.9)
        th = int(size * 0.45)
        tw = int(size * 0.38)
        lh = max(2, int(size * 0.13))
        pygame.draw.rect(surface, color,
                         pygame.Rect(x + tw - 2, cy - lh // 2, lw - tw + 2, lh))
        pygame.draw.polygon(surface, color, [
            (x + tw, cy - th // 2),
            (x + tw, cy + th // 2),
            (x,      cy),
        ])

    # ------------------------------------------------------------------ input
    def handle_event(self, event):
        if self._typing:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    self._typing = False
                    settings.SETTINGS_PLAYER_NAME = self.player_name
                elif event.key == pygame.K_BACKSPACE:
                    self.player_name = self.player_name[:-1]
                else:
                    ch = event.unicode
                    if ch in self._NAME_ALLOWED and len(self.player_name) < self._NAME_MAX_LEN:
                        # Проверяем что с новым символом строка ещё влезает в свиток.
                        prefix = "Имя игрока: "
                        test_w = self.item_font.size(prefix + self.player_name + ch + "|")[0]
                        max_w  = int(self.panel_w * 0.68)
                        if test_w <= max_w:
                            self.player_name += ch
            return None

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self._ROWS)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self._ROWS)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self._adjust(self.selected, -1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._adjust(self.selected, +1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self._activate(self.selected)
            elif event.key == pygame.K_ESCAPE:
                return "back"

        elif event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self._item_rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for i in range(len(self._ROWS)):
                if self._arrow_l_rects[i].width > 0 and self._arrow_l_rects[i].collidepoint(pos):
                    self.selected = i
                    self._adjust(i, -1)
                    return None
                if self._arrow_r_rects[i].width > 0 and self._arrow_r_rects[i].collidepoint(pos):
                    self.selected = i
                    self._adjust(i, +1)
                    return None
            for i, rect in enumerate(self._item_rects):
                if rect.collidepoint(pos):
                    self.selected = i
                    return self._activate(i)

        elif event.type == pygame.MOUSEWHEEL:
            self._adjust(self.selected, event.y)

        return None

    def _adjust(self, i, direction):
        key, _ = self._ROWS[i]
        if key == "brightness":
            self.brightness = max(0.2, min(1.0, round(self.brightness + direction * 0.1, 1)))
            settings.SETTINGS_BRIGHTNESS = self.brightness
        elif key == "volume":
            self.volume = max(0.0, min(1.0, round(self.volume + direction * 0.1, 1)))
            settings.SETTINGS_VOLUME = self.volume
            try:
                pygame.mixer.music.set_volume(self.volume)
            except Exception:
                pass
        self._layout()

    def _activate(self, i):
        key, _ = self._ROWS[i]
        if key == "back":
            return "back"
        if key == "name":
            self._typing = True
            self._cursor_t = 0.0
            self._cursor_vis = True
        elif key in ("brightness", "volume"):
            self._adjust(i, +1)
        return None

    # ------------------------------------------------------------------ update
    def update(self, dt):
        for cloud in self.clouds:
            cloud.update(dt)
        self._cursor_t += dt
        if self._cursor_t >= 0.5:
            self._cursor_t -= 0.5
            self._cursor_vis = not self._cursor_vis

    # ------------------------------------------------------------------ render
    def render(self):
        surf = self.screen

        # 1. Фон (без яркости — оверлей накладывается в main() поверх всего).
        if self.background is not None:
            surf.blit(self.background, (0, 0))
        else:
            surf.fill(settings.MENU_FALLBACK_SKY)

        # 2. Облака.
        for cloud in self.clouds:
            cloud.render(surf)

        # 3. Панель-свиток.
        if self.panel is not None:
            surf.blit(self.panel, (self.panel_x, self.panel_y))
        else:
            pygame.draw.rect(surf, (222, 200, 150),
                             (self.panel_x, self.panel_y, self.panel_w, self.panel_h),
                             border_radius=12)
            pygame.draw.rect(surf, (120, 90, 50),
                             (self.panel_x, self.panel_y, self.panel_w, self.panel_h),
                             width=4, border_radius=12)

        # 4. Заголовок.
        surf.blit(self._title_surf, self._title_pos)
        # Рисуем краткую над «Й» вручную — font.ttf не отображает её.
        # «Й» — 7-й символ (индекс 6) в «НАСТРОЙКИ», каждый символ равной ширины.
        self._draw_breve(surf, self._title_pos, self._title_surf, 6)

        # 5. Строки настроек.
        inner_cx = self.panel_x + self.panel_w // 2
        usable_w = int(self.panel_w * 0.65)
        usable_x = inner_cx - usable_w // 2
        col_norm  = settings.MENU_ITEM_COLOR
        col_light = (180, 140, 80)

        for i, (key, label) in enumerate(self._ROWS):
            hovered = (i == self.selected)
            cy      = self._item_rects[i].centery
            color   = col_light if hovered else col_norm
            arr_size = self.item_font.get_height()

            if key == "name":
                # Вся строка через item_font (font.ttf), значение — тоже.
                display  = self.player_name + ("|" if self._typing and self._cursor_vis else "")
                line     = f"{label}: {display}"
                lbl_surf = self.item_font.render(line, True, color)
                # Обрезаем если не влезает в полезную ширину свитка.
                max_w = int(self.panel_w * 0.68)
                if lbl_surf.get_width() > max_w:
                    # Укорачиваем display с конца до тех пор, пока не влезет.
                    prefix = f"{label}: "
                    trimmed = display
                    while trimmed and self.item_font.size(prefix + trimmed)[0] > max_w:
                        trimmed = trimmed[:-1]
                    line     = prefix + trimmed
                    lbl_surf = self.item_font.render(line, True, color)
                surf.blit(lbl_surf, lbl_surf.get_rect(center=(inner_cx, cy)))

            elif key in ("volume", "brightness"):
                txt_surf = self.item_font.render(self._row_text(i), True, color)
                surf.blit(txt_surf, txt_surf.get_rect(center=(inner_cx, cy)))
                # Стрелки по бокам.
                arr_cx_l = usable_x + arr_size // 2
                arr_cx_r = usable_x + usable_w - arr_size // 2
                self._draw_arrow(surf, arr_cx_l, cy, arr_size, -1, color)
                self._draw_arrow(surf, arr_cx_r, cy, arr_size, +1, color)

            elif key == "back":
                txt_surf = self.item_font.render(label, True, color)
                arr_w  = int(arr_size * 0.9)
                gap    = int(arr_size * 0.3)
                total  = arr_w + gap + txt_surf.get_width()
                start_x = inner_cx - total // 2
                self._draw_back_arrow(surf, start_x, cy, arr_size, color)
                surf.blit(txt_surf, txt_surf.get_rect(midleft=(start_x + arr_w + gap, cy)))

        # Подсказка при вводе имени.
        if self._typing:
            hint = self._input_font.render("Enter / ESC — сохранить", True, (120, 90, 50))
            surf.blit(hint, hint.get_rect(
                centerx=self.panel_x + self.panel_w // 2,
                bottom=self.panel_y + self.panel_h - 14,
            ))
        # flip() вызывается в main() после наложения оверлея яркости.
