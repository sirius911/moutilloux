# Migration backlog → GitHub Issues

> Prompt à donner à Claude Code (terminal ou claude.ai/code) pour exécuter la migration complète.
> Repo cible : `sirius911/moutilloux`
>
> **SESSION_ENGINE.md est déjà réécrit** (protocole GitHub Issues). Claude Code n'a pas à le toucher.

---

## PROMPT POUR CLAUDE CODE

Copier-coller tout ce qui suit dans Claude Code :

---

```
Tu es chargé d'exécuter une migration complète du système de backlog du projet
sirius911/moutilloux. Actuellement les tickets vivent dans des fichiers Markdown
sous `backlog/`. L'objectif est de tout basculer dans GitHub Issues + Milestones.

Repo : sirius911/moutilloux (le GitHub MCP est connecté)
Dossier de travail : racine du repo

Exécute les étapes dans l'ordre. Ne saute aucune étape.

---

## ÉTAPE 1 — Créer les labels GitHub

Créer ces labels sur sirius911/moutilloux (ignorer si déjà existants) :

| Nom           | Couleur  | Description                                      |
|---------------|----------|--------------------------------------------------|
| majeure       | #e4541a  | Dérive bloquante / bug UX critique               |
| mineure       | #f5c518  | Amélioration ou écart non bloquant               |
| sprint-02     | #0075ca  | Tickets du sprint 02 — Admin Tournoi (terminé)   |
| sprint-03     | #0075ca  | Tickets du sprint 03 — Admin Shell (courant)     |
| sprint-04     | #0075ca  | Tickets du sprint 04 — Admin Panel Map           |
| à-reprendre   | #d93f0b  | Ticket échoué lors du dernier traitement         |
| en-attente    | #cccccc  | Bloqué par une dépendance externe ou une spec    |
| dérive        | #bfd4f2  | Écart spec découvert lors d'une Spec Review      |
| infra         | #5319e7  | Infrastructure partagée (fichiers orchestrateur) |

---

## ÉTAPE 2 — Créer les Milestones

Créer ces trois milestones sur sirius911/moutilloux :

1. **"Sprint 02 — Admin Tournoi"**
   - State : closed
   - Description : "Écrans admin tournoi (EditionModal, EventModal, AdminTournoi). Terminé le 2026-06-16."

2. **"Sprint 03 — Admin Shell"**
   - State : open
   - Description : "Aligner AdminLayout.vue sur la spec admin-shell.md. Sprint courant."

3. **"Sprint 04 — Admin Panel Map"**
   - State : open
   - Description : "Supprimer route /admin/config, aligner la structure du panel sur admin-panel-map.md."

---

## ÉTAPE 3 — Migrer les tickets ouverts vers GitHub Issues

Pour chaque ticket ci-dessous :
- Lire le fichier `backlog/NNN-titre.md` pour obtenir le corps de l'issue
- Créer une GitHub Issue avec :
  - Titre : exactement comme indiqué dans la colonne "Titre"
  - Body : contenu du fichier NNN-titre.md (markdown brut, sans modification)
  - Labels : comme indiqué
  - Milestone : comme indiqué (ou aucun si "—")

**Tickets 🟠 Majeures (sans sprint) :**

| Fichier | Titre de l'issue | Labels | Milestone |
|---------|-----------------|--------|-----------|
| `016-tvidle-await-manquant-fetchs-ignores.md` | `016 — TvIdle : await manquant → fetchs secondaires jamais exécutés` | majeure | — |
| `017-tvpoules-events-zero-au-lieu-actif.md` | `017 — TvPoules : affiche events[0] au lieu de l'épreuve active` | majeure | — |
| `018-tvlayout-navigation-onglets-absente.md` | `018 — TvLayout : aucune navigation entre les onglets TV` | majeure | — |
| `020-usepolling-pause-onglet-cache.md` | `020 — usePolling : pas de pause sur onglet caché` | majeure | — |
| `021-editMatchPanel-format-silencieusement-ignore.md` | `021 — EditMatchPanel : onglet Format silencieusement ignoré à la sauvegarde` | majeure | — |
| `030-arbitre-match-finish-modal-ferme-sur-erreur.md` | `030 — ArbitreMatch : modale Terminer se ferme même si sendAction échoue` | majeure | — |
| `038-registre-joueur-contact-licence-incomplets.md` | `038 — Registre joueur : contact et licence absents de la chaîne création/lecture/saisie` | majeure | — |
| `041-admin-groups-verrouillage-poules-non-gere.md` | `041 — AdminGroups : verrouillage des poules invisible à l'UI` | majeure | — |
| `042-autofill-groups-non-verrouille-apres-generation.md` | `042 — Backend : autofill_groups non verrouillé après génération des matchs` | majeure | — |
| `043-admin-matches-file-non-reordonnables-kanban-incomplet.md` | `043 — AdminMatches : file non réordonnables au DnD, LIVE en Backlog, annulés invisibles` | majeure | — |

