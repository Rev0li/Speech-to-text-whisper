# whisper-type

Local speech-to-text that types directly into your active input. Press a hotkey, speak, press again — the transcribed text appears where your cursor is.

Runs 100% offline using [faster-whisper](https://github.com/SYSTRAN/faster-whisper). No cloud, no subscription, no GUI — just a small Python daemon.

---

## Download (Windows)

Pre-built releases are published automatically by GitHub Actions on tagged commits (`v*`) — see [`.github/workflows/release-windows.yml`](.github/workflows/release-windows.yml).

1. Create a dedicated folder for the app, e.g. `Documents\whisper-type` — don't use `Downloads` directly.
2. **Before extracting**, add a Windows Defender exclusion for that folder: `Windows Security → Virus & threat protection → Manage settings → Exclusions → Add an exclusion → Folder`. This app isn't code-signed (see [Roadmap](#roadmap--windows-port) for why), and Defender's ML heuristics commonly flag unsigned PyInstaller apps as `Trojan:Script/Wacatac.B!ml` and **delete the exe on sight** — a well-known false positive, not an actual detection. The exclusion only prevents future scans; if Defender already quarantined the file, restore it first from `Windows Security → Protection history → (the Wacatac entry) → Actions → Restore`.
3. Grab `whisper-type-windows.zip` from the [Releases page](https://github.com/Rev0li/whisper-type/releases) and extract it into that excluded folder.
4. Run `whisper-type.exe`. Windows will likely also show **"Windows protected your PC"** (SmartScreen) — click **More info → Run anyway**; this is a separate, one-time warning per version (unrelated to the Defender exclusion above).
5. Press **F9** to start/stop recording, **Ctrl+Alt+Q** to quit — see [Windows (dev)](#windows-dev) for the full hotkey table and configuration.

The first launch downloads the Whisper model (~461 MB for `small`) — the "loading" toast covers that wait.

**Changing the hotkey:** the setting lives in a config file created automatically on first launch, at `C:\Users\<YourName>\.config\whisper-type\config.toml`. To edit it: press `Win + R`, type `notepad %USERPROFILE%\.config\whisper-type\config.toml`, press Enter. Change the `hotkey = "f9"` line to any key or combo (e.g. `hotkey = "f8"` or `hotkey = "ctrl+alt+r"`), save, then close and relaunch `whisper-type.exe`.

---

## For developers

### Status

| Platform | State |
|---|---|
| **Linux / Hyprland** | ✅ Stable — Python daemon, in daily use |
| **Windows 10/11** | ✅ Packaged & validated — see [Download](#download-windows) |

### Install (Linux / Hyprland)

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

### Install (Linux, no sudo)

For a Debian/Ubuntu machine where you don't have root (e.g. a school/shared
machine) — X11 + GNOME assumed, no Hyprland:

```bash
git clone https://github.com/Rev0li/whisper-type
cd whisper-type
./install_nosudo.sh
```

`install_nosudo.sh` never calls `sudo`. It gets the system libs it needs
(`libportaudio2`, `xdotool`+`libxdo3`) via `apt-get download` (fetches the
`.deb` without installing it) and extracts them with `dpkg -x` into `.local/`
— no system install, no root. `start.sh` sources `.local/env.sh` to point
`PATH`/`LD_LIBRARY_PATH` at them. The hotkey is a native GNOME custom
keybinding (`gsettings`) instead of a Hyprland bind — F9 alone (no modifier).

### Usage

| Action | Result |
|---|---|
| **SUPER + F9** (first press) | Start recording — notification appears |
| **SUPER + F9** (second press) | Stop → transcribe → text typed into the active input |

The daemon starts automatically with Hyprland. The Whisper model loads in the background (~15 s on launch, then stays in memory). The very first launch downloads the model (~461 MB for `small`).

### Configuration

Everything lives in `~/.config/whisper-type/config.toml` (created with defaults on first run):

```toml
model = "small"     # tiny | base | small | medium
language = "fr"     # "fr" | "en" | "auto"
hotkey = "f9"       # Windows only — Linux bind is managed by Hyprland
```

Restart the daemon after editing: `./stop.sh && ./start.sh` (Linux) or relaunch `whisper_type_win.py` (Windows).

### How it works

```
SUPER+F9
  └─→ toggle.sh sends SIGUSR1 to the daemon
        ├─ if idle      → start recording (sounddevice, 16 kHz mono)
        └─ if recording → stop → transcribe (faster-whisper) → wtype text
```

If `wtype` fails, the daemon falls back to `xdotool`, then `ydotool`, then copies the text to the clipboard.

### Windows (dev)

No installer needed for this path — this is the developer path, run from source with Python 3.11+ (for the pre-built `.exe`, see [Download](#download-windows)).

```powershell
git clone https://github.com/Rev0li/whisper-type
cd whisper-type
python -m venv .venv
.venv\Scripts\pip install -r requirements-win.txt
.venv\Scripts\pythonw whisper_type_win.py
```

| Action | Result |
|---|---|
| **F9** (first press) | Start recording — toast notification appears |
| **F9** (second press) | Stop → transcribe → text pasted into the active input (Ctrl+V) |
| **Ctrl+Alt+Q** | Quit the daemon |

The hotkey is configurable via the `hotkey` key in `config.toml` (see [Configuration](#configuration)); Linux ignores this key since the bind is managed by Hyprland instead.

Typing copies the transcribed text to the clipboard and simulates Ctrl+V — reliable for French accents and unicode, unlike key-by-key typing. The previous clipboard content is restored afterwards. If pasting fails, it falls back to typing the text key by key.

Notes:
- Global hotkey capture (`keyboard` module) may need the terminal/script run as Administrator, depending on the target application.
- `F9` uses `suppress=True` so the keypress doesn't reach the foreground app (e.g. Firefox's reader mode, Excel's recalculation shortcut).

### Project layout

| File | Role |
|---|---|
| `whisper_type.py` | Linux entry point: signals, notifications, typing, orchestrates `core.py` |
| `whisper_type_win.py` | Windows entry point: global hotkey, toast notifications, clipboard typing, orchestrates `core.py` |
| `core.py` | Portable core (no platform dependency): `Recorder` (mic capture → WAV), `Transcriber` (faster-whisper) |
| `config.py` | Reads/creates `~/.config/whisper-type/config.toml` |
| `install.sh` | One-shot install (system deps, venv, Hyprland config) — needs sudo |
| `install_nosudo.sh` | One-shot install without sudo (Debian/Ubuntu, GNOME/X11) — `.deb` extraction + `gsettings` hotkey |
| `start.sh` / `stop.sh` | Daemon lifecycle (Linux) |
| `toggle.sh` | Sends SIGUSR1 to the daemon (Linux, bound to the hotkey) |
| `requirements.txt` / `requirements-win.txt` | Linux deps / Windows deps |
| `.github/workflows/release-windows.yml` | Builds `whisper-type.exe` with PyInstaller and publishes it to GitHub Releases on tag `v*` |
| `tests/` | pytest — run with `.venv/bin/python -m pytest tests/ -q` |

### Roadmap — Windows port

Goal: the same minimal UX on Windows (hotkey → speak → text typed), shipped as a downloadable `.exe` for non-technical friends. No GUI framework — plain Python, packaged with PyInstaller. Work is ticketed in `docs/tickets/`:

1. [TICKET-02](docs/tickets/TICKET-02.md) — extract the portable core (recording + transcription) from the Linux layer
2. [TICKET-03](docs/tickets/TICKET-03.md) — Windows entry point (global hotkey, typing, toast notifications)
3. [TICKET-04](docs/tickets/TICKET-04.md) — PyInstaller packaging + GitHub Actions release

Releases aren't code-signed (signing costs money) — unsigned executables trigger Windows SmartScreen and Defender false-positive quarantines, see [Download](#download-windows) for the workarounds.

### History

An earlier iteration wrapped this daemon in a Tauri desktop app (tray icon, settings UI, installers). It was dropped in favor of the plain daemon (`git log c262401`) — three stacks for a program with no UI wasn't worth it.
