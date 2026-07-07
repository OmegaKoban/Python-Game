"""
Auto Arsenal — roguelike-выживач с автоатакой против волн врагов.

Игровой цикл: process input -> update -> render.

Управление:
    WASD / стрелки — движение
    Атака — автоматическая (по ближайшему врагу в радиусе)
    R — рестарт после поражения
    ESC — выход

Запуск:
    python main.py

Ассеты (папка assets/): если файлов нет — всё работает на заглушках
(игрок — кружок, враги — квадраты, снаряды — точки). Пути к ассетам
настраиваются в src/settings.py.
"""

import pygame

from src import settings
from src.tilemap import TileMap
from src.player import Player
from src.camera import Camera
from src.wave_manager import WaveManager
from src.hud import HUD
from src.menu import Menu, SettingsMenu


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.tilemap = TileMap()
        self.reset()

    def reset(self):
        """Полный сброс состояния — для старта и рестарта после поражения."""
        center = (self.tilemap.pixel_width // 2, self.tilemap.pixel_height // 2)
        self.player = Player(start_pos=center)
        self.camera = Camera(self.tilemap)
        self.wave_manager = WaveManager(self.tilemap)
        self.hud = HUD()

        self.enemies = pygame.sprite.Group()
        self.projectiles = []
        self.kills = 0
        self.game_over = False

        # Промежуточный surface в размер видимой области мира (до зума).
        self.view_surface = pygame.Surface(self.camera.get_view_surface_size())

    def update(self, dt):
        if self.game_over:
            return

        # Игрок (движение + автоатака по врагам).
        self.player.update(dt, self.tilemap, self.enemies)
        # Забираем выпущенные игроком снаряды.
        self.projectiles.extend(self.player.collect_projectiles())

        # Волны врагов.
        self.wave_manager.update(dt, self.player, self.enemies)

        # Враги преследуют игрока и бьют при касании.
        for enemy in list(self.enemies):
            enemy.update(dt, self.player, self.tilemap)

        # Снаряды летят и наносят урон.
        for proj in self.projectiles:
            proj.update(dt, self.enemies, self.tilemap)

        # Убираем мёртвых врагов и считаем убийства.
        for enemy in list(self.enemies):
            if not enemy.is_alive:
                self.kills += 1
                self.enemies.remove(enemy)

        # Убираем отработавшие снаряды.
        self.projectiles = [p for p in self.projectiles if p.alive]

        # Камера следит за игроком.
        self.camera.update(self.player.rect)

        # Проверка поражения.
        if not self.player.is_alive:
            self.game_over = True

    def render(self):
        # 1. Рендер мира в промежуточный surface (масштаб 1:1 мира).
        self.view_surface.fill(settings.BACKGROUND_COLOR)
        self.tilemap.render(self.view_surface, self.camera.offset)

        # Снаряды под персонажами.
        for proj in self.projectiles:
            proj.render(self.view_surface, self.camera)

        # Враги.
        for enemy in self.enemies:
            enemy.render(self.view_surface, self.camera)

        # Игрок (мигает при неуязвимости после урона).
        if not (self.player.invuln_timer > 0 and int(self.player.invuln_timer * 20) % 2 == 0):
            self.view_surface.blit(self.player.image, self.camera.apply(self.player.rect))

        # Отладка: хитбокс игрока (красная рамка). Хитбоксы врагов рисуются в Enemy.render.
        if settings.DEBUG_HITBOXES:
            pygame.draw.rect(self.view_surface, (255, 60, 60),
                             self.camera.apply(self.player.hitbox), width=2)

        # 2. Растягиваем на весь экран (зум).
        scaled = pygame.transform.scale(
            self.view_surface, (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        )
        self.screen.blit(scaled, (0, 0))

        # 3. HUD поверх (в экранных координатах, не масштабируется зумом).
        self.hud.render(self.screen, self.player, self.wave_manager, self.kills)
        if self.game_over:
            self.hud.render_game_over(self.screen, self.kills, self.wave_manager.wave_number)
        # flip() намеренно убран — его вызывает main() после наложения оверлея яркости.


def create_screen():
    # Реальное разрешение монитора — нужно, т.к. SCALED не принимает размер (0,0).
    info = pygame.display.Info()
    desktop_size = (info.current_w, info.current_h)

    flags = pygame.SCALED | pygame.DOUBLEBUF
    if settings.SCREEN_MODE == "fullscreen":
        flags |= pygame.FULLSCREEN
        size = desktop_size
    elif settings.SCREEN_MODE == "borderless":
        flags |= pygame.NOFRAME
        size = desktop_size
    else:
        size = (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)

    try:
        screen = pygame.display.set_mode(size, flags, vsync=1)
    except pygame.error:
        try:
            screen = pygame.display.set_mode(size, flags)  # без vsync
        except pygame.error:
            # Полный откат: без SCALED (например, старые драйверы).
            fallback = flags & ~pygame.SCALED
            screen = pygame.display.set_mode(size, fallback)

    settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT = screen.get_size()
    return screen


# Состояния приложения.
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_SETTINGS = "settings"


def main():
    pygame.init()
    pygame.display.set_caption(settings.WINDOW_TITLE)
    screen = create_screen()
    clock = pygame.time.Clock()

    menu = Menu(screen)
    settings_menu = None   # создаётся лазиво при первом открытии
    game = None  # игра создаётся при нажатии «Играть»
    state = STATE_MENU

    # Surface для оверлея яркости — создаём один раз, не каждый кадр.
    dim_overlay = pygame.Surface(screen.get_size())
    dim_overlay.fill((0, 0, 0))

    running = True
    while running:
        dt = clock.tick(settings.FPS) / 1000  # мс -> секунды

        # 1. Process Input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif state == STATE_MENU:
                choice = menu.handle_event(event)
                if choice == "play":
                    game = Game(screen)
                    state = STATE_PLAYING
                elif choice == "settings":
                    settings_menu = SettingsMenu(screen)
                    state = STATE_SETTINGS
                elif choice == "records":
                    pass   # откроем экран рекордов позже
                elif choice == "quit":
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            elif state == STATE_SETTINGS:
                result = settings_menu.handle_event(event)
                if result == "back":
                    state = STATE_MENU

            elif state == STATE_PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # ESC в игре — возврат в меню.
                        state = STATE_MENU
                    elif event.key == pygame.K_r and game.game_over:
                        game.reset()

        # 2. Update + 3. Render
        if state == STATE_MENU:
            menu.update(dt)
            menu.render()
        elif state == STATE_SETTINGS:
            settings_menu.update(dt)
            settings_menu.render()
        else:
            game.update(dt)
            game.render()

        # Яркость — применяется поверх любого экрана.
        # brightness=1.0 -> alpha=0 (не влияет), brightness=0.2 -> alpha=178.
        alpha = int((1.0 - settings.SETTINGS_BRIGHTNESS) * 222)
        if alpha > 0:
            dim_overlay.set_alpha(alpha)
            screen.blit(dim_overlay, (0, 0))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
