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

**Dernière session :** 2026-07-09 — Session #136
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
