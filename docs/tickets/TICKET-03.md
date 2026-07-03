---
ticket: TICKET-03
title: Entrée Windows — hotkey global, typing, notifications
status: validated
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
- [x] Testé sur la VM Windows : dictée dans Notepad ET dans un champ de navigateur, avec accents français
- [x] F9 dans un navigateur toggle l'enregistrement SANS action parasite de l'app (ex. mode lecture Firefox)
- [x] Premier lancement (modèle absent) → téléchargement + toast « chargement », pas de crash
- [x] Hotkey pressé pendant le chargement du modèle → toast « réessayez », pas de crash
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

## 🧪 Test — 2026-07-03
**Couvert :**
- `keyboard`, `pyperclip`, `winotify` ne sont pas installés dans le venv Linux
  (`winotify` est Windows-only) : plutôt que de se limiter à `ast.parse`, ces
  trois libs ont été doublées dans `sys.modules` (`tests/test_whisper_type_win.py`)
  pour importer réellement `whisper_type_win.py` et exercer sa logique
  d'orchestration. 14 nouveaux tests, suite complète **46 tests verts**
  (`.venv/bin/python -m pytest tests/ -q`).
- `notify()` : appel correct de `Notification(app_id=..., title=..., msg=...)`,
  exception de `.show()` avalée sans lever (pas de crash si le service toast
  Windows est indisponible).
- `type_text()` : collage via `pyperclip.copy()` + `keyboard.send("ctrl+v")`,
  sauvegarde/restauration du presse-papier précédent, fallback
  `keyboard.write()` si le collage échoue, pas de restauration tentée si la
  lecture du presse-papier précédent a elle-même échoué.
- `load_model()` : notifie « chargement » puis « prêt » en cas de succès ;
  en cas d'exception de `transcriber.load()`, notifie « échec » et ne
  propage pas (couvre exactement la DoD « premier lancement, pas de crash »
  au niveau logique).
- `toggle()` : dispatch correct vers `start_recording`/`stop_and_transcribe`
  selon `recorder.is_recording`.
- `stop_and_transcribe()` : no-op si `recorder.stop()` retourne `None`,
  notifie « modèle en cours de chargement » et nettoie le WAV sans transcrire
  si `transcriber.is_loaded` est faux, appelle `type_text()` seulement si le
  texte n'est pas vide, et le WAV est bien supprimé (`os.unlink`) même si
  `transcriber.transcribe()` lève une exception.
- Suite `tests/test_config.py` (clé `hotkey`, déjà ajoutée par le rôle Code) :
  toujours verte, relue et jugée correcte (défaut, fallback, override).

**NON couvert (assumé) :**
- Tout ce qui nécessite la VM Windows réelle : dictée effective dans Notepad/
  navigateur avec accents, rendu visuel des toasts, F9 sans action parasite
  dans une appli tierce, téléchargement réel d'un modèle absent, droits admin
  nécessaires ou non pour le hook global `keyboard`. Ce terminal n'a pas
  d'accès à un environnement graphique Windows — c'est explicitement le rôle
  de l'utilisateur sur sa VM (voir DoD, cases laissées décochées avec note).
- Pas de test de la valeur réelle du délai `time.sleep(0.3)` avant restauration
  du presse-papier (patché à no-op dans les tests) — signalé par le rôle Code
  comme à ajuster en usage réel, toujours vrai.

**Sécurité vérifiée :**
- Pas d'auth ni de secrets. `keyboard.send`/`keyboard.write`/`pyperclip.copy`
  reçoivent le texte transcrit tel quel, jamais interprété par un shell
  (pas de `subprocess`/`os.system` dans ce fichier) — pas de surface
  d'injection. Le presse-papier précédent n'est gardé qu'en mémoire locale
  (variable `previous_clipboard`), jamais loggé ni persisté.

