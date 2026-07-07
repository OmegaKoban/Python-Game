"""
Враг с типами (тирами) и полным набором анимаций.

Типы описаны в settings.ENEMY_TYPES (slime1..3, orc1..3). Каждый тип задаёт
пути к спрайт-листам (run/attack/hurt/death), число кадров и характеристики.

Состояния (машина состояний по анимациям):
    run    — базовое: враг догоняет игрока (используется и как idle);
    attack — при контакте с игроком: проигрывается анимация, урон наносится
             в середине анимации (один раз за цикл), затем возврат в run;
    hurt   — короткая реакция при получении урона (не прерывает смерть);
    death  — проигрывается один раз при hp<=0, после чего враг помечается
             на удаление (флаг should_remove).

Если спрайтов типа нет (например, slime2/3, orc2/3 ещё не добавлены) —
рисуется цветная заглушка-квадрат, игра не падает.
"""

import pygame

from src import settings
from src.entity import AnimatedEntity


class Enemy(AnimatedEntity):
    def __init__(self, start_pos, enemy_type="slime1", wave_number=1):
        cfg = settings.ENEMY_TYPES.get(enemy_type, settings.ENEMY_TYPES["slime1"])
        self.enemy_type = enemy_type
        self.cfg = cfg

        # Размер спрайта в пикселях (независимо от TILE_SIZE).
        px = max(8, int(settings.ENEMY_BASE_SIZE * cfg.get("scale", 1.0)))
        size = (px, px)

        # Характеристики с ростом от номера волны (несильно).
        hp_growth = 1.0 + (wave_number - 1) * settings.ENEMY_STAT_HP_GROWTH
        dmg_growth = 1.0 + (wave_number - 1) * settings.ENEMY_STAT_DAMAGE_GROWTH
        max_hp = max(1, int(round(cfg["hp"] * hp_growth)))

        super().__init__(size, start_pos, max_hp)

        # Анимации по состояниям.
        self.animations = self._load_animations(cfg, size)

        self.image = self.animations["run"][0]
        self.rect = self.image.get_rect(center=start_pos)
        self.pos = pygame.Vector2(self.rect.center)

        self.speed = cfg.get("speed", 90)
        self.damage = max(1, int(round(cfg.get("damage", 10) * dmg_growth)))
        self.attack_cooldown = 0.0

        # Флаги состояний.
        self.state = "run"
        self.dying = False          # проигрывается анимация смерти
        self.death_timer = 0.0
        self.should_remove = False  # main.py удалит врага, когда True
        self.attack_hit_done = False  # урон в текущей анимации атаки уже нанесён

        # Хитбокс тела.
        self.init_hitbox(cfg.get("hitbox_scale", settings.ENEMY_HITBOX_SCALE))

    def _load_animations(self, cfg, size):
        """Грузит спрайт-листы всех состояний. Пропущенные заменяет run/заглушкой."""
        import os
        anims = {}
        base_dir = os.path.join(settings.ENEMY_DIR, cfg["dir"])
        for anim, frame_count in cfg["frames"].items():
            path = os.path.join(base_dir, f"{anim}.png")
            frames = self.load_frames(path, frame_count, size)
            if frames:
                anims[anim] = frames

        # Обязательно должен быть run — иначе заглушка.
        if "run" not in anims:
            anims["run"] = [self._make_placeholder()]
        # Недостающие состояния подменяем на run (чтобы код не падал).
        for anim in ("attack", "hurt", "death"):
            if anim not in anims:
                anims[anim] = anims["run"]
        return anims

    def _make_placeholder(self):
        """Заглушка врага: цветной квадрат с рамкой (если спрайтов типа нет)."""
        surface = pygame.Surface(self.size, pygame.SRCALPHA)
        surface.fill(settings.FALLBACK_ENEMY_COLOR)
        pygame.draw.rect(surface, (30, 60, 30), surface.get_rect(), width=2)
        return surface

    # ---------- Урон ----------
    def take_damage(self, amount):
        """Наносит урон. Запускает hurt или death. Возвращает True при смерти."""
        if self.dying:
            return False
        died = super().take_damage(amount)  # уменьшает hp, вернёт True если hp<=0
        if died:
            self._start_death()
        else:
            self._start_hurt()
        return died

    def _start_hurt(self):
        if self.state != "hurt":
            self.set_state("hurt")

    def _start_death(self):
        self.dying = True
        self.death_timer = 0.0
        self.set_state("death")

    # ---------- Обновление ----------
    def update(self, dt, player, tilemap):
        # Анимация смерти: доигрываем и помечаем на удаление.
        if self.dying:
            finished = self.animate(dt, loop=False)
            self.death_timer += dt
            if finished or self.death_timer >= settings.ENEMY_DEATH_MAX_TIME:
                self.should_remove = True
            return

        if self.attack_cooldown > 0:
            self.attack_cooldown = max(0.0, self.attack_cooldown - dt)

        # Движение к игроку.
        to_player = player.pos - self.pos
        distance = to_player.length()
        moving = False
        if distance > 1:
            step = to_player.normalize() * self.speed * dt
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

        touching = self.hitbox.colliderect(player.hitbox)

        # --- Состояние атаки ---
        if self.state == "attack":
            finished = self.animate(dt, loop=False)
            # Урон — один раз, в середине анимации.
            frames = self.animations["attack"]
            hit_frame = max(0, len(frames) // 2)
            if not self.attack_hit_done and self.frame_index >= hit_frame:
                if touching and self.attack_cooldown <= 0:
                    player.take_damage(self.damage)
                    self.attack_cooldown = settings.ENEMY_ATTACK_COOLDOWN
                self.attack_hit_done = True
            if finished:
                self.set_state("run")  # атака доиграла — обратно к бегу
            return

        # --- Состояние hurt ---
        if self.state == "hurt":
            finished = self.animate(dt, loop=False)
            if finished:
                self.set_state("run")
            return

        # --- Обычное состояние: бег/idle ---
        if touching and self.attack_cooldown <= 0:
            # Начинаем анимацию атаки.
            self.set_state("attack")
            self.attack_hit_done = False
            self.animate(dt, loop=False)
            return

        self.set_state("run")
        self.animate(dt, loop=True)

    # ---------- Скорость анимации зависит от состояния ----------
    def animate(self, dt, loop=True):
        self.animation_speed = settings.ENEMY_ANIM_SPEED.get(self.state, 12)
        return super().animate(dt, loop=loop)

    # ---------- Отрисовка ----------
    def render(self, surface, camera):
        surface.blit(self.image, camera.apply(self.rect))
        if not self.dying:
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
