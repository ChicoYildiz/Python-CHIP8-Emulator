"""Runtime configuration for CHIP-8 emulator (quirks & parameters)."""
from dataclasses import dataclass, field

@dataclass()
class QuirkConfig:
    """Configuration flags for interpreter behaviour variations ("quirks").

    These toggles let you run ROMs that depend on behaviour from older
    interpreters without hard-forking core logic.
    """
    shift_legacy: bool = False            # 8xy6 / 8xyE use Vy as source (older / some ROM expectations)
    load_store_increment_i: bool = False  # Fx55 / Fx65 increment I by x+1 after operation
    draw_wrap: bool = False               # Sprites wrap around screen edges instead of clipping
    jump_with_v0_quirk: bool = False      # Some interpreters use Bnnn + V0 (placeholder for future use)

@dataclass()
class EmulatorConfig:
    """Runtime configuration object bundled & passed to the emulator.

    Using a dataclass keeps it explicit and easy to extend while avoiding
    a long parameter list. `slots=True` reduces per-instance memory & guards
    against accidental attribute typos.
    """
    cycles_per_frame: int = 700
    scale: int = 10                        # For pygame renderer
    debug: bool = False
    use_pygame: bool = True                # Attempt pygame window if available (ignored if use_tk True)
    use_tk: bool = False                   # Prefer Tkinter GUI (menus) when True
    sound_enabled: bool = True             # Enable/disable sound beeps
    quirks: QuirkConfig = field(default_factory=QuirkConfig)  # Avoid shared mutable default
