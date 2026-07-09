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
        self.start_pos = pygame.Vector2(start)
        self.pos = pygame.Vector2(start)
        self.damage = damage
        self.color = color
        self.aoe_radius = aoe_radius
        self.exploded = False
        self.explosion_timer = 0.0
        self.trail_particles = []  # частицы следа
        self.max_distance = 0  # максимальная дистанция для фаербола
        self.distance_traveled = 0

        direction = pygame.Vector2(target) - self.pos
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        else:
            # Для фаербола устанавливаем максимальную дистанцию
            if aoe_radius > 0:
                self.max_distance = direction.length() + 150
        
        self.velocity = direction.normalize() * speed
        self.hit_radius = 16
        self.rotation = 0  # угол вращения для анимации

    def update(self, dt, enemies, player, tilemap):
        if self.exploded:
            # Показываем вспышку взрыва ещё немного.
            self.explosion_timer -= dt
            if self.explosion_timer <= 0:
                self.alive = False
            return

        old_pos = pygame.Vector2(self.pos)
        self.pos += self.velocity * dt
        self.distance_traveled += (self.pos - old_pos).length()
        self.rotation += dt * 360  # вращение снаряда
        
        # Проверка на максимальную дистанцию для фаербола
        if self.aoe_radius > 0 and self.max_distance > 0:
            if self.distance_traveled >= self.max_distance:
                # Взрываемся в текущей позиции
                self._apply_aoe((self.pos.x, self.pos.y), self.aoe_radius,
                               self.damage, enemies)
                self.exploded = True
                self.explosion_timer = 0.35
                return
        
        # Добавляем частицу следа
        if random.random() < 0.3:
            self.trail_particles.append({
                'pos': pygame.Vector2(self.pos),
                'life': 0.3,
                'size': random.randint(3, 6)
            })
        
        # Обновляем частицы следа
        for particle in self.trail_particles:
            particle['life'] -= dt
        self.trail_particles = [p for p in self.trail_particles if p['life'] > 0]
        
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
            self.explosion_timer = 0.35
        else:
            # Одиночный урон.
            enemy.take_damage(self.damage)
            self.alive = False

    def render(self, surface, camera):
        px, py = camera.apply_point((self.pos.x, self.pos.y))
        screen_pos = (round(px), round(py))
        
        # Рисуем след из частиц
        for particle in self.trail_particles:
            ppx, ppy = camera.apply_point((particle['pos'].x, particle['pos'].y))
            alpha = int(255 * particle['life'] / 0.3)
            color = (*self.color, alpha)
            trail_surf = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, color, (particle['size'], particle['size']), particle['size'])
            surface.blit(trail_surf, (ppx - particle['size'], ppy - particle['size']))
        
        if self.exploded:
            # Анимация взрыва: расширяющиеся круги с частицами
            progress = 1 - (self.explosion_timer / 0.35)
            max_radius = self.aoe_radius if self.aoe_radius > 0 else 30
            
            # Создаём частицы взрыва при начале
            if not hasattr(self, 'explosion_particles'):
                self.explosion_particles = []
                for _ in range(30):
                    angle = random.uniform(0, 6.28)
                    speed = random.uniform(100, 300)
                    self.explosion_particles.append({
                        'angle': angle,
                        'speed': speed,
                        'size': random.randint(3, 8),
                        'life': random.uniform(0.2, 0.35)
                    })
            
            # Обновляем и рисуем частицы взрыва
            for particle in self.explosion_particles[:]:
                dist = particle['speed'] * progress
                part_x = px + dist * math.cos(particle['angle'])
                part_y = py + dist * math.sin(particle['angle'])
                
                particle_alpha = int(255 * (1 - progress))
                size = int(particle['size'] * (1.5 - progress * 0.5))
                
                # Цвет меняется от белого через желтый к красному
                if progress < 0.3:
                    color = (255, 255, 200, particle_alpha)
                elif progress < 0.6:
                    color = (255, 200, 50, particle_alpha)
                else:
                    color = (255, 100, 30, particle_alpha)
                
                part_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(part_surf, color, (size, size), size)
                surface.blit(part_surf, (part_x - size, part_y - size))
            
            # Основные расширяющиеся волны взрыва
            for i in range(4):
                wave_progress = min(1.0, progress - i * 0.1)
                if wave_progress < 0:
                    continue
                    
                outer_radius = int(max_radius * (0.3 + wave_progress * 0.7))
                wave_alpha = max(0, int(200 * (1 - wave_progress)))
                
                wave_surf = pygame.Surface((outer_radius * 2, outer_radius * 2), pygame.SRCALPHA)
                
                if i == 0:
                    # Яркое ядро
                    pygame.draw.circle(wave_surf, (255, 255, 200, wave_alpha), 
                                     (outer_radius, outer_radius), outer_radius)
                    pygame.draw.circle(wave_surf, (255, 200, 100, min(255, wave_alpha + 50)), 
                                     (outer_radius, outer_radius), int(outer_radius * 0.7))
                else:
                    # Огненные кольца
                    colors = [(255, 200, 100), (255, 150, 50), (255, 80, 30)]
                    width = max(3, outer_radius // 15)
                    pygame.draw.circle(wave_surf, (*colors[i-1], wave_alpha), 
                                     (outer_radius, outer_radius), outer_radius, width=width)
                
                surface.blit(wave_surf, (screen_pos[0] - outer_radius, screen_pos[1] - outer_radius))
        else:
            # Летящий снаряд с вращением и свечением
            # Внешнее свечение
            glow_radius = 14
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color, 100), (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surf, (screen_pos[0] - glow_radius, screen_pos[1] - glow_radius))
            
            # Основной шар
            pygame.draw.circle(surface, self.color, screen_pos, 10)
            pygame.draw.circle(surface, (255, 255, 200), screen_pos, 6)
            
            # Яркая граница
            pygame.draw.circle(surface, (255, 230, 160), screen_pos, 10, width=2)


