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

**Dernière session :** 2026-07-04 — Session #80
**Sprint actif :** 21 — Durcissements API & specs.

**Git :** branche `claude/sprint/21-durcissements-api-specs`, parent effectif
`claude/sprint/20-transverse-erreurs-routing` (sprint 20 toujours non mergé
dans `main` — point récurrent depuis plusieurs sessions, à traiter côté
humain). Working tree propre au démarrage, pas de conflit de merge (déjà à
jour avec le parent).

**Spec review session #80 :** review indépendante des 4 specs, refaite après
la réconciliation #248 (commit `e324629`, postérieur à la review de la
session #79). `planning.md` → ✅ Conforme : les 5 endpoints réconciliés
vérifiés aux emplacements cités ; #249 et #250 toujours valides tels que
décrits (non re-signalés comme nouveaux). `cycle-de-vie-epreuve.md` et
`cycle-de-vie-match.md` → ✅ Conforme, aucun commit sur les fichiers cités
depuis la session #79. `admin-tournoi.md` → ⚠️ Dérive mineure (nouvelle,
non vue en session #79) : la spec décrit encore un bouton « Sélectionner »
par carte d'épreuve, retiré du code par le commit `4ed55bc` (issue #208,
sprint 20) — sélection désormais portée par navigation directe via l'URL
(cohérent avec le principe existant, juste une description d'UI obsolète).
Nouvelle issue #251 créée. Détail complet dans
`backlog/logs/session_2026-07-04_80.md`.

**Tickets traités session #80 :** 2 (#216, #249) —
- **#216** : ajout d'un champ « Durée de match par défaut (min) » dans
  `EditionModal.vue` (borné ≥ 1, défaut 27, cohérent avec le back), câblage
  du payload (`EditionPayload.default_match_duration_min` dans `event.ts`,
  fichier partagé câblé par l'orchestrateur), spec `admin-tournoi.md`
  complétée. ✅ Approuvé. Commit `07298fa`.
- **#249** : `CLAUDE.md` corrigé — le calendrier admin (2 s réels) était classé
  à tort dans le groupe ~5 s ; reclassé avec arbitre/scoreboard. Corrigé au
  passage une incohérence adjacente (mention « cible ~4 s bracket ... encore
  à appliquer » devenue stale face au §4 qui documente déjà la migration
  comme faite). ✅ Approuvé. Commit `3d7d085`.

Reviews réalisées par des agents `reviewer` distincts en lecture seule, un
par ticket, avant clôture. Écart mineur au séquencement strict : #249 (2
lignes de doc, vérifiées par grep) planifié/implémenté directement par
l'orchestrateur en parallèle de l'agent `vue-screen` sur #216, plutôt que
strictement l'un après l'autre — jugé sans risque vu la triviale
non-ambiguïté du changement. Erreur de manipulation git corrigée en session
(un `git add -A` avait groupé les deux tickets dans un seul commit ; scindé
via `git reset --soft` avant tout push, aucune perte).

**Écart au protocole :** sélection volontaire de #216 et #249 (actionnables
sans arbitrage produit préalable) ; #215, #219 laissés de côté (leur body
exige explicitement une « décision produit d'abord », comme les sessions
précédentes) ; #250 laissé de côté pour la même raison (« à trancher » entre
hors-scope assumé ou mémorisation de l'ETA — jugement de conception réservé
à une session humaine) ; #251 (créé cette session) non traité dans la même
session, cohérent avec la limite de 2 tickets/session.

**Fin de sprint non atteinte :** spec review avec 1 dérive (⚠️
admin-tournoi.md) + 4 issues encore ouvertes sous le milestone Sprint 21
(#215, #219, #250, #251). La suite sera traitée à la prochaine échéance
planifiée.

**Sprint 19/20 — PRs non mergées :** toujours d'actualité. Point à traiter
côté humain (revue/merge des PRs), hors périmètre de la Routine automatique.

**Roadmap :** 1 sprint actif (21 — Durcissements API & specs), en cours
(9/13 tickets clos, 4 restants).
