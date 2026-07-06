"""
Базовый анимированный персонаж: загрузка спрайт-листов, нарезка на кадры,
проигрывание анимации, отзеркаливание по направлению и здоровье.
От него наследуются Player и Enemy — общая логика не дублируется.
"""

import pygame


class AnimatedEntity(pygame.sprite.Sprite):
    def __init__(self, size, start_pos, max_hp):
        super().__init__()
        self.size = size
        self.max_hp = max_hp
        self.hp = max_hp

        # Заполняется в наследнике: словарь состояний -> список кадров.
        self.animations = {}
        self.state = "idle"
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_speed = 8
        self.facing_right = True

        # Заглушка на случай, если ни один ассет не загрузился.
        self.image = pygame.Surface(size, pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=start_pos)
        self.pos = pygame.Vector2(self.rect.center)

        # Хитбокс — реальная зона столкновений (меньше спрайта, без прозрачных
        # полей). По умолчанию совпадает с rect; наследник вызывает init_hitbox().
        self.hitbox = self.rect.copy()

    @staticmethod
    def load_frames(image_path, frame_count, size):
        """
        Загружает спрайт-лист (кадры в один горизонтальный ряд) и режет на кадры,
        масштабируя каждый под size. Если файла нет / путь пуст — возвращает None.
        """
        if not image_path:
            return None
        try:
            sheet = pygame.image.load(image_path).convert_alpha()
        except (pygame.error, FileNotFoundError):
            return None

        frame_count = max(1, frame_count)
        sheet_width, sheet_height = sheet.get_size()
        frame_width = sheet_width // frame_count
        frame_height = sheet_height

        frames = []
        for i in range(frame_count):
            frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
            frame_surface = sheet.subsurface(frame_rect).copy()
            frame_surface = pygame.transform.scale(frame_surface, size)
            frames.append(frame_surface)
        return frames

    def init_hitbox(self, scale):
        """
        Создаёт хитбокс как долю от размера спрайта. scale = (ширина, высота)
        в долях (например, (0.5, 0.6)). Центрируется по центру спрайта.
        """
        hw = max(1, int(self.size[0] * scale[0]))
        hh = max(1, int(self.size[1] * scale[1]))
        self.hitbox = pygame.Rect(0, 0, hw, hh)
        self.hitbox.center = self.rect.center

    def sync_hitbox(self):
        """Держит хитбокс по центру спрайта (вызывать после смены позиции)."""
        self.hitbox.center = self.rect.center

    def set_state(self, new_state):
        """Переключает состояние анимации, сбрасывая её с начала при смене."""
        if new_state != self.state:
            self.state = new_state
            self.frame_index = 0
            self.animation_timer = 0.0

    def animate(self, dt, loop=True):
        """
        Проигрывает кадры текущего состояния. Возвращает True, если анимация
        доиграла до последнего кадра (актуально для одноразовых, loop=False).
        """
        frames = self.animations.get(self.state)
        if not frames:
            return False

        finished = False
        if len(frames) > 1:
            self.animation_timer += dt
            frame_duration = 1 / self.animation_speed
            if self.animation_timer >= frame_duration:
                self.animation_timer = 0.0
                self.frame_index += 1
                if self.frame_index >= len(frames):
                    if loop:
                        self.frame_index = 0
                    else:
                        self.frame_index = len(frames) - 1
                        finished = True

        frame = frames[self.frame_index % len(frames)]
        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        self.image = frame
        return finished

    def take_damage(self, amount):
        """Наносит урон. Возвращает True, если сущность умерла."""
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            return True
        return False

    @property
    def is_alive(self):
        return self.hp > 0
