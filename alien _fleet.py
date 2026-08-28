"""
Alien Fleet module for Space Invaders (PyGame)
------------------------------------------------
Covers the requirement:
  "The full invaders array should include the three types of aliens.
   These should move from side to side, and fire at the player at
   random. Their speed of movement should increase as the invaders
   are reduced in number (from being shot)."

Drop this alongside your existing game code and wire it up to your
main loop (see the bottom of the file for an integration sketch).
"""

import pygame
import random

# ------------------------------------------------------------------
# CONFIG - tweak these to match your game's scale / sprite sizes
# ------------------------------------------------------------------
ALIEN_ROWS = 4
ALIEN_COLS = 11
ALIEN_H_SPACING = 50
ALIEN_V_SPACING = 40
ALIEN_START_X = 60
ALIEN_START_Y = 60

BASE_MOVE_INTERVAL_MS = 700   # time between fleet "steps" at full strength
MIN_MOVE_INTERVAL_MS = 80     # fastest the fleet is allowed to move
STEP_DISTANCE = 12            # pixels moved per step
DROP_DISTANCE = 20            # pixels dropped when fleet hits an edge

FIRE_CHECK_INTERVAL_MS = 400  # how often we roll the dice on firing
FIRE_CHANCE = 0.15            # probability an alien fires on a given check


# ------------------------------------------------------------------
# ALIEN TYPES
# ------------------------------------------------------------------
class AlienType:
    """
    Simple data holder describing each of the three alien types.
    Swap the colours for real sprite images with pygame.image.load().
    """
    SQUID = {"name": "squid", "points": 30, "colour": (0, 255, 0), "size": (30, 20)}
    CRAB  = {"name": "crab",  "points": 20, "colour": (0, 200, 255), "size": (34, 22)}
    OCTOPUS = {"name": "octopus", "points": 10, "colour": (255, 255, 0), "size": (36, 24)}


class Alien(pygame.sprite.Sprite):
    def __init__(self, x, y, alien_type):
        super().__init__()
        self.alien_type = alien_type
        w, h = alien_type["size"]
        # Placeholder rectangle graphic - replace with real sprite art
        self.image = pygame.Surface((w, h))
        self.image.fill(alien_type["colour"])
        self.rect = self.image.get_rect(topleft=(x, y))
        self.points = alien_type["points"]

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy


# ------------------------------------------------------------------
# FLEET MANAGER
# ------------------------------------------------------------------
class AlienFleet:
    def __init__(self, screen_width, bullets_group):
        """
        screen_width: used for edge detection so the fleet knows when to drop
        bullets_group: a pygame.sprite.Group that alien bullets get added to
                       (your existing collision code can check this group)
        """
        self.screen_width = screen_width
        self.bullets_group = bullets_group
        self.aliens = pygame.sprite.Group()
        self.direction = 1  # 1 = moving right, -1 = moving left

        self._last_move_time = pygame.time.get_ticks()
        self._last_fire_check = pygame.time.get_ticks()

        self._total_aliens = 0
        self._build_formation()

    # ---------------- formation setup ----------------
    def _build_formation(self):
        """Builds the grid with three alien types, top rows tougher/rarer."""
        for row in range(ALIEN_ROWS):
            if row == 0:
                alien_type = AlienType.SQUID
            elif row in (1, 2):
                alien_type = AlienType.CRAB
            else:
                alien_type = AlienType.OCTOPUS

            for col in range(ALIEN_COLS):
                x = ALIEN_START_X + col * ALIEN_H_SPACING
                y = ALIEN_START_Y + row * ALIEN_V_SPACING
                self.aliens.add(Alien(x, y, alien_type))

        self._total_aliens = len(self.aliens)

    # ---------------- speed scaling ----------------
    def _current_move_interval(self):
        """
        Fewer aliens alive -> shorter interval between steps -> faster fleet.
        Linear scale between BASE_MOVE_INTERVAL_MS (full fleet) and
        MIN_MOVE_INTERVAL_MS (last alien standing).
        """
        alive = len(self.aliens)
        if alive == 0 or self._total_aliens == 0:
            return BASE_MOVE_INTERVAL_MS

        fraction_remaining = alive / self._total_aliens
        interval_range = BASE_MOVE_INTERVAL_MS - MIN_MOVE_INTERVAL_MS
        return MIN_MOVE_INTERVAL_MS + interval_range * fraction_remaining

    # ---------------- movement ----------------
    def update(self):
        now = pygame.time.get_ticks()

        if now - self._last_move_time >= self._current_move_interval():
            self._last_move_time = now
            self._step()

        if now - self._last_fire_check >= FIRE_CHECK_INTERVAL_MS:
            self._last_fire_check = now
            self._maybe_fire()

    def _step(self):
        """Move the whole fleet one step; reverse + drop on edge contact."""
        hit_edge = False
        for alien in self.aliens:
            if (alien.rect.right + STEP_DISTANCE * self.direction >= self.screen_width
                    or alien.rect.left + STEP_DISTANCE * self.direction <= 0):
                hit_edge = True
                break

        if hit_edge:
            self.direction *= -1
            for alien in self.aliens:
                alien.move(0, DROP_DISTANCE)
        else:
            for alien in self.aliens:
                alien.move(STEP_DISTANCE * self.direction, 0)

    # ---------------- random firing ----------------
    def _maybe_fire(self):
        """
        Each check, only the FRONT-most alien in each column can fire
        (so shots always come from the bottom of the formation, matching
        the classic game feel). Then we randomly roll whether it shoots.
        """
        if not self.aliens:
            return

        front_row_aliens = self._get_front_row_aliens()
        for alien in front_row_aliens:
            if random.random() < FIRE_CHANCE:
                self._spawn_bullet(alien)

    def _get_front_row_aliens(self):
        """Group aliens by column (x position), return the lowest one per column."""
        columns = {}
        for alien in self.aliens:
            col_key = alien.rect.x
            if col_key not in columns or alien.rect.y > columns[col_key].rect.y:
                columns[col_key] = alien
        return list(columns.values())

    def _spawn_bullet(self, alien):
        # Replace AlienBullet with your existing bullet class if you have one
        bullet = AlienBullet(alien.rect.centerx, alien.rect.bottom)
        self.bullets_group.add(bullet)

    # ---------------- collision helper ----------------
    def kill_alien(self, alien):
        """Call this from your collision-detection code when a player bullet
        hits an alien. Removing it from self.aliens automatically speeds
        up the fleet via _current_move_interval()."""
        alien.kill()

    def is_defeated(self):
        return len(self.aliens) == 0


# ------------------------------------------------------------------
# Minimal alien bullet (swap for your own if one already exists)
# ------------------------------------------------------------------
class AlienBullet(pygame.sprite.Sprite):
    SPEED = 6

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((4, 12))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(midtop=(x, y))

    def update(self):
        self.rect.y += self.SPEED
        if self.rect.top > 700:  # replace with SCREEN_HEIGHT
            self.kill()
