---
ticket: TICKET-04
title: Packaging Windows — PyInstaller + release GitHub Actions
status: validated
branch: feat/ticket-04
updated: 2026-07-03
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
- [x] Build PyInstaller local OK sur la VM Windows (l'exe se lance, la dictée fonctionne)
- [x] Workflow GitHub Actions vert sur un tag de test
- [x] Zip de release téléchargé « comme le ferait un ami » et testé sur la VM
- [x] README : section Download avec lien release + note SmartScreen (+ note Defender/quarantaine + tuto changement de hotkey, ajoutés en Test)
- [x] Taille du zip notée dans le handoff (attendu : 150-300 MB) — **~90 MiB réel (94 342 867 octets)**, en dessous de l'estimation, sans impact fonctionnel constaté

---

## 🔨 Code — 2026-07-03
**Fait :**
- `.github/workflows/release-windows.yml` : déclenché sur tag `v*` (+
  `workflow_dispatch` pour rejouer sans retagger), `windows-latest`,
  `pip install -r requirements-win.txt pyinstaller`, build `--onedir`
  `--noconsole` de `whisper_type_win.py` nommé `whisper-type`, zip du dossier
  (`Compress-Archive`), upload en asset de release via
  `softprops/action-gh-release@v2`.
- `.gitignore` : ajout de `build/`, `dist/`, `*.spec` (artefacts PyInstaller
  générés par un build local, notamment celui que le rôle Test devra faire
  sur la VM Windows).
- README : nouvelle section « Download (Windows) » (lien Releases, étapes
  extraction/lancement, note SmartScreen « More info → Run anyway ») +
  ligne « Project layout » pour le workflow + note SmartScreen de la Roadmap
  reformulée pour pointer vers cette section au lieu de la dupliquer.

**Décisions (& pourquoi) :**
- **`--collect-all winotify` ajouté** en plus des trois `--collect-all` déjà
  actés dans le ticket (`faster_whisper`, `ctranslate2`, `sounddevice`) — non
  discuté dans les décisions initiales, mais `winotify` n'est utilisé par
  aucun autre ticket packagé avec PyInstaller dans l'historique de ce repo
  (l'ancien `release.yml` Tauri excluait explicitement `keyboard` et n'avait
  jamais empaqueté de lib de toast Windows). Par prudence — les toasts sont
  la seule façon dont l'utilisateur voit "chargement"/"prêt"/"erreur", un
  échec silencieux de PyInstaller à embarquer ses assets serait un régression
  invisible — ajouté en préventif. Coût : quelques Mo de plus dans le zip.
  **À vérifier en priorité par le rôle Test/VM** : si le toast s'affiche bien
  depuis l'exe packagé, ce flag est confirmé utile ; sinon il est inoffensif
  et peut rester ou sauter selon ce qui est observé.
- **`workflow_dispatch` ajouté en plus du trigger sur tag `v*`** — pas dans
  les décisions actées du ticket, mais sert directement le DoD "Workflow
  GitHub Actions vert sur un tag de test" : permet de relancer le build sans
  pousser un nouveau tag à chaque itération de debug CI. Coût nul (une ligne).
- **Zip du dossier entier (`Compress-Archive -Path dist/whisper-type`, pas
  `dist/whisper-type/*`)** : à l'extraction, l'utilisateur récupère un
  dossier `whisper-type/` contenant l'exe + DLL, pas les DLL éparpillées
  directement dans son dossier de Téléchargements.
- **Pas de code signing** (déjà acté dans le ticket) — confirmé : le README
  documente le contournement SmartScreen plutôt que d'introduire une
  dépendance à un service de signature payant, cohérent avec l'abandon de
  SignPath au moment du drop de Tauri (`c262401`).

**Fichiers :**
- `.github/workflows/release-windows.yml` (nouveau)
- `.gitignore` (artefacts PyInstaller)
- `README.md` (section Download, Project layout, Roadmap)

**Reste / questions pour le test :**
- **Branché sur `feat/ticket-03`, pas sur `releases-windows`** — TICKET-04
  a besoin de `whisper_type_win.py`/`requirements-win.txt` qui n'existent que
  sur `feat/ticket-03` (statut `refactored`, pas encore `validated`/mergé).
  L'utilisateur a explicitement demandé de contourner la précondition
  habituelle ("TICKET-04 dépend de TICKET-03 fonctionnel sur la VM") : les
  deux seront testés ensemble sur la VM Windows après ce ticket, pas en deux
  passes séparées. Le rôle Validation de TICKET-04 devra donc valider (ou
  faire valider) TICKET-03 en même temps — ne pas merger TICKET-04 seul si
  TICKET-03 reste non-validated à ce moment-là.
- **Aucun build PyInstaller réel exécuté** dans cette session (pas d'accès
  Windows ; PyInstaller ne cross-compile pas depuis Linux vers Windows) —
  seule la syntaxe YAML du workflow a été validée (`yaml.safe_load`), pas son
  exécution. Tout le reste de la DoD (build local VM, run CI sur tag,
  téléchargement/test du zip, taille du zip) est donc intact et à faire.
- **Tag de test non poussé** : déclencher le workflow réclame de pousser un
  tag `v*` sur le remote, ce qui publie une vraie release GitHub (action
  visible/partagée) — pas fait sans confirmation explicite de l'utilisateur.
  À décider avec lui avant que quiconque (terminal ou humain) le fasse.
- Le nom exact de l'exe généré dépend de `--name whisper-type` : à confirmer
  que `dist/whisper-type/whisper-type.exe` est bien le chemin réel une fois
  un build fait (PyInstaller peut varier selon la version installée).

## 🧪 Test — 2026-07-03
**Couvert :**
- Workflow réellement exécuté (pas juste `yaml.safe_load`) via un tag de test
  `v0.2.0-rc1` poussé avec l'accord explicite de l'utilisateur : run vert en
  **1m28s** sur `windows-latest`, tous les steps OK (checkout, setup Python,
  install deps + PyInstaller, build, zip, upload en asset de release).
- Zip `whisper-type-windows.zip` téléchargé depuis cette release et testé sur
  la VM Windows 10 réelle de l'utilisateur **exactement comme le ferait un
  ami** : dossier dédié créé, extraction, lancement de `whisper-type.exe`,
  dictée bout-en-bout confirmée (voir [TICKET-03](TICKET-03.md) Validation
  pour le détail fonctionnel).
- Taille du zip : **94 342 867 octets (~90 MiB)** — en dessous de l'estimation
  du ticket (150-300 MB), mais aucun fichier manquant constaté à l'usage réel
  (le modèle Whisper n'étant de toute façon pas embarqué).
- `--collect-all winotify` (ajouté par précaution par le rôle Code, non acté
  dans les décisions initiales) confirmé **utile** : les toasts s'affichent
  correctement depuis l'exe packagé.

**NON couvert (assumé) :**
- Pas de smoke test automatisé dans la CI elle-même (ex. lancer l'exe généré
  et vérifier qu'il démarre, dans le runner `windows-latest`) — toute la
  vérification fonctionnelle est manuelle, sur la VM de l'utilisateur.
- Signature de code : explorée puis abandonnée par choix explicite de
  l'utilisateur (voir Bugs trouvés) — pas un trou de couverture, une décision
  produit.

**Sécurité vérifiée :**
- Aucun secret embarqué dans l'artefact généré. `SIGNPATH_API_TOKEN` (secret)
  et `SIGNPATH_ORG_ID` (variable) existent dans les settings du repo GitHub
  mais ne sont référencés par aucune étape active du workflow (l'étape de
  signature a été ajoutée puis retirée, voir Bugs trouvés) — rien à nettoyer
  côté secrets, ils ne sont juste pas utilisés pour l'instant.

**Bugs trouvés :**
- **Réel, non-bloquant (mitigé par doc, pas par le code)** : Windows Defender
  détecte l'exe PyInstaller non signé comme `Trojan:Script/Wacatac.B!ml`
  (« Severe ») et le **supprime silencieusement** dès l'extraction/premier
  lancement — confirmé par une capture d'écran de Windows Security sur la VM
  de test. C'est un faux positif ML très répandu sur les binaires PyInstaller
  non signés (rien de spécifique à ce projet), mais l'impact UX est réel :
  un ami non-technique voyant « this program is dangerous and executes
  commands from an attacker » abandonnera probablement avant de chercher une
  solution. Piste de signature via SignPath explorée (le projet avait déjà
  un compte + une policy `release-signing` réutilisée de l'ancienne CI Tauri,
  secrets déjà en place) : un certificat de test auto-signé a été identifié
  (`whisper-type-test`, `Creation method: Self-signed certificate`) — inutile
  contre Defender/SmartScreen sans passer par la vraie demande de certificat
  Open Source sur signpath.org. L'utilisateur a explicitement renoncé à cette
  démarche (trop lourde pour un simple partage entre amis). **Mitigé par la
  doc** : README mis à jour (section Download) avec instructions précises —
  créer un dossier dédié, ajouter une exclusion Windows Defender **avant**
  extraction, et comment restaurer un fichier déjà mis en quarantaine.
- Pas de bug de code applicatif trouvé dans cette passe. Une fausse alerte a
  eu lieu pendant le test (F9 semblait ne rien faire du tout) — cause réelle :
  une valeur `hotkey` résiduelle (`ctrl+q`) dans le `config.toml` de la VM,
  pas un défaut du packaging ni du code (détail dans TICKET-03 Validation).

**Audit refactor : 1/10** — ce ticket touche uniquement de la config CI
(YAML) et de la doc, pas de logique applicative. Le workflow est simple, un
seul job, pas de duplication ni de code mort. Aucun refactor nécessaire,
passage direct à la validation.

## 🚀 Validation — 2026-07-03
**Lancé en dev :** Workflow testé via le tag non-officiel `v0.2.0-rc1` (à
nettoyer après validation, remplacé par le vrai tag `v1.0.0`) — run GitHub
Actions vert en 1m28s, zip généré et uploadé correctement comme asset de la
release correspondante.

**Lancé en prod :** Zip de cette release de test téléchargé et exécuté sur la
VM Windows 10 réelle de l'utilisateur comme le ferait un ami (dossier dédié,
exclusion Windows Defender après avoir observé la quarantaine
`Trojan:Script/Wacatac.B!ml`, extraction, lancement, dictée bout-en-bout) —
confirmé fonctionnel. Le vrai tag `v1.0.0` sera poussé juste après cette
validation, une fois mergé dans `releases-windows`.

**DoD complète :** Oui, toutes les cases cochées (voir ci-dessus).

**Statut final :** validated
