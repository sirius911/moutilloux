# BACKLOG ENGINE — Moutilloux

> **Comment déclencher :** ouvre un nouveau chat et dis simplement _"Lance le backlog engine"_ (ou colle ce fichier). L'agent lit ce fichier, exécute le protocole, puis s'arrête.

---

## 1. Contexte du projet

**Moutilloux** est une application Django de gestion de tournoi de tennis.  
- Backend : Django (moteur de score, classements, bracket, rôle Arbitre)  
- Frontend : SPA Vue 3 + Vite + TypeScript + Pinia + Vue Router  
- Racine du projet : `/Users/maximelorin/Desktop/dev/moutilloux/`  
- Bash (sandbox) : `/sessions/*/mnt/moutilloux/`

**Règle d'or :** on n'écrit aucune logique métier. On expose et on branche.

---

## 2. Structure des fichiers d'orchestration

```
backlog/
├── BACKLOG_ENGINE.md   ← ce fichier (moteur)
├── backlog.md          ← BDD des tickets EN ATTENTE (source de vérité)
├── backlog_done.md     ← tickets CLÔTURÉS (archivés ici en fin de session)
├── logs/
│   └── session_YYYY-MM-DD_N.md   ← log de chaque session
├── plan/               ← plans d'implémentation générés par session
│   └── NNN-titre.md
└── NNN-titre.md        ← fichiers détail de chaque ticket
```

---

## 3. Protocole d'exécution

### Étape 0 — Lecture de l'état courant

