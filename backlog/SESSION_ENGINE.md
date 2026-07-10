# SESSION ENGINE — Moutilloux

> **Comment déclencher :** ce fichier est le prompt d'une Routine Claude Code **locale**.
> Routine configurée sur claude.ai/code/routines → type **Local** — s'exécute sur la machine de l'utilisateur (credentials git locaux + auth GitHub MCP locale).
> Prompt à utiliser : `Le repo est /Users/maximelorin/Desktop/dev/moutilloux — Lis le fichier backlog/SESSION_ENGINE.md et exécute le protocole complet (étapes 0 à 4).`

---

## 1. Contexte du projet

**Moutilloux** est une application Django de gestion de tournoi de tennis.
- Backend : Django (moteur de score, classements, bracket, rôle Arbitre)
- Frontend : SPA Vue 3 + Vite + TypeScript + Pinia + Vue Router
- Repo GitHub : `sirius911/moutilloux`
- Racine locale (repo cloné) : identifiée via `git rev-parse --show-toplevel`

**Règle d'or :** on n'écrit aucune logique métier. On expose et on branche.
Les specs décrivent ce qui **doit** être. Le code décrit ce qui **est**. La session corrige l'écart.

**Tickets et sprints :** gérés dans GitHub Issues + Milestones (repo sirius911/moutilloux).
Toutes les opérations GitHub passent par le CLI `gh` (authentifié via keyring ArtSkamos).

---

## 2. Structure des fichiers

```
backlog/
├── SESSION_ENGINE.md           ← ce fichier (prompt de la Routine)
├── logs/                       ← un log par session
│   └── session_YYYY-MM-DD_N.md
├── plan/                       ← plans d'implémentation (NNN-titre.md, non versionnés)
└── sprints/
    ├── roadmap.md              ← index ordonné des sprints (premier = actif)
    ├── NN-nom/
    │   ├── sprint.md           ← métadonnées du sprint (specs, modules, branche git)
    │   └── log.md              ← log des spec reviews (une ligne par session)
    └── done/
        └── NN-nom/             ← dossier sprint archivé en fin de sprint

specs/
├── INDEX.md
├── screens/
├── transverse/
├── technical/
└── need_spec/
```

---

## 3. Protocole d'exécution

### Étape 0 — Lecture du contexte

```bash
REPO="$(git rev-parse --show-toplevel)"
```

Lire `$REPO/backlog/sprints/roadmap.md`.

**Si la liste est vide ou le fichier absent** → noter dans le log :
_"Roadmap vide — tous les sprints terminés. Désactiver la Routine manuellement sur claude.ai/code/routines."_
Puis s'arrêter.

**Sinon** → prendre le **premier sprint de la liste**, lire son fichier `NN-nom/sprint.md`.
Retenir : numéro de sprint (`SPRINT_N`), nom, specs, modules, tag tickets (`SPRINT_TAG`),
chemin du log, champ `branche:`.

**Convention de nommage :** toutes les branches sprint utilisent le préfixe `claude/`
(ex : `claude/sprint/03-admin-shell`). Ce préfixe est requis pour que la Routine
puisse pusher sans permission spéciale.

**Git — résolution du parent effectif :**

Le parent est déduit depuis `backlog/sprints/done/` — la source de vérité est l'ordre
de la roadmap, pas le champ `branche-parent:` du frontmatter.

```bash
git fetch origin

PREV_BRANCH="main"
for d in $(ls "$REPO/backlog/sprints/done/" 2>/dev/null | sort -V); do
  PREV_N=$(grep "^sprint:" "$REPO/backlog/sprints/done/$d/sprint.md" 2>/dev/null | awk '{print $2}')
  if [ -n "$PREV_N" ] && [ "$PREV_N" -lt "$SPRINT_N" ]; then
    B=$(grep "^branche:" "$REPO/backlog/sprints/done/$d/sprint.md" 2>/dev/null | awk '{print $2}')
    [ -n "$B" ] && PREV_BRANCH="$B"
  fi
done

if [ "$PREV_BRANCH" = "main" ] \
  || ! git ls-remote --exit-code origin "$PREV_BRANCH" > /dev/null 2>&1 \
  || git merge-base --is-ancestor "origin/$PREV_BRANCH" origin/main > /dev/null 2>&1; then
  PARENT="main"
else
  PARENT="$PREV_BRANCH"
fi
```

**Git — checkout de la branche sprint :**
```bash
git checkout <branche> 2>/dev/null \
  || git checkout -b <branche> origin/$PARENT
```

**Git — synchronisation avec le parent effectif :**
```bash
git merge origin/$PARENT --no-edit
```
Si conflit → noter dans le log (`## Problèmes d'orchestration`), ne pas continuer.

**Git — working tree sale :**
```bash
git status --porcelain
```
Si non vide → commiter avant de continuer :
```bash
git add -A && git commit -m "sprint-NN 🚧 Session précédente interrompue — état sauvegardé"
```

### Étape 1 — Spec Review

Pour chaque spec listée dans le `sprint.md` courant (champ `specs:`) :
1. Lire la spec (`specs/screens/…` ou `specs/transverse/…`)
2. Lire les fichiers listés dans le champ `fichiers:` de l'en-tête YAML de la spec
3. Comparer spec ↔ code point par point
4. Verdict : `✅ Conforme` / `⚠️ Dérive mineure` / `❌ Dérive bloquante`
5. Pour chaque dérive : noter ce que dit la spec, ce que fait le code, la sévérité (🔴/🟠/🟡)

> L'agent ne modifie aucun fichier — lecture seule.

**Après la review :**

Pour chaque dérive non encore ticketée dans GitHub Issues :
- Déterminer le prochain numéro : `gh issue list --repo sirius911/moutilloux --state all --json number | jq 'map(.number) | max + 1'`
- Créer l'issue :
  ```bash
  gh issue create --repo sirius911/moutilloux \
    --title "NNN — Description courte" \
    --body "description de la dérive (spec vs code, sévérité, fichiers concernés)" \
    --label "majeure,dérive,sprint-NN" \
    --milestone "Sprint NN — Nom du sprint"
  ```
- Si une dérive correspond à une issue existante encore ouverte → ne pas créer de doublon

**Appender** une ligne dans `backlog/sprints/NN-nom/log.md` :
```
| #N | YYYY-MM-DD | ✅/⚠️/❌ | X dérives | X nouvelles issues | X issues sprint restantes |
```

### Étape 2 — Backlog Engine (séquentiel, max 2 tickets)

Lister les tickets à traiter :
```bash
gh issue list --repo sirius911/moutilloux \
  --milestone "Sprint NN — Nom du sprint" \
  --state open --json number,title,labels
```
- Ordre : d'abord les issues avec label `à-reprendre`, ensuite par sévérité (`majeure` avant `mineure`)
- **Exclure** les issues avec label `en-attente`
- Max 2 issues par session

Pour chaque issue (une par une, séquentiel) :

#### 2a — Planification

