---
ticket: TICKET-02
title: Extraire le cœur portable (core.py) de la couche Linux
status: coded
branch: feat/ticket-02
updated: 2026-07-03
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
- [x] `core.py` sans aucune dépendance plateforme (vérifiable en lisant ses imports)
- [ ] Daemon Linux inchangé à l'usage (test manuel : SUPER+F9, parler, texte tapé) — partiellement vérifié (voir « Reste » ci-dessus, pas de vraie phrase parlée testée)
- [x] Tests passent : `.venv/bin/python -m pytest tests/ -q`
- [x] Tests unitaires de `core.py` ajoutés (au moins : conversion `auto`→None, écriture WAV depuis des frames factices)
- [x] Doc à jour (tableau « Project layout » du README + CLAUDE.md)

---

## 🔨 Code — 2026-07-03
**Fait :**
- Créé `core.py` : `Recorder` (start/stop autour de `sounddevice.InputStream`,
  16 kHz mono int16, écriture WAV temporaire) et `Transcriber` (chargement lazy
  `faster_whisper.WhisperModel` cpu/int8, `transcribe(wav_path) -> str`).
- `whisper_type.py` réduit à l'orchestration : signaux, PID file, `notify()`,
  `type_text()` (wtype → xdotool → ydotool → clipboard), instancie
  `core.Recorder()` / `core.Transcriber()` et enchaîne leurs appels.
- Tests unitaires `tests/test_core.py` (23 tests au total, tous verts).
- Doc à jour : tableau « Project layout » du README + section Fichiers de CLAUDE.md.

**Décisions (& pourquoi) :**
- Ajouté `Recorder.abort()` distinct de `Recorder.stop()`, utilisé uniquement
  par `cleanup()` (SIGTERM/SIGINT) : `stop()` écrit toujours un WAV s'il y a des
  frames, ce qui aurait fait fuir un fichier temp jamais nettoyé à l'arrêt du
  daemon pendant un enregistrement en cours. `abort()` reproduit exactement
  l'ancien `cleanup()` (reset état + `try/except` silencieux sur l'arrêt du
  stream, pas d'écriture disque).
- `Transcriber` expose `is_loaded` : `whisper_type.py` continue de précharger
  le modèle dans un thread de fond au démarrage (UX inchangée — pas d'attente
  au premier raccourci) et vérifie `is_loaded` avant de transcrire pour garder
  le message « modèle en cours de chargement, réessayez » plutôt que de
  bloquer sur un `load()` synchrone. `transcribe()` reste capable de charger
  le modèle à la volée (lazy) si un futur appelant (Windows) ne précharge pas.
- Extrait la conversion `"auto" → None` dans une fonction pure
  `_resolve_language()` pour pouvoir la tester isolément sans instancier de
  vrai modèle Whisper.
- `Recorder.start()` avale toujours silencieusement l'échec d'ouverture du
  micro (log seulement, pas de `notify()`) — comportement identique à
  l'original, non modifié volontairement pour ne rien changer à l'usage.

**Fichiers :**
- `core.py` (nouveau)
- `whisper_type.py` (refactorisé — orchestration uniquement)
- `tests/test_core.py` (nouveau)
- `README.md`, `CLAUDE.md` (doc)

**Reste / questions pour le test :**
- Vérifié manuellement en conditions réelles : daemon relancé, `toggle.sh`
  (start puis stop) avec micro réel et modèle `small` chargé — pipeline
  complet mic → WAV → VAD → transcription → notify sans exception. Mais
  uniquement avec du silence ambiant (pas de vraie phrase parlée dans cette
  session) : le chemin `type_text()` avec un texte non-vide n'a donc été
  exercé qu'à la lecture du code (inchangé caractère pour caractère), pas en
  conditions réelles. À couvrir si possible côté test.
- `Recorder` n'a pas de test qui exerce un vrai `sounddevice.InputStream`
  (nécessiterait du matériel micro en CI) — seuls `stop()`/`abort()` sont
  testés avec des frames factices injectées directement.

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
