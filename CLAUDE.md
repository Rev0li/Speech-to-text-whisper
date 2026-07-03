# whisper-type — guide pour l'IA

Speech-to-text local : hotkey → micro → faster-whisper → texte tapé dans l'input actif.
**Daemon Python pur, pas de framework UI.** Tauri a été essayé puis abandonné
(commit `c262401`) — ne pas proposer d'y revenir.

## Fichiers

- `core.py` — cœur portable (aucun import spécifique plateforme) : `Recorder`
  (capture `sounddevice` → WAV temporaire) et `Transcriber` (chargement lazy
  `faster-whisper`, `transcribe(wav_path) -> str`)
- `whisper_type.py` — le daemon Linux : signaux (SIGUSR1 = toggle enregistrement),
  orchestre `core.py`, typing `wtype` (fallbacks : xdotool → ydotool → clipboard),
  notifications `notify-send`
- `config.py` — lit/crée `~/.config/whisper-type/config.toml` (clés : `model`, `language`)
- `install.sh` — install one-shot (deps dnf, venv, bind Hyprland **SUPER+F9**)
- `start.sh` / `stop.sh` / `toggle.sh` — cycle de vie du daemon (PID file `/tmp/whisper-type.pid`)
- `tests/` — pytest : `.venv/bin/python -m pytest tests/ -q`
- `docs/tickets/` — ticketing, protocole **ticket-handoff** : un ticket = un fichier
  `TICKET-XX.md` = une branche `feat/ticket-xx`

## Conventions

- Un fichier = une responsabilité ; garder les fichiers petits (< ~300 lignes).
- Architecture (portage Windows en cours, voir `docs/tickets/`) : le cœur
  audio/transcription portable vit dans `core.py`, tout ce qui est spécifique plateforme
  dans le point d'entrée de la plateforme (`whisper_type.py` Linux, `whisper_type_win.py` Windows à venir).
- Commits conventionnels avec ID de ticket : `feat(TICKET-03): …`
