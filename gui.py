# Alternative system as GUI to spawn Pygame as subprocess (direct launch did not work on MacOS)
import sys
import os
import signal
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional

DEFAULT_SPEED = 12
SPEED_PRESETS = [
    ("Very Slow: 8", 8),
    ("Slow: 10", 10),
    ("Normal: 12", 12),
    ("Fast: 30", 30),
    ("Faster: 60", 60),
    ("Turbo: 500", 500),
]


class EmulatorProcessController:
    def __init__(self):
        self.proc: Optional[subprocess.Popen] = None
        self.rom_path: Optional[str] = None
        self.speed: int = DEFAULT_SPEED
        self.paused: bool = False

    def start(self, rom_path: str, speed: int):
        self.stop()
        self.rom_path = rom_path
        self.speed = speed
        py = sys.executable
        main_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py')
        try:
            self.proc = subprocess.Popen([py, main_path, rom_path, str(speed)])
        except FileNotFoundError:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to launch emulator: {e}")
        self.paused = False

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
            except Exception:
                pass
        self.proc = None
        self.paused = False

    def restart(self):
        if self.rom_path:
            self.start(self.rom_path, self.speed)

    def toggle_pause(self):
        if not self.proc or self.proc.poll() is not None:
            return
        if sys.platform != 'win32':  # Use POSIX signals
            try:
                if not self.paused:
                    os.kill(self.proc.pid, signal.SIGSTOP)
                    self.paused = True
                else:
                    os.kill(self.proc.pid, signal.SIGCONT)
                    self.paused = False
            except Exception:
                pass


class TkMainLauncher:
    def __init__(self, initial_rom: Optional[str]):
        self.root = tk.Tk()
        self.root.title("CHIP-8 Emulator Launcher")
        self.root.geometry("480x190")
        self.ctrl = EmulatorProcessController()

        self.status_var = tk.StringVar(value="No ROM loaded")
        self.speed_var = tk.StringVar(value=f"Speed: {DEFAULT_SPEED}")

        self._build_ui()
        self._build_menu()
        self._monitor_proc()  # start monitoring

        if initial_rom:
            self.root.after(100, lambda: self._launch_rom(initial_rom))

    # --- UI ---
    def _build_ui(self):
        tk.Label(self.root, text="CHIP-8 Emulator", font=("Arial", 16, "bold")).pack(pady=4)
        tk.Label(self.root, textvariable=self.status_var, font=("Arial", 12), fg="blue").pack()
        tk.Label(self.root, textvariable=self.speed_var, font=("Arial", 10), fg="gray40").pack(pady=2)
        tk.Label(self.root, text="Open a ROM via File → Open ROM...", font=("Arial", 9), fg="gray55").pack(pady=4)
        tk.Label(self.root, text="Keypad 123C/456D/789E/A0BF → 1234/QWER/ASDF/ZXCV", font=("Arial", 9)).pack(pady=2)
        tk.Label(self.root, text="A separate terminal/pygame window will appear.", font=("Arial", 8), fg="gray55").pack(side=tk.BOTTOM, pady=4)

    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open ROM...", command=self._menu_open)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._quit)
        menubar.add_cascade(label="File", menu=file_menu)

        emu_menu = tk.Menu(menubar, tearoff=0)
        emu_menu.add_command(label="Restart", command=self._restart)
        emu_menu.add_command(label="Pause/Resume", command=self._pause_resume)
        emu_menu.add_command(label="Stop", command=self._stop)
        menubar.add_cascade(label="Emulation", menu=emu_menu)

        speed_menu = tk.Menu(menubar, tearoff=0)
        for label, val in SPEED_PRESETS:
            speed_menu.add_command(label=label, command=lambda v=val: self._set_speed(v))
        menubar.add_cascade(label="Speed", menu=speed_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "CHIP-8 Emulator Launcher\nSpawns main.py"))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    # --- Actions ---
    def _menu_open(self):
        path = filedialog.askopenfilename(title="Select ROM", filetypes=[("CHIP-8 ROMs", "*.ch8 *.c8 *.rom"), ("All files", "*.*")])
        if path:
            self._launch_rom(path)

    def _launch_rom(self, path: str):
        try:
            self.ctrl.start(path, self.ctrl.speed)
            self.status_var.set(f"ROM: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Launch Failed", str(e))

    def _restart(self):
        self.ctrl.restart()

    def _pause_resume(self):
        self.ctrl.toggle_pause()
        suffix = " (Paused)" if self.ctrl.paused else ""
        base = self.status_var.get().split(" (Paused)")[0]
        self.status_var.set(base + suffix)

    def _stop(self):
        self.ctrl.stop()
        self.status_var.set("Stopped (ROM loaded)" if self.ctrl.rom_path else "No ROM loaded")

    def _set_speed(self, speed: int):
        self.ctrl.speed = speed
        self.speed_var.set(f"Speed: {speed}")
        # If running, restart with new speed
        if self.ctrl.proc and self.ctrl.proc.poll() is None:
            self.ctrl.restart()

    def _quit(self):
        self.ctrl.stop()
        self.root.destroy()

    def _monitor_proc(self):
        if self.ctrl.proc and self.ctrl.proc.poll() is not None:
            code = self.ctrl.proc.returncode
            current = self.status_var.get().split(' (Exited')[0]
            self.status_var.set(f"{current} (Exited {code})")
            self.ctrl.proc = None
        self.root.after(1000, self._monitor_proc)

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        self.root.mainloop()


def main():
    rom_arg = sys.argv[1] if len(sys.argv) > 1 else None
    launcher = TkMainLauncher(rom_arg)
    launcher.run()


if __name__ == "__main__":  # pragma: no cover
    main()
