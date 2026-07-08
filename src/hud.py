"""
Интерфейс поверх игры (HUD): полоска здоровья игрока, номер волны,
счётчик убийств и обратный отсчёт до следующей волны. Рисуется прямо на
экране (после зума), в экранных координатах, поэтому не масштабируется.
"""

import os

import pygame

from src import settings


def _make_font(size: int, bold: bool = False) -> pygame.font.Font:
    """
    Создаёт шрифт с поддержкой кириллицы.
    Приоритет:
      1. font.ttf из ассетов меню (уже проверен на кириллицу).
      2. Системный шрифт с поддержкой Unicode/кириллицы (arialunicode, arial,
         helveticaneue, dejavusans — кросс-платформенный список).
      3. Дефолтный шрифт pygame (кириллицу не поддерживает, но лучше чем ничего).
    """
    font_path = os.path.join(settings.MENU_DIR, "font.ttf")
    if os.path.exists(font_path):
        try:
            return pygame.font.Font(font_path, size)
        except Exception:
            pass

    # Список системных шрифтов с широкой поддержкой Unicode/кириллицы.
    candidates = [
        "arialunicode",   # macOS — Arial Unicode MS, полная кириллица
        "arial",          # Windows / macOS
        "helveticaneue",  # macOS
        "dejavusans",     # Linux
        "liberationsans", # Linux
        "freesans",       # Linux
    ]
    for name in candidates:
        font = pygame.font.SysFont(name, size, bold=bold)
        # SysFont не выбрасывает исключение при отсутствии шрифта — проверяем
        # реальное имя, чтобы убедиться, что он нашёлся.
        if font.get_bold() == bold or not bold:
            # Дополнительная проверка: убеждаемся, что рендер кириллицы даёт
            # ненулевую ширину символа (а не тофу-квадраты шириной 0).
            test = font.render("А", True, (255, 255, 255))
            if test.get_width() > 2:
                return font

    # Крайний запасной вариант — встроенный шрифт pygame.
    return pygame.font.Font(None, size)


