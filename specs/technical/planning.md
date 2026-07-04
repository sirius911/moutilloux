---
type: technical
module: planning
fichiers:
  - live/models.py
  - live/api_views.py
  - live/admin_views.py
  - frontend/app/src/stores/event.ts
  - frontend/app/src/views/admin/AdminMatches.vue
---

# Spec technique — Planning des matchs (calendrier)

> Modèle de données, états dérivés et algorithmes communs au **Calendrier des
> matchs** (admin, [[admin-matchs]]) et à ses surfaces publiques TV
> ([[tv-programme]]). Source de vérité du « fonctionnement » du calendrier : les
> specs d'écran décrivent l'UI, celle-ci décrit les règles.

## Principe

Mono-court (décision 12 de [[admin-panel-map]]) : le calendrier est **une file
ordonnée unique**, découpée en **journées**. L'**ordre** (`order_index`) est la
vérité ; les **heures sont estimées** et se recalent au fil du tournoi. Aucune
heure n'est saisie à la main.

---

## Modèle de données

### Champs réutilisés de `Match` (existant — aucune migration)

| Champ | Rôle dans le calendrier |
|---|---|
| `order_index` | rang dans la séquence (déjà **unique par édition**). **Persiste à travers `LIVE`/`FINISHED`** — un match joué garde sa place. `NULL` = **hors séquence** : jamais placé (pile « À planifier ») ou annulé. |
| `scheduled_time` | **porte la journée** : sa *date* = le jour d'affectation. Sa valeur = l'ETA calculée, écrite par le serveur (dérivée, jamais saisie). |
| `court` | mono-court : « Central » seedé, attribué trivialement à l'entrée en séquence. Non discriminant. |
| `status` | `SCHEDULED` / `LIVE` / `FINISHED` / `CANCELED`. Décide si la ligne est **déplaçable** (`SCHEDULED`) ou **verrouillée** (`LIVE`/`FINISHED`) — **pas** sa présence dans la séquence (portée par `order_index`). |
| `is_featured` | match « à l'antenne » TV (hero), pilotable manuellement. |
| `started_at` / `finished_at` | horodatage réel, base du re-flow. |

### Modèles à créer

**`PlayDay`** — une journée de jeu pré-déterminée, par édition.

| Champ | Type | Rôle |
|---|---|---|
| `edition` | FK | l'édition |
| `date` | Date | le jour |
| `start_time` | Time | heure de début de la journée |
| `target_end_time` | Time | heure de fin **cible** (alerte souple) |

**`Break`** — une pause dans la séquence d'une journée (déjeuner, remise des prix).

| Champ | Type | Rôle |
|---|---|---|
| `play_day` | FK | la journée |
| `order_index` | int | rang dans la séquence (cohabite avec les matchs) |
| `duration_min` | int | durée bloquée |
| `label` | str | libellé affiché |

Une pause n'est pas un match : elle ne porte pas de joueurs ; le moteur d'ETA
l'**enjambe** (le curseur avance de `duration_min`).

> **Périmètre MVP** : seuls les matchs de **poule** (`stage = GROUP`) entrent au
> calendrier — leurs deux joueurs sont connus dès la génération. Le bracket
> (QF / SF / F, étiquettes « A1 », « D2 ») est hors périmètre (voir Phase 2).

---

## États dérivés

Les cinq états affichés ne sont **pas stockés** : ils se déduisent de
`status` + planification + `is_featured`.

| État | Règle de dérivation |
|---|---|
| **À planifier** | `SCHEDULED` et `order_index` `NULL` (pas de journée) |
| **Planifié** | `SCHEDULED` avec `order_index` et une journée |
| **Next** | premier `SCHEDULED` de la séquence après le match en cours (plus petit `order_index` non joué de la journée courante) — **calculé**, jamais stocké |
| **En cours** | `LIVE` (un seul par édition — garanti par `mark_live()`). **Conserve son `order_index`** : reste à sa place dans la journée, verrouillé (non déplaçable). |
| **Terminé** | `FINISHED`. **Conserve son `order_index`** : reste à sa place, verrouillé, avec son heure réelle. |