**Bugs trouvés :**
- **Non bloquant mais réel** : `main()` appelle
  `keyboard.add_hotkey(HOTKEY, toggle, suppress=True)` sans aucun
  `try/except`. Vérifié en installant `keyboard` dans un venv jetable et en
  lisant sa source : un nom de touche non reconnu fait lever
  `ValueError` par `key_to_scan_codes()` (appelée par `parse_hotkey`/
  `add_hotkey`). Si la clé `hotkey` du config.toml contient une valeur
  invalide (typo utilisateur), le process plante **au démarrage**, et comme
  il est lancé via `pythonw` (sans console), l'utilisateur ne voit strictement
  rien — contrairement à `load_model()` qui a explicitement été protégé pour
  cette même raison (voir décisions du rôle Code). Recouvrable en éditant le
  config, donc pas bloquant pour la validation, mais incohérent avec le soin
  apporté ailleurs dans ce ticket.

**Audit refactor : 5/10** — le découpage et la logique sont propres (validés
par les 14 tests ci-dessus), mais je recommande d'entourer l'appel à
`keyboard.add_hotkey()` dans `main()` d'un `try/except` qui notifie l'échec
et sort proprement, sur le même principe que `load_model()`. Risque concret
si non traité : un daemon Windows qui semble "ne rien faire" au lancement
sans aucun log visible (pythonw), pour un utilisateur qui aurait mal
recopié la syntaxe d'un hotkey personnalisé dans le TOML.

## ♻️ Refactor — 2026-07-03
**Changé :**
- `main()` dans `whisper_type_win.py` : l'appel `keyboard.add_hotkey(HOTKEY, toggle, suppress=True)`
  est maintenant entouré d'un `try/except`. En cas d'exception (touche
  invalide dans `config.toml`), on logge l'erreur, on notifie l'utilisateur
  (« Raccourci '<valeur>' invalide dans config.toml — voir les logs ») et on
  sort proprement de `main()` (`return`) sans jamais atteindre `keyboard.wait()`.
- Ajout de `tests/test_whisper_type_win.py::TestMain` (2 tests) : chemin
  nominal (hotkey enregistré, `keyboard.wait("ctrl+alt+q")` appelé, cleanup
  `recorder.abort()`/`keyboard.unhook_all()` en sortie) et chemin d'échec
  (hotkey invalide → notify explicite, pas de crash, pas d'attente engagée).

**Pourquoi :**
- Trouvaille du rôle Test : c'était le seul point d'entrée non protégé de ce
  fichier, incohérent avec `load_model()` qui suit déjà ce principe (avaler
  l'exception + notifier plutôt que planter silencieusement, car lancé via
  `pythonw` sans console — une exception non rattrapée ne laisse absolument
  aucune trace visible pour l'utilisateur).

**Risque :** faible — changement localisé (un seul appel entouré), suit un
patron déjà utilisé et testé ailleurs dans le même fichier. Pas de changement
de comportement sur le chemin nominal.

**Tests verts avant ET après :** oui — 46 tests verts avant, 48 après
(2 nouveaux dans `TestMain`), `.venv/bin/python -m pytest tests/ -q`.

## 🚀 Validation — 2026-07-03
**Lancé en dev :** Testé sur la VM Windows 10 réelle de l'utilisateur (premier
test réel de ce ticket sur Windows — jusqu'ici seulement des doubles/mocks
côté Linux) : dictée bout-en-bout confirmée (Notepad + champ de navigateur,
accents français), F9 toggle sans action parasite dans le navigateur, premier
lancement avec modèle absent → téléchargement réel + toast « chargement »
sans crash, hotkey pressé pendant le chargement → toast « réessayez » sans
crash. Un faux départ de debug a eu lieu (F9 semblait ne rien faire, aucun
toast, aucune activation micro) : cause réelle **hors code** — `hotkey` dans
`config.toml` avait été positionné sur une valeur résiduelle d'un test
antérieur (`ctrl+q`) au lieu du défaut `f9`. Pas un bug de l'app ; document
comme piste de faux positif pour un futur debug similaire.

**Lancé en prod :** Testé via l'exe packagé livré par TICKET-04 (build
PyInstaller réel téléchargé depuis la release GitHub, pas lancé depuis les
sources Python) — même comportement confirmé de bout en bout.

**DoD complète :** Oui, toutes les cases cochées.

**Statut final :** validated
