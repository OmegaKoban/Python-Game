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

        pygame.display.flip()


def create_screen():
    if settings.SCREEN_MODE == "fullscreen":
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT = screen.get_size()
    elif settings.SCREEN_MODE == "borderless":
        screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)
        settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT = screen.get_size()
    else:
        screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    return screen


def main():
    pygame.init()
    pygame.display.set_caption(settings.WINDOW_TITLE)
    screen = create_screen()
    clock = pygame.time.Clock()

    game = Game(screen)

    running = True
    while running:
        dt = clock.tick(settings.FPS) / 1000  # мс -> секунды

        # 1. Process Input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r and game.game_over:
                    game.reset()

        # 2. Update
        game.update(dt)

        # 3. Render
        game.render()

    pygame.quit()


if __name__ == "__main__":
    main()