class AuraTick(Effect):
    """Кольцо-вспышка ауры (визуал). Урон наносит менеджер в момент тика."""
    def __init__(self, radius, color):
        super().__init__(duration=0.35)
        self.radius = radius
        self.color = color
        self.owner_pos = None       # обновляется каждый кадр из менеджера
        self.particles = []
        # Создаём начальные частицы
        for _ in range(20):
            angle = random.uniform(0, 6.28)
            speed = random.uniform(50, 150)
            self.particles.append({
                'angle': angle,
                'speed': speed,
                'life': random.uniform(0.2, 0.35),
                'size': random.randint(4, 8)
            })

    def update(self, dt, enemies, player, tilemap):
        super().update(dt, enemies, player, tilemap)
        for particle in self.particles:
            particle['life'] -= dt
        self.particles = [p for p in self.particles if p['life'] > 0]

    def render(self, surface, camera):
        if self.owner_pos is None:
            return
        px, py = camera.apply_point(self.owner_pos)
        screen_pos = (round(px), round(py))
        progress = 1 - (self.time_left / 0.35)
        
        # Рисуем расширяющиеся кольца пламени
        for i in range(3):
            ring_progress = min(1.0, progress + i * 0.15)
            ring_radius = int(self.radius * (0.6 + ring_progress * 0.4))
            alpha = max(0, int(180 * (1 - ring_progress)))
            
            ring_surf = pygame.Surface((ring_radius * 2, ring_radius * 2), pygame.SRCALPHA)
            
            # Внутренний градиент
            colors = [
                (255, 255, 100, alpha),  # яркое желтое ядро
                (255, 150, 50, alpha),   # оранжевый
                (255, 80, 30, alpha)     # красный
            ]
            
            for j, color in enumerate(colors):
                r = ring_radius - j * (ring_radius // 4)
                if r > 0:
                    pygame.draw.circle(ring_surf, color, 
                                     (ring_radius, ring_radius), r, width=max(1, ring_radius // 8))
            
            surface.blit(ring_surf, (screen_pos[0] - ring_radius, screen_pos[1] - ring_radius))
        
        # Рисуем летящие частицы огня
        for particle in self.particles:
            if particle['life'] <= 0:
                continue
            dist = particle['speed'] * (0.35 - particle['life'])
            part_x = px + dist * math.cos(particle['angle'])
            part_y = py + dist * math.sin(particle['angle'])
            
            alpha = int(255 * (particle['life'] / 0.35))
            size = particle['size']
            
            # Градиент от желтого к красному
            if particle['life'] > 0.2:
                color = (255, 200, 50, alpha)
            else:
                color = (255, 100, 30, alpha)
            
            part_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(part_surf, color, (size, size), size)
            # Добавляем яркое ядро
            pygame.draw.circle(part_surf, (255, 255, 200, min(255, alpha + 50)), 
                             (size, size), max(1, size // 2))
            surface.blit(part_surf, (part_x - size, part_y - size))


class LightningStrike(Effect):
    """Луч молнии от неба к цели (визуал). Урон наносится сразу при создании."""
    def __init__(self, target_pos, color):
        super().__init__(duration=0.5)
        self.target = pygame.Vector2(target_pos)
        self.color = color
        self.branches = []  # ветвления молнии
        self.flash_particles = []  # частицы вспышки
        self.electric_arcs = []  # дополнительные электрические дуги
        self.generate_lightning()
        
        # Создаём частицы вспышки
        for _ in range(25):
            angle = random.uniform(0, 6.28)
            speed = random.uniform(100, 250)
            self.flash_particles.append({
                'angle': angle,
                'speed': speed,
                'size': random.randint(2, 8),
                'life': random.uniform(0.25, 0.5)
            })
        
        # Создаём электрические дуги вокруг удара
        for _ in range(5):
            angle = random.uniform(0, 6.28)
            length = random.uniform(40, 80)
            self.electric_arcs.append({
                'angle': angle,
                'length': length,
                'segments': self._generate_arc(angle, length)
            })
    
    def _generate_arc(self, base_angle, length):
        """Генерирует изогнутую электрическую дугу"""
        segments = []
        num_points = 6
        for i in range(num_points):
            progress = i / (num_points - 1)
            dist = length * progress
            # Добавляем волнистость
            perpendicular = base_angle + 1.57  # перпендикуляр
            wave = math.sin(progress * 3.14 * 2) * 15
            x = self.target.x + dist * math.cos(base_angle) + wave * math.cos(perpendicular)
            y = self.target.y + dist * math.sin(base_angle) + wave * math.sin(perpendicular)
            segments.append((x, y))
        return segments
    
    def generate_lightning(self):
        """Генерирует основной луч молнии с ответвлениями"""
        self.main_bolt = []
        segments = 10
        
        # Начинаем сверху над целью
        start_x = self.target.x
        start_y = self.target.y - 350
        
        # Основной луч
        current_x = start_x
        current_y = start_y
        self.main_bolt.append((current_x, current_y))
        
        for i in range(1, segments):
            progress = i / segments
            current_y = start_y + (self.target.y - start_y) * progress
            # Добавляем случайное отклонение, которое уменьшается к концу
            deviation = random.uniform(-25, 25) * (1 - progress * 0.7)
            current_x = start_x + deviation
            self.main_bolt.append((current_x, current_y))
            
            # Создаём больше ответвлений
            if random.random() < 0.5 and i < segments - 2:
                branch = self.generate_branch((current_x, current_y), 
                                              (self.target.x, self.target.y), 
                                              progress, length=random.randint(3, 5))
                self.branches.append(branch)
        
        self.main_bolt.append((self.target.x, self.target.y))
    
    def generate_branch(self, start, main_target, progress, length):
        """Генерирует ответвление молнии"""
        branch = [start]
        angle = random.uniform(-1.5, 1.5)
        
        for i in range(1, length):
            prev = branch[-1]
            # Ответвление идёт в сторону и вниз с затуханием
            offset_x = random.uniform(20, 45) * (1 if random.random() > 0.5 else -1)
            offset_y = random.uniform(15, 35)
            new_x = prev[0] + offset_x * (1 - i / length * 0.5)
            new_y = prev[1] + offset_y
            branch.append((new_x, new_y))
        
        return branch
    
    def update(self, dt, enemies, player, tilemap):
        super().update(dt, enemies, player, tilemap)
        # Обновляем частицы
        for particle in self.flash_particles:
            particle['life'] -= dt
        self.flash_particles = [p for p in self.flash_particles if p['life'] > 0]

    def render(self, surface, camera):
        progress = 1 - (self.time_left / 0.5)
        alpha = int(255 * (1 - progress * 0.8)) if progress < 0.8 else int(255 * (1 - progress) * 5)
        
        tx, ty = camera.apply_point((self.target.x, self.target.y))
        tx, ty = round(tx), round(ty)
        
        # Рисуем частицы вспышки в точке удара
        for particle in self.flash_particles:
            dist = particle['speed'] * (0.5 - particle['life'])
            part_x = tx + dist * math.cos(particle['angle'])
            part_y = ty + dist * math.sin(particle['angle'])
            
            particle_alpha = int(255 * (particle['life'] / 0.5))
            size = particle['size']
            
            # Яркий электрический эффект с градиентом
            if particle['life'] > 0.35:
                color = (200, 230, 255, particle_alpha)
            elif particle['life'] > 0.2:
                color = (150, 200, 255, particle_alpha)
            else:
                color = (100, 150, 255, particle_alpha)
            
            part_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(part_surf, color, (size, size), size)
            # Яркое белое ядро
            pygame.draw.circle(part_surf, (255, 255, 255, min(255, particle_alpha + 80)), 
                             (size, size), max(1, size // 2))
            surface.blit(part_surf, (part_x - size, part_y - size))
        
        # Рисуем электрические дуги вокруг удара (только в начале)
        if progress < 0.4:
            arc_alpha = int(alpha * (1 - progress / 0.4))
            for arc in self.electric_arcs:
                screen_arc = [camera.apply_point(p) for p in arc['segments']]
                if len(screen_arc) > 1 and arc_alpha > 0:
                    # Свечение дуги
                    pygame.draw.lines(surface, (100, 180, 255, arc_alpha // 2), False, screen_arc, 4)
                    # Основная линия
                    pygame.draw.lines(surface, (180, 220, 255, arc_alpha), False, screen_arc, 2)
                    # Яркое ядро
                    pygame.draw.lines(surface, (255, 255, 255, arc_alpha), False, screen_arc, 1)
        
        # Рисуем ответвления молнии
        for branch in self.branches:
            screen_branch = [camera.apply_point(p) for p in branch]
            if len(screen_branch) > 1:
                # Внешнее свечение
                glow_color = (80, 140, 255, max(0, alpha // 2))
                if alpha > 0:
                    pygame.draw.lines(surface, glow_color, False, screen_branch, 8)
                # Основная линия ветви
                branch_color = (150, 210, 255, alpha)
                if alpha > 0:
                    pygame.draw.lines(surface, branch_color, False, screen_branch, 4)
                # Яркое ядро
                core_color = (255, 255, 255, alpha)
                if alpha > 0:
                    pygame.draw.lines(surface, core_color, False, screen_branch, 2)
        
        # Рисуем основной луч молнии (более яркий и толстый)
        screen_bolt = [camera.apply_point(p) for p in self.main_bolt]
        if len(screen_bolt) > 1:
            # Самое широкое свечение (синее)
            outer_glow = (60, 100, 255, max(0, alpha // 4))
            if alpha > 0:
                pygame.draw.lines(surface, outer_glow, False, screen_bolt, 18)
            
            # Среднее свечение (голубое)
            middle_glow = (100, 160, 255, max(0, alpha // 2))
            if alpha > 0:
                pygame.draw.lines(surface, middle_glow, False, screen_bolt, 11)
            
            # Основная линия (яркий голубой)
            main_color = (180, 220, 255, alpha)
            if alpha > 0:
                pygame.draw.lines(surface, main_color, False, screen_bolt, 6)
            
            # Яркое белое ядро
            core_color = (255, 255, 255, alpha)
            if alpha > 0:
                pygame.draw.lines(surface, core_color, False, screen_bolt, 3)
        
        # Вспышка в точке удара
        if progress < 0.6:
            flash_progress = progress / 0.6
            flash_alpha = int(220 * (1 - flash_progress))
            
            # Пульсирующее свечение
            pulse = 1 + math.sin(progress * 20) * 0.15
            
            # Расширяющееся кольцо удара
            for i in range(4):
                ring_radius = int(40 * pulse * (1 + i * 0.25 + flash_progress * 0.8))
                ring_alpha = max(0, flash_alpha - i * 40)
                
                ring_surf = pygame.Surface((ring_radius * 2, ring_radius * 2), pygame.SRCALPHA)
                if i == 0:
                    # Яркое ядро
                    pygame.draw.circle(ring_surf, (255, 255, 255, ring_alpha), 
                                     (ring_radius, ring_radius), ring_radius)
                elif i == 1:
                    # Первое кольцо - самое яркое
                    pygame.draw.circle(ring_surf, (220, 240, 255, ring_alpha), 
                                     (ring_radius, ring_radius), ring_radius, width=4)
                else:
                    # Внешние кольца
                    colors = [(180, 220, 255), (140, 200, 255)]
                    pygame.draw.circle(ring_surf, (*colors[i-2], ring_alpha), 
                                     (ring_radius, ring_radius), ring_radius, width=3)
                
                surface.blit(ring_surf, (tx - ring_radius, ty - ring_radius))


class Meteor(Effect):
    """
    Метеорит: падает в заранее выбранную точку карты за fall_time секунд,
    затем взрыв по области (урон в момент удара).
    """
    def __init__(self, target_pos, damage, radius, fall_time, color):
        super().__init__(duration=fall_time + 0.5)
        self.target = pygame.Vector2(target_pos)
        self.damage = damage
        self.radius = radius
        self.fall_time = fall_time
        self.color = color
        self.timer = 0.0
        self.landed = False
        self.warning_particles = []  # частицы предупреждения
        self.smoke_trail = []  # дымовой след метеорита

    def update(self, dt, enemies, player, tilemap):
        self.timer += dt
        
        # Добавляем более интенсивные частицы предупреждения
        if not self.landed and random.random() < 0.6:
            angle = random.uniform(0, 6.28)
            dist = random.uniform(0, self.radius * 0.9)
            self.warning_particles.append({
                'pos': pygame.Vector2(
                    self.target.x + dist * math.cos(angle),
                    self.target.y + dist * math.sin(angle)
                ),
                'life': 0.6,
                'size': random.randint(3, 7)
            })
        
        # Обновляем частицы
        for particle in self.warning_particles:
            particle['life'] -= dt
        self.warning_particles = [p for p in self.warning_particles if p['life'] > 0]
        
        # Обновляем дымовой след
        for smoke in self.smoke_trail:
            smoke['life'] -= dt
            smoke['size'] += dt * 10  # расширяется со временем
        self.smoke_trail = [s for s in self.smoke_trail if s['life'] > 0]
        
        if not self.landed and self.timer >= self.fall_time:
            self.landed = True
            self._apply_aoe((self.target.x, self.target.y), self.radius,
                            self.damage, enemies)
        super().update(dt, enemies, player, tilemap)

    def render(self, surface, camera):
        tx, ty = camera.apply_point((self.target.x, self.target.y))
        tx, ty = round(tx), round(ty)
        
        if not self.landed:
            progress = min(1.0, self.timer / self.fall_time)
            
            # Рисуем частицы предупреждения с более ярким эффектом
            for particle in self.warning_particles:
                ppx, ppy = camera.apply_point((particle['pos'].x, particle['pos'].y))
                alpha = int(255 * particle['life'] / 0.6)
                size = particle['size']
                
                # Огненные оттенки с градиентом
                if particle['life'] > 0.4:
                    color = (255, 150, 0, alpha)
                elif particle['life'] > 0.2:
                    color = (255, 100, 0, alpha)
                else:
                    color = (200, 50, 0, alpha)
                
                part_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(part_surf, color, (size, size), size)
                # Яркое ядро
                pygame.draw.circle(part_surf, (255, 200, 100, min(255, alpha + 50)), 
                                 (size, size), max(1, size // 2))
                surface.blit(part_surf, (ppx - size, ppy - size))
            
            # Более интенсивный пульсирующий круг предупреждения
            pulse = 0.75 + 0.25 * math.sin(self.timer * 12)
            warning_radius = int(self.radius * pulse)
            
            # Многослойный круг предупреждения
            warning_surf = pygame.Surface((warning_radius * 2, warning_radius * 2), pygame.SRCALPHA)
            for i in range(5):
                alpha = int(100 * (1 - i / 5) * (1 - progress * 0.3))
                r = warning_radius - i * 3
                if r > 0:
                    # Цвет от ярко-оранжевого к красному
                    colors = [(255, 100, 0), (255, 70, 0), (220, 50, 0), (180, 30, 0), (140, 20, 0)]
                    pygame.draw.circle(warning_surf, (*colors[i], alpha), 
                                     (warning_radius, warning_radius), r, width=3)
            surface.blit(warning_surf, (tx - warning_radius, ty - warning_radius))
            
            # Летящий метеорит с более эффектным следом
            rock_y = ty - int(400 * (1 - progress * progress))  # ускоряется при падении
            
            # Добавляем частицы в дымовой след
            if random.random() < 0.5:
                self.smoke_trail.append({
                    'x': tx,
                    'y': rock_y,
                    'life': 0.4,
                    'size': random.randint(8, 15)
                })
            
            # Рисуем дымовой след
            for smoke in self.smoke_trail:
                smoke_alpha = int(120 * (smoke['life'] / 0.4))
                smoke_size = int(smoke['size'])
                smoke_surf = pygame.Surface((smoke_size * 2, smoke_size * 2), pygame.SRCALPHA)
                # Тёмно-серый дым
                pygame.draw.circle(smoke_surf, (60, 40, 30, smoke_alpha),
                                 (smoke_size, smoke_size), smoke_size)
                surface.blit(smoke_surf, (smoke['x'] - smoke_size, smoke['y'] - smoke_size))
            
            # Огненный след из частиц (более длинный и яркий)
            for i in range(8):
                trail_offset = i * 18
                trail_alpha = int(180 * (1 - i / 8))
                trail_size = 22 - i * 2
                
                # Градиент от жёлтого к красному
                if i < 2:
                    trail_color = (255, 200, 100, trail_alpha)
                elif i < 4:
                    trail_color = (255, 150, 50, trail_alpha)
                elif i < 6:
                    trail_color = (255, 100, 30, trail_alpha)
                else:
                    trail_color = (200, 50, 20, trail_alpha)
                
                trail_surf = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf, trail_color, (trail_size, trail_size), trail_size)
                surface.blit(trail_surf, (tx - trail_size, rock_y + trail_offset - trail_size))
            
            # Сам метеорит с более детальной отрисовкой
            rock_size = 22
            
            # Большое свечение вокруг
            glow_surf = pygame.Surface((rock_size * 4, rock_size * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 120, 0, 80), 
                             (rock_size * 2, rock_size * 2), rock_size * 2)
            surface.blit(glow_surf, (tx - rock_size * 2, rock_y - rock_size * 2))
            
            # Слои метеорита
            pygame.draw.circle(surface, (80, 40, 20), (tx, rock_y), rock_size)
            pygame.draw.circle(surface, (120, 60, 30), (tx, rock_y), rock_size - 3)
            pygame.draw.circle(surface, (255, 120, 40), (tx, rock_y), rock_size - 6)
            pygame.draw.circle(surface, (255, 180, 80), (tx, rock_y), rock_size - 10)
            pygame.draw.circle(surface, (255, 220, 150), (tx, rock_y), rock_size - 14)
            
            # Яркие искры вокруг метеорита
            for i in range(6):
                angle = (self.timer * 8 + i * 1.047) % 6.28
                spark_dist = rock_size + 8
                spark_x = tx + spark_dist * math.cos(angle)
                spark_y = rock_y + spark_dist * math.sin(angle)
                pygame.draw.circle(surface, (255, 200, 100), (int(spark_x), int(spark_y)), 3)
        else:
            # Мощная вспышка взрыва с улучшенной анимацией
            explosion_progress = (self.timer - self.fall_time) / 0.5
            alpha = int(220 * (1 - explosion_progress))
            
            # Ударная волна с пульсацией
            pulse = 1 + math.sin(explosion_progress * 15) * 0.1
            
            # Множественные расширяющиеся круги с разными цветами
            for i in range(6):
                radius_mult = 0.8 + i * 0.25 + explosion_progress * 1.2
                exp_radius = int(self.radius * radius_mult * pulse)
                ring_alpha = max(0, alpha - i * 30)
                
                exp_surf = pygame.Surface((exp_radius * 2, exp_radius * 2), pygame.SRCALPHA)
                
                if i == 0:
                    # Яркое белое ядро
                    pygame.draw.circle(exp_surf, (255, 255, 255, ring_alpha), 
                                     (exp_radius, exp_radius), exp_radius)
                elif i == 1:
                    # Жёлтый круг
                    pygame.draw.circle(exp_surf, (255, 240, 150, ring_alpha), 
                                     (exp_radius, exp_radius), exp_radius)
                else:
                    # Огненные кольца с градиентом
                    colors = [(255, 200, 100), (255, 150, 50), (255, 100, 30), (200, 50, 20)]
                    pygame.draw.circle(exp_surf, (*colors[min(i-2, 3)], ring_alpha), 
                                     (exp_radius, exp_radius), exp_radius, width=max(4, 8 - i))
                
                surface.blit(exp_surf, (tx - exp_radius, ty - exp_radius))
            
            # Летящие обломки и искры
            if explosion_progress < 0.7:
                for i in range(20):
                    angle = i * 0.314
                    dist = explosion_progress * 120
                    debris_x = tx + dist * math.cos(angle)
                    debris_y = ty + dist * math.sin(angle)
                    debris_alpha = int(200 * (1 - explosion_progress / 0.7))
                    
                    debris_size = random.randint(2, 5)
                    debris_surf = pygame.Surface((debris_size * 2, debris_size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(debris_surf, (255, 150, 50, debris_alpha), 
                                     (debris_size, debris_size), debris_size)
                    surface.blit(debris_surf, (int(debris_x) - debris_size, int(debris_y) - debris_size))


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
            # Ищем ближайшего врага в той же дальности, что и обычная атака
            target = self._nearest_enemy(origin, enemies, max_range=settings.PLAYER_ATTACK_RANGE)
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
            # Метеорит падает около игрока, в пределах видимости
            # Случайная точка в радиусе 400-600 пикселей от игрока
            angle = random.uniform(0, 6.28)  # 2*pi
            distance = random.uniform(200, 500)
            tx = player.pos.x + distance * math.cos(angle)
            ty = player.pos.y + distance * math.sin(angle)
            
            # Ограничиваем границами карты
            tx = max(radius, min(tx, tilemap.pixel_width - radius))
            ty = max(radius, min(ty, tilemap.pixel_height - radius))
            
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
