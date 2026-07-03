"""Lecture et initialisation de ~/.config/whisper-type/config.toml."""

import tomllib
from pathlib import Path

CONFIG_DIR  = Path.home() / ".config" / "whisper-type"
CONFIG_PATH = CONFIG_DIR / "config.toml"

DEFAULTS = {
    "model":    "small",
    "language": "fr",
    "hotkey":   "f9",
}

_DEFAULT_TOML = """\
# whisper-type — configuration
# Modifiez ce fichier puis relancez le daemon (stop.sh && start.sh sous Linux,
# ou relancez whisper_type_win.py sous Windows).

# Modèle Whisper : tiny | base | small | medium
# tiny   : ~1s  ultra rapide, moins précis
# base   : ~2s  bon compromis
# small  : ~4s  meilleur pour le français  ← défaut
# medium : ~8s  le plus précis, plus lent
model = "small"

# Langue : "fr" | "en" | "auto"
# "auto" laisse Whisper détecter automatiquement
language = "fr"

# Raccourci global — Windows uniquement (sous Linux, le bind est géré par Hyprland).
# Une seule touche, ex. "f9". Syntaxe des combos : voir la doc du module Python `keyboard`.
hotkey = "f9"
"""


def load() -> dict:
    if not CONFIG_PATH.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(_DEFAULT_TOML, encoding="utf-8")

    with CONFIG_PATH.open("rb") as f:
        data = tomllib.load(f)

    return {**DEFAULTS, **data}
