---
ticket: TICKET-03
title: Entrée Windows — hotkey global, typing, notifications
status: coded
branch: feat/ticket-03
updated: 2026-07-03
---

# TICKET-03 — Entrée Windows

## 🎯 Objectif
Même UX que sous Hyprland, sur Windows 10/11 : un hotkey global toggle
l'enregistrement, le texte transcrit est tapé dans l'input actif. Livrable :
`whisper_type_win.py`, lançable avec `pythonw` (pas de fenêtre console).

## 📎 Contexte (à lire avant de coder)
- **Dépend de TICKET-02** (importe `core.Recorder` / `core.Transcriber`).
  Ne pas commencer avant qu'il soit `validated`.
- `config.py` fonctionne tel quel sous Windows (`Path.home()/.config/whisper-type/`) —
  choix assumé : un seul chemin cross-platform, pas de `%APPDATA%`.
- Environnement de test : la VM Windows de l'utilisateur.

## 🔧 Décisions déjà prises (ne pas re-débattre)
- **Hotkey global** : lib `keyboard` (`keyboard.add_hotkey`). Défaut **`f9`**
  (une seule touche, cohérent avec le bind Linux SUPER+F9), surchargeable via une
  nouvelle clé `hotkey` dans config.toml (l'ajouter aux `DEFAULTS` de `config.py`
  + au TOML généré ; l'entrée Linux l'ignore, le bind y étant géré par Hyprland).
  Utiliser `suppress=True` pour que F9 n'atteigne pas l'application au premier
  plan (F9 déclenche p. ex. le mode lecture dans Firefox, le recalcul dans Excel).
- **Typing** : copie dans le presse-papier + simulation Ctrl+V — fiable pour les
  accents français et l'unicode, contrairement à la frappe touche par touche.
  Sauvegarder puis restaurer le presse-papier précédent. Fallback si le collage
  échoue : `keyboard.write(text)`.
- **Notifications** : toasts via `winotify` (léger, zéro dépendance lourde).
  Pas de tray icon dans ce ticket — c'est du confort, pas du MVP.
- **Cycle de vie** : `keyboard.wait()` en boucle principale ; hotkey de sortie
  propre `ctrl+alt+q`.
- **Deps** : nouvelles dépendances dans `requirements-win.txt` (ne pas polluer
  `requirements.txt` qui reste Linux).

## ✅ Definition of Done
- [x] `whisper_type_win.py` + `requirements-win.txt`
- [ ] Testé sur la VM Windows : dictée dans Notepad ET dans un champ de navigateur, avec accents français
- [ ] F9 dans un navigateur toggle l'enregistrement SANS action parasite de l'app (ex. mode lecture Firefox)
- [ ] Premier lancement (modèle absent) → téléchargement + toast « chargement », pas de crash
- [ ] Hotkey pressé pendant le chargement du modèle → toast « réessayez », pas de crash
- [x] Tests Linux toujours verts (`.venv/bin/python -m pytest tests/ -q`) + tests unitaires de la clé `hotkey` dans config
- [x] Doc à jour (README : section dev Windows)

---

## 🔨 Code — 2026-07-03
**Fait :**
- `whisper_type_win.py` : entrée Windows complète — hotkey global (`keyboard.add_hotkey`,
  défaut `f9`, `suppress=True`), notifications toast (`winotify`), typing par
  presse-papier + Ctrl+V (`pyperclip` + `keyboard.send`) avec sauvegarde/restauration
  du presse-papier précédent et fallback `keyboard.write()`, orchestration de
  `core.Recorder` / `core.Transcriber` (même structure que `whisper_type.py`).
- `requirements-win.txt` : liste autonome (deps core + `keyboard`, `winotify`,
  `pyperclip`) — ne touche pas à `requirements.txt` (Linux).
- `config.py` : ajout de la clé `hotkey` (défaut `"f9"`) aux `DEFAULTS` et au
  TOML généré, avec commentaire précisant qu'elle est ignorée côté Linux.
- Tests unitaires de la clé `hotkey` dans `tests/test_config.py` (défaut,
  fallback si absente du fichier, override). Suite complète : 32 tests verts.
