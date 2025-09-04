"""Console display backend using only built-ins (no os.system calls).

Clearing now uses ANSI escape sequences instead of spawning a subshell.
This avoids overhead and external dependencies; works on most modern
terminals (including macOS default Terminal and iTerm). On the first
render we issue a full clear (2J) then subsequent renders just move the
cursor to home (H) before redrawing frame buffer.
"""

class Display:
    """Minimal ANSI terminal display backend.

    Kept intentionally simple; callers toggle `draw_flag` when a frame should
    be flushed. This backend is a portability fallback when pygame / Tk are
    unavailable.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.pixels: list[list[int]] = [[0] * width for _ in range(height)]
        self.draw_flag: bool = False
        self._first_render = True

    def clear(self) -> None:
        self.pixels = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.draw_flag = True

    def draw_sprite(self, x: int, y: int, sprite, height: int, wrap: bool = False):
        """Draw a sprite at (x, y).

        If wrap is True, pixels wrap around screen edges (Super-CHIP style quirk);
        otherwise they are clipped when exceeding bounds.
        Returns True if any pixel unset due to XOR collision.
        """
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

    def render(self) -> None:
        if not self.draw_flag:
            return
        # ANSI clear strategy: full clear once, then home cursor only.
        if self._first_render:
            print("\x1b[2J\x1b[H", end="")  # Clear entire screen & home
            self._first_render = False
        else:
            print("\x1b[H", end="")  # Home cursor only
        # Build lines then join for fewer print calls
        out_lines = [''.join('█' if px else ' ' for px in row) for row in self.pixels]
        print("\n".join(out_lines))
        self.draw_flag = False