class HUD:
    def __init__(self):
        pygame.font.init()
        self.font = _make_font(settings.HUD_FONT_SIZE)
        self.hp_font = _make_font(settings.HUD_HP_FONT_SIZE)
        self.big_font = _make_font(settings.HUD_FONT_SIZE * 2, bold=True)
        self.card_title_font = pygame.font.SysFont("consolas",int(settings.HUD_FONT_SIZE * 1.15), bold=True)
        self.card_desc_font = pygame.font.SysFont("consolas", settings.HUD_FONT_SIZE)

    def _text(self, surface, text, pos, color=None):
        color = color or settings.HUD_TEXT_COLOR
        img = self.font.render(text, True, color)
        surface.blit(img, pos)

    def render(self, surface, player, wave_manager, kills):
        # --- Полоска здоровья игрока (слева сверху) ---
        bar_x, bar_y = 20, 20
        bar_w, bar_h = 300, 34
        pygame.draw.rect(surface, settings.PLAYER_HP_BAR_BG, (bar_x, bar_y, bar_w, bar_h),
                         border_radius=4)
        ratio = max(0.0, player.hp / player.max_hp)
        pygame.draw.rect(surface, settings.PLAYER_HP_BAR_FG,
                         (bar_x, bar_y, int(bar_w * ratio), bar_h), border_radius=4)
        pygame.draw.rect(surface, (0, 0, 0), (bar_x, bar_y, bar_w, bar_h), width=2,
                         border_radius=4)
        img = self.hp_font.render(f"HP: {player.hp} / {player.max_hp}", True, settings.HUD_TEXT_COLOR)
        surface.blit(img, (bar_x + 8, bar_y + (bar_h - img.get_height()) // 2))

        # --- Волна и убийства (справа сверху) ---
        wave_text = f"Волна: {wave_manager.wave_number}"
        kills_text = f"Убито: {kills}"
        wave_img = self.font.render(wave_text, True, settings.HUD_TEXT_COLOR)
        kills_img = self.font.render(kills_text, True, settings.HUD_TEXT_COLOR)
        surface.blit(wave_img, (surface.get_width() - wave_img.get_width() - 20, 20))
        surface.blit(kills_img, (surface.get_width() - kills_img.get_width() - 20, 48))

        # --- Обратный отсчёт до следующей волны (по центру сверху) ---
        countdown = wave_manager.time_to_next_wave
        if countdown is not None and countdown > 0:
            msg = f"Следующая волна через {countdown:0.1f}"
            img = self.font.render(msg, True, (255, 220, 120))
            surface.blit(img, (surface.get_width() // 2 - img.get_width() // 2, 20))

        self._render_xp_bar(surface, player)    

    def render_game_over(self, surface, kills, wave):
        """Экран поражения."""
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

        cx = surface.get_width() // 2
        cy = surface.get_height() // 2

        title = self.big_font.render("ПОРАЖЕНИЕ", True, (240, 80, 80))
        surface.blit(title, (cx - title.get_width() // 2, cy - 90))

        stats = self.font.render(f"Волн пройдено: {wave}    Убито врагов: {kills}",
                                 True, settings.HUD_TEXT_COLOR)
        surface.blit(stats, (cx - stats.get_width() // 2, cy - 10))

        hint = self.font.render("R — заново    ESC — выход", True, (200, 200, 210))
        surface.blit(hint, (cx - hint.get_width() // 2, cy + 30))

    def _render_xp_bar(self, surface, player):
        w = surface.get_width(); h = surface.get_height()
        bar_h = 14; margin = 40
        bar_x = margin; bar_y = h - bar_h - 12; bar_w = w - margin * 2
        pygame.draw.rect(surface, settings.XP_BAR_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=6)
        ratio = 0.0
        if player.xp_to_next > 0:
            ratio = max(0.0, min(1.0, player.xp / player.xp_to_next))
        pygame.draw.rect(surface, settings.XP_BAR_FG,
                         (bar_x, bar_y, int(bar_w * ratio), bar_h), border_radius=6)
        pygame.draw.rect(surface, (0, 0, 0), (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=6)
        img = self.font.render(f"Уровень {player.level}", True, settings.HUD_TEXT_COLOR)
        surface.blit(img, (bar_x, bar_y - img.get_height() - 2))

    def render_levelup(self, surface, player, choices, selected_index):
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190)); surface.blit(overlay, (0, 0))
        w = surface.get_width(); h = surface.get_height(); cx = w // 2
        title = self.big_font.render("НОВЫЙ УРОВЕНЬ!", True, (255, 220, 120))
        surface.blit(title, (cx - title.get_width() // 2, int(h * 0.14)))
        sub = self.font.render("Выбери улучшение:  1 / 2 / 3,  стрелки + Enter или мышь",
                               True, (210, 210, 220))
        surface.blit(sub, (cx - sub.get_width() // 2, int(h * 0.14) + title.get_height() + 8))
        n = len(choices)
        if n == 0:
            return []
        card_w = min(320, (w - 80) // max(1, n) - 20)
        card_h = int(h * 0.34); gap = 28
        total_w = card_w * n + gap * (n - 1)
        start_x = cx - total_w // 2; card_y = int(h * 0.40)
        rects = []
        for i, choice in enumerate(choices):
            cardx = start_x + i * (card_w + gap)
            rect = pygame.Rect(cardx, card_y, card_w, card_h); rects.append(rect)
            selected = (i == selected_index)
            bg = (55, 60, 90) if selected else (35, 38, 55)
            border = (255, 220, 120) if selected else (90, 95, 120)
            pygame.draw.rect(surface, bg, rect, border_radius=10)
            pygame.draw.rect(surface, border, rect, width=(4 if selected else 2), border_radius=10)
            num_img = self.big_font.render(str(i + 1), True, border)
            surface.blit(num_img, (cardx + 14, card_y + 10))
            kind_label = "Способность" if choice.get("type") == "ability" else "Улучшение"
            kind_img = self.card_desc_font.render(kind_label, True, (150, 160, 190))
            surface.blit(kind_img, (cardx + 14, card_y + card_h - kind_img.get_height() - 12))
            ty = card_y + 60
            ty = self._blit_wrapped(surface, choice.get("title", ""), self.card_title_font,
                                    (240, 240, 250), cardx + 14, ty, card_w - 28)
            ty += 8
            self._blit_wrapped(surface, choice.get("desc", ""), self.card_desc_font,
                               (200, 205, 220), cardx + 14, ty, card_w - 28)
        return rects

    def _blit_wrapped(self, surface, text, font, color, x, y, max_w):
        words = text.split(); line = ""; lh = font.get_height() + 2
        for word in words:
            test = (line + " " + word).strip()
            if font.size(test)[0] <= max_w:
                line = test
            else:
                if line:
                    surface.blit(font.render(line, True, color), (x, y)); y += lh
                line = word
        if line:
            surface.blit(font.render(line, True, color), (x, y)); y += lh
        return y    
