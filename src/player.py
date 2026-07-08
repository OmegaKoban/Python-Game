"""
Персонаж игрока: анимации покоя/движения/двух атак (чередуются),
автоатака по таймеру с наведением на ближайшего врага, здоровье и
неуязвимость после получения урона.
"""

import pygame

from src import settings
from src.entity import AnimatedEntity
from src.projectile import Projectile
from src.abilities import AbilityManager


class Player(AnimatedEntity):
    def __init__(self, start_pos):
        super().__init__(settings.PLAYER_SIZE, start_pos, settings.PLAYER_MAX_HP)

        # --- Анимации ---
        idle = self.load_frames(
            settings.PLAYER_IDLE_IMAGE_PATH, settings.PLAYER_IDLE_FRAME_COUNT, self.size
        ) or [self._make_placeholder()]
        walk = self.load_frames(
            settings.PLAYER_WALK_IMAGE_PATH, settings.PLAYER_WALK_FRAME_COUNT, self.size
        ) or idle

        self.animations = {"idle": idle, "walk": walk}

        # Два набора кадров атаки, которые будут чередоваться.
        self.attack_frame_sets = []
        a1 = self.load_frames(
            settings.PLAYER_ATTACK1_IMAGE_PATH, settings.PLAYER_ATTACK1_FRAME_COUNT, self.size
        )
        a2 = self.load_frames(
            settings.PLAYER_ATTACK2_IMAGE_PATH, settings.PLAYER_ATTACK2_FRAME_COUNT, self.size
        )
        if a1:
            self.attack_frame_sets.append(a1)
        if a2:
            self.attack_frame_sets.append(a2)

        self.animation_speed = settings.PLAYER_ANIMATION_SPEED
        self.image = idle[0]
        self.rect = self.image.get_rect(center=start_pos)
        self.pos = pygame.Vector2(self.rect.center)

        self.speed = settings.PLAYER_SPEED

        # --- Состояние атаки ---
        self.is_attacking = False
        self.attack_timer = 0.0
        self.next_attack_index = 0
        self.attack_anim_frames = None
        self.attack_frame_index = 0
        self.attack_anim_timer = 0.0
        # Флаг: удар этой атаки уже нанесён (урон в середине анимации, один раз).
        self.attack_hit_done = False
        # Цель, зафиксированная в момент начала атаки (для наведения снаряда/удара).
        self.attack_target = None
        self.pending_projectiles = []  # снаряды, которые надо добавить в игру

         # --- Опыт и уровень ---
        self.level = 1
        self.xp = 0
        self.xp_to_next = self._xp_threshold(1)
        self.pending_levelups = 0

        # --- Множители от пассивных улучшений ---
        self.damage_mult = 1.0
        self.attack_interval = settings.PLAYER_ATTACK_INTERVAL

        # --- Активные способности ---
        self.abilities = AbilityManager()

        # --- Неуязвимость ---
        self.invuln_timer = 0.0

        # Реальный хитбокс тела (меньше спрайта) — по нему враги наносят урон.
        self.init_hitbox(settings.PLAYER_HITBOX_SCALE)

    def _make_placeholder(self):
        placeholder = pygame.Surface(self.size, pygame.SRCALPHA)
        pygame.draw.circle(
            placeholder,
            settings.FALLBACK_PLAYER_COLOR,
            (self.size[0] // 2, self.size[1] // 2),
            min(self.size) // 2,
        )
        return placeholder

    def handle_input(self):
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            direction.y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            direction.y += 1
        if direction.length_squared() > 0:
            direction = direction.normalize()
        return direction

    # ---------- Боевая система ----------
    def _find_nearest_enemy(self, enemies):
        """Ближайший живой враг в радиусе атаки, иначе None."""
        nearest = None
        nearest_dist_sq = settings.PLAYER_ATTACK_RANGE ** 2
        for enemy in enemies:
            if not enemy.is_alive:
                continue
            dx = enemy.pos.x - self.pos.x
            dy = enemy.pos.y - self.pos.y
            dist_sq = dx * dx + dy * dy
            if dist_sq <= nearest_dist_sq:
                nearest_dist_sq = dist_sq
                nearest = enemy
        return nearest

    def _start_attack(self, target):
        """Запускает атаку, беря следующий по очереди набор кадров (чередование)."""
        if not self.attack_frame_sets:
            # Ассетов атаки нет — атакуем «мгновенно», без анимации.
            self._deal_attack(target)
            return

        self.attack_anim_frames = self.attack_frame_sets[self.next_attack_index]
        self.next_attack_index = (self.next_attack_index + 1) % len(self.attack_frame_sets)

        self.is_attacking = True
        self.attack_frame_index = 0
        self.attack_anim_timer = 0.0
        self.attack_hit_done = False
        self.attack_target = target

        # Повернуться к цели.
        if target is not None:
            self.facing_right = target.pos.x >= self.pos.x

    def _deal_attack(self, target):
        """Наносит урон: либо снаряд (ranged), либо удар по области (melee)."""
        if target is None:
            return
        if settings.PLAYER_COMBAT_MODE == "ranged":
            proj = Projectile(
                start_pos=(self.pos.x, self.pos.y),
                target_pos=(target.pos.x, target.pos.y),
                damage = int(round(settings.PLAYER_ATTACK_DAMAGE * self.damage_mult)),
            )
            self.pending_projectiles.append(proj)
        else:
            # melee: прямой урон цели (она в радиусе, раз мы её выбрали).
            target.take_damage(settings.PLAYER_ATTACK_DAMAGE)

    def _update_attack_animation(self, dt):
        """Проигрывает анимацию атаки; урон наносится в середине анимации."""
        frames = self.attack_anim_frames
        frame_duration = 1 / settings.PLAYER_ATTACK_ANIMATION_SPEED

        self.attack_anim_timer += dt
        if self.attack_anim_timer >= frame_duration:
            self.attack_anim_timer = 0.0
            self.attack_frame_index += 1

        # Наносим урон один раз примерно на середине анимации.
        hit_frame = len(frames) // 2
        if not self.attack_hit_done and self.attack_frame_index >= hit_frame:
            self._deal_attack(self.attack_target)
            self.attack_hit_done = True

        if self.attack_frame_index >= len(frames):
            self.is_attacking = False
            self.attack_anim_frames = None
            return

        frame = frames[self.attack_frame_index]
        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        self.image = frame

    def take_damage(self, amount):
        """Урон с учётом неуязвимости. Возвращает True при смерти."""
        if self.invuln_timer > 0:
            return False
        self.invuln_timer = settings.PLAYER_INVULN_TIME
        return super().take_damage(amount)

    # ---------- Основной апдейт ----------
    def update(self, dt, tilemap, enemies):
        if self.invuln_timer > 0:
            self.invuln_timer = max(0.0, self.invuln_timer - dt)

        # Движение (работает всегда, в т.ч. во время атаки).
        direction = self.handle_input()
        self.pos += direction * self.speed * dt
        moving = direction.length_squared() > 0

        if not self.is_attacking:
            if direction.x > 0:
                self.facing_right = True
            elif direction.x < 0:
                self.facing_right = False

        self.rect.centerx = round(self.pos.x)
        self.rect.centery = round(self.pos.y)
        tilemap.clamp_to_bounds(self.rect)
        self.pos.update(self.rect.center)
        self.sync_hitbox()

        # Автоатака по таймеру: копим интервал, при наличии цели — бьём.
        self.attack_timer += dt
        if not self.is_attacking and self.attack_timer >= self.attack_interval:
            target = self._find_nearest_enemy(enemies)
            if target is not None:
                self.attack_timer = 0.0
                self._start_attack(target)

        # Анимация: атака имеет приоритет над idle/walk.
        if self.is_attacking and self.attack_anim_frames:
            self._update_attack_animation(dt)
        else:
            self.set_state("walk" if moving else "idle")
            self.animate(dt, loop=True)

        self.abilities.update(dt, self, enemies, tilemap)    

    def collect_projectiles(self):
        """Отдаёт накопленные снаряды и очищает буфер (вызывается из main)."""
        projs = self.pending_projectiles
        self.pending_projectiles = []
        return projs

    # ---------- Опыт и уровни ----------
    def _xp_threshold(self, level):
        base = settings.XP_BASE * (settings.XP_GROWTH ** (level - 1))
        return int(round(base + settings.XP_FLAT_ADD * (level - 1)))

    def add_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.pending_levelups += 1
            self.xp_to_next = self._xp_threshold(self.level)

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def roll_upgrade_choices(self):
        import random
        pool = []
        for uid, title, desc in settings.UPGRADES_PASSIVE:
            pool.append({"type": "passive", "id": uid, "title": title, "desc": desc})
        for aid in self.abilities.available_ability_upgrades():
            cfg = settings.ABILITIES[aid]
            lvl = self.abilities.level_of(aid)
            title = f"{cfg['name']} (новая)" if lvl == 0 else f"{cfg['name']} ур. {lvl + 1}"
            pool.append({"type": "ability", "id": aid, "title": title, "desc": cfg["desc"]})
        random.shuffle(pool)
        return pool[:settings.LEVELUP_CHOICES]

    def apply_upgrade(self, choice):
        ctype = choice.get("type")
        cid = choice.get("id")
        if ctype == "passive":
            if cid == "dmg":
                self.damage_mult += settings.UPGRADE_ATTACK_DAMAGE_MULT
            elif cid == "aspd":
                self.attack_interval = max(
                    settings.PLAYER_ATTACK_INTERVAL_MIN,
                    self.attack_interval * (1.0 - settings.UPGRADE_ATTACK_SPEED_MULT),
                )
            elif cid == "hp":
                self.max_hp += settings.UPGRADE_MAX_HP_ADD
                self.hp += settings.UPGRADE_MAX_HP_ADD
        elif ctype == "ability":
            self.abilities.add_or_upgrade(cid)
        if self.pending_levelups > 0:
            self.pending_levelups -= 1