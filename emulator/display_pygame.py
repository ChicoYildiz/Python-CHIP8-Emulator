"""Pygame-based display for CHIP-8 with simple scaling and optional color customization."""
from __future__ import annotations
import pygame

class PygameDisplay:
    def __init__(self, width: int, height: int, scale: int = 10):
        self.width = width
        self.height = height
        self.scale = scale
        self.surface = None
        self.window = None
        self.draw_flag = False
        self.pixels = [[0 for _ in range(width)] for _ in range(height)]
        self._init_window()

    def _init_window(self):
        pygame.init()
        self.window = pygame.display.set_mode((self.width * self.scale, self.height * self.scale))
        pygame.display.set_caption("CHIP-8 Emulator")
        self.surface = pygame.display.get_surface()

    def clear(self):
        self.pixels = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.draw_flag = True

    def draw_sprite(self, x, y, sprite, height, wrap=False):
        """Draw sprite with optional wrapping (default False to match base display)."""
        collision = False
        for row in range(height):
            yy = (y + row) % self.height if wrap else (y + row)
            if yy >= self.height:
                break
            sprite_byte = sprite[row]
            for col in range(8):
                if (sprite_byte & (0x80 >> col)) == 0:
                    continue
                xx = (x + col) % self.width if wrap else (x + col)
                if xx >= self.width:
                    break
                if self.pixels[yy][xx] == 1:
                    collision = True
                self.pixels[yy][xx] ^= 1
        self.draw_flag = True
        return collision

    def render(self):
        if not self.draw_flag:
            return
        self.surface.fill((0, 0, 0))
        on_color = (0, 255, 120)
        for y in range(self.height):
            for x in range(self.width):
                if self.pixels[y][x]:
                    pygame.draw.rect(
                        self.surface,
                        on_color,
                        (x * self.scale, y * self.scale, self.scale, self.scale),
                    )
        pygame.display.flip()
        self.draw_flag = False

    def poll_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                raise KeyboardInterrupt
        return events
