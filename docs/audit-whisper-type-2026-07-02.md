---
type: audit-forme
scope: whisper-type
date: 2026-07-02
readiness: { navigation: ⚠️, fragmentation: ⚠️ }
---

# Audit forme — whisper-type — 2026-07-02

## Synthèse
Le code de production est exemplaire côté forme : 3 fichiers (`whisper_type.py` 183 l.,
`config.py` 40 l., 3 scripts shell courts), un fichier = un concept, noms explicites.
Ce qui bloque : le README date de l'ère Tauri abandonnée (commit `c262401`) et
contredit le code sur trois points clés (raccourci, choix du modèle, stack), et
~2 500 lignes de tests (≈80 % du volume du repo) vérifient des artefacts qui
n'existent plus. Une IA fraîche qui entre dans ce repo croit travailler sur une
app Tauri avec sidecar — c'est le principal frein au vibecoding.

| Axe | Note | En une phrase |
|---|---|---|
| Navigabilité & doc (IA) | ⚠️ | Le README existe et le flux daemon est juste, mais 3 sections sur 5 décrivent la stack Tauri disparue et le mauvais raccourci. |
| Fragmentation (humain)  | ⚠️ | Code prod parfaitement fragmenté, mais le corpus de tests mort noie la navigation. |

## Axe A — Navigabilité & doc

### Doc ↔ code
- **Section Tauri fantôme** — `README.md:32-49` (« Dev prerequisites (frontend / Tauri) »)
  décrit `src-tauri/`, `npm install`, `npm run dev`. Ni `src-tauri/`, ni `package.json`
  n'existent depuis le commit `c262401` (« drop Tauri, retour au daemon Python pur »).
- **Section Download trompeuse** — `README.md:9-19` promet des installeurs `.exe` /
  `.AppImage` : c'étaient les builds Tauri, le repo ne peut plus les produire.
- **Raccourci : 3 versions contradictoires** —
  - `README.md:64,70-71` : `SUPER + \``
  - `install.sh:40,48,69` : `SUPER + F9` (ce que le code installe réellement)
  - `toggle.sh:3` (commentaire) : `SUPER, SPACE`
- **Choix du modèle obsolète** — `README.md:77-82` documente `./start.sh tiny|base|…`,
  mais `start.sh` ne prend aucun argument : le modèle vient de
  `~/.config/whisper-type/config.toml` (`config.py:10-28`). **`config.toml` n'est
  mentionné nulle part dans le README** alors que c'est désormais LE point de config
  (modèle + langue, y compris `language = "auto"` déjà implémenté).
- **Roadmap périmée** — `README.md:86-101` : « Auto language detection » (v0.2) est
  déjà implémentée (`whisper_type.py:114`) ; v0.3/v1.0 décrivent tray/app native,
  soit la voie Tauri qui vient d'être abandonnée — à re-trancher.
- ✅ Le diagramme « How it works » (`README.md:105-114`) est, lui, exact et suffit
  à comprendre l'archi réelle en 10 lignes.

### Sommaire, plan d'archi, liens
- Pas de `docs/` avant cet audit, pas de `CLAUDE.md`. Vu la taille (223 lignes de
  prod), un README juste ferait office de plan d'archi — pas besoin de plus.
- Pas de liens Markdown internes → pas de liens morts.

## Axe B — Fragmentation & modularité
- ✅ **Code prod exemplaire** : `whisper_type.py` (183 l., daemon), `config.py`
  (40 l., config), `start.sh`/`stop.sh`/`toggle.sh` (cycle de vie). Rien à splitter.
- **Corpus de tests mort** — 10 fichiers de tests sur 12 (~2 500 lignes) testent
  l'ère Tauri : `tests/test_tauri_scaffold.py`, `test_release_build.py`,
  `test_linux_build.py`, `test_download.py`, `test_sidecar_ipc.py`,
  `test_overlay.py`, `test_settings.py`, `test_tray_static.py`,
  `test_hotkey_static.py`, `test_whisper_type_win.py`. Ils référencent des chemins
  disparus (`src-tauri/binaries`, `src-tauri/target/`). C'est du bruit de
  navigation massif : en volume, le repo « ressemble » à un projet Tauri.
  *(Signalé, pas tranché : à toi de décider si c'est de la référence à garder —
  p.ex. dans une branche/tag — ou à supprimer.)*
- **Import mort** — `whisper_type.py:19` : `import json` inutilisé.
- **Shebangs machine-spécifiques** — `whisper_type.py:1` et `config.py:1` codent en
  dur `/home/rev0li/dev/outils/whisper-type/.venv/bin/python3`. `start.sh` passe déjà par
  `$DIR/.venv/bin/python3`, donc le shebang absolu est redondant ET casse le clone
  sur une autre machine/un autre chemin.
- **Commentaire trompeur** — `toggle.sh:3` code en dur un chemin absolu
  `/home/rev0li/...` et le mauvais bind (voir Axe A).

## Plan d'amélioration

### P1 — à faire d'abord
- **Constat** : README aux ⅗ obsolète (sections Tauri/Download, raccourci, modèle).
  **Gêne** : les deux — l'IA part sur la mauvaise stack, l'humain suit des commandes qui ne font rien.
  **Action** : réécrire le README autour du daemon pur : supprimer sections Tauri/Download, documenter `config.toml`, unifier le raccourci sur `SUPER+F9` (ou celui voulu), rafraîchir la roadmap.
  **Effort** : S
- **Constat** : ~2 500 lignes de tests d'artefacts Tauri disparus (10 fichiers listés en Axe B).
  **Gêne** : les deux — 80 % du volume du repo pointe vers une architecture morte.
  **Action** : décider du sort (suppression, ou archivage dans un tag/branche `tauri-era`) puis purger `tests/` pour ne garder que `test_config.py` + `conftest.py` (et écrire de vrais tests du daemon si souhaité).
  **Effort** : S (suppression) / M (si réécriture de tests daemon)

### P2 — ensuite
- **Constat** : shebangs absolus `/home/rev0li/...` dans `whisper_type.py:1` et `config.py:1`.
  **Gêne** : humain (install sur une autre machine) et IA (suggère un mauvais pattern).
  **Action** : `#!/usr/bin/env python3` (le venv est déjà résolu par `start.sh`) ; même nettoyage pour le commentaire de `toggle.sh:3`.
  **Effort** : S
- **Constat** : pas de `CLAUDE.md`.
  **Gêne** : IA (léger — le projet est petit).
  **Action** : 10 lignes : stack (daemon Python + signaux), les 5 fichiers et leur rôle, la config, la commande de test.
  **Effort** : S

### P3 — confort
- **Constat** : `import json` mort (`whisper_type.py:19`).
  **Action** : supprimer.
  **Effort** : S
- **Constat** : roadmap README à re-trancher après l'abandon de Tauri (garder v0.2/v0.3 ? nouvelle cible ?).
  **Action** : décision produit, puis mise à jour (fusionnable avec le P1 README).
  **Effort** : S

## Pour la suite
Deux tickets suffisent : **(1)** « README + roadmap post-Tauri » (P1.1 + P2.2 + P3.2,
tout est de la doc, une session), **(2)** « Purge tests Tauri » (P1.2 + P3.1, après
ta décision garder/archiver/supprimer). Le P2 shebangs peut se glisser dans l'un ou
l'autre. À piloter via [ticket-handoff].
