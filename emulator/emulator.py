"""Core CHIP-8 emulator implementation.

Quick-fix refactor highlights:
* Separate single-instruction execution (step) from per-frame timing (run_frame).
* Add bounds / safety checks (stack overflow/underflow, PC fetch guard, ROM size check).
* Increase instruction throughput (hundreds of instructions per 60Hz frame) while keeping timer frequency at 60Hz.
* Explicitly coerce VF to 0/1 and clarify collision semantics.
"""

import random
import array
from typing import List, Optional

from .constants import (
    FONTSET,
    KEYMAP,
    MEMORY_SIZE,
    STACK_SIZE,
    V_COUNT,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    TIMER_FREQ,
)
from .display import Display
from .display_pygame import PygameDisplay  # type: ignore
try:
    from .display_tk import TkDisplay  # type: ignore
except Exception:  # pragma: no cover
    TkDisplay = None  # type: ignore
from .input import InputHandler
try:
    from .input_pygame import PygameInputHandler  # type: ignore
except Exception:  # pragma: no cover - fallback if pygame not available
    PygameInputHandler = None  # type: ignore
from .sound import Sound
from .config import EmulatorConfig


DEFAULT_CYCLES_PER_FRAME = 700  # Reasonable starting point for smooth gameplay


class Chip8:
    """CHIP-8 virtual machine.

    Public attributes kept minimal; methods provide core execution primitives.
    """

    def __init__(self, cycles_per_frame: int = DEFAULT_CYCLES_PER_FRAME, config: Optional[EmulatorConfig] = None):
        # Core memory & registers
        self.memory = array.array('B', [0] * MEMORY_SIZE)
        self.V = array.array('B', [0] * V_COUNT)
        self.stack = array.array('H', [0] * STACK_SIZE)
        self.sp = 0
        self.pc = 0x200
        self.I = 0
        self.delay_timer = 0
        self.config = config or EmulatorConfig(cycles_per_frame=cycles_per_frame)

        # Display backend selection (Tk > pygame > console)
        self.using_pygame = False
        if self.config.use_tk and TkDisplay is not None:
            try:
                self.display = TkDisplay(SCREEN_WIDTH, SCREEN_HEIGHT, self.config.scale)
            except Exception as e:
                if self.config.debug:
                    print(f"[WARN] Tk init failed, falling back: {e}")
                self.display = Display(SCREEN_WIDTH, SCREEN_HEIGHT)
        elif self.config.use_pygame:
            try:
                self.display = PygameDisplay(SCREEN_WIDTH, SCREEN_HEIGHT, self.config.scale)
                self.using_pygame = True
            except Exception as e:
                if self.config.debug:
                    print(f"[WARN] Pygame init failed, falling back to console display: {e}")
                self.display = Display(SCREEN_WIDTH, SCREEN_HEIGHT)
        else:
            self.display = Display(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Input subsystem
        if self.using_pygame and PygameInputHandler is not None:
            self.input_handler = PygameInputHandler(KEYMAP)
        else:
            self.input_handler = InputHandler(KEYMAP)
        self.sound = Sound(enabled=self.config.sound_enabled)

        # Flags / config derived
        self.debug = self.config.debug
        self.cycles_per_frame = self.config.cycles_per_frame
        self.halted = False

        # Load fontset
        self.load_fontset()

        # RNG and ROM state
        self._rand = random.Random()
        self.rom_loaded = False

    def load_fontset(self) -> None:
        for i, byte in enumerate(FONTSET):
            self.memory[i] = byte

    def load_rom(self, rom_path: str) -> None:
        with open(rom_path, 'rb') as f:
            rom = f.read()
        max_len = MEMORY_SIZE - 0x200
        if len(rom) > max_len:
            raise ValueError(f"ROM too large ({len(rom)} bytes > {max_len})")
        for i, byte in enumerate(rom):
            self.memory[0x200 + i] = byte
        self.pc = 0x200
        self.halted = False
        self.rom_loaded = True

    def fetch_opcode(self) -> int:
        if self.pc >= MEMORY_SIZE or self.pc + 1 >= MEMORY_SIZE:
            self.halted = True
            raise RuntimeError(f"PC out of bounds: {self.pc:04X}")
        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        self.pc += 2
        return opcode

    def decode_and_execute(self, opcode: int) -> None:
        nnn = opcode & 0x0FFF
        nn = opcode & 0x00FF
        n = opcode & 0x000F
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        op = (opcode & 0xF000) >> 12

        if self.debug:
            print(f"PC: {self.pc-2:04X}, Opcode: {opcode:04X}")

        # Dispatch based on first nibble
        if op == 0x0:
            if opcode == 0x00E0:
                self.display.clear()
            elif opcode == 0x00EE:
                if self.sp == 0:
                    self.halted = True
                    raise RuntimeError("Stack underflow on RET")
                self.sp -= 1
                self.pc = self.stack[self.sp]
            else:
                # Unimplemented 0x0??? instructions (scroll / extended) placeholder
                if self.debug:
                    print(f"Unknown 0x0 opcode: {opcode:04X}")
        elif op == 0x1:
            self.pc = nnn
        elif op == 0x2:
            if self.sp >= STACK_SIZE:
                self.halted = True
                raise RuntimeError("Stack overflow on CALL")
            self.stack[self.sp] = self.pc
            self.sp += 1
            self.pc = nnn
        elif op == 0x3:
            if self.V[x] == nn:
                self.pc += 2
        elif op == 0x4:
            if self.V[x] != nn:
                self.pc += 2
        elif op == 0x5:
            if n == 0 and self.V[x] == self.V[y]:
                self.pc += 2
        elif op == 0x6:
            self.V[x] = nn
        elif op == 0x7:
            self.V[x] = (self.V[x] + nn) & 0xFF
        elif op == 0x8:
            if n == 0x0:
                self.V[x] = self.V[y]
            elif n == 0x1:
                self.V[x] |= self.V[y]
            elif n == 0x2:
                self.V[x] &= self.V[y]
            elif n == 0x3:
                self.V[x] ^= self.V[y]
            elif n == 0x4:
                sum_val = self.V[x] + self.V[y]
                self.V[x] = sum_val & 0xFF
                self.V[0xF] = 1 if sum_val > 0xFF else 0
            elif n == 0x5:
                self.V[0xF] = 1 if self.V[x] > self.V[y] else 0
                self.V[x] = (self.V[x] - self.V[y]) & 0xFF
            elif n == 0x6:
                source = self.V[y] if self.config.quirks.shift_legacy else self.V[x]
                self.V[0xF] = source & 0x1
                self.V[x] = (source >> 1) & 0xFF
            elif n == 0x7:
                self.V[0xF] = 1 if self.V[y] > self.V[x] else 0
                self.V[x] = (self.V[y] - self.V[x]) & 0xFF
            elif n == 0xE:
                source = self.V[y] if self.config.quirks.shift_legacy else self.V[x]
                self.V[0xF] = (source & 0x80) >> 7
                self.V[x] = (source << 1) & 0xFF
            else:
                if self.debug:
                    print(f"Unknown 8xy? opcode: {opcode:04X}")
        elif op == 0x9:
            if n == 0 and self.V[x] != self.V[y]:
                self.pc += 2
        elif op == 0xA:
            self.I = nnn
        elif op == 0xB:
            self.pc = nnn + self.V[0]
        elif op == 0xC:
            # Random byte AND nn
            self.V[x] = (self._rand.getrandbits(8)) & nn
        elif op == 0xD:
            x_pos = self.V[x]
            y_pos = self.V[y]
            # Bounds / safety: ensure sprite bytes readable
            if self.I + n > MEMORY_SIZE:
                self.halted = True
                raise RuntimeError("Sprite fetch out of memory bounds")
            sprite: List[int] = [self.memory[self.I + i] for i in range(n)]
            collision = self.display.draw_sprite(x_pos, y_pos, sprite, n, wrap=self.config.quirks.draw_wrap)
            self.V[0xF] = 1 if collision else 0
        elif op == 0xE:
            if nn == 0x9E:
                if self.input_handler.is_key_pressed(self.V[x]):
                    self.pc += 2
            elif nn == 0xA1:
                if not self.input_handler.is_key_pressed(self.V[x]):
                    self.pc += 2
            else:
                if self.debug:
                    print(f"Unknown Ex?? opcode: {opcode:04X}")
        elif op == 0xF:
            if nn == 0x07:
                self.V[x] = self.delay_timer
            elif nn == 0x0A:
                self.V[x] = self.input_handler.wait_for_key()
            elif nn == 0x15:
                self.delay_timer = self.V[x]
            elif nn == 0x18:
                self.sound.set_timer(self.V[x])
            elif nn == 0x1E:
                self.I += self.V[x]
            elif nn == 0x29:
                self.I = self.V[x] * 5
            elif nn == 0x33:
                val = self.V[x]
                self.memory[self.I] = val // 100
                self.memory[self.I + 1] = (val // 10) % 10
                self.memory[self.I + 2] = val % 10
            elif nn == 0x55:
                for i in range(x + 1):
                    self.memory[self.I + i] = self.V[i]
                if self.config.quirks.load_store_increment_i:
                    self.I += x + 1
            elif nn == 0x65:
                for i in range(x + 1):
                    self.V[i] = self.memory[self.I + i]
                if self.config.quirks.load_store_increment_i:
                    self.I += x + 1
            else:
                if self.debug:
                    print(f"Unknown Fx?? opcode: {opcode:04X}")
        else:
            if self.debug:
                print(f"Unknown opcode: {opcode:04X}")

    def update_timers(self) -> None:
        if self.delay_timer > 0:
            self.delay_timer -= 1
        self.sound.update()

    # --- New execution model ---
    def step(self) -> None:
        """Execute a single instruction (no timer or render side-effects)."""
        if self.halted:
            return
        self.input_handler.update_keys()
        opcode = self.fetch_opcode()
        self.decode_and_execute(opcode)

    def run_frame(self) -> None:
        """Execute one *video frame* worth of emulation work.

        Rough model: execute N instructions (where N = cycles_per_frame), then
        tick timers once (60 Hz) and present a frame. Event polling happens
        once per frame to keep input latency low without excessive overhead.
        """
        if self.halted:
            # Still tick timers so sounds decay properly
            self.update_timers()
            self.display.render()
            return
        # Process window events (once per frame) before executing instructions
        events = None
        if self.using_pygame and hasattr(self.display, 'poll_events'):
            try:
                events = self.display.poll_events()
            except KeyboardInterrupt:
                raise
            except Exception as e:
                if self.debug:
                    print(f"[WARN] Event polling error: {e}")
        if events:
            # Route events to input handler if it provides handle_event
            for ev in events:
                handler = getattr(self.input_handler, 'handle_event', None)
                if handler:
                    handler(ev)

        for _ in range(self.cycles_per_frame):
            if self.halted:
                break
            self.step()
        # Timers at 60Hz
        self.update_timers()
        # Only render once per frame
        self.display.render()
        # Poll window events if pygame backend
    # (Event polling moved to top of frame)

    def save_state(self, filename: str) -> None:
        """Persist a raw snapshot of core state to a binary file.

        This is intentionally *not* a stable format; future versions may
        change layout. Intended for quick experimentation.
        """
        with open(filename, 'wb') as f:
            f.write(self.memory.tobytes())
            f.write(self.V.tobytes())
            f.write(self.stack.tobytes())
            f.write(self.pc.to_bytes(2, 'big'))
            f.write(self.I.to_bytes(2, 'big'))
            f.write(self.sp.to_bytes(1, 'big'))
            f.write(self.delay_timer.to_bytes(1, 'big'))
            f.write(self.sound.timer.to_bytes(1, 'big'))

    def load_state(self, filename: str) -> None:
        with open(filename, 'rb') as f:
            self.memory = array.array('B', f.read(MEMORY_SIZE))
            self.V = array.array('B', f.read(V_COUNT))
            self.stack = array.array('H', f.read(STACK_SIZE * 2))
            self.pc = int.from_bytes(f.read(2), 'big')
            self.I = int.from_bytes(f.read(2), 'big')
            self.sp = int.from_bytes(f.read(1), 'big')
            self.delay_timer = int.from_bytes(f.read(1), 'big')
            timer_byte = f.read(1)
            if timer_byte:
                self.sound.set_timer(int.from_bytes(timer_byte, 'big'))

    # --- Utility additions ---
    def reset(self) -> None:
        """Soft reset registers, timers, stack; keep loaded ROM and fontset."""
        for i in range(V_COUNT):
            self.V[i] = 0
        self.sp = 0
        self.pc = 0x200
        self.I = 0
        self.delay_timer = 0
        self.sound.set_timer(0)
        self.halted = False
