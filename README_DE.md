# CHIP-8 Emulator (Python)

Ein leichter, verständlicher CHIP-8 Emulator in Python 3. Fokus: Übersichtlichkeit, minimale Abhängigkeiten und modularer Aufbau (pygame, Tk-Launcher oder reines Terminal). Ideal zum Lernen oder für Experimente mit Interpreter-„Quirks“.

[English README](./README.md)

## Merkmale
- Vollständige CHIP-8 CPU (Standard-Befehlssatz)
- Einstellbare Ausführungsgeschwindigkeit (`cycles_per_frame`)
- Mehrere Anzeige-Backends:
  - `pygame` Fenster (Standard, falls installiert)
  - ANSI Terminal-Ausgabe (Fallback)
  - Tk Launcher (`gui.py`) für ROM-Auswahl & Geschwindigkeits-Presets
- Eingabe:
  - Tastatur mit pygame (Tasten-Druck & -Loslassen)
  - Terminal-Eingabe (Unix-artige Systeme)
- Einfacher Sound (Terminal-Glocke) – keine Zusatzpakete nötig
- Konfigurierbare Quirks (Shift, Fx55/Fx65 Index-Inkrement, Wrap beim Zeichnen)
- Einfaches Speichern / Laden eines Zustands (Snapshot)

## Tastenbelegung
```
CHIP-8:  1 2 3 C    Tastatur: 1 2 3 4
          4 5 6 D               Q W E R
          7 8 9 E               A S D F
          A 0 B F               Z X C V
```

## Schnellstart
### 1. Abhängigkeiten installieren
Python 3.9+ empfohlen.
```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 2. Direkt starten
```bash
python main.py pfad/zur/rom.ch8
```
Optional: Zyklen pro Frame anpassen:
```bash
python main.py pfad/zur/rom.ch8 900
```

### 3. Tk Launcher nutzen
```bash
python gui.py              # ROM später über Menü öffnen
python gui.py beispiel.ch8 # ROM direkt laden
```

## Konfiguration
In `emulator/config.py` (`EmulatorConfig`). Beispiel:
```python
from emulator.config import EmulatorConfig, QuirkConfig
cfg = EmulatorConfig(cycles_per_frame=900, debug=True, quirks=QuirkConfig(draw_wrap=True))
```
Beim Erstellen des Emulators: `Chip8(config=cfg)`.

## Verzeichnisstruktur
```
emulator/               Kernmodule
  emulator.py           CPU + Ausführung
  display.py            ANSI Terminal Renderer
  display_pygame.py     Pygame Renderer
  input.py              Terminal Eingabe
  input_pygame.py       Pygame Eingabe
  sound.py              Einfacher Sound-Timer
  config.py             Konfig & Quirks
  constants.py          Font, Keymap, Dimensionen
main.py                 Frame-Schleife (60 Hz Timer)
gui.py                  Tk ROM Launcher
requirements.txt        Abhängigkeiten
```

## Geschwindigkeit & Timing
Timer laufen mit 60 Hz. Pro Frame werden `cycles_per_frame` Instruktionen ausgeführt (Standard 700). Höhere Werte = flüssiger / schneller. Extrem hohe Werte können ungleichmäßiges Timing verursachen.

## Quirks
- `shift_legacy`: 8xy6 / 8xyE benutzen Vy als Quelle
- `load_store_increment_i`: I nach Fx55 / Fx65 erhöhen
- `draw_wrap`: Sprite-Zeichnen wrappt am Bildschirmrand
- `jump_with_v0_quirk`: Platzhalter (derzeit ohne Effekt)

## Zustand speichern / laden
Einfaches Rohformat:
```python
emu.save_state("state.bin")
emu.load_state("state.bin")
```
Nicht als permanentes Format gedacht.

## Sound
Terminal-Glocke (`\a`) beim Start eines aktiven Sound-Timers. Viele Terminals drosseln oder ignorieren diesen. Erweiterbar über `sound.py`.
