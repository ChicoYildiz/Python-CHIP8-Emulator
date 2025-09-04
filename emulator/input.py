"""Terminal-based input handler (Unix-like systems).

Quick fixes:
* Persist key state across update polls (no mass reset each frame).
* Graceful terminal restoration via atexit safeguard.
* ESC raises KeyboardInterrupt still.
* Foundation for future key release handling (currently immediate set-on-press only).
"""

import sys
import termios
import tty
import select
import atexit


class InputHandler:
    def __init__(self, keymap):
        self.keymap = keymap
        self.keys = [False] * 16
        if sys.stdin.isatty():
            self.old_settings = termios.tcgetattr(sys.stdin)
            atexit.register(self._restore)
        else:
            self.old_settings = None

    def _restore(self):  # Safe to call multiple times
        if self.old_settings is None:
            return
        try:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
        except Exception:
            pass

    def update_keys(self):
        # Non-blocking key check; we do not reset keys blindly anymore.
        # (Terminal does not easily provide key release here.)
        if not sys.stdin.isatty():  # No interactive input available
            return
        while select.select([sys.stdin], [], [], 0)[0]:
            key = sys.stdin.read(1)
            if key in self.keymap:
                self.keys[self.keymap[key]] = True
            elif key == '\x1b':  # ESC to quit
                raise KeyboardInterrupt
            else:
                # Ignore unknown keys
                continue

    def is_key_pressed(self, key):
        return self.keys[key]

    def wait_for_key(self):
        # Blocking wait for any mapped key
        if not sys.stdin.isatty():
            # No TTY; block until we can never read -> raise
            raise RuntimeError("wait_for_key not supported (no TTY)")
        tty.setraw(sys.stdin)
        try:
            while True:
                key = sys.stdin.read(1)
                if key in self.keymap:
                    code = self.keymap[key]
                    self.keys[code] = True
                    return code
                elif key == '\x1b':
                    raise KeyboardInterrupt
        finally:
            self._restore()