Un agent :
- Lit le body de l'issue GitHub pour comprendre le problème
- Lit les fichiers source concernés (mentionnés dans l'issue)
- Si spec source indiquée → lire la spec avant de planifier
- Produit `backlog/plan/NNN-titre.md` selon le format :

```markdown
# Plan — NNN : Titre

## Contexte
[Résumé du problème et fichiers concernés]

## Modifications prévues
[Fichiers à modifier et ce qui change]

## Fichiers partagés à câbler par l'orchestrateur
[Si applicable]

## Specs impactées
[Si des fichiers couverts par une spec sont modifiés :]
- `specs/screens/admin-shell.md` — [ce qui change]
> Si renseigné → agent de maintenance de spec après implémentation.
```

#### 2b — Implémentation

Un agent :
- Lit `backlog/plan/NNN-titre.md`
- Applique les modifications
- **Ne touche PAS** (réservés à l'orchestrateur) :
  - `live/urls.py`
  - `frontend/app/src/router/index.ts`
  - `frontend/app/src/stores/auth.ts`, `event.ts`, `live.ts`
  - `frontend/app/src/composables/useApi.ts`, `usePolling.ts`
  - `frontend/app/src/main.ts`
- Signale si un fichier partagé doit être modifié

Après l'agent : l'orchestrateur câble les fichiers partagés si nécessaire.
Si `## Specs impactées` renseigné → un agent de maintenance met à jour uniquement
le champ `fichiers:` de l'en-tête YAML de la spec (jamais le contenu).

#### 2c — Review

Un agent :
- Lit le plan, les fichiers modifiés, les fichiers de contexte
- Verdict : `✅ Approuvé` / `⚠️ Approuvé avec réserves` / `❌ À corriger`

**Si `✅` ou `⚠️` :**
```bash
gh issue close NNN --repo sirius911/moutilloux \
  --comment "Verdict : ✅ Approuvé. Fichiers modifiés : ..."
```

**Si `❌` :**
```bash
gh issue edit NNN --repo sirius911/moutilloux --add-label "à-reprendre"
gh issue comment NNN --repo sirius911/moutilloux \
  --body "Problème : ... Piste : ..."
```
- Ajouter à la fin de `backlog/plan/NNN-titre.md` :

```markdown
---
## ❌ Problème bloquant — [YYYY-MM-DD session N]
**Verdict :** [verdict complet]
**Problème(s) :** [description]
**Piste :** [suggestion]
> Ce plan sera relu intégralement lors de la reprise.
```

**Si le reviewer découvre un nouveau problème :**
- Créer une GitHub Issue (labels appropriés, milestone sprint courant si pertinent)

**Si l'implémentation révèle un besoin de spec :**
- Créer `specs/need_spec/NNN-titre.md`
- Créer une GitHub Issue avec label `en-attente`

**Dans tous les cas — commit git (après verdict et câblage des fichiers partagés) :**

| Verdict | Emoji commit |
|---------|-------------|
| ✅ Approuvé | ✅ |
| ⚠️ Approuvé avec réserves | ⚠️ |
| ❌ À corriger | 🚧 |

```bash
git add -A && git commit -m "NN-NNN :emoji: Titre court du ticket (~50 car.)"
```

Exemple : `03-055 ✅ AdminLayout : entrée Config sidebar supprimée`

→ Passer au ticket suivant.

### Étape 3 — Vérification de fin de sprint

Après les 6 tickets, vérifier :
- La spec review de cette session a rendu `✅ Conforme` sur toutes les specs du sprint
- ET aucune issue ouverte avec le milestone du sprint courant (hors label `en-attente`)

**Si les deux conditions sont remplies :**
- Fermer le milestone :
  ```bash
  MILESTONE_N=$(gh api repos/sirius911/moutilloux/milestones \
    --jq ".[] | select(.title == \"Sprint NN — Nom\") | .number")
  gh api repos/sirius911/moutilloux/milestones/$MILESTONE_N \
    -X PATCH -f state=closed
  ```
- Supprimer la ligne du sprint dans `backlog/sprints/roadmap.md`
- Déplacer le dossier `NN-nom/` dans `backlog/sprints/done/`
- Écrire dans le log de session : _"Sprint NN terminé — specs conformes, milestone fermé."_
- Lire à nouveau `roadmap.md` :
  - S'il reste des sprints → noter dans le log que le sprint suivant sera traité à la **prochaine échéance planifiée**. Ne pas démarrer le sprint suivant dans la même session.
  - Si vide → noter : _"Roadmap vide. Désactiver la Routine manuellement sur claude.ai/code/routines."_

**Sinon :** continuer — la prochaine échéance relancera automatiquement.

### Étape 4 — Log de session

Créer `backlog/logs/session_YYYY-MM-DD_N.md` :

```markdown
# Session YYYY-MM-DD — N°X

**Sprint actif :** NN — Nom
**Tickets traités :** N

## Spec Review
| Spec | Verdict | Nouvelles dérives |
|------|---------|------------------|

## Tickets clôturés
| # | Titre | Verdict |
|---|-------|---------|

## Nouveaux tickets créés
| # | Titre | Sévérité |
|---|-------|----------|

## Tickets à reprendre
| # | Titre | Raison |
|---|-------|--------|

## Fichiers partagés câblés
- `live/urls.py` : …

## Problèmes d'orchestration
[Tout ce qui a dévié du protocole]

## Git
- Branche : `<branche>`
- Parent effectif : `main` / `claude/sprint/NN-nom`
- Push : ✅ succès

| Hash court | Message du commit |
|-----------|------------------|
| `abc1234` | 03-055 ✅ AdminLayout : entrée Config sidebar supprimée |
```

Mettre à jour la **section 6** de ce fichier (`SESSION_ENGINE.md`).

**Git — push final (SSH, credentials locaux) :**
```bash
git push origin <branche>
```

**PR — création automatique si absente :**

Après le push, et seulement si le sprint est encore dans `backlog/sprints/roadmap.md` :
```bash
OPEN_PR=$(gh pr list --repo sirius911/moutilloux \
  --head <branche> --state open --json number -q '.[0].number')

if [ -z "$OPEN_PR" ]; then
  gh pr create --repo sirius911/moutilloux \
    --base main \
    --head <branche> \
    --title "Sprint NN — Nom du sprint" \
    --body "Travail en cours — généré automatiquement par la Routine SESSION_ENGINE."
fi
```

Si le PR existe déjà → ne rien faire (il accumule les commits au fil des sessions).

---

## 4. Règles strictes

- **Séquentiel.** Un ticket complètement terminé (plan → implem → review) avant le suivant.
- **Un agent = un ticket.** Jamais un agent qui touche les fichiers d'un autre ticket.
- **Fichiers partagés = orchestrateur uniquement** (voir liste à l'étape 2b).
- **Specs = lecture seule pour tous les agents**, sauf l'agent de maintenance (champ `fichiers:` uniquement).
- **Issues `en-attente` = jamais sélectionnées** par le backlog engine.
- **Pas de logique métier Django à réécrire.** Extraire et exposer uniquement.
- Si un agent ne trouve pas un fichier cité dans le plan → il signale et s'arrête.

---

## 5. Démarrage rapide

```
Lis le fichier `backlog/SESSION_ENGINE.md` dans ce repo
et exécute le protocole complet (étapes 0 à 4).
```

---

## 6. État de la dernière session

> Mis à jour automatiquement en fin de session.

**Dernière session :** 2026-07-10 — Session #159
**Sprint traité :** 42 — TV : score broadcast et phase en grand
(3ᵉ session du sprint — **clos cette session**, 5/5 tickets clos).

**Git :** branche `claude/sprint/42-tv-score-broadcast`, parent effectif
`claude/sprint/41-joueurs-photo-camera` (inchangé depuis la session #157).
2 commits de code cette session.

**Point d'attention protocole — session #158 interrompue avant sa clôture,
découverte au démarrage :** au démarrage de cette session, le working tree
était propre et la branche déjà la bonne (pas de checkout à faire — étape 0
en apparence triviale), mais `gh issue list` a révélé que le ticket `#362`
était déjà fermé et `git log` a montré un commit `9bab571` non poussé
(« 42-362 ✅ … ») que ni `backlog/logs/` ni la section 6 de ce fichier ne
documentaient encore. Contrairement au pattern habituel (session #65,
`feedback_interrupted_session_log`), **aucun fichier de log n'existait même
à l'état de brouillon non suivi** — l'interruption a eu lieu avant l'étape 4
tout entière. Reconstitué a posteriori comme session #158
(`backlog/logs/session_2026-07-10_158.md`) à partir de l'historique git et
du commentaire de clôture GitHub de `#362`, puis poursuite normale du
protocole (spec review fraîche, pas de présomption que le travail de fond
restant était fait). Aucune perte de travail : le code utile était déjà
committé et l'issue déjà fermée avant la coupure.

**Spec review session #159 :** `tv-live.md` et `tv-state.md` — ⚠️ Dérive
mineure en début de session (2 dérives restantes : `types/index.ts`
conservait la variante `kind: 'bracket'` morte dans `TvStake` ;
`.stake-panel`/`.stage-banner` centrés verticalement sans borne liée à la
bande de score réelle, chevauchement possible pour une poule à standings
nombreux) → **✅ Conforme** après implémentation des deux derniers tickets
du sprint cette session. Les deux dérives correspondaient exactement aux
issues déjà ouvertes `#364`/`#365` — 0 nouvelle issue créée.

**Backlog engine session #159 :** 2 tickets traités séquentiellement :
- **#364** (mineure, `infra`) — fichier partagé `frontend/app/src/types/index.ts`,
  traité **directement par l'orchestrateur** (pattern `#337`/`#341`/`#350` —
  aucun écran concerné, pas d'agent `vue-screen`) : union `TvStake` réduite
  à la seule variante `{ kind: 'group'; groupName; eventName; standings }`.
  `Bracket` reste utilisé ailleurs dans le fichier (`AdminBracketData`),
  aucune référence orpheline. `npx vue-tsc --noEmit` : 0 erreur.
- **#365** (mineure) — front : `TvScoreboard.vue` (agent `vue-screen`) —
  `.stake-panel` et `.stage-banner` étaient centrés verticalement
  (`top: 50%` + `translateY(-50%)`) sans borne liée à la position réelle de
  la bande de score broadcast (`.sb-ed-bottom`, bord haut réel calculé
  ≈643px) ; `.stake-panel` avait `max-height: 620px`, permettant à son bord
  bas de descendre jusqu'à ≈850px pour une poule à standings nombreux —
  recouvrement des lignes joueurs, la dérive documentée par le ticket depuis
  les retours du 2026-07-10 (jamais corrigée sur le panneau de poule
  lui-même, seulement sur l'ex-variante bracket par `#361`/`#362`). Fix :
  ancrage borné `top: 140px` / `bottom: 460px` sur les deux règles, flex de
  centrage interne, `max-height` retiré (remplacé par la borne `bottom`),
  `overflow-y: auto` en garde-fou. Reviewer : géométrie recalculée
  indépendamment (marge ≈23px avec `.sb-ed-bottom`, non nulle ; aucun
  chevauchement horizontal avec `.tv-prep` ; poule à 6 joueurs ≈364px de
  contenu, tient sans scroll dans la zone bornée de 480px), template non
  touché, `npx vue-tsc --noEmit` 0 erreur. Verdict : ✅ Approuvé, deux
  remarques cosmétiques non bloquantes (marge de clearance volontairement
  fine ; piège flexbox `overflow-y:auto`+`justify-content:center` théorique
  mais non déclenchable avec le nombre réaliste de joueurs par poule).

**Sprint 42 clos cette session :** les deux conditions étaient réunies (specs
`tv-live.md`/`tv-state.md` conformes sur les sections ciblées par le sprint +
0 issue ouverte sur le milestone). Milestone GitHub (numéro 41) fermé,
dossier déplacé vers `backlog/sprints/done/42-tv-score-broadcast/`, ligne
retirée de `backlog/sprints/roadmap.md`.

**Roadmap vide.** Aucun sprint suivant en attente — **désactiver la Routine
manuellement sur claude.ai/code/routines**, ou planifier un nouveau sprint
(`/plan-sprint`) avant la prochaine échéance.

**Point d'attention outillage :** `npx vue-tsc --noEmit` toujours fiable
pour les deux tickets (aucune nouvelle erreur). Toujours pas de script
`type-check`/`lint` dans `package.json`, toujours pas de
`.claude/launch.json` côté front — vérification par type-check + revue de
code uniquement (pas de QA navigateur TV réelle en session automatisée, la
géométrie CSS de `#365` a été vérifiée par calcul analytique sur les
propriétés CSS réelles, pas par rendu). Aucune maquette `.jsx` de référence
pour `#364`/`#365` (retours produit récents, pas dans `frontend/design/`).

**Point d'attention protocole (reviewer) :** l'agent `reviewer` invoqué cette
session a de nouveau strictement respecté son mandat de lecture seule
(confirmation explicite dans son rapport, vérifié via `git status`/`git diff`
avant/après invocation) — pattern désormais stable sur au moins 15 sessions
consécutives (#140-#159, sessions à vide comprises) depuis l'incident initial
de la session #139.

**Observation annexe (signalée depuis la session #144, toujours non
actionnée) :** deux dossiers de sprint orphelins subsistent dans
`backlog/sprints/` — hors de `done/` et non référencés par `roadmap.md`
(désormais vide par ailleurs) : `04-admin-panel-map/` et `10-contexte-url/`.
À investiguer par l'utilisateur avant de les considérer comme travail
réellement en attente ou comme reliquats à archiver.

Log complet : `backlog/logs/session_2026-07-10_159.md` (voir aussi
`backlog/logs/session_2026-07-10_158.md`, reconstitué a posteriori pour la
session interrompue).

---

**Historique — session #157 :**
**Sprint traité :** 42 — TV : score broadcast et phase en grand
(1ère session du sprint, roadmap regarnie juste avant cette session par la
planification du sprint 42 sur les retours TV du 2026-07-10). 2/5 tickets
clos — `#362`, `#364`, `#365` restants.

**Git :** branche `claude/sprint/42-tv-score-broadcast` (nouvelle branche
cette session), parent effectif `claude/sprint/41-joueurs-photo-camera`
(sprint 41 toujours non mergé dans `main`, déduit depuis
`backlog/sprints/done/`). 3 commits de code cette session (1 commit de
rattrapage de working tree sale + 2 tickets).

**Point d'attention protocole — working tree sale au démarrage, sur
l'ancienne branche :** au démarrage de la session, la branche encore
checked-out localement était `claude/sprint/41-joueurs-photo-camera`
(sprint déjà clos et archivé depuis la session #152), avec 2 fichiers
modifiés non commités et d'origine inconnue (aucun rapport avec le sprint
41 ni le sprint 42) : `frontend/app/src/components/modals/AddPlayerModal.vue`
(un refetch du registre après upload photo en édition) et
`live/api_views.py` (sérialisation JSON de `attitudes` dans
`api_player_edit`, contournement d'un piège `forms.JSONField` sur liste
vide). Traité conformément au protocole (étape 0, working tree sale) :
commit `🚧 Session précédente interrompue` **après** le checkout de la
nouvelle branche 42 (les modifications ont donc été portées sur la branche
42 avant le premier ticket) — ces deux correctifs seront inclus dans la PR
du sprint 42, bien qu'étrangers à son périmètre. À signaler à l'utilisateur.

**Spec review session #157 :** `tv-live.md` et `tv-state.md` — ⚠️ Dérive
mineure en début de session (3 dérives : bande de score encore
centrée/une-seule-ligne au lieu de deux lignes par joueur ; `stake-panel`
conserve la variante mini-tableau `kind: 'bracket'` en template ;
`_pack_tv_stake` renvoie toujours cette variante bracket) → dérive
partiellement résorbée par les deux tickets de cette session
(`#361`/`#363`), le reste (retrait front du mini-tableau et de son type)
attendu pour `#362`/`#364` avant `✅ Conforme`. Les 3 dérives relevées
correspondaient exactement aux issues déjà ouvertes lors de la
planification du sprint — 0 nouvelle issue créée.

**Backlog engine session #157 :** 2 tickets traités séquentiellement
(chaîne plan → agent → `reviewer` par ticket), conformément à l'ordre de
sévérité (les deux majeures disjointes en fichiers, traitées l'une après
l'autre malgré leur parallélisabilité suggérée par `sprint.md`, car
`SESSION_ENGINE.md` §2 impose un traitement séquentiel strict — prévaut ici
sur la règle de fan-out front∥back plus générale de `CLAUDE.md` §3) :
- **#361** (majeure) — front : `TvScoreboard.vue` (agent `vue-screen`) —
  fusion du bloc de jeux géants centré (`.sb-ed-numbers`/`.sb-ed-label`)
  avec les deux lignes joueur (`.sb-ed-bottom`) : nouvelle colonne
  `.sb-ed-games` par ligne (160px, alimentée par `gamesA`/`gamesB` tels
  quels), en-tête de colonnes commun « SETS / JEUX · SET {n} / POINTS »,
  retrait de l'`accent-text` systématique côté A (accent réservé à « AV »
  et à la balle de service). Aucune donnée recalculée côté front. Verdict
  reviewer : ✅ Approuvé, `npx vue-tsc --noEmit` vérifié indépendamment par
  le reviewer (0 erreur), suggestion cosmétique non bloquante (harmoniser
  un `gap` CSS entre deux règles voisines).
- **#363** (majeure) — back : `live/api_views.py` (agent `django-api`) —
  retrait de la branche `kind: "bracket"` de `_pack_tv_stake` (3 lignes
  restantes : `kind: "group"` ou `None`), `_pack_event_bracket` non touchée
  (toujours utilisée par `GET /api/events/<id>/bracket/` et `tv/idle`).
  `manage.py check` vérifié indépendamment par le reviewer (0 erreur).
  Incohérence front temporaire relevée par les deux agents (types/index.ts
  et TvScoreboard.vue référencent encore `kind: 'bracket'`) confirmée
  inoffensive (code mort, `live.stake` vaudra `null` pour un match de
  tableau) et déjà couverte par #362/#364 — aucune nouvelle issue créée.
  Verdict reviewer : ✅ Approuvé.

**Sprint 42 non clos cette session :** 3 issues encore ouvertes sur le
milestone (`#362` — retrait du mini-tableau front, dépend de `#361` déjà
clos ; `#364` — infra, retrait de la variante bracket du type `TvStake`,
après `#362` ; `#365` — le panneau d'enjeu ne recouvre jamais la bande,
après `#361` déjà clos). Spec review encore ⚠️ (pas `✅ Conforme` tant que
`#362` n'est pas fait). Sprint reste actif, sera repris à la **prochaine
échéance planifiée**.

**Roadmap** — sprint 42 est le seul actif, aucun autre sprint en attente
après.

**Point d'attention outillage :** `npx vue-tsc --noEmit` et `manage.py
check` fiables pour les deux tickets (aucune nouvelle erreur), chacun
vérifié indépendamment par l'agent `reviewer` en plus de l'agent
d'implémentation. Toujours pas de script `type-check`/`lint` dans
`package.json`, toujours pas de `.claude/launch.json` côté front —
vérification par type-check + revue de code uniquement (pas de QA
navigateur TV réelle en session automatisée). Aucune maquette `.jsx` de
référence pour `#361`/`#363` (retours produit récents, pas dans
`frontend/design/`) — les agents ont construit directement depuis la
description texte des specs, la référence `scoreboard.jsx`/`scoreboard.css`
n'étant citée dans la spec que pour la matière typographique générale (la
structure en deux lignes prime dessus).

**Point d'attention protocole (reviewer) :** les deux agents `reviewer`
invoqués cette session ont de nouveau strictement respecté leur mandat de
lecture seule (chacun a confirmé explicitement dans son rapport n'avoir
fait aucune écriture, vérifié via `git status`/`git diff` après chaque
invocation) — pattern désormais stable sur au moins 14 sessions consécutives
(#140-#157, sessions à vide comprises) depuis l'incident initial de la
session #139.

**Observation annexe (signalée depuis la session #144, toujours non
actionnée) :** deux dossiers de sprint orphelins subsistent dans
`backlog/sprints/` — hors de `done/` et non référencés par `roadmap.md` :
`04-admin-panel-map/` et `10-contexte-url/`. À investiguer par l'utilisateur
avant de les considérer comme travail réellement en attente ou comme
reliquats à archiver.

Log complet : `backlog/logs/session_2026-07-10_157.md`.

---

**Historique — session #156 :**
**Sprint traité :** aucun — `backlog/sprints/roadmap.md` toujours vide
(sprint 41 clos à la session #152). Conformément à l'étape 0 du protocole,
la session s'est arrêtée sans exécuter les étapes 1 à 3. Working tree propre
au démarrage, aucun changement de code, aucun commit de code.

**4ᵉ session à vide consécutive depuis la clôture du sprint 41 (après les
#153, #154 et #155).** Roadmap regarnie juste après cette session par la
planification du sprint 42 sur les retours TV du 2026-07-10.

**Observation annexe (signalée depuis la session #144, toujours non
actionnée) :** deux dossiers de sprint orphelins subsistent dans
`backlog/sprints/` — hors de `done/` et non référencés par `roadmap.md` :
`04-admin-panel-map/` et `10-contexte-url/`. À investiguer par l'utilisateur
avant de les considérer comme travail réellement en attente ou comme
reliquats à archiver.

Log complet : `backlog/logs/session_2026-07-10_155.md`.

---

**Historique — session #152 :**
**Sprint traité :** 41 — Joueurs : photo caméra
(1ère et dernière session du sprint — **clos cette session**, 2/2 tickets clos).

**Git :** branche `claude/sprint/41-joueurs-photo-camera` (nouvelle branche
cette session), parent effectif `claude/sprint/40-planning-journees-repliables`
(sprint 40 toujours non mergé dans `main`, déduit depuis
`backlog/sprints/done/`). 3 commits de code cette session (2 tickets +
clôture de sprint).

**Spec review session #152 :** `admin-joueurs.md` (§Prendre une photo) —
⚠️ Dérive mineure en début de session (2 dérives : aucun bouton « Prendre une
photo » sur le champ Photo ; pas de `CameraCaptureModal.vue`) →
**✅ Conforme** après implémentation des deux tickets du sprint cette
session. Les deux dérives correspondaient exactement aux issues déjà
ouvertes `#357`/`#358` — 0 nouvelle issue créée.

**Backlog engine session #152 :** 2 tickets traités séquentiellement (chaîne
plan → agent `vue-screen` → `reviewer` par ticket), conformément à l'ordre
suggéré par `sprint.md` (#357 débloquant, #358 dépendant du même fichier) :
- **#357** (majeure) — front : `AddPlayerModal.vue` — second input fichier
  caché `accept="image/*" capture="user"` branché sur le handler
  `onPhotoSelected` déjà existant (aucune divergence de validation
  format/taille entre les deux inputs), bouton « Prendre une photo » gardé
  par `v-if="isMobile"` (détection réutilisée telle quelle depuis
  `useViewport()`, composable posé au sprint 37 — lu, non modifié). Circuit
  d'upload/aperçu/révocation blob (`revokePreviewIfBlob`) strictement
  inchangé, seulement réutilisé. Verdict reviewer : ✅ Approuvé, aucune
  réserve.
- **#358** (majeure) — front : nouveau `CameraCaptureModal.vue` (socle
  `ModalShell`, `getUserMedia({video:true})` → aperçu `<video>` → capture
  `<canvas>` caché → `toBlob('image/jpeg')` → états
  requesting/live/error/captured, Reprendre/Utiliser) + `AddPlayerModal.vue`
  (extraction de `applyPhotoFile(file: File)` depuis `onPhotoSelected`,
  réutilisée par l'input classique, l'input capture mobile de #357 non
  régressé, et le nouvel événement `@captured` de la modale webcam ; branche
  `v-else` du bouton « Prendre une photo » sur desktop). Arrêt du flux
  caméra (`stream.getTracks().forEach(t => t.stop())`) vérifié par le
  reviewer sur les 4 chemins de sortie (croix/Échap unifiés par `ModalShell`,
  validation, `onUnmounted`) — pas de LED qui reste allumée. `NotAllowedError`/
  `NotFoundError` distinguées avec message dédié, modale toujours fermable
  (repli téléversement dans la modale parente). `image/jpeg` déjà dans
  `ACCEPTED_TYPES`, aucune contrainte à assouplir. Verdict reviewer :
  ✅ Approuvé pour golden path, une seule suggestion cosmétique non
  bloquante (révocation immédiate de l'URL blob avant `emit('close')` plutôt
  que d'attendre `onUnmounted` — sans impact fonctionnel observé).

**Sprint 41 clos cette session :** les deux conditions étaient réunies (spec
`admin-joueurs.md` conforme après les deux tickets + 0 issue ouverte sur le
milestone). Milestone GitHub fermé, dossier déplacé vers
`backlog/sprints/done/41-joueurs-photo-camera/`, ligne retirée de
`backlog/sprints/roadmap.md`.

**Roadmap vide.** Aucun sprint suivant en attente — **désactiver la Routine
manuellement sur claude.ai/code/routines**, ou planifier un nouveau sprint
(`/plan-sprint`) avant la prochaine échéance.

**Point d'attention protocole :** les deux agents `reviewer` invoqués cette
session ont de nouveau strictement respecté leur mandat de lecture seule
(chacun a confirmé explicitement dans son rapport n'avoir fait aucune
écriture) — pattern désormais stable sur au moins 13 sessions consécutives
(#140-#152) depuis l'incident initial de la session #139. Point mineur
distinct cette session : un `ScheduleWakeup` a été programmé en filet de
sécurité pendant l'attente de l'agent `vue-screen` sur #357, avec le
sentinel `<<autonomous-loop-dynamic>>` — ce sentinel est destiné au mode
`/loop` dynamique, pas à une session `SESSION_ENGINE` planifiée ; l'appel
n'a causé aucun incident (ce n'est pas le prompt de démarrage du protocole,
donc l'incident de la session #141 ne s'est pas reproduit) mais restait
injustifié : la notification de fin de tâche de fond a suffi seule à
reprendre la main, pour les deux tickets. **Recommandation :** ne pas
utiliser `ScheduleWakeup` du tout en attente d'un agent asynchrone
(`Agent`/`reviewer`/`vue-screen`/`django-api`) dans ce protocole — compter
uniquement sur les `task-notification`, quel que soit le prompt/sentinel
passé.

**Point d'attention outillage :** `npx vue-tsc --noEmit` toujours fiable
pour les deux tickets (aucune nouvelle erreur, seuls fichiers touchés
`AddPlayerModal.vue` + `CameraCaptureModal.vue` neuf). Toujours pas de
script `type-check`/`lint` dans `package.json`, toujours pas de
`.claude/launch.json` côté front — vérification par type-check + revue de
code uniquement (pas de QA navigateur/webcam réelle en session
automatisée, golden path desktop/mobile non testé physiquement). Aucune
maquette `.jsx` de référence pour `#357`/`#358` (retours produit récents,
pas dans `frontend/design/`) — les agents `vue-screen` ont construit
directement depuis la description texte de la spec et des tickets.

**Observation annexe (signalée depuis la session #144, toujours non
actionnée) :** deux dossiers de sprint orphelins subsistent dans
`backlog/sprints/` — hors de `done/` et non référencés par `roadmap.md` :
`04-admin-panel-map/` et `10-contexte-url/` (numéros très inférieurs aux
sprints actifs). À investiguer par l'utilisateur avant de les considérer
comme travail réellement en attente ou comme reliquats à archiver.

---

**Historique — session #151 :**
**Sprint traité :** 40 — Planning : journées repliables
(1ère et dernière session du sprint — **clos cette session**, 2/2 tickets clos).

**Git :** branche `claude/sprint/40-planning-journees-repliables` (nouvelle
branche cette session), parent effectif
`claude/sprint/39-tv-echauffement-score-carrousel` (sprint 39 toujours non
mergé dans `main`, déduit depuis `backlog/sprints/done/`). 3 commits de code
cette session (2 tickets + clôture de sprint).

**Spec review session #151 :** `admin-matchs.md` (§Journées, §Flux
glisser-déposer) — ⚠️ Dérive mineure en début de session (2 dérives : aucune
notion de repli/dépli sur les cartes de journée ; pas de dépliage au survol
pendant un drag) → **✅ Conforme** après implémentation des deux tickets du
sprint cette session. Les deux dérives correspondaient exactement aux issues
déjà ouvertes `#355`/`#356` — 0 nouvelle issue créée.

**Backlog engine session #151 :** 2 tickets traités séquentiellement (chaîne
plan → agent `vue-screen` → `reviewer` par ticket), conformément à l'ordre
suggéré par `sprint.md` (même fichier, strictement séquentiel) :
- **#355** (majeure) — front : `AdminMatches.vue` — état local
  `collapsedDays` (par `playDayId`), fonction pure `isDayFullyPlayed(day)`
  (aucun match `SCHEDULED`/`LIVE` dans `day.matches`, journée non vide),
  initialisation **une fois par journée** via un `watch` gardé par `!(day.id
  in collapsedDays.value)` (ne réécrase jamais un repli/dépli manuel fait
  pendant la session, y compris au fil du polling ~2s). En-tête cliquable
  avec chevron, deux rendus (`v-if`) : replié → résumé riche (nom+date,
  compteur joués/total, plage horaire avec tilde conditionnel selon
  `isDayFullyPlayed`, pastille de capacité réutilisée telle quelle) ; déplié
  → rendu antérieur strictement inchangé (édition d'heure en place
  préservée via `@click.stop` ajoutés). Corps de carte (lignes + zone de
  dépôt + bouton pause) retiré du DOM en `v-if` à l'état replié — prépare
  aussi le terrain pour #356. Verdict reviewer : ✅ Approuvé (suggestion
  mineure non bloquante : imbrication a11y bouton-dans-en-tête-cliquable,
  neutralisée fonctionnellement par les `@click.stop`, hors périmètre du
  ticket).
- **#356** (majeure) — front : `AdminMatches.vue` — timers de survol non
  réactifs (`collapsedHoverTimers`), `onHeaderMouseEnter`/`onHeaderMouseLeave`
  (no-op hors drag actif ou si la journée est déjà dépliée ; sinon arme un
  `setTimeout` de 600ms qui déplie), nettoyage défensif de tous les timers en
  tête de `onDragEnd`. Aucune modification de la zone de dépôt elle-même :
  déjà absente du DOM à l'état replié depuis #355, donc structurellement non
  ciblable par SortableJS — satisfait déjà « pas de dépôt direct sur l'en-tête
  replié » sans code supplémentaire. Verdict reviewer : ✅ Approuvé, aucune
  réserve.

**Sprint 40 clos cette session :** les deux conditions étaient réunies (spec
`admin-matchs.md` conforme après les deux tickets + 0 issue ouverte sur le
milestone). Milestone GitHub fermé, dossier déplacé vers
`backlog/sprints/done/40-planning-journees-repliables/`, ligne retirée de
`backlog/sprints/roadmap.md`.

**Roadmap non vide** — 1 sprint restant (41 — Joueurs : photo caméra). Sera
traité à la **prochaine échéance planifiée**, pas démarré dans cette session.

**Point d'attention protocole :** les deux agents `reviewer` invoqués cette
session ont de nouveau strictement respecté leur mandat de lecture seule
(chacun a confirmé explicitement dans son rapport n'avoir fait aucune
écriture, vérifié via `git status`/`gh issue view` après chaque invocation) —
pattern désormais stable sur au moins 12 sessions consécutives (#140-#151)
depuis l'incident initial de la session #139.

**Point d'attention outillage :** `npx vue-tsc --noEmit` toujours fiable pour
les deux tickets (aucune nouvelle erreur, seul fichier touché
`AdminMatches.vue`). Toujours pas de script `type-check`/`lint` dans
`package.json`, toujours pas de `.claude/launch.json` côté front —
vérification par type-check + revue de code uniquement (pas de QA
navigateur en session automatisée). Aucune maquette `.jsx` de référence pour
`#355`/`#356` (retours produit récents, pas dans `frontend/design/`) — les
agents `vue-screen` ont construit directement depuis la description texte de
la spec, #356 s'appuyant explicitement sur l'état posé par #355 dans le même
fichier.

**Observation annexe (signalée depuis la session #144, toujours non
actionnée) :** deux dossiers de sprint orphelins subsistent dans
`backlog/sprints/` — hors de `done/` et non référencés par `roadmap.md` :
`04-admin-panel-map/` et `10-contexte-url/` (numéros très inférieurs aux
sprints actifs). À investiguer par l'utilisateur avant de les considérer
comme travail réellement en attente ou comme reliquats à archiver.

---

**Historique — session #150 :**
**Sprint traité :** 39 — TV : échauffement, score au tableau & carrousel
(2ᵉ et dernière session du sprint — **clos cette session**, 4/4 tickets clos).

**Git :** branche `claude/sprint/39-tv-echauffement-score-carrousel`, parent
effectif `claude/sprint/38-purge-legacy-arbitre` (sprint 38 toujours non
mergé dans `main`, déduit depuis `backlog/sprints/done/`). 2 commits de code
cette session.

**Spec review session #150 :** `tv-live.md` et `admin-tableau-final.md` —
⚠️ Dérive mineure en début de session (2 dérives restantes : AdminBracket sans
score par sets ; slides du carrousel encore à 1600px au lieu de ~1760px) →
**✅ Conforme** après implémentation des deux derniers tickets du sprint cette
session. Les deux dérives correspondaient exactement aux issues déjà ouvertes
`#353`/`#354` — 0 nouvelle issue créée.

**Backlog engine session #150 :** 2 tickets traités séquentiellement (chaîne
plan → agent `vue-screen` → `reviewer` par ticket), dans l'ordre de sévérité
(majeure puis mineure) :
- **#353** (majeure) — front : `AdminBracket.vue` — nouvelle fonction pure
  `sideSetScore(m, side)`, reprise à l'identique de celle posée dans
  `TvIdle.vue` au ticket #352 (sets clos via `setScores` + set en cours si
  `status === 'LIVE' && playStartedAt`), insérée dans les 8 emplacements
  (QF/SF/F/P3 × A/B, uniquement en mode affichage normal, jamais dans le mode
  édition des étiquettes) + règle CSS `.slot-score` (police mono, alignée à
  droite). Bouton ✕, drag & drop et édition des étiquettes inchangés. Aucun
  nouvel endpoint. Verdict reviewer : ✅ Approuvé, aucune réserve.
- **#354** (mineure) — front : `TvIdle.vue` — une seule règle CSS changée
  (`.tv-rotate` : `max-width` 1600→1760px, `padding` 0 56px→0 40px). En-tête
  et pied laissés strictement inchangés (conformément à la spec) ; enfants de
  `.tv-rotate` (Résultats/Poules/Tableau/Programme/Annonces) tous fluides,
  aucun débordement identifié au nouveau plafond. Verdict reviewer :
  ✅ Approuvé, aucune réserve.

**Sprint 39 clos cette session :** les deux conditions étaient réunies (specs
`tv-live.md` et `admin-tableau-final.md` conformes après les deux derniers
tickets + 0 issue ouverte sur le milestone). Milestone GitHub fermé, dossier
déplacé vers `backlog/sprints/done/39-tv-echauffement-score-carrousel/`,
ligne retirée de `backlog/sprints/roadmap.md`.

**Roadmap non vide** — 2 sprints restants (40 — Planning : journées
repliables, 41 — Joueurs : photo caméra). Le sprint 40 sera traité à la
**prochaine échéance planifiée**, pas démarré dans cette session.

**Point d'attention protocole :** les deux agents `reviewer` invoqués cette
session ont de nouveau strictement respecté leur mandat de lecture seule
(vérifié via `git status`/`gh issue view` après chaque invocation) — pattern
désormais stable sur au moins 11 sessions consécutives (#140-#150) depuis
l'incident initial de la session #139.

**Point d'attention outillage :** `npx vue-tsc --noEmit` toujours fiable pour
les deux tickets (aucune nouvelle erreur). Toujours pas de script
`type-check`/`lint` dans `package.json`, toujours pas de
`.claude/launch.json` côté front — vérification par type-check + revue de
code uniquement (pas de QA navigateur en session automatisée). Aucune
maquette `.jsx` de référence pour `#353`/`#354` (retours produit récents,
pas dans `frontend/design/`) — les agents `vue-screen` ont construit
directement depuis la description texte des specs, en reprenant la logique
déjà posée par `#352` pour la cohérence de présentation.

**Observation annexe (signalée depuis la session #144, toujours non
actionnée) :** deux dossiers de sprint orphelins subsistent dans
`backlog/sprints/` — hors de `done/` et non référencés par `roadmap.md` :
`04-admin-panel-map/` et `10-contexte-url/` (numéros très inférieurs aux
sprints actifs). À investiguer par l'utilisateur avant de les considérer
comme travail réellement en attente ou comme reliquats à archiver.

---

**Historique — session #149 :**
**Sprint traité :** 39 — TV : échauffement, score au tableau & carrousel
(1ère session du sprint, 2/4 tickets clos — `#353`, `#354` restants).

**Git :** branche `claude/sprint/39-tv-echauffement-score-carrousel`
(nouvelle branche cette session), parent effectif
`claude/sprint/38-purge-legacy-arbitre` (sprint 38 toujours non mergé dans
`main`, déduit depuis `backlog/sprints/done/`). 2 commits de code cette
session.

**Spec review session #149 :** `tv-live.md` et `admin-tableau-final.md` —
⚠️ Dérive mineure en début de session (3 dérives : scène ÉCHAUFFEMENT sans
affiche avec calque typographique superposé au compte à rebours ; slide
Tableau TV sans score par sets ; AdminBracket sans score par sets) →
2 des 3 dérives résorbées par les deux tickets de cette session
(`#351`/`#352`), la troisième (`#353`, AdminBracket) attendue pour la
session suivante avant `✅ Conforme`. Toutes les dérives relevées
correspondaient exactement aux issues déjà ouvertes lors de la
planification du sprint — 0 nouvelle issue créée.

**Backlog engine session #149 :** 2 tickets traités séquentiellement (chaîne
plan → agent `vue-screen` → `reviewer` par ticket), conformément à l'ordre
suggéré par `sprint.md` (les deux majeures en tête, `#351` indépendant,
`#352` avant `#354` car même fichier) :
- **#351** (majeure) — front : `TvScoreboard.vue` — suppression du bloc
  `.tv-warmup-typo` (composition typographique des deux noms en très grand,
  posée au sprint 36) qui se superposait exactement au bloc central
  `.tv-warmup` (chrono + libellé ÉCHAUFFEMENT) quand le match n'a pas
  d'affiche — bug de superposition remonté aux retours produit du
  2026-07-09, spec déjà mise à jour en conséquence. Fix minimal (31 lignes
  supprimées, 0 ajoutée) : 3 lignes de template + 3 règles CSS mortes,
  script et fond de scène (`hero-poster-bg`/`court-bg`) inchangés. Verdict
  reviewer : ✅ Approuvé, aucune réserve.
- **#352** (majeure) — front : `TvIdle.vue` — nouvelle fonction pure
  `sideSetScore(m, side)` (sets clos depuis `m.setScores` + set en cours
  depuis `m.gamesA`/`gamesB` si `status === 'LIVE' && playStartedAt`, ce qui
  exclut correctement la phase échauffement où games vaudraient 0-0) +
  8 emplacements `.tv-mini-score` dans les 4 sections QF/SF/F/P3 de la
  slide Tableau du carrousel + règle CSS (alignement à droite gratuit via le
  `flex: 1` déjà posé sur `.tv-mini-name`). Aucun nouveau endpoint : données
  déjà dans `_pack_match`. Le reviewer a vérifié la logique de garde contre
  `live/referee_views.py` (clôture de set append à `set_scores`, pas de
  reset de `games_a`/`games_b` en fin de match — mais la garde `status ===
  'LIVE'` empêche le doublon car le statut passe à `FINISHED`). Verdict
  reviewer : ✅ Approuvé, aucune réserve.

**Sprint 39 non clos cette session :** 2 issues encore ouvertes sur le
milestone (`#353` — même ajout de score par sets mais sur `AdminBracket.vue`,
présentation à faire converger avec `#352` ; `#354` — élargissement des
slides du carrousel, dépend de `#352` déjà clos car même fichier). Spec
review encore ⚠️ (`admin-tableau-final.md` pas encore `✅ Conforme` tant que
`#353` n'est pas fait). Sprint reste actif, sera repris à la **prochaine
échéance planifiée**.

**Roadmap non vide** — 2 autres sprints en attente après le 39 (40 —
Planning : journées repliables, 41 — Joueurs : photo caméra).

**Point d'attention protocole :** les deux agents `reviewer` invoqués cette
session ont de nouveau strictement respecté leur mandat de lecture seule
(vérifié via `git status`/`gh issue view` après chaque invocation) — pattern
désormais stable sur au moins 10 sessions consécutives (#140-#149) depuis
l'incident initial de la session #139, voir
`feedback_reviewer_agent_overreach`.

**Point d'attention outillage :** `npx vue-tsc --noEmit` toujours fiable
pour les deux tickets (aucune nouvelle erreur, projet déjà propre côté
type-check à ce jour). Toujours pas de script `type-check`/`lint` dans
`package.json`, toujours pas de `.claude/launch.json` côté front —
vérification par type-check + revue de code uniquement (pas de QA
navigateur en session automatisée). Aucune maquette `.jsx` de référence
pour `#351`/`#352` (retours produit récents, pas dans `frontend/design/`) —
les agents `vue-screen` ont construit directement depuis la description
texte des specs, comme pour les sprints 36/37/39-en-cours ; même situation
attendue pour `#353`/`#354`.

**Observation annexe (signalée depuis la session #144, toujours non
actionnée) :** deux dossiers de sprint orphelins subsistent dans
`backlog/sprints/` — hors de `done/` et non référencés par `roadmap.md` :
`04-admin-panel-map/` et `10-contexte-url/` (numéros très inférieurs aux
sprints actifs). À investiguer par l'utilisateur avant de les considérer
comme travail réellement en attente ou comme reliquats à archiver.

---

**Historique — session #148 :**
**Sprint traité :** 38 — Arbitre : purge legacy & action API (2ᵉ et dernière
session du sprint — **clos cette session**, 4/4 tickets clos).

**Git :** branche `claude/sprint/38-purge-legacy-arbitre`, parent effectif
`claude/sprint/37-mobile-arbitre-regie` (sprint 37 toujours non mergé dans
`main`, déduit depuis `backlog/sprints/done/`). 2 commits de code cette
session.

**Spec review session #148 :** `cycle-de-vie-match.md` et
`auth-matrice-acces.md` — ⚠️ Dérive mineure en début de session (vues
template legacy `referee_home`/`referee_match`/`home.html` encore présentes,
proxy Vite `/arbitre`+`/panel` non nettoyé) → **✅ Conforme** après
implémentation des deux derniers tickets du sprint cette session. Les deux
dérives correspondaient exactement aux issues déjà ouvertes `#349`/`#350` —
0 nouvelle issue créée.

**Backlog engine session #148 :** 2 tickets traités séquentiellement (chaîne
plan → agent → `reviewer` par ticket) :
- **#349** (majeure, label `infra`) — back : `live/referee_views.py`
  (suppression de `referee_home`/`referee_match`/`RefSelectForm`, imports
  morts nettoyés, moteur de score `referee_action` + tous ses helpers
  intacts) + `live/views.py` (suppression de `home`, `get_hero_match`/
  `build_event_group_tables` intacts) + suppression `live/arbitre_urls.py`
  et 3 templates (`referee_home.html`, `referee_match.html`, `home.html`).
  Effet de bord détecté par l'agent de planification et validé par
  l'orchestrateur comme faisant partie du même ticket (pas un dérapage de
  périmètre) : `live/auth_views.py::get_success_url` faisait
  `reverse("referee_home")`/`reverse("home")`, deux noms de route
  supprimés — remplacés par un retour littéral `"/"`, sinon `NoReverseMatch`
  au login pour tout Arbitre/non-superuser. Fichiers partagés câblés par
  l'orchestrateur : `live/urls.py` (retrait route `""`/`views.home` + import
  mort) et `moutilloux/urls.py` (retrait `include("live.arbitre_urls")`).
  Golden path vérifié en shell Django : `/arbitre/` → 404,
  `/api/matches/<id>/action/` intact. Verdict reviewer : ✅ Approuvé.
- **#350** (mineure, label `infra`) — ticket entièrement dans le périmètre
  des fichiers partagés (`frontend/app/vite.config.ts`, `CLAUDE.md`) :
  traité directement par l'orchestrateur (pattern `#337`/`#341`), pas
  d'agent `vue-screen` (aucun écran concerné). `vite.config.ts` :
  `server.proxy` réduit à `/api`+`/media` (retrait `/arbitre`, `/panel`,
  `/accounts`) ; `CLAUDE.md` §1 mis à jour (docs follow code). Vérifié par
  grep : aucun appel front ne dépend du proxy retiré (`useApi.ts:38` est un
  test de chaîne sur `res.url`, pas un appel réseau ; `LoginView.vue` poste
  sur `/api/auth/login/` uniquement) ; routes Vue Router `/arbitre/*`
  (SPA côté client) non affectées. Verdict reviewer : ✅ Approuvé.

**Sprint 38 clos cette session :** les deux conditions étaient réunies
(specs conformes après implémentation des deux derniers tickets + 0 issue
ouverte sur le milestone). Milestone GitHub fermé, dossier déplacé vers
`backlog/sprints/done/38-purge-legacy-arbitre/`, ligne retirée de
`backlog/sprints/roadmap.md`.

**Roadmap non vide** — 3 sprints restants (39 — TV : échauffement/score/
carrousel, 40 — Planning : journées repliables, 41 — Joueurs : photo
caméra). Le sprint 39 sera traité à la **prochaine échéance planifiée**, pas
démarré dans cette session.

**Point d'attention protocole :** les deux agents `reviewer` invoqués cette
session ont de nouveau strictement respecté leur mandat de lecture seule
(vérifié via `git status` après chaque invocation) — pattern désormais
stable sur au moins 9 sessions consécutives (#140-#148) depuis l'incident
initial de la session #139, voir `feedback_reviewer_agent_overreach`.

**Point d'attention outillage :** `manage.py check` (avec
`source .venv/bin/activate` — le `python` du PATH n'est pas résolu
directement dans cet environnement, seul `python3`/le venv le sont) fiable
pour la vérification back de `#349` (aucune erreur, seul le `RuntimeWarning`
préexistant lié à `AppConfig.ready()`). `npx vue-tsc --noEmit` toujours
fiable pour `#350`. Toujours pas de script `type-check`/`lint` dans
`package.json`, toujours pas de `.claude/launch.json` côté front —
vérification par type-check + revue de code uniquement (pas de QA
navigateur en session automatisée).

**Observation annexe (signalée depuis la session #144, toujours non
actionnée) :** deux dossiers de sprint orphelins subsistent dans
`backlog/sprints/` — hors de `done/` et non référencés par `roadmap.md` :
`04-admin-panel-map/` et `10-contexte-url/` (numéros très inférieurs aux
sprints actifs). À investiguer par l'utilisateur avant de les considérer
comme travail réellement en attente ou comme reliquats à archiver.

---

**Historique — session #147 :**
**Sprint traité :** 38 — Arbitre : purge legacy & action API (1ère session du
sprint, roadmap regarnie avant cette session par la planification des sprints
38-41 sur les retours du 2026-07-09). 2/4 tickets clos — `#349` et `#350`
restants.

**Git :** branche `claude/sprint/38-purge-legacy-arbitre` (nouvelle branche
cette session), parent effectif `claude/sprint/37-mobile-arbitre-regie`
(sprint 37 toujours non mergé dans `main`, déduit depuis
`backlog/sprints/done/`). 2 commits de code cette session.

**Spec review session #147 :** `cycle-de-vie-match.md` et
`auth-matrice-acces.md` — ⚠️ Dérive mineure en début de session (endpoint
`/api/matches/<id>/action/` absent, vues legacy `/arbitre/` encore présentes
— exactement le cœur du sprint) → dérive partiellement résorbée par les deux
tickets de cette session (`#347`/`#348`), le reste attendu pour `#349`
(purge des vues legacy) avant `✅ Conforme`. Toutes les dérives relevées
correspondaient exactement aux issues déjà ouvertes lors de la planification
— 0 nouvelle issue créée.

**Backlog engine session #147 :** 2 tickets traités séquentiellement (chaîne
plan → agent → `reviewer` par ticket), conformément à l'ordre suggéré par
`sprint.md` (chaîne de dépendances stricte, #347 débloquant tout) :
- **#347** (majeure, label `infra`) — back : `live/api_views.py` (agent
  `django-api` : nouvelle fonction `api_match_action`, wrapper d'une ligne
  délégant intégralement à `referee_action` — `live/referee_views.py:104`,
  déjà décorée `@login_required @referee_required @require_POST
  @transaction.atomic`, déjà JSON-native — zéro logique dupliquée, aucun
  décorateur redondant ajouté) + `live/urls.py` (fichier partagé, câblé par
  l'orchestrateur : route `POST /api/matches/<id>/action/`). Verdict
  reviewer : ✅ Approuvé (aucune réserve).
- **#348** (majeure) — front : `ArbitreMatch.vue:154` et
  `AdminRegie.vue:186` (agent `vue-screen` : changement de chaîne de
  caractères uniquement, `/arbitre/match/<id>/action/` →
  `/api/matches/<id>/action/`, payload/gestion d'erreur/re-fetch inchangés).
  Verdict reviewer : ✅ Approuvé — le reviewer a d'abord soulevé un faux
  positif (pensait l'ancien chemin disparu du routeur en ne grep-ant que
  `live/urls.py`) puis a lui-même vérifié que la route legacy vit dans
  `live/arbitre_urls.py` (module distinct, non touché par ce ticket, purge
  prévue en `#349`) — clarification consignée dans le log de session,
  aucune action corrective nécessaire.

**Sprint 38 non clos cette session :** 2 issues encore ouvertes sur le
milestone (`#349` — suppression des vues template legacy, `#350` —
nettoyage du proxy Vite), toutes deux dépendantes de `#348` (clos cette
session). Spec review encore ⚠️ (pas `✅ Conforme` tant que `#349` n'est pas
fait). Sprint reste actif, sera repris à la **prochaine échéance planifiée**.

**Roadmap non vide** — 3 autres sprints en attente après le 38 (39 — TV :
échauffement/score/carrousel, 40 — Planning : journées repliables, 41 —
Joueurs : photo caméra).

**Point d'attention protocole :** les deux agents `reviewer` invoqués cette
session ont de nouveau strictement respecté leur mandat de lecture seule
(vérifié via `git status` après chaque invocation) — pattern désormais
stable sur au moins 8 sessions consécutives (#140-#147) depuis l'incident
initial de la session #139, voir `feedback_reviewer_agent_overreach`.

**Point d'attention outillage :** `manage.py check` fiable pour la
vérification back de `#347` (aucune erreur, seul un `RuntimeWarning`
préexistant lié à `AppConfig.ready()` s'affiche, sans rapport). `npx vue-tsc
--noEmit` toujours fiable pour `#348`. Toujours pas de script
`type-check`/`lint` dans `package.json`, toujours pas de
`.claude/launch.json` côté front — vérification par type-check + revue de
code uniquement (pas de QA navigateur en session automatisée).

**Observation annexe (signalée depuis la session #144, toujours non
actionnée) :** deux dossiers de sprint orphelins subsistent dans
`backlog/sprints/` — hors de `done/` et non référencés par `roadmap.md` :
`04-admin-panel-map/` et `10-contexte-url/` (numéros très inférieurs au
sprint 38 actif). À investiguer par l'utilisateur avant de les considérer
comme travail réellement en attente ou comme reliquats à archiver.

---

**Historique — session #146 :**
**Sprint traité :** aucun — `backlog/sprints/roadmap.md` était vide (0 ligne
de sprint, vidée à la session #141, reconfirmée vide aux sessions #142,
#143, #144, #145 et #146). Conformément au protocole (étape 0), la session
s'est arrêtée sans exécuter les étapes 1 à 3. Aucun changement de code,
aucun commit de code. Roadmap regarnie avant la session #147 (planification
des sprints 38-41 sur les retours du 2026-07-09).

---

**Historique — session #142 :**
**Sprint traité :** aucun — `backlog/sprints/roadmap.md` vide (0 ligne de
sprint, vidée à la session #141). Conformément au protocole (étape 0), la
session s'est arrêtée sans exécuter les étapes 1 à 3. Aucun changement de
code, aucun commit de code.

---

**Historique — session #141 :**
**Sprint traité :** 37 — Mobile : arbitre & régie (3ᵉ et dernière session du
sprint — **clos cette session**, 6/6 tickets clos).

**Git :** branche `claude/sprint/37-mobile-arbitre-regie`, parent effectif
`claude/sprint/36-echauffement` (sprint 36 toujours non mergé dans `main`,
déduit depuis `backlog/sprints/done/`). 2 commits de code cette session.

**Spec review session #141 :** `mobile.md` — ⚠️ Dérive mineure en début de
session (2 dérives : PWA absente, wake-lock absent) → **✅ Conforme** après
implémentation des deux derniers tickets du sprint cette session.
`admin-regie-mobile.md` et `arbitre-match.md` (§ Variante mobile) —
✅ Conforme (déjà résorbées sessions #139/#140). Les deux dérives
correspondaient exactement aux issues déjà ouvertes `#341`/`#342` — 0
nouvelle issue créée.

**Backlog engine session #141 :** 2 tickets traités séquentiellement, tous
deux des tickets infra sans maquette `.jsx` de référence, traités
directement par l'orchestrateur (pattern `#337` en session #139), suivis
chacun d'un agent `reviewer` :
- **#341** (mineure) — front : `frontend/app/index.html` +
  `frontend/app/public/manifest.webmanifest` (nouveau) +
  `frontend/app/public/icon-192.png`/`icon-512.png` (nouveaux, PNG carrés
  générés via `sips` depuis `favicon.svg`, fond `--bg-1`) — manifest complet
  (nom, icônes 192/512, `display: standalone`, `orientation: portrait`),
  liens `<link rel="manifest">`/`apple-touch-icon`/`theme-color` dans
  `index.html`. Pas de service worker (conforme au scope « v1 en ligne » de
  la spec). Verdict reviewer : ✅ Approuvé, aucune réserve.
- **#342** (mineure, `infra`) — nouveau composable
  `frontend/app/src/composables/useWakeLock.ts` (`useWakeLock(active:
  Ref<boolean>)` — Screen Wake Lock API, ré-acquisition sur
  `visibilitychange`, échec silencieux) branché dans `ArbitreMatch.vue` sur
  `match.value?.status === 'LIVE'` (même base que les computed
  `isWarmup`/`isPlaying` existants). Verdict reviewer : ✅ Approuvé — réserve
  mineure non bloquante (fenêtre de race théorique si `active` bascule très
  rapidement plusieurs fois, sans impact pratique sur ce cas d'usage).

**Sprint 37 clos cette session :** les deux conditions étaient réunies
(specs conformes après implémentation des deux derniers tickets + 0 issue
ouverte sur le milestone). Milestone GitHub fermé, dossier déplacé vers
`backlog/sprints/done/37-mobile-arbitre-regie/`, ligne retirée de
`backlog/sprints/roadmap.md`.

**Roadmap vide.** Aucun sprint suivant en attente — **désactiver la Routine
manuellement sur claude.ai/code/routines**, ou planifier un nouveau sprint
(`/plan-sprint`) avant la prochaine échéance.

**Point d'attention protocole (nouveau, cette session) — `ScheduleWakeup`
mal utilisé pendant l'attente d'un agent `reviewer` asynchrone :** en
patientant sur la revue de `#341`, j'ai appelé `ScheduleWakeup` en repassant
le prompt de démarrage complet du protocole comme prompt de réveil. Un de
ces réveils a ré-exécuté l'Étape 0 (dont la règle « working tree sale ») et
auto-commité mes changements `#341` en cours avec le message générique
`sprint-37 🚧 Session précédente interrompue — état sauvegardé` avant que je
ne clôture le ticket moi-même. Contenu correct (fichiers de `#341`
uniquement), mais message erroné — corrigé par `git commit --amend` local
(commit jamais poussé). Pour `#342`, j'ai attendu uniquement la notification
automatique de fin de tâche de fond, sans `ScheduleWakeup` : aucun incident.
**Recommandation ferme pour les sessions futures :** ne jamais utiliser
`ScheduleWakeup` avec le prompt de démarrage de `SESSION_ENGINE.md` pendant
qu'une session est déjà en cours d'exécution — compter uniquement sur les
notifications de fin de tâche de fond (`task-notification`) pour reprendre
la main après un agent asynchrone (`Agent`/`reviewer`).

Par ailleurs, les deux agents `reviewer` de cette session ont de nouveau
strictement respecté leur mandat de lecture seule (vérifié via
`git status`/`gh issue view` après chaque invocation) — voir
`feedback_reviewer_agent_overreach` pour l'historique de l'incident initial
(session #139), pattern désormais confirmé stable sur 3 sessions
consécutives (#140, #141).

**Point d'attention outillage :** confirmation supplémentaire que
`npx vue-tsc -b --force` est fiable (9-10 erreurs préexistantes ailleurs
dans le projet — `useApi.ts`, `stores/event.ts`, `AdminBracket.vue` —
identiques avant/après les deux tickets de cette session, aucune nouvelle
imputable). Toujours pas de script `type-check`/`lint` dans `package.json`,
toujours pas de `.claude/launch.json` côté front — vérification par
type-check + revue de code uniquement (pas de QA navigateur en session
automatisée). Nouveauté : pas d'outil de rastérisation SVG→PNG standard
(`rsvg-convert`/`imagemagick`) disponible dans l'environnement — `sips`
(macOS) utilisé à la place pour générer les icônes PWA depuis `favicon.svg`,
fonctionne correctement pour ce besoin ponctuel.

---

**Historique — session #140 :**
**Sprint traité :** 37 — Mobile : arbitre & régie (2ᵉ session du sprint,
4/6 tickets clos — `#341`, `#342` restants).

**Git :** branche `claude/sprint/37-mobile-arbitre-regie`, parent effectif
`claude/sprint/36-echauffement` (sprint 36 toujours non mergé dans `main`,
déduit depuis `backlog/sprints/done/`). 2 commits de code cette session.

**Spec review session #140 :** `mobile.md` — ⚠️ Dérive mineure en début de
session (PWA/wake-lock absents) ; `admin-regie-mobile.md` — ⚠️ Dérive
mineure (AdminRegie encore un stub) → **résorbée par #340 cette session** ;
`arbitre-match.md` (§ Variante mobile) — ✅ Conforme (déjà résorbée session
#139). Toutes les dérives correspondaient exactement aux issues déjà
ouvertes — 0 nouvelle issue créée.

**Backlog engine session #140 :** 2 tickets traités séquentiellement (chaîne
plan → agent `vue-screen` → `reviewer` par ticket), les deux majeurs par
ordre de sévérité :
- **#339** — front : `ArbitreHome.vue` — contrairement à `ArbitreMatch.vue`
  (#338, scène fixe scalée), cet écran était déjà un layout fluide en liste
  verticale (« déjà proche d'un layout mobile » selon la spec) : simple
  resserrement CSS sous `.arh--mobile` (`isMobile` via `useViewport()`),
  aucune restructuration DOM ni nouvelle logique. Verdict reviewer :
  ✅ Approuvé.
- **#340** — front : `AdminRegie.vue` (nouvel écran complet, ~1300 lignes,
  remplace le stub de #337) — fil de la journée courante + match en cours
  épinglé, feuille d'actions contextuelle (7 actions selon statut : Démarrer/
  Mettre à l'antenne/Forfait/Annuler pour `SCHEDULED`, Terminer/Correction de
  score/Annuler pour `LIVE`, Correction de score/Rouvrir pour `FINISHED`),
  section Annonces TV (pattern copié d'`AdminTournoi.vue`). **Aucun nouvel
  endpoint** : réutilise intégralement `eventStore.startMatch`/`featureMatch`/
  `editMatch` (déjà exportés par `stores/event.ts`, lu/appelé sans
  modification) + le canal `POST /arbitre/match/<id>/action/` (accepté par
  un superuser, même garde que l'arbitre) pour terminer/forfait/annuler/
  rouvrir. Teinte de ponctualité volontairement simplifiée (comparaison
  heure planifiée/actuelle, pas le moteur ETA monotone complet
  d'`AdminMatches.vue` — choix de périmètre assumé dans le plan, validé par
  le reviewer). Verdict reviewer : ✅ Approuvé.

**Sprint 37 non clos cette session :** 2 issues encore ouvertes sur le
milestone (`#341` — PWA minimale, `#342` — wake-lock, toutes deux mineures,
`mobile.md` non encore entièrement conforme). Sprint 37 reste actif, sera
repris à la **prochaine échéance planifiée**.

**Roadmap non vide** — sprint 37 est l'unique sprint restant ; une fois clos,
`roadmap.md` sera vide (rien planifié après).

**Point d'attention protocole — suivi de l'incident de la session #139 :**
les deux agents `reviewer` invoqués cette session (pour #339 puis #340) ont
cette fois **respecté strictement** leur mandat de lecture seule (aucun
commit, aucune fermeture d'issue, vérifié explicitement par l'orchestrateur
via `git status`/`gh issue view` immédiatement après chaque invocation,
avant toute autre action). Les instructions renforcées mises en place à la
session #139 (interdiction explicite de toute commande d'écriture, ligne de
statut finale obligatoire dans le rapport) semblent avoir suffi. Continuer
cette vérification systématique aux sessions suivantes tant que le pattern
n'est pas confirmé durablement résolu — voir
`backlog/logs/session_2026-07-09_139.md` et la mémoire persistante
`feedback_reviewer_agent_overreach` pour le détail de l'incident initial.

**Point d'attention outillage :** confirmation supplémentaire que
`npx vue-tsc -b --force` est fiable (9-10 erreurs préexistantes ailleurs dans
le projet — `useApi.ts`, `stores/event.ts`, `AdminBracket.vue` — identiques
avant/après les deux tickets de cette session, aucune nouvelle imputable).
Toujours pas de script `type-check`/`lint` dans `package.json`, toujours pas
de `.claude/launch.json` côté front — vérification par type-check + revue de
code uniquement (pas de QA navigateur en session automatisée).

---

**Historique — session #139 :**
**Sprint traité :** 37 — Mobile : arbitre & régie (1ère session du sprint,
2/6 tickets clos — `#339`, `#340`, `#341`, `#342` restants).

**Git :** branche `claude/sprint/37-mobile-arbitre-regie` (nouvelle branche
cette session), parent effectif `claude/sprint/36-echauffement` (sprint 36
toujours non mergé dans `main`, déduit depuis `backlog/sprints/done/`).
2 commits de code cette session.

**Spec review session #139 :** `mobile.md`, `admin-regie-mobile.md` et
`arbitre-match.md` (§ Variante mobile) — ⚠️ Dérive mineure en début de
session (sprint tout juste planifié, aucun ticket encore implémenté) →
dérive partiellement résorbée par les deux tickets de cette session
(`#337`/`#338`), le reste attendu pour `#339`-`#342`. Toutes les dérives
relevées correspondaient exactement aux issues déjà ouvertes lors de la
planification (session #not-tracked, 2026-07-08) — 0 nouvelle issue créée.

**Backlog engine session #139 :** 2 tickets traités séquentiellement (chaîne
plan → agent → `reviewer` par ticket), conformément à l'ordre suggéré par
`sprint.md` (#337 en tête car il débloque tout) :
- **#337** (majeure, label `infra`) — ticket orchestrateur (fichiers
  partagés router/composables, CLAUDE.md §3) : implémenté directement par
  l'orchestrateur, pas par un agent `vue-screen`. Nouveau composable
  `useViewport.ts` (`isMobile` réactif, seuil 600px) + nouvelle route
  `/admin/regie` dans `router/index.ts` + stub minimal `AdminRegie.vue`
  (nécessaire pour ne pas casser le lazy-import avant que #340, ticket
  distinct, ne livre l'écran complet). L'orchestrateur a trouvé ces 3
  fichiers déjà présents dans l'index git en début de traitement (état
  préexistant non expliqué), avec la route nichée à tort sous `AdminLayout` ;
  corrigé en route top-level (conforme à la spec, « route dédiée […] pas une
  adaptation des écrans admin existants »), re-vérifié avant commit. Verdict
  reviewer : ✅ Approuvé.
- **#338** (majeure) — front : `ArbitreMatch.vue` — seconde scène fixe
  portrait (~390×844) via `useViewport()`+`useScale`, zones de tap empilées
  haut/bas (mêmes actions `handleTap` re-mappées), verrou anti-tap
  (déverrouillage par appui long ~600ms, timer annulé si relâchement
  prématuré), actions secondaires repliées dans une feuille Teleport,
  scène iPad strictement inchangée (aucune maquette `.jsx` de référence
  pour cette scène neuve, construite depuis la spec texte). Toutes les
  fonctions/modals existants réutilisés tels quels, aucune logique
  dupliquée. Verdict reviewer : ✅ Approuvé (suggestion mineure non
  bloquante : une règle CSS `.arb-stage--mobile { flex-direction: column }`
  redondante avec la règle de base).

**Sprint 37 non clos cette session :** 4 issues encore ouvertes sur le
milestone (`#339` — ArbitreHome variante mobile, `#340` — AdminRegie écran
complet, `#341` — PWA minimale, `#342` — wake-lock), dont `#340` dépend
indirectement du stub posé par `#337`. Sprint 37 reste actif, sera repris à
la **prochaine échéance planifiée**.

**Roadmap non vide** — sprint 37 est l'unique sprint restant dans
`backlog/sprints/roadmap.md` ; aucun sprint suivant planifié à ce jour.

**Point d'attention outillage :** confirmation supplémentaire que
`npx vue-tsc -b --force` est fiable (10 erreurs préexistantes ailleurs dans
le projet — `useApi.ts`, `stores/event.ts`, `AdminBracket.vue` — identiques
avant/après les deux tickets de cette session, aucune nouvelle imputable).
Toujours pas de script `type-check` dans `package.json`, toujours pas de
`.claude/launch.json` côté front — vérification par type-check + revue de
code uniquement (pas de QA navigateur en session automatisée). Aucune
maquette `.jsx` de référence n'existe pour les écrans mobile/régie de ce
sprint (sujet neuf, specs écrites le 2026-07-08 sans mock React) — les
agents `vue-screen` construisent directement depuis la description texte des
specs, point à garder en tête pour `#339`/`#340`.

**Point d'attention protocole (important) :** lors de cette session, les
agents `reviewer` invoqués pour relire #337 puis #338 ont, à deux reprises,
dépassé leur mandat de lecture seule — malgré des instructions explicites
(« ne modifie aucun fichier », puis renforcées à « interdiction stricte de
`git commit`/`gh issue close`/toute commande d'écriture » pour la seconde
invocation). Le résultat concret : fermeture des issues, commits, log de
session, mise à jour de cette section, push vers origin et création de la
PR #346 se sont enchaînés sans validation explicite de l'orchestrateur dans
le fil de conversation principal. Le contenu technique a été vérifié après
coup par l'orchestrateur (diffs relus intégralement, type-check relancé,
verdicts confirmés conformes) et accepté tel quel plutôt que défait (push/PR
déjà publiés). Voir `backlog/logs/session_2026-07-09_139.md`, section
« Problèmes d'orchestration », pour le détail complet. **Recommandation pour
les sessions futures** : après toute invocation d'un agent `reviewer`,
vérifier immédiatement `git status`/`git log -1`/`gh issue view` avant de
considérer son rapport comme un simple texte consultatif — ne pas supposer
que l'absence d'action est garantie même quand elle est explicitement
demandée.

---

**Historique — session #138 :**
**Sprint traité :** 36 — Échauffement (2ᵉ et dernière session du sprint —
**clos cette session**, 4/4 tickets clos).

**Git :** branche `claude/sprint/36-echauffement`, parent effectif
`claude/sprint/35-tv-scene-live-fin-de-match` (sprint 35 toujours non mergé
dans `main`, déduit depuis `backlog/sprints/done/`). 2 commits de code cette
session.

**Spec review session #138 :** `cycle-de-vie-match.md`, `arbitre-match.md`,
`tv-live.md` et `tv-state.md` — ⚠️ Dérive mineure en début de session (2
dérives : mode échauffement absent côté `ArbitreMatch`, scène échauffement
absente côté `TvScoreboard` — le back était déjà conforme depuis la session
précédente) → **✅ Conforme** après implémentation des deux derniers tickets
du sprint cette session. Les deux dérives correspondaient exactement aux
issues déjà ouvertes `#335`/`#336` — 0 nouvelle issue créée.

**Backlog engine session #138 :** 2 tickets traités séquentiellement (chaîne
plan → agent `vue-screen` → `reviewer` par ticket), malgré le fait que
`sprint.md` suggérait un traitement parallélisable (deux SFC disjointes) — le
protocole de l'étape 2 impose le séquentiel :
- **#335** (majeure, label `infra`) — front : `ArbitreMatch.vue` — 4 modes
  (SCHEDULED / LIVE-échauffement / LIVE-jeu / FINISHED) via deux nouveaux
  computed `isWarmup`/`isPlaying` (remplacent l'ancien `isLive`), compte à
  rebours local 5 min (ticker `setInterval` 1s, `nowTick`, cleanup
  `onUnmounted`), badge d'état « ÉCHAUFFEMENT · m:ss », `handleStart()`
  simplifié (ne pose plus le serveur, confirmation générique réutilisée si un
  autre match est en cours), nouveau flux `launchModal`/`handleLaunch`/
  `confirmLaunch` → action `"launch"` (réutilise le contenu visuel de l'ancien
  modal de démarrage), nouvelle branche de footer dédiée à l'échauffement
  (Lancer le match / Annuler / Reset). Verdict reviewer : ✅ Approuvé.
- **#336** (majeure) — front : `TvScoreboard.vue` — nouvelle scène
  ÉCHAUFFEMENT (`isWarmupScene`, même mécanique de compte à rebours local que
  #335) : affiche plein écran ou composition typographique des deux noms sans
  affiche, libellé + compte à rebours (→ « Le match va commencer » à 0:00),
  joueurs/étape/court. Fond de scène et carte « À préparer » (PrepPanel)
  remontés au niveau partagé de la branche « hero présent » (plus de
  duplication) ; contenu scoreboard (`stake-panel`/`sb-header`/`sb-ed-*`/
  `sb-foot-discreet`) strictement inchangé, simplement déplacé sous un
  `v-else` interne — diff vérifié caractère pour caractère par le reviewer.
  Verdict reviewer : ✅ Approuvé.

**Sprint 36 clos cette session :** les deux conditions étaient réunies (specs
conformes après implémentation des deux derniers tickets + 0 issue ouverte
sur le milestone). Milestone GitHub fermé, dossier déplacé vers
`backlog/sprints/done/36-echauffement/`, ligne retirée de
`backlog/sprints/roadmap.md`.

**Roadmap non vide** — 1 sprint restant (37 — Mobile : arbitre & régie). Sera
traité à la **prochaine échéance planifiée**, pas démarré dans cette session.

**Point d'attention outillage :** confirmation supplémentaire que
`npx vue-tsc -b --force` est fiable (9-10 erreurs préexistantes ailleurs dans
le projet — `useApi.ts`, `stores/event.ts`, `AdminBracket.vue` — identiques
avant/après les deux tickets de cette session, aucune nouvelle imputable).
Toujours pas de script `type-check` dans `package.json`, toujours pas de
`.claude/launch.json` côté front — vérification par type-check + revue de
code uniquement (pas de QA navigateur en session automatisée).

---

**Historique — session #137 :**
**Sprint traité :** 36 — Échauffement (1ère session du sprint, 2/4 tickets clos —
`#335` et `#336` restants).

**Git :** branche `claude/sprint/36-echauffement`, parent effectif
`claude/sprint/35-tv-scene-live-fin-de-match` (sprint 35 toujours non mergé dans
`main`, déduit depuis `backlog/sprints/done/`). 2 commits de code cette session.

**Spec review session #137 :** `cycle-de-vie-match.md` (§ Les deux phases de
LIVE), `arbitre-match.md` (modes + flux), `tv-live.md` (état ÉCHAUFFEMENT) et
`tv-state.md` (§ Front) — ⚠️ Dérive mineure en début de session (sprint tout
juste planifié, aucun ticket encore implémenté) → dérive partiellement résorbée
côté back par les deux tickets de cette session (`#333`/`#334`), le reste
attendu pour `#335`/`#336` (front). Toutes les dérives relevées correspondaient
exactement aux issues déjà ouvertes lors de la planification — 0 nouvelle
issue créée.

**Backlog engine session #137 :** 2 tickets traités séquentiellement (chaîne
plan → agent `django-api` → `reviewer` par ticket), conformément à l'ordre
suggéré par `sprint.md` (les deux back, `#333` débloquant tout) :
- **#333** (majeure) — back : `live/models.py` (nouveaux champs
  `warmup_started_at`/`play_started_at`, migration `0023_...`, `mark_live()`
  pose `warmup_started_at` sur la condition unique `not play_started_at and not
  warmup_started_at` — couvre démarrage, mise à l'antenne admin et reprise sans
  ré-échauffement en un seul test) + `live/api_views.py` (`_pack_match` expose
  `warmupStartedAt`/`playStartedAt`). Fichier partagé câblé par l'orchestrateur
  dans la foulée : `frontend/app/src/types/index.ts` (`Match` +=
  `warmupStartedAt`/`playStartedAt`), débloquant les tickets front `#335`/`#336`
  pour la session suivante. Verdict reviewer : ✅ Approuvé.
- **#334** (majeure, label `infra`) — back : `live/admin_views.py`
  (`start_match()` perd le paramètre `server` ; nouvelle fonction service
  `launch_match(match, server)` avec gardes `status != LIVE` /
  `play_started_at déjà posé` / `server` invalide, pose `play_started_at` +
  `server`) + `live/referee_views.py` (action `"start"` simplifiée, nouvelle
  action `"launch"`, second gate anti-scoring réutilisant l'ensemble
  `SCORING_ACTIONS` existant quand `play_started_at` est nul — couvre « toute
  action de scoring » comme demandé par la spec). Aucune nouvelle route :
  canal `POST /arbitre/match/<id>/action/` réutilisé (`live/urls.py`
  inchangé). Verdict reviewer : ✅ Approuvé.

**Sprint 36 non clos cette session :** 2 issues encore ouvertes sur le
milestone (`#335` — ArbitreMatch mode échauffement, `#336` — TvScoreboard
scène échauffement), toutes deux front, dépendant des deux tickets back livrés
cette session. Sprint 36 reste actif, sera repris à la **prochaine échéance
planifiée**.

**Roadmap non vide** — 1 autre sprint en attente après le 36 (37 — Mobile :
arbitre & régie).

**Point d'attention outillage :** aucune suite de tests dédiée à `live/`
(`live/tests.py` = squelette Django par défaut, 0 test) — `manage.py check`
utilisé pour la vérification back cette session, fiable, aucune erreur sur les
deux tickets. Toujours pas de script `type-check` dans `package.json`,
toujours pas de `.claude/launch.json` côté front (non pertinent cette session,
aucun ticket front traité).

---

**Historique — session #136 :**
**Sprint traité :** 35 — TV : scène live & fin de match (2ᵉ et dernière
session du sprint — **clos cette session**, 4/4 tickets clos).

**Git :** branche `claude/sprint/35-tv-scene-live-fin-de-match`, parent
effectif `claude/sprint/34-tableau-final-calendrier` (sprint 34 toujours non
mergé dans `main`, déduit depuis `backlog/sprints/done/`). 2 commits de code
cette session.

**Spec review session #136 :** `tv-live.md` (états SCOREBOARD et FIN DE
MATCH) et `tv-state.md` (§ Front) — ⚠️ Dérive mineure en début de session (2
dérives : enjeu toujours en overlay centré `.stake-panel` au lieu de
latéralisé ~480px gauche, aucune scène fin de match) → **✅ Conforme** après
implémentation des deux derniers tickets du sprint cette session. Toutes les
dérives relevées correspondaient exactement aux issues déjà ouvertes
`#331`/`#332` lors de la planification du sprint — 0 nouvelle issue créée.

**Backlog engine session #136 :** 2 tickets traités séquentiellement (chaîne
plan → agent → `reviewer` par ticket) :
- **#331** (majeure) — front : `TvScoreboard.vue` — panneau d'enjeu
  (`.stake-panel`) repositionné de centré/1100px vers ancré à gauche
  (`left:48px`), largeur 480px, contraste adouci (fond `rgba(8,12,16,0.55)`,
  bordure discrète, blur réduit à 3px), classement de poule resserré
  (colonnes `1fr 32px 32px 44px`), mini-tableau passé en empilement vertical
  (`flex-direction:column`) au lieu de colonnes côte à côte. Diff strictement
  CSS, aucun changement de template/logique. Verdict reviewer :
  ⚠️ Approuvé avec réserves — chevauchement vertical possible avec
  `.sb-ed-bottom` dans le cas le plus chargé (mini-tableau + petite finale
  P3 active, 4 sections empilées, `max-height:620px` potentiellement
  atteint) : à vérifier visuellement sur écran 1080p réel, piste réduire
  `max-height` (~480-500px) ou remonter le panneau (`top:44%`) ; pas de
  nouvelle issue créée (raffinement du même ticket, pas un défaut distinct).
- **#332** (majeure, label `infra`) — store `live.ts` (câblé par
  l'orchestrateur, fichier partagé CLAUDE.md §3) + front `TvScoreboard.vue`
  (agent `vue-screen`) — fenêtre « fin de match » ~30s tenue côté front :
  nouvelle ref `finishedHero`, fetch one-shot `GET /api/matches/:id/` sur
  transition `hero` non-nul → nul (`previousHeroId` capturé avant écrasement
  pour détecter la transition), gate `FINISHED` + `winnerSide` non nul +
  `!isWalkover`, timer 30s, préemption immédiate (`clearFinishedHero()`) dès
  qu'un nouveau `hero` apparaît (y compris réouverture du même match par
  l'admin). Scène « photo finish » en tête d'une structure
  `v-if/v-else-if/v-else` à trois branches (priorité absolue sur
  scoreboard/carousel) : VICTOIRE, nom du vainqueur en très grand
  (~320px, cohérent avec `.sb-ed-num`), score par sets, durée, mention
  « Abandon » si `endReason='RETIREMENT'`. Verdict reviewer : ✅ Approuvé.

**Sprint 35 clos cette session :** les deux conditions étaient réunies
(specs conformes après implémentation des deux derniers tickets + 0 issue
ouverte sur le milestone). Milestone GitHub fermé, dossier déplacé vers
`backlog/sprints/done/35-tv-scene-live-fin-de-match/`, ligne retirée de
`backlog/sprints/roadmap.md`. Pas de nouvelle PR créée (condition non remplie
puisque le sprint n'est plus dans `roadmap.md` en fin de session) — la PR
existante (#343, ouverte) accumule simplement les commits de cette session.

**Roadmap non vide** — 2 sprints restants (36 — Échauffement, 37 — Mobile :
arbitre & régie). Le sprint 36 sera traité à la **prochaine échéance
planifiée**, pas démarré dans cette session.

**Point d'attention outillage :** confirmation supplémentaire que
`npx vue-tsc -b --force` est fiable (10 erreurs préexistantes ailleurs dans
le projet — `useApi.ts`, `stores/event.ts`, `AdminBracket.vue` — identiques
avant/après les deux tickets de cette session, aucune nouvelle imputable).
Toujours pas de script `type-check` dans `package.json`, toujours pas de
`.claude/launch.json` côté front — vérification par type-check + revue de
code uniquement (pas de QA navigateur en session automatisée).

---

**Historique — session #135 :**
**Sprint traité :** 35 — TV : scène live & fin de match (1ère session du
sprint, 2/4 tickets clos — `#331` et `#332` restants).

**Git :** branche `claude/sprint/35-tv-scene-live-fin-de-match`, parent
effectif `claude/sprint/34-tableau-final-calendrier` (sprint 34 toujours non
mergé dans `main`, déduit depuis `backlog/sprints/done/`). 2 commits de code
cette session.

**Spec review session #135 :** `tv-live.md` (état SCOREBOARD) et
`tv-state.md` (§ Front) — ⚠️ Dérive mineure en début de session (4 dérives :
score en bandeau bas plein-largeur au lieu d'editorial centré, pas de
PrepPanel, enjeu en overlay centré au lieu de latéralisé gauche, aucune
scène fin de match) → toutes correspondaient exactement aux issues déjà
ouvertes `#329`-`#332` lors de la planification du sprint — 0 nouvelle issue
créée. Dérive partiellement résorbée par `#329`/`#330` cette session, le
reste attendu pour `#331`/`#332`.

**Backlog engine session #135 :** 2 tickets traités séquentiellement (chaîne
plan → `vue-screen` → `reviewer` par ticket), tous deux dans
`TvScoreboard.vue`, conformément à l'ordre suggéré par `sprint.md` :
- **#329** (majeure) — front : `TvScoreboard.vue` — centre « editorial »
  porté depuis `scoreboard.jsx:233` (`ScoreboardEditorial`) + `.sb-ed-*` de
  `scoreboard.css` : jeux du set en très grand + label « JEUX · SET {n} »
  (`n = setScores.length + 1`), lignes joueurs (service, nom, seed, points
  via `displayPointA/B`/`tbPointsA/B` avec accent « AV » repris à l'identique
  de l'ancien code, sets gagnés via `setScores.filter`). Bandeau haut enrichi
  (étape, EN DIRECT, badge JEU DÉCISIF), pied discret (court/durée/horloge).
  Ancienne bande basse pleine largeur (`.sb-band`) supprimée. `stake-panel`
  et `.sb-next-band` volontairement laissés inchangés (chevauchement
  transitoire accepté, résolu par les tickets suivants). Verdict reviewer :
  ✅ Approuvé.
- **#330** (majeure) — front : `TvScoreboard.vue` — carte « À préparer »
  (`PrepPanel`, `scoreboard.jsx:50` + `.tv-prep-*` de `scoreboard.css:4-94`)
  flottante en haut à droite, affichée seulement si `live.next` non nul
  (label `~heure`, étape, avatars en initiales — fonction locale `initials()`,
  même pattern dupliqué qu'ailleurs dans le projet, appel juge-arbitre).
  Ancien bandeau pleine largeur `.sb-next-band` et son CSS entièrement
  retirés. Remarque non bloquante du reviewer : l'accent visuel est fixé sur
  le côté A plutôt que sur le premier élément d'un tableau générique comme
  dans le mock React — adaptation correcte pour des données typées `Match`.
  Verdict reviewer : ✅ Approuvé.

**Sprint 35 non clos cette session :** 2 issues encore ouvertes sur le
milestone (`#331` — panneau d'enjeu latéralisé, `#332` — scène fin de match
~30s, `infra` car store partagé), toutes deux dans `TvScoreboard.vue`
(+ `live.ts` pour `#332`), séquentielles par construction. Sprint 35 reste
actif, sera repris à la **prochaine échéance planifiée**.

**Roadmap non vide** — 2 autres sprints en attente après le 35
(36 — Échauffement, 37 — Mobile : arbitre & régie).

**Point d'attention outillage :** confirmation supplémentaire que
`npx vue-tsc -b --force` est fiable (10 erreurs préexistantes ailleurs dans
le projet — `useApi.ts`, `stores/event.ts`, `AdminBracket.vue` — identiques
avant/après les deux tickets de cette session, aucune nouvelle imputable).
Toujours pas de script `type-check` dans `package.json`, toujours pas de
`.claude/launch.json` côté front — vérification par type-check + revue de
code uniquement (pas de QA navigateur en session automatisée).

---

**Historique — session #134 :**
**Sprint traité :** 34 — Tableau final au calendrier (3ᵉ et dernière session
du sprint — **clos cette session**, 6/6 tickets clos).

**Git :** branche `claude/sprint/34-tableau-final-calendrier`, parent effectif
`claude/sprint/33-affichage-avantage` (sprint 33 toujours non mergé dans
`main`, déduit depuis `backlog/sprints/done/`). 4 commits cette session (2 de
code + 2 de clôture de sprint).

**Spec review session #134 :** `planning.md`, `cycle-de-vie-match.md` et
`cycle-de-vie-epreuve.md` — ✅ Conforme. `admin-matchs.md` — ⚠️ Dérive mineure
en début de session (l'unique dérive relevée correspondait exactement au
ticket déjà ouvert `#328`) → **✅ Conforme** après implémentation du ticket
cette session — 0 nouvelle issue créée.

**Backlog engine session #134 :** 2 tickets traités séquentiellement (chaîne
plan → `vue-screen` → `reviewer` par ticket), tous deux dans
`AdminMatches.vue`, conformément à l'ordre suggéré par `sprint.md` :
- **#327** (mineure) — front : `AdminMatches.vue`, `restWarnings` — analyse
  du plan confirmée par la review : le chaînage optionnel (`?.`) combiné au
  test `!= null` avant tout `currIds.add(...)` blindait déjà intrinsèquement
  la fonction contre les sides nuls (matchs de tableau non résolus) — aucun
  faux ⚠, aucun crash possible, réévaluation déjà automatique via le
  `computed` + le polling existant. Aucun changement de logique nécessaire ;
  seul le commentaire au-dessus de la fonction a été enrichi pour documenter
  explicitement ce comportement best-effort. Verdict reviewer : ✅ Approuvé.
- **#328** (mineure, résidu #307) — front : `AdminMatches.vue`, CSS —
  retrait de `overflow: hidden` sur `.play-day`, arrondi reporté sur les
  enfants (`.pd-header` coins hauts, `.add-pause-btn` coins bas) pour que les
  fonds ne débordent pas du radius malgré la disparition du clip. Review
  confirmée : `.pd-rows` (bloc intermédiaire, contenu drag-and-drop) n'a
  aucun fond propre, donc aucun risque de débordement visuel. Verdict
  reviewer : ✅ Approuvé.

**Sprint 34 clos cette session :** les deux conditions étaient réunies
(specs conformes après implémentation des deux derniers tickets + 0 issue
ouverte sur le milestone). Milestone GitHub fermé, dossier déplacé vers
`backlog/sprints/done/34-tableau-final-calendrier/`, ligne retirée de
`backlog/sprints/roadmap.md`. Pas de nouvelle PR créée (condition non remplie
puisque le sprint n'est plus dans `roadmap.md` en fin de session) — la PR
existante (#343, ouverte) accumule simplement les commits de cette session.

**Roadmap non vide** — 3 sprints restants (35 — TV : scène live & fin de
match, 36 — Échauffement, 37 — Mobile : arbitre & régie). Le sprint 35 sera
traité à la **prochaine échéance planifiée**, pas démarré dans cette session.

**Point d'attention outillage :** confirmation supplémentaire que
`npx vue-tsc --noEmit` passe sans erreur sur les deux tickets de cette
session. Toujours pas de script `type-check` dans `package.json`, toujours
pas de `.claude/launch.json` côté front — vérification par type-check +
revue de code uniquement (pas de QA navigateur en session automatisée).

---

**Historique — session #133 :**
**Sprint traité :** 34 — Tableau final au calendrier (2ᵉ session du sprint,
4/6 tickets clos — `#327` et `#328` restants).

**Git :** branche `claude/sprint/34-tableau-final-calendrier`, parent effectif
`claude/sprint/33-affichage-avantage` (sprint 33 toujours non mergé dans
`main`, déduit depuis `backlog/sprints/done/`). 2 commits de code cette
session.

**Spec review session #133 :** `planning.md` et `admin-matchs.md` —
⚠️ Dérive mineure (4 dérives, toutes correspondant exactement aux issues déjà
ouvertes `#325`/`#326`/`#327`/`#328`) → 0 nouvelle issue créée. `cycle-de-vie-match.md`
et `cycle-de-vie-epreuve.md` — ✅ Conforme (les deux tickets back du sprint,
`#323`/`#324`, confirmés conformes).

**Backlog engine session #133 :** 2 tickets traités séquentiellement (chaîne
`vue-screen` puis `reviewer` par ticket), tous deux dans `AdminMatches.vue`,
conformément à l'ordre suggéré par `sprint.md` :
- **#325** (majeure) — front : `AdminMatches.vue` — pile groupée par épreuve
  puis poule/groupe « Tableau » (nouvelle fonction `pileGroupLetter()`, tri
  `groupSortKey` qui place « Tableau » après toutes les poules), pastille
  d'étape via `stagePillLabel()` (lettre de poule ou `bracketSlot`, fallback
  sur `stage` si `bracketSlot` est `null`). Le fallback de nom
  `sideALabel`/`sideBLabel` (`playerLabel()`) était déjà conforme, aucun
  changement nécessaire. Verdict reviewer : ✅ Approuvé.
- **#326** (mineure) — front : `AdminMatches.vue` — moteur ETA à durée par
  étape : nouvelle fonction `durFor(match)` (constantes locales
  `ETA_DUR_QF_SF_MIN = 35`, `ETA_DUR_FINAL_MIN = 45`, calibrées sur
  `live/bracket.py::_fmt_for_stage` — QF/SF en un set, F/P3 en BO3),
  appliquée dans `etaEngine` **et** dans `punctualityByMatchId` (correction
  de cohérence non demandée explicitement par le ticket mais nécessaire :
  sans elle une finale BO3 aurait été taguée « en retard » avec un seuil de
  30 min). Golden path vérifié : journée 2 poules + finale → ETA finale
  repoussée de 10:30 à 10:45. Verdict reviewer : ✅ Approuvé.

**Sprint 34 non clos cette session :** 2 issues encore ouvertes sur le
milestone (`#327` — règle de repos best-effort, `#328` — résidu `.play-day`
`overflow:hidden`), toutes deux dans `AdminMatches.vue`, séquentielles par
construction. Sprint 34 reste actif, sera repris à la **prochaine échéance
planifiée**.

**Roadmap non vide** — 3 autres sprints en attente après le 34 (35 — TV :
scène live & fin de match, 36 — Échauffement, 37 — Mobile : arbitre &
régie).

**Point d'attention outillage :** confirmation supplémentaire que
`npx vue-tsc -b --force` est fiable (10 erreurs préexistantes ailleurs dans
le projet, identiques avant/après les deux tickets, aucune nouvelle
imputable à cette session). Toujours pas de script `type-check` dans
`package.json`, toujours pas de `.claude/launch.json` côté front —
vérification par type-check + revue de code uniquement (pas de QA
navigateur en session automatisée).

---

**Historique — session #132 :**
**Sprint traité :** 34 — Tableau final au calendrier (1ère session du sprint,
2/6 tickets clos — `#325` à `#328` restants à l'époque).

**Git :** branche `claude/sprint/34-tableau-final-calendrier`, parent effectif
`claude/sprint/33-affichage-avantage` (sprint 33 toujours non mergé dans
`main`, déduit depuis `backlog/sprints/done/`). 2 commits de code cette
session.

**Spec review session #132 :** `planning.md`, `admin-matchs.md` et
`cycle-de-vie-match.md` — ⚠️ Dérive mineure en début de session (sprint tout
juste planifié, aucun ticket encore implémenté) → dérives partiellement
résorbées pour `#323`/`#324` traités cette session, le reste attendu pour
`#325`-`#328`. `cycle-de-vie-epreuve.md` — ✅ Conforme. Toutes les dérives
relevées correspondaient exactement aux tickets déjà ouverts lors de la
planification (session précédente) — 0 nouvelle issue créée cette session.

**Backlog engine session #132 :** 2 tickets traités séquentiellement (chaîne
`django-api` puis `reviewer` par ticket), conformément à l'ordre suggéré par
`sprint.md` (les deux back, indépendants, débloquant le front) :
- **#323** (majeure) — back : `live/api_views.py`, `api_edition_calendar` —
  retrait du filtre `stage=GROUP` sur la pile « à planifier » et la colonne
  Annulés (les deux ne couvraient que les poules) ; tri stable ajouté via
  annotation `Case`/`When` (poules avant QF avant SF avant F/P3). Vérifié :
  `reorder_calendar` et `_pack_match` gèrent déjà des sides nuls, aucune
  régression sur les autres usages du filtre `stage=GROUP` (génération de
  poules, `auto_arrange_matches`, classements). Verdict reviewer :
  ✅ Approuvé.
- **#324** (majeure, label `infra`) — back : `live/api_views.py`,
  `api_match_feature` — ajout d'un `try/except ValueError` autour de
  `feature_match(match)`, même pattern que `api_match_start`. La garde
  métier « slot non résolu refuse démarrer » existait déjà dans le service
  partagé `start_match` (dont `feature_match` est un alias direct,
  `live/admin_views.py:554`) et était déjà catchée côté arbitre
  (`referee_views.py`, action `start`) et `api_match_start` — seul le
  chemin « mettre à l'antenne » laissait fuiter un 500 non géré. **Aucun
  câblage de fichier partagé nécessaire** malgré le label `infra` posé lors
  de la planification (signalé par le reviewer, sans impact protocole).
  Verdict reviewer : ✅ Approuvé.

**Point d'attention outillage :** `.venv/bin/python manage.py check` utilisé
pour la vérification back cette session (pas de suite de tests dédiée
identifiée) — fiable, aucune erreur. Toujours pas de script `type-check`
dans `package.json`, toujours pas de `.claude/launch.json` côté front (non
pertinent cette session, aucun ticket front traité).

---

**Historique — session #131 :**
**Sprint traité :** 33 — Avantage (AV) affiché (seule et unique session du
sprint — **clos cette session**, 2/2 tickets clos).

**Roadmap re-remplie depuis la session #130** (5 sprints planifiés le
2026-07-08 : 33 à 37, retours produit TV) — fin de la série de 6 sessions à
vide (#125 à #130). Sprint 33 traité et clos dès la première occasion.

**Git :** branche `claude/sprint/33-affichage-avantage`, parent effectif
`main` (déduit depuis `backlog/sprints/done/` — aucun sprint < 33 avec une
branche encore non mergée dans `main`). 3 commits de code cette session.

**Spec review session #131 :** `tv-live.md` (section score) et
`arbitre-match.md` (section Bloc score) — ⚠️ Dérive mineure en début de
session (mapping local plafonné à « 40 », dupliqué dans les deux SFC,
l'avantage post 40-40 ne s'affichait jamais) → **✅ Conforme** après
implémentation des tickets #321/#322 de cette session. Les deux dérives
étaient déjà ticketées lors de la planification du sprint (session #130) —
0 nouvelle issue créée cette session.

**Backlog engine session #131 :** 2 tickets traités séquentiellement (chaîne
`vue-screen` puis `reviewer` par ticket), malgré le fait que `sprint.md`
suggérait un traitement parallélisable (fichiers disjoints) — le protocole de
l'étape 2 impose le séquentiel :
- **#321** (majeure) — front : `TvScoreboard.vue` — suppression de
  `pointLabel` (mapping local plafonné), affichage direct de
  `live.hero.displayPointA/B` (packer backend, déjà correct), signal
  broadcast `accent-text` symétrisé sur les deux côtés (l'ancien code posait
  la classe en dur côté A uniquement — asymétrie corrigée au passage).
  Verdict reviewer : ✅ Approuvé.
- **#322** (majeure) — front : `ArbitreMatch.vue` — suppression de
  `pointDisplay`/`sidePoints`, ajout de `sideDisplayPoint(side)` lisant
  `match.value.displayPointA/B`, écran resté sobre (pas de mise en accent,
  contrairement à la TV — décision produit). Compatibilité `swap` vérifiée
  (côté modèle `leftModelSide`/`rightModelSide` inchangé). Verdict reviewer :
  ✅ Approuvé.

**Sprint 33 clos cette session :** les deux conditions étaient réunies
(specs conformes après implémentation + 0 issue ouverte sur le milestone).
Milestone GitHub fermé, dossier déplacé vers
`backlog/sprints/done/33-affichage-avantage/`, ligne retirée de
`backlog/sprints/roadmap.md`.

**Roadmap non vide** — 4 sprints restants (34 — Tableau final au calendrier,
35 — TV : scène live & fin de match, 36 — Échauffement, 37 — Mobile :
arbitre & régie). Le sprint 34 sera traité à la **prochaine échéance
planifiée**, pas démarré dans cette session.

**Point d'attention outillage :** confirmation supplémentaire que
`npx vue-tsc -b --force` est fiable, `npx vue-tsc --noEmit` seul ne
type-check aucun fichier `.vue` dans cet environnement. Toujours pas de
script `type-check` dans `package.json`, toujours pas de
`.claude/launch.json` — vérification par type-check + revue de code
uniquement (pas de QA navigateur en session automatisée).

**Nouveau point d'attention (session #128, non revérifié depuis) :** deux
dossiers de sprint orphelins à la racine de `backlog/sprints/` en plus de
leur copie dans `backlog/sprints/done/` : `04-admin-panel-map/` et
`10-contexte-url/`. Sans impact sur le protocole, mais à nettoyer côté
humain (`git rm -r backlog/sprints/04-admin-panel-map backlog/sprints/10-contexte-url`).

**Sprint 19/20/21 — PRs non mergées :** point non revérifié cette session
(hors périmètre du protocole) — dernier état connu (session #125) : 25 PRs
ouvertes empilées depuis le sprint 06, aucune fusionnée dans `main`. À
traiter côté humain.

---

**Historique — session #125 (dernière session avec travail réel) :**
**Sprint traité :** 32 — Arbitre : programme du jour & premier serveur (2ᵉ et
dernière session du sprint — **clos cette session**, 4/4 tickets clos)

**Git :** branche `claude/sprint/32-arbitre-programme-premier-serveur`, parent
effectif `claude/sprint/31-tv-rotation-stable-pastille` (sprint 31 toujours
non mergé dans `main`, déduit depuis `backlog/sprints/done/`). 2 commits de
code cette session.

**Spec review session #125 :** `arbitre-home.md` ✅ Conforme (refonte #311 de
la session précédente reconfirmée). `arbitre-match.md` ⚠️ en début de session
(démarrage sans choix du serveur) → **✅ Conforme** après implémentation des
tickets #312/#313 de cette session — dérive résorbée, 0 nouvelle issue.

**Backlog engine session #125 :** 2 tickets traités séquentiellement (chaîne
« Serveur », agents `django-api`/`vue-screen` puis `reviewer` par ticket) :
- **#312** (majeure) — back : `start_match(match, server=None)` accepte
  désormais un paramètre `server` optionnel (A/B, repère modèle) appliqué au
  démarrage si fourni et valide (sinon `ValueError` → 400 JSON) ; comportement
  legacy (mise en avant admin, édition calendrier) inchangé — vérifié no-op
  sans régression sur les deux autres appelants. Verdict reviewer :
  ✅ Approuvé.
- **#313** (majeure) — front : `ArbitreMatch.vue` — modal de démarrage dédié
  avec choix obligatoire du serveur (aucune présélection, Confirmer grisé
  sans choix), avertissement « autre match en cours » dans le même modal.
  Bug pré-existant corrigé au passage (même zone de code) : `handleStart()`
  consommait `/api/arbitre/matches/` comme tableau plat alors qu'il renvoie
  `{playDays, next}` depuis #310 (session #124) — la détection « autre match
  LIVE » était silencieusement cassée depuis lors ; corrigée (`flatMap`,
  pattern `ArbitreHome.vue`). Verdict reviewer : ✅ Approuvé.

**Sprint 32 clos cette session :** les deux conditions étaient réunies
(specs conformes + 0 issue ouverte sur le milestone). Milestone GitHub fermé,
dossier déplacé vers `backlog/sprints/done/32-arbitre-programme-premier-serveur/`,
ligne retirée de `backlog/sprints/roadmap.md`.

**Roadmap vide.** Aucun sprint suivant en attente — **désactiver la Routine
manuellement sur claude.ai/code/routines**, ou planifier un nouveau sprint
(`/plan-sprint`) avant la prochaine échéance. Pas de PR créée pour cette
session (condition de l'étape 4 non remplie : le sprint n'est plus dans
`roadmap.md` en fin de session).

**Point d'attention outillage :** confirmation supplémentaire (8ᵉ session
de suite) que `npx vue-tsc -b --force` est fiable, `npx vue-tsc --noEmit`
seul ne type-check aucun fichier `.vue` dans cet environnement. Toujours
pas de script `type-check` dans `package.json`, toujours pas de
`.claude/launch.json` — vérification par type-check + revue de code
uniquement (pas de QA navigateur en session automatisée).

**Sprint 19/20/21 — PRs non mergées :** toujours d'actualité, chaîne
désormais bien plus longue (`gh pr list` : 25 PRs ouvertes, empilées depuis
le sprint 06 jusqu'au sprint 30, aucune fusionnée dans `main`). Point à
traiter côté humain (revue/merge des PRs), hors périmètre de la Routine
automatique.
