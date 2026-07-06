"""
Интерфейс поверх игры (HUD): полоска здоровья игрока, номер волны,
счётчик убийств и обратный отсчёт до следующей волны. Рисуется прямо на
экране (после зума), в экранных координатах, поэтому не масштабируется.
"""

import pygame

from src import settings


class HUD:
    def __init__(self):
        pygame.font.init()
        self.font = pygame.font.SysFont("consolas", settings.HUD_FONT_SIZE)
        self.big_font = pygame.font.SysFont("consolas", settings.HUD_FONT_SIZE * 2, bold=True)

    def _text(self, surface, text, pos, color=None):
        color = color or settings.HUD_TEXT_COLOR
        img = self.font.render(text, True, color)
        surface.blit(img, pos)

    def render(self, surface, player, wave_manager, kills):
        # --- Полоска здоровья игрока (слева сверху) ---
        bar_x, bar_y = 20, 20
        bar_w, bar_h = 260, 24
        pygame.draw.rect(surface, settings.PLAYER_HP_BAR_BG, (bar_x, bar_y, bar_w, bar_h),
                         border_radius=4)
        ratio = max(0.0, player.hp / player.max_hp)
        pygame.draw.rect(surface, settings.PLAYER_HP_BAR_FG,
                         (bar_x, bar_y, int(bar_w * ratio), bar_h), border_radius=4)
        pygame.draw.rect(surface, (0, 0, 0), (bar_x, bar_y, bar_w, bar_h), width=2,
                         border_radius=4)
        self._text(surface, f"HP: {player.hp} / {player.max_hp}", (bar_x + 8, bar_y + 2))

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
