"""
Система активных способностей (в духе Vampire Survivors).

AbilityManager хранит, какие способности активны и на каком они уровне,
тикает их кулдауны и порождает визуальные эффекты, наносящие урон врагам.

Способности описаны в settings.ABILITIES. Каждая имеет уровень; повторный
выбор в меню повышения уровня увеличивает уровень (up to max_level), отчего
растут урон/радиус и падает кулдаун.

Виды (kind):
    projectile   — огненная пуля: летит из игрока в ближайшего врага (одиночный урон)
    fireball_aoe — фаербол: летит из игрока и взрывается по области в точке цели
    aura         — постоянный урон по кругу вокруг игрока (тикает по кулдауну)
    lightning    — сама бьёт по ближайшему врагу в радиусе (без снаряда)
    meteor       — падает в случайное место карты, взрыв по области

Пока нет спрайтов эффектов — рисуются простые фигуры-заглушки
(круги/лучи/вспышки цветом из настроек). Пути к спрайтам можно указать
в settings.ABILITIES[...]["image_path"] — тогда подхватятся автоматически.
"""

import math
import random

import pygame

from src import settings


# ---------------------------------------------------------------------------
#  Визуальные эффекты (живут ограниченное время, часть из них наносит урон)
# ---------------------------------------------------------------------------

class Effect:
    """Базовый эффект: живёт time_left секунд, рисуется в мировых координатах."""
    def __init__(self, duration):
        self.time_left = duration
        self.alive = True

    def update(self, dt, enemies, player, tilemap):
        self.time_left -= dt
        if self.time_left <= 0:
            self.alive = False

    def render(self, surface, camera):
        pass

    @staticmethod
    def _apply_aoe(center, radius, damage, enemies):
        """Наносит урон всем живым врагам в круге. Возвращает число задетых."""
        hit = 0
        r_sq = radius * radius
        for enemy in enemies:
            if not enemy.is_alive:
                continue
            dx = enemy.pos.x - center[0]
            dy = enemy.pos.y - center[1]
            if dx * dx + dy * dy <= r_sq:
                enemy.take_damage(damage)
                hit += 1
        return hit