> **Invariant `order_index`.** La place physique dans la séquence est portée par
> `order_index` **de bout en bout** : un match la conserve en passant `LIVE` puis
> `FINISHED`. `order_index = NULL` a **une seule** signification — le match est
> **hors séquence** : soit jamais placé (pile « À planifier »), soit **annulé**.
> Ce n'est donc **pas** le statut qui décide la présence dans une journée, mais la
> seule valeur d'`order_index` ; le **statut** décide seulement si la ligne est
> **déplaçable** (`SCHEDULED`) ou **verrouillée** (`LIVE`/`FINISHED`).

`CANCELED` est l'**annulation sèche** (sans vainqueur) : le match **quitte la
séquence** (`order_index` → `NULL`, `scheduled_time` effacé) et bascule dans une
**colonne « Annulés »** distincte, affichée seulement s'il existe au moins un match
annulé (voir [[admin-matchs]]). Le créneau qu'il libère est récupéré par le
re-flow. Le **forfait** en est distinct : c'est un **walkover** (`FINISHED` +
`is_walkover`, **avec** vainqueur — voir [[cycle-de-vie-epreuve]]) qui **reste à sa
place** dans la journée, verrouillé, libellé « Forfait ». `is_featured` désigne le
match à l'antenne TV : en règle générale le *next* ou le *live*, mais forçable
manuellement (voir [[admin-matchs]], « mettre en avant »).

---

## Algorithme d'estimation des heures (ETA) et re-flow

Par journée, on parcourt sa séquence (matchs + pauses, ordonnés par
`order_index`) avec un curseur `t` initialisé à `start_time` :

- **match terminé** → heure affichée = son heure réelle ; `t = finished_at`.
- **match en cours** → `t = max(maintenant, started_at + durée)`.
- **match planifié** → ETA = `t` ; puis `t += durée`.
- **pause** → `t += duration_min` (aucune heure de match ; bande « Pause »).

`durée` = durée de match par défaut, **25–30 min** (réglable par édition ; une
seule valeur au MVP — durées par format en Phase 2).

Propriétés garanties :
- **Re-flow automatique** : le curseur des matchs à venir est ancré sur
  `max(maintenant, dernière fin réelle)` → un match qui déborde **repousse tout
  l'aval** de sa journée.