**Tickets 🟠 Majeures (sprint-03) :**

| Fichier | Titre de l'issue | Labels | Milestone |
|---------|-----------------|--------|-----------|
| `055-admin-shell-nav-config-a-supprimer.md` | `055 — Sidebar admin : entrée Configuration à supprimer` | majeure, sprint-03 | Sprint 03 — Admin Shell |
| `056-admin-shell-compteurs-nav-absents.md` | `056 — Sidebar admin : compteurs de navigation absents` | majeure, sprint-03 | Sprint 03 — Admin Shell |
| `057-admin-shell-selecteur-epreuve-etat-vide.md` | `057 — Sidebar admin : sélecteur épreuve non géré si aucune épreuve` | majeure, sprint-03 | Sprint 03 — Admin Shell |

**Tickets 🟠 Majeures (sprint-04) :**

| Fichier | Titre de l'issue | Labels | Milestone |
|---------|-----------------|--------|-----------|
| `060-router-config-non-supprime-decision-11.md` | `060 — Router : route /admin/config non supprimée malgré décision 11` | majeure, sprint-04 | Sprint 04 — Admin Panel Map |

**Tickets 🟡 Mineures (sans sprint) :**

| Fichier | Titre de l'issue | Labels | Milestone |
|---------|-----------------|--------|-----------|
| `024-extract-api-error-incoherent.md` | `024 — extractApiError non utilisé dans plusieurs modales` | mineure | — |
| `025-polling-tv-mal-calibre.md` | `025 — Polling TV mal calibré (TvPoules 5s, TvBracket 10s → cible 4s)` | mineure | — |
| `026-etats-vides-absents.md` | `026 — États vides absents sur plusieurs écrans` | mineure | — |
| `027-useapi-logs-console-production.md` | `027 — useApi : logs de débogage laissés en production` | mineure | — |
| `029-tvidle-donnees-figees-sans-polling.md` | `029 — TvIdle : données kanban/groups/bracket figées (polling absent)` | mineure | — |
| `044-admin-bracket-creation-sans-choix-etape-labels-absents.md` | `044 — AdminBracket : création sans choix d'étape, labels de provenance non éditables` | mineure | — |
| `045-doublon-ensure-final-bracket-exists.md` | `045 — Backend : deux implémentations divergentes de ensure_final_bracket_exists` | mineure, infra | — |

**Tickets 🟡 Mineures (sprint-03) :**

| Fichier | Titre de l'issue | Labels | Milestone |
|---------|-----------------|--------|-----------|
| `058-admin-shell-sous-titre-marque-hardcode.md` | `058 — Sidebar admin : sous-titre de marque hard-codé et état neutre absent` | mineure, sprint-03 | Sprint 03 — Admin Shell |
| `059-admin-shell-fetcheditions-sans-try-catch.md` | `059 — Sidebar admin : fetchEditions sans gestion d'erreur au montage` | mineure, sprint-03 | Sprint 03 — Admin Shell |

**Tickets 🟡 Mineures (sprint-04) :**

| Fichier | Titre de l'issue | Labels | Milestone |
|---------|-----------------|--------|-----------|
| `040-generation-matchs-ecran-poules-au-lieu-matchs.md` | `040 — Génération des matchs de poule portée par Poules au lieu de Matchs` | mineure, sprint-04 | Sprint 04 — Admin Panel Map |
| `050-router-catch-all-absent.md` | `050 — Router : aucune route catch-all → URL inconnue rend une page vide` | mineure, sprint-04 | Sprint 04 — Admin Panel Map |

Total : 25 issues à créer.

---

## ÉTAPE 4 — Créer les issues fermées (historique)

Pour chaque ticket dans `backlog/backlog_done.md`, créer une issue GitHub fermée.
Lire le fichier correspondant dans `backlog/NNN-titre.md` pour le body (si le fichier
existe). Si le fichier n'existe pas, utiliser le titre et la note de backlog_done.md
comme body.

Ajouter le label `sprint-02` pour tous les tickets fermés.
Milestone : "Sprint 02 — Admin Tournoi".
Créer l'issue puis la fermer immédiatement (state: closed).

Liste des tickets fermés à migrer (lire backlog_done.md pour le titre exact) :
001, 002, 003, 004, 005, 006, 007, 008, 009, 010, 011, 012, 013, 014, 015,
019, 022, 023, 028, 031, 032, 033, 034, 035, 036, 037, 039, 046, 047, 048,
049, 051, 052, 053, 054