class FlyingProjectile(Effect):
    """
    Летящий снаряд способности: одиночный урон (aoe_radius=0) или взрыв по
    области при попадании/долёте (aoe_radius>0 -> фаербол).
    """
    def __init__(self, start, target, damage, speed, color, aoe_radius=0):
        super().__init__(duration=2.5)
        self.pos = pygame.Vector2(start)
        self.damage = damage
        self.color = color
        self.aoe_radius = aoe_radius
        self.exploded = False
        self.explosion_timer = 0.0

        direction = pygame.Vector2(target) - self.pos
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        self.velocity = direction.normalize() * speed
        self.hit_radius = 16

    def update(self, dt, enemies, player, tilemap):
        if self.exploded:
            # Показываем вспышку взрыва ещё немного.
            self.explosion_timer -= dt
            if self.explosion_timer <= 0:
                self.alive = False
            return

        self.pos += self.velocity * dt
        # За границей карты — гаснем.
        if (self.pos.x < 0 or self.pos.x > tilemap.pixel_width or
                self.pos.y < 0 or self.pos.y > tilemap.pixel_height):
            self.alive = False
            return

        # Проверка попадания в хитбокс врага.
        hitbox = pygame.Rect(0, 0, self.hit_radius * 2, self.hit_radius * 2)
        hitbox.center = (round(self.pos.x), round(self.pos.y))
        for enemy in enemies:
            if not enemy.is_alive:
                continue
            if hitbox.colliderect(enemy.hitbox):
                self._on_hit(enemy, enemies)
                return

    def _on_hit(self, enemy, enemies):
        if self.aoe_radius > 0:
            # Фаербол — взрыв по области.
            self._apply_aoe((self.pos.x, self.pos.y), self.aoe_radius,
                            self.damage, enemies)
            self.exploded = True
            self.explosion_timer = 0.25
        else:
            # Одиночный урон.
            enemy.take_damage(self.damage)
            self.alive = False

    def render(self, surface, camera):
        px, py = camera.apply_point((self.pos.x, self.pos.y))
        screen_pos = (round(px), round(py))
        if self.exploded:
            pygame.draw.circle(surface, self.color, screen_pos, max(6, self.aoe_radius // 2))
            pygame.draw.circle(surface, (255, 230, 160), screen_pos,
                               max(4, self.aoe_radius // 3), width=3)
        else:
            pygame.draw.circle(surface, self.color, screen_pos, 8)
            pygame.draw.circle(surface, (255, 230, 160), screen_pos, 8, width=2)


class AuraTick(Effect):
    """Кольцо-вспышка ауры (визуал). Урон наносит менеджер в момент тика."""
    def __init__(self, radius, color):
        super().__init__(duration=0.18)
        self.radius = radius
        self.color = color
        self.owner_pos = None       # обновляется каждый кадр из менеджера

    def render(self, surface, camera):
        if self.owner_pos is None:
            return
        px, py = camera.apply_point(self.owner_pos)
        screen_pos = (round(px), round(py))
        alpha = max(0, int(120 * (self.time_left / 0.18)))
        ring = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(ring, (*self.color, alpha), (self.radius, self.radius),
                           self.radius)
        pygame.draw.circle(ring, (*self.color, min(255, alpha + 80)),
                           (self.radius, self.radius), self.radius, width=3)
        surface.blit(ring, (screen_pos[0] - self.radius, screen_pos[1] - self.radius))


class LightningStrike(Effect):
    """Луч молнии от неба к цели (визуал). Урон наносится сразу при создании."""
    def __init__(self, target_pos, color):
        super().__init__(duration=0.22)
        self.target = pygame.Vector2(target_pos)
        self.color = color

    def render(self, surface, camera):
        tx, ty = camera.apply_point((self.target.x, self.target.y))
        tx, ty = round(tx), round(ty)
        # Зигзаг сверху вниз к цели.
        top_y = ty - 220
        points = [(tx, top_y)]
        segments = 6
        for i in range(1, segments):
            y = top_y + (ty - top_y) * i / segments
            x = tx + random.randint(-14, 14)
            points.append((x, y))
        points.append((tx, ty))
        pygame.draw.lines(surface, self.color, False, points, 3)
        pygame.draw.circle(surface, (255, 255, 255), (tx, ty), 10, width=2)


class Meteor(Effect):
    """
    Метеорит: падает в заранее выбранную точку карты за fall_time секунд,
    затем взрыв по области (урон в момент удара).
    """
    def __init__(self, target_pos, damage, radius, fall_time, color):
        super().__init__(duration=fall_time + 0.3)
        self.target = pygame.Vector2(target_pos)
        self.damage = damage
        self.radius = radius
        self.fall_time = fall_time
        self.color = color
        self.timer = 0.0
        self.landed = False

    def update(self, dt, enemies, player, tilemap):
        self.timer += dt
        if not self.landed and self.timer >= self.fall_time:
            self.landed = True
            self._apply_aoe((self.target.x, self.target.y), self.radius,
                            self.damage, enemies)
        super().update(dt, enemies, player, tilemap)

    def render(self, surface, camera):
        tx, ty = camera.apply_point((self.target.x, self.target.y))
        tx, ty = round(tx), round(ty)
        if not self.landed:
            # Тень-маркер места падения + летящий сверху камень.
            progress = min(1.0, self.timer / self.fall_time)
            pygame.draw.circle(surface, (0, 0, 0), (tx, ty), self.radius, width=2)
            rock_y = ty - int(260 * (1 - progress))
            pygame.draw.circle(surface, self.color, (tx, rock_y), 14)
            pygame.draw.circle(surface, (255, 220, 150), (tx, rock_y), 14, width=2)
        else:
            # Вспышка взрыва.
            pygame.draw.circle(surface, self.color, (tx, ty), self.radius)
            pygame.draw.circle(surface, (255, 230, 160), (tx, ty), self.radius, width=4)


# ---------------------------------------------------------------------------
#  Менеджер способностей
# ---------------------------------------------------------------------------

class AbilityManager:
    def __init__(self):
        # id способности -> текущий уровень (1..max_level)
        self.levels = {}
        self.timers = {}            # id -> накопленное время до следующего срабатывания
        self.effects = []           # активные визуальные эффекты
        # Примечание: стартовая "огненная пуля" реализована как основная
        # автоатака игрока (см. player.py), поэтому здесь менеджер стартует
        # пустым — дополнительные способности добавляются через прокачку.

    # ---------- Управление уровнями ----------
    def has(self, ability_id):
        return ability_id in self.levels

    def level_of(self, ability_id):
        return self.levels.get(ability_id, 0)

    def is_maxed(self, ability_id):
        cfg = settings.ABILITIES[ability_id]
        return self.level_of(ability_id) >= cfg["max_level"]

    def add_or_upgrade(self, ability_id):
        """Даёт способность или повышает её уровень (Vampire Survivors стиль)."""
        if ability_id not in settings.ABILITIES:
            return
        if ability_id in self.levels:
            cfg = settings.ABILITIES[ability_id]
            self.levels[ability_id] = min(cfg["max_level"], self.levels[ability_id] + 1)
        else:
            self.levels[ability_id] = 1
            self.timers[ability_id] = 0.0

    # ---------- Расчёт характеристик по уровню ----------
    def _stat(self, ability_id):
        """Возвращает (cooldown, damage, radius) с учётом текущего уровня."""
        cfg = settings.ABILITIES[ability_id]
        lvl = self.levels[ability_id]
        steps = lvl - 1
        cooldown = cfg["cooldown"] * (cfg["cooldown_mult"] ** steps)
        damage = cfg["damage"] + cfg["damage_add"] * steps
        radius = cfg.get("radius", 0) + cfg.get("radius_add", 0) * steps
        return cooldown, damage, radius

    # ---------- Основной апдейт ----------
    def update(self, dt, player, enemies, tilemap):
        # 1. Тикаем кулдауны активных способностей и запускаем их.
        for ability_id in list(self.levels.keys()):
            self.timers[ability_id] = self.timers.get(ability_id, 0.0) + dt
            cooldown, damage, radius = self._stat(ability_id)
            if self.timers[ability_id] >= cooldown:
                triggered = self._trigger(ability_id, damage, radius, player,
                                          enemies, tilemap)
                # Сбрасываем таймер только если способность реально сработала
                # (например, молнии/пуле нужна цель).
                if triggered:
                    self.timers[ability_id] = 0.0

        # 2. Обновляем визуальные эффекты (они наносят урон летящим/взрывом).
        for eff in self.effects:
            # Ауре нужно знать текущую позицию игрока.
            if isinstance(eff, AuraTick):
                eff.owner_pos = (player.pos.x, player.pos.y)
            eff.update(dt, enemies, player, tilemap)
        self.effects = [e for e in self.effects if e.alive]

    def _nearest_enemy(self, origin, enemies, max_range=None):
        nearest, best = None, (max_range ** 2 if max_range else float("inf"))
        for enemy in enemies:
            if not enemy.is_alive:
                continue
            dx = enemy.pos.x - origin[0]
            dy = enemy.pos.y - origin[1]
            d = dx * dx + dy * dy
            if d <= best:
                best = d
                nearest = enemy
        return nearest

    def _trigger(self, ability_id, damage, radius, player, enemies, tilemap):
        """Активирует конкретную способность. Возвращает True, если сработала."""
        cfg = settings.ABILITIES[ability_id]
        kind = cfg["kind"]
        origin = (player.pos.x, player.pos.y)

        if kind == "projectile":
            target = self._nearest_enemy(origin, enemies)
            if target is None:
                return False
            self.effects.append(FlyingProjectile(
                origin, (target.pos.x, target.pos.y), damage,
                cfg.get("speed", 500), cfg["color"], aoe_radius=0))
            return True

        if kind == "fireball_aoe":
            target = self._nearest_enemy(origin, enemies)
            if target is None:
                return False
            self.effects.append(FlyingProjectile(
                origin, (target.pos.x, target.pos.y), damage,
                cfg.get("speed", 380), cfg["color"], aoe_radius=int(radius)))
            return True

        if kind == "aura":
            # Урон по кругу вокруг игрока + визуальное кольцо.
            Effect._apply_aoe(origin, radius, damage, enemies)
            self.effects.append(AuraTick(int(radius), cfg["color"]))
            return True

        if kind == "lightning":
            target = self._nearest_enemy(origin, enemies, max_range=radius)
            if target is None:
                return False
            target.take_damage(damage)
            self.effects.append(LightningStrike((target.pos.x, target.pos.y),
                                                cfg["color"]))
            return True

        if kind == "meteor":
            # Случайная точка на карте.
            tx = random.uniform(0, tilemap.pixel_width)
            ty = random.uniform(0, tilemap.pixel_height)
            self.effects.append(Meteor((tx, ty), damage, int(radius),
                                       cfg.get("fall_time", 0.8), cfg["color"]))
            return True

        return False

    def render(self, surface, camera):
        for eff in self.effects:
            eff.render(surface, camera)

    # ---------- Для меню выбора апгрейдов ----------
    def available_ability_upgrades(self):
        """
        Список id способностей, которые можно предложить в меню:
        ещё не открытые ИЛИ открытые, но не достигшие max_level.
        Стартовая fireball сюда не входит (это основная автоатака,
        качается пассивками силы/скорости).
        """
        result = []
        for ability_id in settings.ABILITY_ORDER:
            if ability_id == settings.ABILITY_START:
                continue  # стартовая пуля = основная автоатака, не предлагаем
            if not self.is_maxed(ability_id):
                result.append(ability_id)
        return result