Lire `backlog/backlog.md` et identifier les **6 premiers tickets non traités**, en respectant cet ordre de priorité :
1. 🔁 **À reprendre** en premier (tickets bloqués lors d'une session précédente)
2. 🔴 Critiques
3. 🟠 Majeures
4. 🟡 Mineures

> **⏸️ En attente** : les tickets marqués `⏸️ En attente` sont **exclus de la sélection**. Ils représentent des besoins de spec non encore rédigés par l'humain. Ne jamais les traiter.

**Pour les tickets `🔁 À reprendre` :** le plan existant dans `backlog/plan/NNN-titre.md` contient déjà une section `## ❌ Problème bloquant` documentant ce qui n'a pas fonctionné. L'agent de planification (Étape 1) doit lire ce plan existant en entier — problème inclus — avant de rédiger un plan corrigé à la suite.

### Étape 1 — Planification → Implémentation → Review (séquentiel, ticket par ticket)

Traiter les tickets **un par un**, dans l'ordre de priorité défini à l'étape 0.
Pour chaque ticket, enchaîner les trois sous-étapes 1a / 1b / 1c avant de passer au ticket suivant.

#### 1a — Planification

Lancer **un agent de planification**.

L'agent :
- Lit le fichier ticket `backlog/NNN-titre.md`
- Lit les fichiers source concernés dans le projet
- **Si le ticket précise une spec source** (`specs/screens/…` ou `specs/transverse/…`) : lire cette spec avant de planifier
- Produit un plan dans `backlog/plan/NNN-titre.md` selon le format ci-dessous
- Ne modifie aucun autre fichier

**Format du fichier plan `backlog/plan/NNN-titre.md` :**

```markdown
# Plan — NNN : Titre du ticket

## Contexte
[Résumé du problème et des fichiers concernés]

## Modifications prévues
[Liste des fichiers à modifier et ce qui change]

## Fichiers partagés à câbler par l'orchestrateur
[Si applicable — routes urls.py, imports stores, etc.]

## Specs impactées
[Si des fichiers couverts par une spec dans `specs/` sont modifiés, lister ici :]
- `specs/screens/login.md` — [décrire ce qui change et pourquoi la spec doit être mise à jour]

> Si cette section est renseignée, l'orchestrateur déclenchera un agent de maintenance
> de spec après l'implémentation et avant la review.
```

> Si aucune spec n'est impactée, la section "Specs impactées" peut être omise ou laissée vide.

#### 1b — Implémentation

Lancer **un agent d'implémentation**.

L'agent :
- Lit son fichier plan `backlog/plan/NNN-titre.md`
- Applique les modifications dans les fichiers du projet
- **Ne touche PAS ces fichiers partagés** (réservés à l'orchestrateur) :
  - `live/urls.py`
  - `frontend/app/src/router/index.ts`
  - `frontend/app/src/stores/auth.ts`, `event.ts`, `live.ts`
  - `frontend/app/src/composables/useApi.ts`, `usePolling.ts`
  - `frontend/app/src/main.ts`
- Signale explicitement si une modification de fichier partagé est nécessaire

Après l'agent d'implémentation :
1. **L'orchestrateur câble lui-même** les fichiers partagés si nécessaire (routes `urls.py`, imports stores, etc.)
2. **Si le plan contient une section "Specs impactées" renseignée** → lancer un agent de maintenance de spec :
   - Lit le plan et la spec concernée
   - Met à jour **uniquement le champ `fichiers:` de l'en-tête YAML** si des fichiers ont été renommés, déplacés ou ajoutés
   - **Ne modifie jamais le contenu de la spec** (comportement attendu, flux, règles) — ce contenu est réservé à l'humain
   - Ne touche qu'à la spec, pas au code

#### 1c — Review

Lancer **un agent reviewer**.

L'agent :
- Lit le plan, les fichiers modifiés, et les fichiers de contexte
- Rend un verdict : `✅ Approuvé` / `⚠️ Approuvé avec réserves` / `❌ À corriger`
- Liste les problèmes trouvés avec sévérité (critique / majeure / mineure)

Mettre à jour le backlog immédiatement après le verdict (étape 4 ci-dessous), puis passer au ticket suivant.

### Étape 2 — Mise à jour du backlog (après chaque ticket)

Pour chaque ticket reviewé :

**Si `✅ Approuvé` ou `⚠️ Approuvé avec réserves` (réserves mineures) :**
- Supprimer la ligne du ticket dans `backlog/backlog.md`
- Ajouter une entrée dans `backlog/backlog_done.md` avec la date et le verdict

**Si `❌ À corriger` :**
- Laisser le ticket dans `backlog/backlog.md` avec un statut `🔁 À reprendre`
- **Ajouter à la fin du fichier plan** `backlog/plan/NNN-titre.md` la section suivante :

```markdown
---

## ❌ Problème bloquant — [YYYY-MM-DD session N]

**Verdict reviewer :** [copier le verdict complet]

**Problème(s) identifié(s) :**
- [description précise de chaque blocage]

**Piste de correction :**
- [suggestion du reviewer]

> Ce plan sera relu intégralement lors de la reprise du ticket.
```

- Documenter le ticket dans le log de session (section "Tickets à reprendre")

**Si le reviewer a trouvé de nouveaux problèmes :**
- Créer un nouveau ticket `NNN-titre.md` (prochain numéro disponible)
- L'ajouter dans `backlog/backlog.md` à la bonne sévérité

**Si l'implémentation révèle un besoin de spec** (nouvelle modale, nouveau comportement non spécifié, etc.) :
- Créer un fichier `specs/need_spec/NNN-titre.md` décrivant le besoin (ce qui manque, pourquoi)
- Ajouter le ticket lié dans `backlog/backlog.md` avec le statut `⏸️ En attente` et la mention `Attend spec : specs/need_spec/NNN-titre.md`
- Ce ticket ne sera traité qu'une fois la spec rédigée par l'humain et le statut retiré

### Étape 3 — Log de session et condition d'arrêt

Créer `backlog/logs/session_YYYY-MM-DD_N.md` (N = numéro de session du jour, commence à 1).

Format du log :

```markdown
# Session YYYY-MM-DD — N°X

**Tickets traités :** N
**Durée estimée :** ~X min

## Tickets clôturés
| # | Titre | Verdict |
|---|-------|---------|
| NNN | ... | ✅ / ⚠️ |

## Nouveaux tickets créés (par les reviewers)
| # | Titre | Sévérité | Source |
|---|-------|----------|--------|
| NNN | ... | 🟡 | reviewer ticket YYY |

## Tickets à reprendre (❌ non clôturés)
| # | Titre | Raison |
|---|-------|--------|

## Fichiers partagés câblés par l'orchestrateur
- `live/urls.py` : [description des routes ajoutées]
- (etc.)

## Problèmes d'orchestration rencontrés
[Tout ce qui a bloqué ou dévié du protocole normal]
```

Après avoir écrit le log, mettre à jour la section **6. État de la dernière session** de ce fichier avec la date, le nombre de tickets restants et le prochain numéro disponible.

**Condition d'arrêt :** si `backlog.md` est vide après la session →
- Écrire dans le log : _"Backlog vide — passage au cycle de review des specs."_
- Désactiver `moutilloux-backlog-engine` via `update_scheduled_task` avec `enabled: false`
- Activer `moutilloux-spec-review` via `update_scheduled_task` avec `enabled: true`
- Le SPEC_REVIEW_ENGINE prendra le relais et réactivera le backlog engine si des dérives sont trouvées

> La tâche planifiée tourne toutes les 6h automatiquement — l'agent n'a pas à se re-planifier lui-même.

---

## 4. Règles strictes

- **Un agent = un ticket.** Jamais un agent qui touche les fichiers d'un autre ticket.
- **Les agents ne se parlent pas.** Ils remontent uniquement à l'orchestrateur.
- **Fichiers partagés = orchestrateur uniquement** (voir liste à l'Étape 2).
- **Ne jamais enchaîner deux sessions sans créer le log** de la précédente.
- **Pas de logique métier Django à réécrire.** Extraire et exposer uniquement.
- Si un agent ne trouve pas un fichier cité dans le plan, il le signale et s'arrête — il n'invente pas.

## 5. État de la dernière session

> Mis à jour automatiquement par l'agent en fin de session.

**Dernière session :** 2026-06-12 — Session 2  
**Tickets restants dans backlog.md :** 30 (tickets 038–046 ajoutés hors session, lors de la rédaction des specs admin)  
**Prochain numéro de ticket disponible :** 047