Note : ignorer les doublons de 034 dans backlog_done.md — créer une seule issue
fermée avec le titre "034 — LoginView : valider le redirect post-login (interne +
permis au rôle)".

---

## ÉTAPE 5 — Simplifier les fichiers sprint.md

Éditer `backlog/sprints/03-admin-shell/sprint.md` :
- Garder le bloc YAML frontmatter complet (sprint, nom, specs, modules, tickets-tag,
  branche, branche-parent, log)
- Garder les sections "Objectif", "Définition de terminé", "Specs ciblées",
  "Périmètre backend", "Ordre d'exécution suggéré"
- **Supprimer** les tableaux de tickets (les tickets sont maintenant dans GitHub Issues)
- Ajouter après "Définition de terminé" :
  `> Les tickets sont gérés dans GitHub Issues (milestone "Sprint 03 — Admin Shell").`

Faire de même pour `backlog/sprints/04-admin-panel-map/sprint.md`.

---

## ÉTAPE 6 — Nettoyer les fichiers obsolètes

Supprimer les fichiers suivants du repo :

**Tickets individuels :**
Tous les fichiers `backlog/[0-9][0-9][0-9]-*.md`

**Fichiers backlog :**
- `backlog/backlog.md`
- `backlog/backlog_done.md`
- `backlog/git-session.sh`

**Plans des tickets clôturés :**
Supprimer dans `backlog/plan/` tous les fichiers correspondant à des tickets maintenant
fermés sur GitHub : 001-015, 019, 022-023, 028, 031-037, 039, 046-049, 051-054.
Garder les plans des tickets encore ouverts (016-018, 020-021, 024-027, 029-030,
038, 040-045, 050, 055-060). Si un plan d'un ticket ouvert n'existe pas, c'est normal —
il sera créé par la prochaine session.

---

## ÉTAPE 7 — Mettre à jour .gitignore

Dans `.gitignore` à la racine :
- Localiser la ligne `backlog/`
- La remplacer par : `backlog/plan/`

(On versionne maintenant SESSION_ENGINE.md, sprints/, logs/, mais pas les plans
qui sont du travail temporaire.)

---

## ÉTAPE 8 — Commit sur main et push

```bash
# S'assurer d'être sur main
git checkout main

# Vérifier si sprint/02-admin-tournoi est mergé
git log --oneline origin/sprint/02-admin-tournoi ^origin/main | head -5
# Si cette commande retourne des commits → sprint 02 PAS encore mergé dans main.
# Dans ce cas : noter dans le log et continuer quand même (migration indépendante).

# Stager, commiter, pusher
git add -A
git commit -m "infra: migration backlog → GitHub Issues (SESSION_ENGINE v2, cleanup)"
git push origin main
```

---

## ÉTAPE 9 — Informer l'utilisateur

Après le push réussi, afficher ce récapitulatif :

"Migration terminée. Actions restantes pour l'humain :
1. Si sprint/02-admin-tournoi n'est pas encore mergé dans main, créer et merger
   la Pull Request sur GitHub.
2. Aller sur https://claude.ai/code/routines et réactiver (ou recréer) la Routine
   SPRINT_ENGINE :
   - Repo : sirius911/moutilloux
   - Schedule : toutes les 5h (0 */5 * * *)
   - Prompt : 'Lis le fichier backlog/SESSION_ENGINE.md dans ce repo et exécute le
     protocole complet (étapes 0 à 4).'
3. La prochaine session traitera le sprint 03 (tickets 055-059)."
```

---

## RÉCAPITULATIF

**Dans GitHub après migration :**
- 9 labels
- 3 milestones (Sprint 02 fermé, 03 et 04 ouverts)
- 25 issues ouvertes (tickets actifs)
- ~35 issues fermées (historique)

**Dans le repo après migration :**

| Fichier | Action |
|---------|--------|
| `backlog/SESSION_ENGINE.md` | ✅ Déjà réécrit (protocole GitHub Issues) |
| `backlog/sprints/roadmap.md` | Inchangé |
| `backlog/sprints/03-admin-shell/sprint.md` | Simplifié (étape 5) |
| `backlog/sprints/04-admin-panel-map/sprint.md` | Simplifié (étape 5) |
| `backlog/sprints/done/` | Inchangé |
| `backlog/logs/` | Inchangé |
| `backlog/plan/` | Plans des tickets clôturés supprimés (étape 6) |
| `backlog/backlog.md` | Supprimé (étape 6) |
| `backlog/backlog_done.md` | Supprimé (étape 6) |
| `backlog/git-session.sh` | Supprimé (étape 6) |
| `backlog/[0-9][0-9][0-9]-*.md` (60 fichiers) | Supprimés (étape 6) |
| `.gitignore` | `backlog/` → `backlog/plan/` (étape 7) |
