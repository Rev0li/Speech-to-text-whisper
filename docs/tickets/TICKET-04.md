---
ticket: TICKET-04
title: Packaging Windows — PyInstaller + release GitHub Actions
status: todo
branch: feat/ticket-04
updated: 2026-07-02
---

# TICKET-04 — Packaging Windows (.exe + release)

## 🎯 Objectif
Un artefact téléchargeable par des amis non-techniques : un zip contenant
`whisper-type.exe`, buildé automatiquement par GitHub Actions à chaque tag `v*`
et attaché à la release.

## 📎 Contexte (à lire avant de coder)
- **Dépend de TICKET-03** (`whisper_type_win.py` fonctionnel sur la VM Windows).
- Il n'y a **aucune** infra CI dans le repo (l'ancienne CI Tauri a été supprimée
  avec le commit `c262401`) : partir de zéro.

## 🔧 Décisions déjà prises (ne pas re-débattre)
- **PyInstaller `--onedir` + zip du dossier** — pas de `--onefile` : avec
  ctranslate2 embarqué, onefile = extraction lente à chaque lancement et plus de
  faux positifs antivirus. Options : `--noconsole`, nom `whisper-type`.
- **Le modèle Whisper n'est PAS embarqué** : téléchargé au premier lancement
  (~461 MB, cache HuggingFace) — le toast « chargement » de TICKET-03 couvre l'attente.
- **Workflow** `.github/workflows/release-windows.yml` : déclencheur tag `v*`,
  runner `windows-latest`, `pip install -r requirements-win.txt pyinstaller`
  → build → zip → upload en asset de release (`gh release upload` ou
  `softprops/action-gh-release`).
- **Pas de signature de code** (coût). En contrepartie : documenter le
  contournement SmartScreen dans le README (« More info → Run anyway »).

## ✅ Definition of Done
- [ ] Build PyInstaller local OK sur la VM Windows (l'exe se lance, la dictée fonctionne)
- [ ] Workflow GitHub Actions vert sur un tag de test
- [ ] Zip de release téléchargé « comme le ferait un ami » et testé sur la VM
- [ ] README : section Download avec lien release + note SmartScreen
- [ ] Taille du zip notée dans le handoff (attendu : 150-300 MB)

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
