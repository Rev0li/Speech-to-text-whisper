# whisper-type — guide pour l'IA

Speech-to-text local : hotkey → micro → faster-whisper → texte tapé dans l'input actif.
**Daemon Python pur, pas de framework UI.** Tauri a été essayé puis abandonné
(commit `c262401`) — ne pas proposer d'y revenir.

## Fichiers

- `whisper_type.py` — le daemon Linux : signaux (SIGUSR1 = toggle enregistrement),
  capture `sounddevice`, transcription `faster-whisper`, typing `wtype`
  (fallbacks : xdotool → ydotool → clipboard), notifications `notify-send`
- `config.py` — lit/crée `~/.config/whisper-type/config.toml` (clés : `model`, `language`)
- `install.sh` — install one-shot (deps dnf, venv, bind Hyprland **SUPER+F9**)
- `start.sh` / `stop.sh` / `toggle.sh` — cycle de vie du daemon (PID file `/tmp/whisper-type.pid`)
- `tests/` — pytest : `.venv/bin/python -m pytest tests/ -q`
- `docs/tickets/` — ticketing, protocole **ticket-handoff** : un ticket = un fichier
  `TICKET-XX.md` = une branche `feat/ticket-xx`

## Conventions

- Un fichier = une responsabilité ; garder les fichiers petits (< ~300 lignes).
- Cible d'architecture (portage Windows en cours, voir `docs/tickets/`) : le cœur
  audio/transcription portable dans `core.py`, tout ce qui est spécifique plateforme
  dans le point d'entrée de la plateforme (`whisper_type.py` Linux, `whisper_type_win.py` Windows).
- Commits conventionnels avec ID de ticket : `feat(TICKET-03): …`
