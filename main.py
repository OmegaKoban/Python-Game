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

from src.pickups import Pickup
from src.menu import Menu, SettingsMenu, RecordsMenu
from src.records import add_record



class Game:
    def __init__(self, screen):
        self.screen = screen
        self.tilemap = TileMap()
        self.reset()

    def reset(self):
        """Полный сброс состояния — для старта и рестарта после поражения."""
        center = (self.tilemap.pixel_width // 2, self.tilemap.pixel_height // 2 + 200)
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

        self.pickups = []
        self.level_up_active = False
        self.levelup_choices = []
        self.levelup_selected = 0
        self.levelup_rects = []

    def update(self, dt):
        if self.game_over or self.level_up_active:
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
                for kind, value, pos in enemy.roll_drops():       # <-- ДОБАВИТЬ
                    self.pickups.append(Pickup(pos, kind, value))  # <-- ДОБАВИТЬ
                self.enemies.remove(enemy)

        # Дропы: магнитятся к игроку, при подборе дают опыт / здоровье.  # <-- ДОБАВИТЬ весь блок
        for pickup in list(self.pickups):
            if pickup.update(dt, self.player):
                if pickup.kind == "xp":
                    self.player.add_xp(pickup.value)
                elif pickup.kind == "heal":
                    self.player.heal(pickup.value)
        self.pickups = [p for p in self.pickups if p.alive]

        # Убираем отработавшие снаряды.
        self.projectiles = [p for p in self.projectiles if p.alive]

        # Камера следит за игроком.
        self.camera.update(self.player.rect)

        # Проверка поражения.
        if not self.player.is_alive:
            self.game_over = True
            return                              # <-- ДОБАВИТЬ

        # Повышение уровня: есть очередь выборов — встаём на паузу.  # <-- ДОБАВИТЬ весь блок
        if self.player.pending_levelups > 0:
            self._open_level_up()

    def render(self):
        # 1. Рендер мира в промежуточный surface (масштаб 1:1 мира).
        self.view_surface.fill(settings.BACKGROUND_COLOR)
        self.tilemap.render(self.view_surface, self.camera.offset)

        # Дропы под персонажами.
        for pickup in self.pickups:
            pickup.render(self.view_surface, self.camera)

        # Снаряды под персонажами.
        for proj in self.projectiles:
            proj.render(self.view_surface, self.camera)

        # Враги.
        for enemy in self.enemies:
            enemy.render(self.view_surface, self.camera)

        # Игрок (мигает при неуязвимости после урона).
        if not (self.player.invuln_timer > 0 and int(self.player.invuln_timer * 20) % 2 == 0):
            self.view_surface.blit(self.player.image, self.camera.apply(self.player.rect))

        # Эффекты активных способностей поверх.
        self.player.abilities.render(self.view_surface, self.camera)    

        # Отладка: хитбокс игрока (красная рамка). Хитбоксы врагов рисуются в Enemy.render.
        if settings.DEBUG_HITBOXES:
            pygame.draw.rect(self.view_surface, (255, 60, 60),
                             self.camera.apply(self.player.hitbox), width=2)
        
        # Отладка: зоны коллизий (синие рамки).
        if settings.DEBUG_COLLISION_ZONES:
            for zone in self.tilemap.collision_zones:
                pygame.draw.rect(self.view_surface, (0, 100, 255),
                                 self.camera.apply(zone), width=3)

        # 2. Растягиваем на весь экран (зум).
        scaled = pygame.transform.scale(
            self.view_surface, (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        )
        self.screen.blit(scaled, (0, 0))

        # 3. HUD поверх (в экранных координатах, не масштабируется зумом).
        self.hud.render(self.screen, self.player, self.wave_manager, self.kills)
        if self.game_over:
            self.hud.render_game_over(self.screen, self.kills, self.wave_manager.wave_number)
        elif self.level_up_active:                                   
            self.levelup_rects = self.hud.render_levelup(self.screen, self.player, self.levelup_choices, self.levelup_selected)    
        # flip() намеренно убран — его вызывает main() после наложения оверлея яркости.

    def _open_level_up(self):
        self.level_up_active = True
        self.levelup_choices = self.player.roll_upgrade_choices()
        self.levelup_selected = 0

    def choose_upgrade(self, index):
        if not (0 <= index < len(self.levelup_choices)):
            return
        self.player.apply_upgrade(self.levelup_choices[index])
        if self.player.pending_levelups > 0:
            self.levelup_choices = self.player.roll_upgrade_choices()
            self.levelup_selected = 0
        else:
            self.level_up_active = False
            self.levelup_choices = []    


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
STATE_PAUSED = "paused"
STATE_SETTINGS = "settings"
STATE_RECORDS = "records"


def main():
    pygame.init()
    pygame.display.set_caption(settings.WINDOW_TITLE)
    screen = create_screen()
    clock = pygame.time.Clock()

    menu = Menu(screen)
    settings_menu = None
    records_menu  = None
    game = None
    state = STATE_MENU
    _record_saved = False   # флаг: рекорд уже сохранён для текущей партии

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
                    _record_saved = False
                    state = STATE_PLAYING
                elif choice == "settings":
                    settings_menu = SettingsMenu(screen)
                    state = STATE_SETTINGS
                elif choice == "records":
                    records_menu = RecordsMenu(screen)
                    state = STATE_RECORDS
                elif choice == "quit":
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            elif state == STATE_SETTINGS:
                result = settings_menu.handle_event(event)
                if result == "back":
                    state = STATE_MENU

            elif state == STATE_RECORDS:
                result = records_menu.handle_event(event)
                if result == "back":
                    state = STATE_MENU

            elif state == STATE_PLAYING:
                if game.level_up_active:                          # <-- НОВАЯ ветка (меню уровня)
                    if event.type == pygame.KEYDOWN:
                        n = len(game.levelup_choices)
                        if event.key in (pygame.K_1, pygame.K_KP1) and n >= 1:
                            game.choose_upgrade(0)
                        elif event.key in (pygame.K_2, pygame.K_KP2) and n >= 2:
                            game.choose_upgrade(1)
                        elif event.key in (pygame.K_3, pygame.K_KP3) and n >= 3:
                            game.choose_upgrade(2)
                        elif event.key in (pygame.K_LEFT, pygame.K_a) and n:
                            game.levelup_selected = (game.levelup_selected - 1) % n
                        elif event.key in (pygame.K_RIGHT, pygame.K_d) and n:
                            game.levelup_selected = (game.levelup_selected + 1) % n
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            game.choose_upgrade(game.levelup_selected)
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for i, rect in enumerate(game.levelup_rects):
                            if rect.collidepoint(event.pos):
                                game.choose_upgrade(i)
                                break
                elif event.type == pygame.KEYDOWN:                # <-- ТВОЯ ПРЕЖНЯЯ обработка
                    if event.key == pygame.K_ESCAPE and not game.game_over:
                        state = STATE_PAUSED
                    elif event.key == pygame.K_r and game.game_over:
                        game.reset()
                        _record_saved = False

            elif state == STATE_PAUSED:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_p):
                        state = STATE_PLAYING
                    elif event.key == pygame.K_r:
                        game.reset()
                        _record_saved = False
                        state = STATE_PLAYING
                    elif event.key == pygame.K_q:
                        state = STATE_MENU

        # 2. Update + 3. Render
        if state == STATE_MENU:
            menu.update(dt)
            menu.render()
        elif state == STATE_SETTINGS:
            settings_menu.update(dt)
            settings_menu.render()
        elif state == STATE_RECORDS:
            records_menu.update(dt)
            records_menu.render()
        elif state == STATE_PAUSED:
            game.render()
            game.hud.render_pause(screen)
        else:
            game.update(dt)
            game.render()
            # Сохранить рекорд при первом game over.
            if game.game_over and not _record_saved:
                add_record(settings.SETTINGS_PLAYER_NAME,
                           game.kills, game.wave_manager.wave_number)
                _record_saved = True

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
