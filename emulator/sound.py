"""Minimal sound timer that uses only built-ins (terminal bell).

The CHIP-8 sound timer is a simple countdown; while > 0 a tone should
play. Instead of spawning external audio programs (afplay) we emit the
ASCII bell (\a) on transition from silent -> playing. Many terminals
ignore or throttle the bell; for richer audio a future optional module
could be plugged in. This keeps implementation dependency-free.
"""

class Sound:
    def __init__(self, enabled: bool = True):
        self.timer = 0
        self.playing = False
        self.enabled = enabled

    def set_timer(self, value: int):
        self.timer = int(value) & 0xFF
        # If timer becomes zero, ensure playing resets
        if self.timer == 0:
            self.playing = False

    def update(self):
        if self.timer > 0:
            # Emit bell only once per active period start
            if not self.playing and self.enabled:
                print('\a', end='')  # Terminal bell
            self.playing = True
            self.timer -= 1
            if self.timer == 0:
                self.playing = False
        else:
            self.playing = False

    def stop(self):
        # Nothing external to stop; just reset state
        self.timer = 0
        self.playing = False
