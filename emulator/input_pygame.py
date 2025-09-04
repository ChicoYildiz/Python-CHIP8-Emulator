"""Pygame-based input handler providing proper key press & release state.

This replaces the terminal-based handler when the pygame display backend is active,
so the user can keep focus on the game window instead of the terminal.
"""
from __future__ import annotations
import pygame


class PygameInputHandler:
    def __init__(self, keymap):
        self.keymap = keymap
        self.keys = [False] * 16

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            name = pygame.key.name(event.key)
            if name in self.keymap:
                self.keys[self.keymap[name]] = True
        elif event.type == pygame.KEYUP:
            name = pygame.key.name(event.key)
            if name in self.keymap:
                self.keys[self.keymap[name]] = False

    def update_keys(self):  # Kept for interface compatibility; no per-frame polling needed.
        return

    def is_key_pressed(self, key):
        return self.keys[key]

    def wait_for_key(self):
        # Block until a mapped key is pressed (process QUIT events too)
        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                raise KeyboardInterrupt
            if event.type == pygame.KEYDOWN:
                name = pygame.key.name(event.key)
                if name in self.keymap:
                    code = self.keymap[name]
                    self.keys[code] = True
                    return code
