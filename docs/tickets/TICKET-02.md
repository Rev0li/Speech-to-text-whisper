---
ticket: TICKET-02
title: Extraire le cœur portable (core.py) de la couche Linux
status: todo
branch: feat/ticket-02
updated: 2026-07-02
---

# TICKET-02 — Extraire le cœur portable (core.py)

## 🎯 Objectif
Préparer le portage Windows en séparant ce qui est portable (enregistrement micro +
transcription Whisper) de ce qui est spécifique Linux (signaux SIGUSR1, notify-send,
wtype). Après ce ticket, le daemon Hyprland fonctionne **exactement comme avant**,
mais le cœur est importable par une future entrée Windows (TICKET-03).

## 📎 Contexte (à lire avant de coder)
- Tout le comportement actuel vit dans `whisper_type.py` (~180 lignes) : le lire en entier.
- `config.py` lit `~/.config/whisper-type/config.toml` (clés `model`, `language`) — ne pas le modifier ici.
- Le daemon est lancé par `start.sh` via `.venv/bin/python3 whisper_type.py` ; le toggle
  vient de `toggle.sh` qui envoie SIGUSR1.

## 🔧 Découpage attendu
- **`core.py`** (nouveau, portable — AUCUN import spécifique plateforme, pas de
  `signal`, pas de `subprocess` vers des outils Linux) :
  - `Recorder` : start/stop autour de `sounddevice.InputStream` (16 kHz mono int16),
    accumulation des frames, écriture d'un WAV temporaire à l'arrêt (reprendre la
    logique de `start_recording()` et la moitié écriture-WAV de `stop_and_transcribe()`).
  - `Transcriber` : chargement lazy de `faster_whisper.WhisperModel` (cpu, int8),
    `transcribe(wav_path) -> str` (beam_size=5, vad_filter=True, `language=None`
    si config vaut `"auto"`).
- **`whisper_type.py`** (conservé, devient l'entrée Linux) : PID file, handlers de
  signaux, `notify()`, `type_text()` (wtype → xdotool → ydotool → wl-copy),
  orchestration de Recorder/Transcriber.
- Les notifications sont **injectées** dans le cœur (callback `on_status` ou retour
  de valeurs), jamais importées dans `core.py`.

## ✅ Definition of Done
- [ ] `core.py` sans aucune dépendance plateforme (vérifiable en lisant ses imports)
- [ ] Daemon Linux inchangé à l'usage (test manuel : SUPER+F9, parler, texte tapé)
- [ ] Tests passent : `.venv/bin/python -m pytest tests/ -q`
- [ ] Tests unitaires de `core.py` ajoutés (au moins : conversion `auto`→None, écriture WAV depuis des frames factices)
- [ ] Doc à jour (tableau « Project layout » du README + CLAUDE.md)

---

## 🔨 Code — <date>
**Fait :**
**Décisions (& pourquoi) :**
**Fichiers :**
**Reste / questions pour le test :**

## 🧪 Test — <date>
**Couvert :**
**NON couvert (assumé) :**
**Sécurité vérifiée :**
**Bugs trouvés :**
**Audit refactor : X/10** — <arguments>

## ♻️ Refactor — <date>
**Changé :**
**Pourquoi :**
**Risque :**
**Tests verts avant ET après :**

## 🚀 Validation — <date>
**Lancé en dev :**
**Lancé en prod :**
**DoD complète :**
**Statut final :**
