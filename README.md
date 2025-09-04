# CHIP-8 Emulator (Python)

A lightweight, dependency-minimal CHIP-8 emulator written in Python 3. Features a modular display/input stack (pygame, Tk launcher, or pure terminal fallback) plus a simple sound timer. Designed for clarity and approachability while still supporting common interpreter quirks.

[Deutsch / German README](./README_DE.md)

## Features
- Core CHIP-8 CPU with standard instruction set
- Adjustable execution speed (`cycles_per_frame`)
- Multiple display backends:
  - `pygame` window (default if available)
  - ANSI terminal rendering (fallback)
  - Optional Tk-based launcher (`gui.py`) for ROM selection & speed control
- Input handling:
  - Pygame keyboard (press + release)
  - Terminal key press capture (Unix-like)
- Basic sound (terminal bell) — dependency-free
- Quirk toggles (shift instructions, Fx55/Fx65 index increment, draw wrapping)
- Save / load rudimentary state snapshot

## Key Mapping
```
CHIP-8:  1 2 3 C    Keyboard: 1 2 3 4
          4 5 6 D               Q W E R
          7 8 9 E               A S D F
          A 0 B F               Z X C V
```

## Quick Start
### 1. Install dependencies
Python 3.9+ recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate  # (macOS/Linux)
pip install -r requirements.txt
```

### 2. Run directly
```bash
python main.py path/to/rom.ch8
```
Optional second argument overrides cycles per frame:
```bash
python main.py path/to/rom.ch8 900
```

### 3. Use the Tk launcher (optional GUI)
```bash
python gui.py               # choose a ROM via menu
python gui.py example.ch8  # auto-load specific ROM
```
Menu lets you restart, pause (POSIX only via SIGSTOP/SIGCONT), and change speed presets.

## Configuration
Runtime knobs are defined in `emulator/config.py` (`EmulatorConfig`). Example snippet:
```python
from emulator.config import EmulatorConfig, QuirkConfig
cfg = EmulatorConfig(cycles_per_frame=900, debug=True, quirks=QuirkConfig(draw_wrap=True))
```
Pass `config=cfg` into `Chip8(...)` if constructing manually.

## Project Layout
```
emulator/               Core modules
  emulator.py           CPU + execution model
  display.py            ANSI terminal renderer
  display_pygame.py     Pygame renderer
  input.py              Terminal input
  input_pygame.py       Pygame input
  sound.py              Simple sound timer (bell)
  config.py             Dataclass-based config & quirks
  constants.py          Font, keymap, sizes
main.py                 Frame scheduler & loop (60Hz timers)
gui.py                  Tk-based ROM launcher
requirements.txt        Dependency list (pygame optional)
```

## Speed & Timing
The loop targets a 60 Hz timer update frequency. Each frame runs `cycles_per_frame` instructions (default 700). Increase for smoother or faster games; some ROMs rely on rough proportionality rather than cycle accuracy. Extremely large values (e.g. 5000+) may cause uneven timing without further throttling.

## Quirks
Set in `QuirkConfig`:
- `shift_legacy`: Use Vy as source for 8xy6 / 8xyE
- `load_store_increment_i`: Increment I after Fx55 / Fx65
- `draw_wrap`: Wrap sprite drawing off screen edges
- `jump_with_v0_quirk`: Placeholder (not currently altering behaviour)

## Save / Load State
Basic raw snapshot:
```python
emu.save_state("state.bin")
emu.load_state("state.bin")
```
Primarily for experimentation; not a stable serialization format.

## Sound
A simple terminal bell (ASCII `\a`) fires when the sound timer transitions from 0 to active. Many terminals rate-limit or mute it; feel free to extend `sound.py` with richer audio (pygame mixer, simple square wave, etc.).
