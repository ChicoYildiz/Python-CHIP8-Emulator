# Entry point for running the CHIP-8 emulator directly.
import sys
import time
from emulator.emulator import Chip8, DEFAULT_CYCLES_PER_FRAME
from emulator.constants import TIMER_FREQ

def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python main.py <rom_file> [cycles_per_frame]")
        return 1
    rom_file = sys.argv[1]
    try:
        cycles = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_CYCLES_PER_FRAME
    except ValueError:
        print("cycles_per_frame must be an integer")
        return 1

    emulator = Chip8(cycles_per_frame=cycles)
    try:
        emulator.load_rom(rom_file)
    except FileNotFoundError:
        print(f"ROM file {rom_file} not found.")
        return 1

    frame_time = 1 / TIMER_FREQ  # 60Hz
    next_frame = time.perf_counter()
    try:
        while True:
            now = time.perf_counter()
            if now >= next_frame:
                emulator.run_frame()
                # Catch up if we're behind (avoid cumulative drift)
                while next_frame <= now:
                    next_frame += frame_time
            # Sleep until next frame minus small safety margin
            sleep_for = next_frame - time.perf_counter() - 0.0002
            if sleep_for > 0:
                time.sleep(sleep_for)
    except KeyboardInterrupt:
        print("Emulation stopped.")
        emulator.sound.stop()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