- README : nouvelle section « Windows (dev) » (install from source, table
  raccourcis, note sur le presse-papier, note admin/`suppress`), tableau
  « Project layout » et bloc `Configuration` mis à jour.

**Décisions (& pourquoi) :**
- **Pas de PID file / signaux côté Windows** : contrairement à Linux (process
  daemon + `toggle.sh` externe envoyant SIGUSR1), le hotkey Windows est géré
  *dans* le process via `keyboard.add_hotkey` — pas besoin d'un mécanisme IPC
  séparé. Le cycle de vie est donc plus simple : un seul script, pas de
  `start.sh`/`stop.sh`/`toggle.sh` équivalents.
- **Sortie propre via `keyboard.wait("ctrl+alt+q")` plutôt qu'un hotkey avec
  callback** : `keyboard.add_hotkey()` exécute son callback dans un thread
  d'écoute interne à la lib, pas le thread principal — lever `SystemExit`
  depuis ce callback n'aurait tué que ce thread-là et laissé
  `keyboard.wait()` bloqué indéfiniment sur le thread principal. Passer
  directement la combo de sortie à `keyboard.wait(...)` la fait retourner
  normalement quand elle est pressée, sans ce piège de thread.
- **`type_text()` : presse-papier + Ctrl+V, jamais `keyboard.write()` en
  premier choix** — décision déjà actée dans le ticket (fiabilité accents/
  unicode) ; `keyboard.write()` reste en fallback silencieux si le collage
  échoue (presse-papier verrouillé par une autre appli, par ex.).
- **`load_model()` et `stop_and_transcribe()` avalent les exceptions et
  notifient plutôt que de laisser planter le thread de fond** — sur Linux le
  process entier tourne sous supervision (signal handlers, log fichier) donc
  une exception silencieuse dans un thread daemon est moins grave ; côté
  Windows, lancé via `pythonw` sans console, une exception qui tue le thread
  de chargement laisserait l'utilisateur bloqué sur « modèle en cours de
  chargement » sans aucun indice. D'où le toast d'échec explicite dans
  `load_model()`.
- **`requirements-win.txt` autonome** (redondant avec `requirements.txt` sur
  `faster-whisper`/`sounddevice`/`numpy`) plutôt qu'un `-r requirements.txt`
  en tête : un utilisateur Windows n'a pas de venv Linux à côté, il fait
  `pip install -r requirements-win.txt` seul — et TICKET-04 (PyInstaller)
  aura besoin d'une liste Windows complète et autonome de toute façon.

**Fichiers :**
- `whisper_type_win.py` (nouveau)
- `requirements-win.txt` (nouveau)
- `config.py` (clé `hotkey`)
- `tests/test_config.py` (tests `hotkey`)
- `README.md` (section Windows (dev), Configuration, Project layout, Status)

**Reste / questions pour le test :**
- **Aucun test réel sur Windows dans cette session** — `keyboard`, `winotify`,
  `pyperclip` ne sont pas installés dans le venv Linux de dev (ni installables
  proprement : `winotify` est spécifique Windows) et n'ont donc été vérifiés
  que par lecture + `ast.parse` (syntaxe). Toute la DoD liée à la VM Windows
  (dictée Notepad/navigateur avec accents, F9 sans action parasite dans un
  navigateur, chargement modèle absent, hotkey pendant chargement) reste à
  cocher par le rôle Test sur la VM Windows de l'utilisateur — c'est
  explicitement l'environnement de test prévu par le ticket.
- Le presse-papier restauré après un délai fixe `time.sleep(0.3)` avant le
  Ctrl+V de restauration — valeur choisie arbitrairement pour laisser le
  temps au collage de se faire ; à ajuster si ça s'avère trop court/long en
  usage réel sur la VM.
- Pas de garde contre un second hotkey pressé pendant qu'une transcription
  est déjà en cours (comportement hérité de `whisper_type.py` Linux, jamais
  garanti là non plus) — à signaler si ça pose problème en test réel.
- `keyboard` peut nécessiter des droits administrateur sur certaines cibles
  Windows pour le hook global — documenté en note README mais pas vérifié
  faute de VM disponible dans cette session.

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