- **Jamais d'avance surprise** : une ETA ne recule pas sous l'heure déjà annoncée
  (un match annoncé ~15:00 ne saute pas à 14:40 si on a de l'avance).
- **Journées indépendantes** : chaque journée part de son propre `start_time` ; un
  débordement de la veille ne décale pas le lendemain.

Les heures publiques sont affichées **approximatives** (préfixe `~`), voir
[[tv-programme]].

---

## Règle de repos (détection de conflit)

Sur mono-court, deux matchs ne se chevauchent jamais (ils sont séquentiels). Le
seul conflit réel est le **repos insuffisant** :

> Un joueur ne doit pas jouer **deux matchs consécutifs** : il faut **au moins un
> autre match** entre deux de ses matchs (dans l'ordre de la séquence ; les pauses
> ne comptent pas comme un match intercalé).

- En manuel, deux matchs adjacents partageant un joueur sont **signalés** (⚠),
  sans blocage.
- La pré-pose respecte la règle par construction.
- Cas dégénéré (petite poule où l'évitement est impossible) : best-effort, le
  conflit résiduel reste signalé.

---

## Capacité d'une journée (alerte souple)

Fin estimée d'une journée = valeur finale du curseur ETA. Si elle dépasse
`target_end_time`, la journée est **surlignée** (« dépasse HH:MM »), **sans
blocage** : on n'empêche pas d'ajouter des matchs au-delà de la cible.

---

## Heuristique de pré-pose (« Pré-poser »)

Action qui range automatiquement les matchs **à planifier** (la pile), sans
toucher à ce qui est déjà placé :

1. Grouper les matchs à planifier par poule.
2. Construire l'ordre en **entrelaçant les poules** (A, B, C, A, B, C…) — ce qui
   sépare naturellement les deux matchs d'un même joueur et respecte le repos.
3. **Distribuer sur les journées** dans l'ordre : remplir la première journée tant
   que sa fin estimée reste ≤ `target_end_time`, puis déborder sur la suivante.
4. **Ne consomme que la pile** : les matchs déjà planifiés (et les ajustements
   manuels) ne sont jamais réorganisés. Relancer « Pré-poser » ne range que les
   nouveaux à-planifier.

---

## Contrat d'API

### Réutilisé (existant)

| Endpoint | Usage calendrier |
|---|---|
| `POST /api/events/<id>/matches/generate/` | génère le round-robin → matchs en **à planifier** (`SCHEDULED`, sans `order_index`). Désormais appelé par **« Débuter l'épreuve »** (qui verrouille les poules et passe l'épreuve `EN_COURS`, voir [[cycle-de-vie-epreuve]]) ; réutilisé tel quel pour l'ajout tardif (additif). |
| `POST /api/editions/<id>/calendar/reorder/` | applique l'ordre complet du calendrier (drag) ; (ré)attribue `order_index` par journée. Les matchs `LIVE`/`FINISHED` sont **fixes** : leur rang est préservé, jamais recalculé. **Contrat** : le payload couvre toutes les journées avec la **séquence complète de l'édition** — tout match `SCHEDULED` absent du payload est **renvoyé à la pile** (`order_index` et `scheduled_time` effacés) ; c'est ainsi qu'un drag vers la pile dé-planifie. Un client ne doit donc **jamais filtrer** la séquence (par épreuve ou autre) avant de la renvoyer. |
| `POST /api/matches/<id>/edit/` | édition fine (score correctif, format, statut, journée, mise en avant). |
| `POST /api/matches/<id>/feature/` | passe le match à l'antenne (→ `LIVE`, `is_featured`) **sans effacer son `order_index`** : le match reste à sa place. |
| `POST /api/events/<id>/matches/auto-arrange/` | applique l'heuristique de pré-pose côté serveur (`live/urls.py:98`, `api_matches_auto_arrange` — `api_views.py:1799`). |
| CRUD `PlayDay` | gérer les journées de jeu (date, début, fin cible). Surface UI : modale **« Gérer les journées »** de [[admin-matchs]]. **Suppression refusée** si la journée porte encore des matchs ou des pauses (`live/urls.py:86-89` ; `api_play_days_list:1541`, `api_play_day_create:1551`, `api_play_day_edit:1576`, `api_play_day_delete:1611`). |
| CRUD `Break` | insérer / déplacer / retirer une pause dans une journée (déjà branché côté Calendrier) (`live/urls.py:91-94` ; `api_breaks_list:1623`, `api_break_create:1633`, `api_break_edit:1659`, `api_break_delete:1691`). |
| Packer « calendrier » (lecture) | matchs regroupés par journée + ordonnés + la pile à planifier ; réutilise `_pack_match` (`api_views.py:97`) (`live/urls.py:96`, `api_edition_calendar` — `api_views.py:1702`). Les ETA peuvent être calculées côté front. |
| Enrichissement de l'état TV | exposer les **N prochains matchs planifiés** + le **next** pour [[tv-programme]] (`live/urls.py:100`, `api_tv_upcoming` — `api_views.py:1817`). |

> **Retrait.** L'ancien endpoint kanban `POST /api/events/<id>/matches/reorder/`
> (`reorder_event_matches`) est **supprimé** : il remettait à `NULL` l'`order_index`
> de tout l'event et n'est plus branché (le calendrier réordonne via
> `calendar/reorder/`). Corollaire : **aucune** transition de statut (`mark_live`,
> fin de match arbitre, forfait, édition → `FINISHED`, mise en avant) n'efface plus
> `order_index` ; seules la **génération** (pile) et l'**annulation** le laissent /
> le remettent à `NULL`.

> Conventions back (CLAUDE.md §5) : chaque mutation est d'abord une **fonction de
> service** réutilisable dans `admin_views.py`, exposée ensuite par un endpoint
> `/api/` fin ; `live/urls.py` est câblé par l'orchestrateur.

---

## Hors périmètre (Phase 2)

- **Bracket au calendrier** : planifier QF / SF / F avec participants « à désigner »
  (étiquettes A1 / D2) tant que les poules ne sont pas finies.
- **Multi-court** : le mono-court est une hypothèse ferme (décision 12). Si elle
  tombe, l'agenda devient une grille Temps × Courts — le champ `court` le supporte
  déjà.
- **Durées par format / apprises** : une durée par format (poule ≠ finale), voire
  apprise de `finished_at − started_at` (les horodatages existent déjà).
- **Heures ancrées** : figer l'heure réelle de certains matchs (ex. finale à
  17:00) — écarté au MVP (heures purement dérivées).
