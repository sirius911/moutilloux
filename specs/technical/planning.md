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
> ([[tv-live]]). Source de vérité du « fonctionnement » du calendrier : les
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
| `scheduled_time` | **porte la journée** : sa *date* = le jour d'affectation (l'heure stockée n'est qu'un placeholder posé à l'affectation). L'**ETA affichée est calculée à la lecture, côté serveur** (voir « Où vit le calcul ») — jamais saisie, jamais persistée (arbitrage 2026-07-11). |
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

> **Périmètre** : **tous les matchs** entrent au calendrier — les matchs de
> **poule** (joueurs connus dès la génération) **et** les matchs de **tableau**
> (QF / SF / F / P3), planifiables dès la création du squelette avec leurs
> étiquettes de provenance (« A1 vs D2 », « Vainqueur QF1 ») tant que les
> joueurs ne sont pas résolus. Voir « Matchs de tableau au calendrier »
> ci-dessous. *(L'exclusion initiale du bracket — ex-« Phase 2 » — est levée :
> retours TV du 2026-07-08.)*

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
`order_index`) avec un curseur `t` initialisé à `start_time`. Le curseur est
**monotone : il ne recule jamais** — c'est lui qui garantit « jamais d'avance
surprise » :

- **match terminé** → heure affichée = son heure réelle de début ;
  `t = max(t + durée, finished_at)`. Un match fini **en avance** ne tire donc
  pas l'aval vers l'avant (la marge devient du temps de pause naturel) ; un
  match fini **en retard** pousse tout l'aval.
