"""
Враг-заглушка: движется к игроку, наносит урон при касании, имеет здоровье
и полоску HP над головой. Анимации реализованы так же, как у игрока
(спрайт-листы idle/walk) — сейчас None -> заглушка-квадрат, легко заменить
на ассеты, просто прописав пути в settings.py.
"""

import pygame

from src import settings
from src.entity import AnimatedEntity


class Enemy(AnimatedEntity):
    def __init__(self, start_pos, hp_multiplier=1.0):
        max_hp = int(settings.ENEMY_MAX_HP * hp_multiplier)
        super().__init__(settings.ENEMY_SIZE, start_pos, max_hp)

        idle = self.load_frames(
            settings.ENEMY_IDLE_IMAGE_PATH, settings.ENEMY_IDLE_FRAME_COUNT, self.size
        ) or [self._make_placeholder()]
        walk = self.load_frames(
            settings.ENEMY_WALK_IMAGE_PATH, settings.ENEMY_WALK_FRAME_COUNT, self.size
        ) or idle
        self.animations = {"idle": idle, "walk": walk}
        self.animation_speed = settings.ENEMY_ANIMATION_SPEED

        self.image = idle[0]
        self.rect = self.image.get_rect(center=start_pos)
        self.pos = pygame.Vector2(self.rect.center)

        self.speed = settings.ENEMY_SPEED
        self.damage = settings.ENEMY_DAMAGE
        self.attack_cooldown = 0.0  # таймер до следующего удара по игроку

        # Реальный хитбокс тела (меньше спрайта).
        self.init_hitbox(settings.ENEMY_HITBOX_SCALE)

    def _make_placeholder(self):
        """Заглушка врага: цветной квадрат с рамкой (легко отличить от игрока)."""
        surface = pygame.Surface(self.size, pygame.SRCALPHA)
        surface.fill(settings.FALLBACK_ENEMY_COLOR)
        pygame.draw.rect(surface, (30, 60, 30), surface.get_rect(), width=2)
        return surface

    def update(self, dt, player, tilemap):
        if self.attack_cooldown > 0:
            self.attack_cooldown = max(0.0, self.attack_cooldown - dt)

        # ИИ: движемся прямо к игроку.
        to_player = player.pos - self.pos
        distance = to_player.length()
        moving = False
        if distance > 1:
            step = to_player.normalize() * self.speed * dt
            # Не перелетаем игрока за один кадр.
            if step.length() > distance:
                step = to_player
            self.pos += step
            moving = True
            self.facing_right = to_player.x >= 0

        self.rect.centerx = round(self.pos.x)
        self.rect.centery = round(self.pos.y)
        tilemap.clamp_to_bounds(self.rect)
        self.pos.update(self.rect.center)
        self.sync_hitbox()

        # Урон игроку — только при пересечении реальных хитбоксов (а не
        # прозрачных полей спрайтов), с кулдауном против ударов каждый кадр.
        if self.hitbox.colliderect(player.hitbox):
            if self.attack_cooldown <= 0:
                player.take_damage(self.damage)
                self.attack_cooldown = settings.ENEMY_ATTACK_COOLDOWN

        self.set_state("walk" if moving else "idle")
        self.animate(dt, loop=True)

    def render(self, surface, camera):
        surface.blit(self.image, camera.apply(self.rect))
        self._render_hp_bar(surface, camera)
        if settings.DEBUG_HITBOXES:
            pygame.draw.rect(surface, (255, 60, 60), camera.apply(self.hitbox), width=2)

    def _render_hp_bar(self, surface, camera):
        """Полоска здоровья над врагом (скрыта, если HP полное)."""
        if self.hp >= self.max_hp:
            return
        bar_w = self.rect.width
        bar_h = 5
        screen_rect = camera.apply(self.rect)
        x = screen_rect.x
        y = screen_rect.y - bar_h - 3

        pygame.draw.rect(surface, settings.ENEMY_HP_BAR_BG, (x, y, bar_w, bar_h))
        ratio = max(0.0, self.hp / self.max_hp)
        pygame.draw.rect(surface, settings.ENEMY_HP_BAR_FG, (x, y, int(bar_w * ratio), bar_h))
