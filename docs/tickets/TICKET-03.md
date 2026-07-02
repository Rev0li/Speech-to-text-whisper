---
ticket: TICKET-03
title: Entrée Windows — hotkey global, typing, notifications
status: todo
branch: feat/ticket-03
updated: 2026-07-02
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
- [ ] `whisper_type_win.py` + `requirements-win.txt`
- [ ] Testé sur la VM Windows : dictée dans Notepad ET dans un champ de navigateur, avec accents français
- [ ] F9 dans un navigateur toggle l'enregistrement SANS action parasite de l'app (ex. mode lecture Firefox)
- [ ] Premier lancement (modèle absent) → téléchargement + toast « chargement », pas de crash
- [ ] Hotkey pressé pendant le chargement du modèle → toast « réessayez », pas de crash
- [ ] Tests Linux toujours verts (`.venv/bin/python -m pytest tests/ -q`) + tests unitaires de la clé `hotkey` dans config
- [ ] Doc à jour (README : section dev Windows)

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
