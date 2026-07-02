# whisper-type

Local speech-to-text that types directly into your active input. Press a hotkey, speak, press again — the transcribed text appears where your cursor is.

Runs 100% offline using [faster-whisper](https://github.com/SYSTRAN/faster-whisper). No cloud, no subscription, no GUI — just a small Python daemon.

---

## Status

| Platform | State |
|---|---|
| **Linux / Hyprland** | ✅ Stable — Python daemon, in daily use |
| **Windows 10/11** | 🚧 Planned — lightweight port, see [Roadmap](#roadmap--windows-port) |

---

## Install (Linux / Hyprland)

Requirements: Fedora (adapt the `dnf` line for other distros), Hyprland, Python 3.11+.

```bash
git clone https://github.com/Rev0li/whisper-type
cd whisper-type
./install.sh
```

The install script:
- installs system deps (`portaudio`, `wtype`, `libnotify`)
- creates a Python venv and installs `faster-whisper` + `sounddevice`
- adds to `hyprland.conf`:
  - `exec-once` → the daemon auto-starts with Hyprland
  - `bind = SUPER, F9` → toggle recording

## Usage

| Action | Result |
|---|---|
| **SUPER + F9** (first press) | Start recording — notification appears |
| **SUPER + F9** (second press) | Stop → transcribe → text typed into the active input |

The daemon starts automatically with Hyprland. The Whisper model loads in the background (~15 s on launch, then stays in memory). The very first launch downloads the model (~461 MB for `small`).

## Configuration

Everything lives in `~/.config/whisper-type/config.toml` (created with defaults on first run):

```toml
model = "small"     # tiny | base | small | medium
language = "fr"     # "fr" | "en" | "auto"
```

Restart the daemon after editing: `./stop.sh && ./start.sh`.

## How it works

```
SUPER+F9
  └─→ toggle.sh sends SIGUSR1 to the daemon
        ├─ if idle      → start recording (sounddevice, 16 kHz mono)
        └─ if recording → stop → transcribe (faster-whisper) → wtype text
```

If `wtype` fails, the daemon falls back to `xdotool`, then `ydotool`, then copies the text to the clipboard.

## Project layout

| File | Role |
|---|---|
| `whisper_type.py` | The daemon: recording, transcription, typing, notifications |
| `config.py` | Reads/creates `~/.config/whisper-type/config.toml` |
| `install.sh` | One-shot install (system deps, venv, Hyprland config) |
| `start.sh` / `stop.sh` | Daemon lifecycle |
| `toggle.sh` | Sends SIGUSR1 to the daemon (bound to the hotkey) |
| `tests/` | pytest — run with `.venv/bin/python -m pytest tests/ -q` |

## Roadmap — Windows port

Goal: the same minimal UX on Windows (hotkey → speak → text typed), shipped as a downloadable `.exe` for non-technical friends. No GUI framework — plain Python, packaged with PyInstaller. Work is ticketed in `docs/tickets/`:

1. [TICKET-02](docs/tickets/TICKET-02.md) — extract the portable core (recording + transcription) from the Linux layer
2. [TICKET-03](docs/tickets/TICKET-03.md) — Windows entry point (global hotkey, typing, toast notifications)
3. [TICKET-04](docs/tickets/TICKET-04.md) — PyInstaller packaging + GitHub Actions release

Note for future releases: unsigned executables trigger Windows SmartScreen ("Windows protected your PC") — users must click "More info → Run anyway".

## History

An earlier iteration wrapped this daemon in a Tauri desktop app (tray icon, settings UI, installers). It was dropped in favor of the plain daemon (`git log c262401`) — three stacks for a program with no UI wasn't worth it.