- **match en cours** → heure affichée = son heure réelle de début ;
  `t = max(t + durée, started_at + durée, maintenant)`. C'est le **démarrage
  réel** d'un match qui recale l'aval : démarré à l'heure ou en avance, rien ne
  bouge ; démarré en retard (ou s'éternisant au-delà de sa durée), tout l'aval
  se décale.
- **match planifié** → ETA = `t` ; puis `t += durée`.
- **pause** → `t += duration_min` (aucune heure de match ; bande « Pause »).

`durée` = durée de match par défaut, **par étape** (constantes applicatives,
pas de config) : **poule** ~30 min, **QF/SF** ~30–35 min, **finale / 3e place**
~45 min — valeurs à caler sur les formats réels (`_fmt_for_stage`,
`live/bracket.py`) au moment de l'implémentation. La durée **inclut
l'échauffement** : `started_at` est posé à l'entrée en échauffement (le court
est occupé dès ce moment — voir [[cycle-de-vie-match]]).

Propriétés garanties :
- **Re-flow automatique** : un match qui déborde (démarrage tardif ou durée
  dépassée) **repousse tout l'aval** de sa journée.
- **Jamais d'avance surprise** : le curseur étant monotone, une ETA ne recule
  jamais sous l'heure dérivée des durées par défaut (un match annoncé ~15:00 ne
  saute pas à 14:40 si on a de l'avance). Le match suivant **peut** être démarré
  en avance par l'arbitre — rien ne l'y oblige, et son ETA affichée n'aura pas
  bougé.
- **Journées indépendantes** : chaque journée part de son propre `start_time` ; un
  débordement de la veille ne décale pas le lendemain.

**Où vit le calcul (arbitrage 2026-07-11).** L'algorithme est implémenté **une
seule fois, côté serveur**, en fonction de service, et appliqué **à la
lecture** : les packers renvoient dans `scheduledTime` l'ETA du moment pour
les matchs `SCHEDULED` planifiés (heure réelle de début pour `LIVE` /
`FINISHED`). Toutes les surfaces (calendrier admin, `tv/state`, `tv/idle`,
programme arbitre) affichent ainsi des heures recalées en continu par l'heure
courante, sans écriture en base. Le moteur front d'[[admin-matchs]] ne sert
plus qu'à la **préview locale pendant un drag** ; l'affichage au repos vient
du serveur.

Les heures publiques sont affichées **approximatives** (préfixe `~`), voir
[[tv-live]].

**Format canonique du préfixe `~` (arbitrage 2026-07-14, #398).** Le préfixe
`~` fait partie de la chaîne `scheduledTime` renvoyée par le serveur — il
n'est **jamais** ajouté côté client. Un client qui affiche `scheduledTime`
l'affiche tel quel (`m.scheduledTime ?? '—'`), sans re-préfixer, sous peine
de double tilde (`~~14h30`) sur un match `SCHEDULED`, ou d'un `~` erroné sur
l'heure réelle d'un match `LIVE`/`FINISHED`.

**Heures au-delà de minuit (arbitrage 2026-07-14, #397).** Le curseur `t` est
un entier de minutes **continu, jamais wrappé pendant le calcul** — ancré sur
la date de la journée (`play_day.date`/`day.date`), pas sur l'heure brute d'un
`started_at`/`finished_at` qui pourrait tomber un autre jour (match
rejoué/reporté). Le **wrap 24h ne se fait qu'à l'affichage** : une ETA à 1541
min s'affiche « ~01h41 », pas « ~25h41 ». Pas de mention « +1 jour » — aucune
autre surface du produit n'affiche de badge de jour. Cette règle s'applique
identiquement côté serveur (`_min_to_hhmm`, `_dt_to_min`) et côté front
(`AdminMatches.vue::minToTime`, `isoToMin`, préview de drag uniquement).

---

## Indicateur de ponctualité (rouge / orange / vert)

État **dérivé, jamais stocké**, calculé par rapport à l'ETA et à une
**tolérance de 5 min**. Surface : teinte de la ligne du calendrier admin
([[admin-matchs]]) ; repris dans la légende.

| Couleur | Règle |
|---|---|
| **Rouge** — en retard, pas démarré | `SCHEDULED` planifié et `maintenant > ETA + 5 min` |
| **Orange** — démarré mais en retard | `LIVE` et (`started_at > ETA + 5 min` **ou** `maintenant > started_at + durée + 5 min` — le match s'éternise) |
| **Vert** — démarré et à l'heure | `LIVE`, démarré dans la tolérance et dans sa durée |

Les matchs `SCHEDULED` encore dans les temps, `FINISHED` et `CANCELED` ne
portent **aucune** teinte de ponctualité (leurs états existants suffisent).
L'indicateur se recalcule en continu (au rythme du polling de l'écran).

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
- **Matchs de tableau** : la règle est **inévaluable** tant que les joueurs ne
  sont pas résolus — best-effort, le ⚠ apparaît quand les slots se résolvent.

---

## Matchs de tableau au calendrier

Les matchs de tableau (QF / SF / F / P3) suivent les **mêmes règles** que les
matchs de poule, avec les particularités suivantes :

- **Entrée dans la pile « à planifier » dès « Débuter »** : le squelette créé
  par la transition Débuter ([[cycle-de-vie-epreuve]]) fait naître ses matchs
  `SCHEDULED` sans `order_index` — ils apparaissent immédiatement dans la pile,
  affichés avec leurs **étiquettes de provenance** (`side_a_label` /
  `side_b_label` de `_pack_match` : « A1 vs D2 », « Vainqueur QF1 vs Vainqueur
  QF2 »). L'organisateur peut ainsi **réserver les créneaux de la phase finale
  avant la fin des poules** ; le public voit « Quart de finale — A1 vs D2 ·
  ~14h » sur la TV.
- **Garde de démarrage** : un match de tableau dont un slot n'est pas résolu
  **refuse `démarrer`** (garde serveur, voir [[cycle-de-vie-match]]). Le
  planifier est permis ; le jouer, non.
- Une fois placés (`order_index`), ils bénéficient de **tout le circuit
  existant** sans logique dédiée : définition du *next*, « À suivre » et slide
  Programme TV, programme arbitre, indicateur de ponctualité, panneau
  d'édition.
- **Pré-pose** : l'heuristique continue de **ne consommer que les matchs de
  poule** (son entrelacement est par poule) ; les matchs de tableau (≤ 8 par
  épreuve) se placent **à la main**.
- **Finale à heure fixe** : pas d'heure ancrée — une **pause** dimensionnée
  avant la finale cale son début (le moteur d'ETA l'enjambe). L'ancrage vrai
  reste hors périmètre (voir plus bas).

---

## Capacité d'une journée (alerte souple)

Fin estimée d'une journée = valeur finale du curseur ETA. Si elle dépasse
`target_end_time`, la journée est **surlignée** (« dépasse HH:MM »), **sans
blocage** : on n'empêche pas d'ajouter des matchs au-delà de la cible.

**Source au repos (#397).** Comme pour `scheduledTime`, le calendrier
(`GET /api/editions/<id>/calendar/`) expose la fin de journée calculée côté
serveur sur chaque `PlayDay` packée : `estimatedEnd` (`"HH:MM"`, wrappée 24h,
pour l'affichage) et `estimatedEndMin` (le même curseur **non wrappé**,
utilisé pour la comparaison à `target_end_time` — une journée qui déborde
après minuit doit rester détectée en dépassement même si son affichage
wrappe à une petite heure). Le moteur front (`AdminMatches.vue::etaEngine`)
ne recalcule ces deux valeurs que pour la **préview pendant un drag** ; au
repos, l'écran lit `estimatedEnd`/`estimatedEndMin`.

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
| `POST /api/editions/<id>/play-days/generate/` | **génération des journées depuis les dates de l'édition** : crée une `PlayDay` par jour entre `start_date` et `end_date` de l'édition (bornes incluses), en **sautant** les dates portant déjà une journée. Plage horaire commune passée dans le body (défaut proposé par l'UI : **9:00 → 20:00**), modifiable journée par journée ensuite (CRUD). Refusée si l'édition n'a pas ses deux dates. Surface UI : modale « Gérer les journées » de [[admin-matchs]]. *(Endpoint à créer — service d'abord, convention CLAUDE.md §5.)* |
| CRUD `PlayDay` | gérer les journées de jeu (date, début, fin cible). Surface UI : modale **« Gérer les journées »** de [[admin-matchs]]. **Suppression refusée** si la journée porte encore des pauses, ou des matchs `SCHEDULED`/`LIVE` (ces derniers sont **actionnables** : renvoyer d'abord les matchs vers la pile « à planifier » puis réessayer). Si la journée porte au moins un match `FINISHED`, le refus est **définitif** : la journée est conservée comme **archive** et ne redevient jamais supprimable (`live/urls.py:86-89` ; `api_play_days_list:1541`, `api_play_day_create:1551`, `api_play_day_edit:1576`, `api_play_day_delete:1611`). |
| CRUD `Break` | insérer / déplacer / retirer une pause dans une journée (déjà branché côté Calendrier) (`live/urls.py:91-94` ; `api_breaks_list:1623`, `api_break_create:1633`, `api_break_edit:1659`, `api_break_delete:1691`). |
| Packer « calendrier » (lecture) | matchs regroupés par journée + ordonnés + la pile à planifier ; réutilise `_pack_match` (`api_views.py:97`) (`live/urls.py:96`, `api_edition_calendar` — `api_views.py:1702`). Les ETA sont renvoyées par le serveur (calcul à la lecture, voir « Où vit le calcul ») ; le front ne garde qu'une préview de drag. **La pile et la colonne Annulés couvrent tous les stages** (le filtre `stage=GROUP` du MVP est retiré — voir « Matchs de tableau au calendrier »). |
| Enrichissement de l'état TV | exposer les **N prochains matchs planifiés** + le **next** pour [[tv-live]] (`live/urls.py:100`, `api_tv_upcoming` — `api_views.py:1817`). |

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

## Hors périmètre

- **Multi-court** : le mono-court est une hypothèse ferme (décision 12). Si elle
  tombe, l'agenda devient une grille Temps × Courts — le champ `court` le supporte
  déjà.
- **Durées apprises** : affiner les constantes par étape avec
  `finished_at − started_at` (les horodatages existent déjà).
- **Heures ancrées** : figer l'heure réelle de certains matchs (ex. finale à
  17:00) — toujours écarté (heures purement dérivées) ; le contournement
  retenu est la **pause** avant la finale (voir « Matchs de tableau au
  calendrier »). À rouvrir si le contournement s'avère pénible.

> *(« Bracket au calendrier », l'ancienne Phase 2, est entré au périmètre —
> retours TV du 2026-07-08, section « Matchs de tableau au calendrier ».)*
