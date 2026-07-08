---
type: technical
module: cycle-de-vie
fichiers:
  - live/models.py
  - live/referee_views.py
  - live/admin_views.py
  - live/api_views.py
  - competition/standings.py
  - live/bracket.py
  - frontend/app/src/views/arbitre/ArbitreMatch.vue
  - frontend/app/src/views/admin/AdminMatches.vue
  - frontend/app/src/stores/live.ts
---

# Spec technique — Cycle de vie d'un match

> Comment un **match** unique progresse de « prévu » à « terminé » (ou « annulé ») :
> un statut stocké, des transitions explicites, et **qui** a le droit de les
> déclencher. Source de vérité du grain **match**, complémentaire de
> [[cycle-de-vie-epreuve]] (grain **épreuve**) et de [[planning]] (le calendrier).
> Les écrans [[arbitre-match]], [[arbitre-home]] et [[admin-matchs]] décrivent l'UI ;
> celle-ci décrit les états et les règles communes aux deux espaces.

## Principe

Un match est piloté depuis **deux surfaces** qui partagent la **même logique** :
- l'**arbitre** (tablette iPad, [[arbitre-match]]) — la saisie temps réel ;
- l'**admin** (panneau d'édition du calendrier, [[admin-matchs]]) — la régie et les
  corrections.

Règle d'architecture (CLAUDE.md §5) : chaque transition est **une fonction de
service unique** dans le back (`démarrer`, `terminer`, `forfait`, `annuler`,
`rouvrir`), appelée aussi bien par l'endpoint arbitre (`POST /arbitre/match/<id>/action/`)
que par l'écran admin. **Une seule vérité, deux écrans** — jamais deux implémentations.

---

## La machine à états

Statut stocké sur `Match.status` (déjà présent, `models.py:23`) :

```
                    ┌──── forfait (walkover, vainqueur) ─────────────► FINISHED
                    │                                                   ▲  │  ▲
   SCHEDULED ──démarrer──► LIVE ──point gagnant / terminer manuel───────┘  │  │
   « prévu »    │           │                                              │  │
               │           ├──── abandon (vainqueur, score figé) ─────────┘  │
               │           │                                                 │
               │           │                            FINISHED ──rouvrir───┘
               └── annuler ─┴──► CANCELED               (score CONSERVÉ, ADMIN seul)
                    « Annulés » (sans vainqueur)
```

| Statut | Libellé UI | Sens |
|---|---|---|
| `SCHEDULED` | PRÉVU | pas encore commencé (planifié ou « à planifier ») |
| `LIVE` | EN DIRECT | en cours de jeu, alimente le scoreboard TV |
| `FINISHED` | TERMINÉ | joué jusqu'au bout, forfait, ou abandon — **avec vainqueur** |
| `CANCELED` | ANNULÉ | annulation sèche, **sans vainqueur** (voir [[admin-matchs]]) |

### Invariant : un seul match `LIVE` par édition

`mark_live()` (`models.py:147`) rétrograde **automatiquement** tout autre match
`LIVE` de la même édition en `SCHEDULED` avant de passer celui-ci `LIVE`. C'est la
traduction du modèle **court central unique** : on ne joue qu'un match à la fois,
et le match `LIVE` **est** le match affiché sur la TV ([[tv-live]]). Démarrer le
match suivant « met en pause » le précédent (il repasse `SCHEDULED` en **conservant
son score** ; il pourra être repris).

### Les deux phases de `LIVE` : échauffement puis jeu

`LIVE` se subdivise en **deux phases dérivées** de deux horodatages — pas de
statut supplémentaire :

| Champ | Posé par | Sens |
|---|---|---|
| `warmup_started_at` | l'entrée en `LIVE` d'un match jamais lancé | début de l'échauffement (le court est occupé) |
| `play_started_at` | le **choix du premier serveur** | début du jeu réel |

- **Échauffement** = `LIVE` **et** `play_started_at` nul. Le moteur **refuse
  toute action de scoring** (`point_left/right`, jeux±, sets±) pendant cette
  phase — erreur JSON affichée en toast ([[arbitre-match]]). La TV affiche la
  scène échauffement ([[tv-live]]) : affiche du match + compte à rebours
  **5 min** (constante applicative, purement **indicative** — rien ne se
  déclenche à 0:00).
- **Jeu** = `LIVE` et `play_started_at` posé. Comportement actuel inchangé.
- Le passage échauffement → jeu est l'action de **choix du serveur** (modal
  « Qui sert en premier ? », [[arbitre-match]]) : elle pose `play_started_at`
  et le serveur choisi. Le choisir tôt **court-circuite** l'échauffement — il
  n'y a pas d'action « passer » distincte.
- Un match **repris** après une mise en pause (`play_started_at` déjà posé)
  revient **directement en jeu** : pas de ré-échauffement. Un match **mis à
  l'antenne** depuis l'admin sans avoir jamais été lancé entre en échauffement
  comme n'importe quel démarrage — règle dérivée, aucun cas particulier.
- `started_at` (base des ETA et de la ponctualité, [[planning]]) est posé à
  l'**entrée en échauffement** : c'est le moment où le court est occupé. La
  durée par défaut d'un match inclut donc l'échauffement.

---

## Transitions

### Démarrer — `SCHEDULED → LIVE` (phase échauffement)

- **Qui** : arbitre **et** admin.
- **Effet** : `mark_live()` (statut `LIVE` + `started_at` si vide), pose de
  `warmup_started_at` si le match n'a jamais été lancé (voir « Les deux phases
  de `LIVE` »), **mise en avant TV** (`is_featured = True`), rétrogradation de
  l'éventuel autre match `LIVE`. Le match **garde sa place** dans le calendrier
  (`order_index` conservé — voir plus bas).
- **Gardes** :
  - si un autre match est déjà `LIVE`, une **confirmation** explicite l'effet
    (« Un autre match est en cours — le démarrer le mettra en pause »), cohérent
    avec la mise en avant côté admin ([[admin-matchs]], « mettre un match en avant ») ;
  - un match de **tableau dont un slot n'est pas résolu** (side manquant) est
    **refusé par le serveur** (erreur JSON) — on ne démarre pas un match sans
    ses deux joueurs (voir [[planning]], matchs de tableau au calendrier).
- **Idempotence** : démarrer un match déjà `LIVE` est sans effet (pas d'erreur).

### Lancer le jeu — échauffement → jeu (choix du serveur)

- **Qui** : arbitre (et admin le cas échéant — même service).
- **Effet** : pose `play_started_at` et le `server` choisi (A/B, repère modèle,
  indépendant du `swap`). Les actions de scoring deviennent acceptées ; la TV
  bascule de la scène échauffement au scoreboard ([[tv-live]]).
- **Garde** : refusé si le match n'est pas `LIVE` en phase d'échauffement.

### Scorer — pendant `LIVE`

- **Qui** : arbitre (saisie point par point). L'admin ne score pas ; il **corrige**
  (voir ci-dessous).
- Le moteur de score (`referee_action`) gère automatiquement points → jeux → sets →
  tie-break selon le format du match. Décrit côté UI dans [[arbitre-match]].

### Terminer (normal) — `LIVE → FINISHED`

- **Automatique** : dès que le score atteint la condition de victoire (dernier point
  du dernier set), le moteur clôt le match (`models.py` / `referee_views.py:263`).
  Le point gagné **est** la fin du match ; il n'y a pas de confirmation intermédiaire.
- **Manuel** : un bouton « Terminer » permet de forcer la clôture en désignant le
  vainqueur (litige, score déjà décisif non détecté). `end_reason = NORMAL`.
- **Effets** (dans les deux cas) : `winner_side` fixé, `is_featured = False`,
  recalcul des classements de poule (`recalc_one_group`) et propagation au tableau
  (`sync_final_*`, `bracket.py`) — logique existante, inchangée. Le match **garde sa
  place** dans le calendrier.

### Forfait / walkover — `SCHEDULED → FINISHED`

- **Qui** : arbitre et admin.
- **Quand** : avant le match, un joueur ne se présente pas.
- **Effet** : `FINISHED`, `winner_side` = le joueur **présent**, `end_reason =
  WALKOVER` (`is_walkover = True`), **score de convention** (l'adversaire à
  `games_to_win`, l'absent à 0). Le match **reste à sa place** (verrouillé, libellé
  « Forfait »).
- Même mécanique que le forfait d'une **entry** décrit dans [[cycle-de-vie-epreuve]],
  mais **scopé à un seul match** (déclaré depuis la fiche du match, sans retirer le
  joueur de toute l'épreuve). Le retrait complet d'un inscrit reste l'ajustement
  épreuve (cascade).

### Abandon — `LIVE → FINISHED`

- **Qui** : arbitre et admin.
- **Quand** : en cours de match, un joueur se retire.
- **Effet** : `FINISHED`, `winner_side` = l'**autre** joueur, `end_reason =
  RETIREMENT`, **score figé en l'état** (on ne complète pas les jeux manquants). Le
  match reste à sa place ; recalcul poule/tableau comme une fin normale.

### Annuler — `→ CANCELED`

- **Qui** : arbitre et admin.
- **Quand** : les deux joueurs absents, ou décision d'organisation.
- **Effet** : `CANCELED`, **aucun vainqueur**. Le match **quitte sa journée** (perd
  son `order_index`) et bascule dans la colonne « Annulés » ([[admin-matchs]]).
- **Classement** : un match annulé est **exclu** du calcul de poule — ni victoire ni
  défaite pour personne (`standings.py` ne compte que les `FINISHED`). C'est le choix
  « annulation neutre » : à distinguer du forfait, où l'absent perd. *(Pas de
  « double défaite » : décision produit — un annulé n'impacte pas le classement.)*

### Rouvrir — `FINISHED → LIVE`  ·  **ADMIN uniquement**

- **Qui** : **l'admin seul**. L'arbitre ne peut pas rouvrir un match terminé ; il
  signale l'erreur, l'admin corrige.
- **Effet** : repasse `LIVE` en **conservant** le score et l'historique des sets
  (`set_scores`). Les corrections se font ensuite (drawer arbitre ou onglet Score
  admin) ; le recalcul poule/tableau est rejoué à la clôture suivante. La
  ré-ouverture d'urgence côté épreuve ([[cycle-de-vie-epreuve]], « Rouvrir »)
  partage cette contrainte.

---

## Répartition des pouvoirs

| Transition | Arbitre | Admin |
|---|:--:|:--:|
| Démarrer (`SCHEDULED → LIVE`) | ✓ | ✓ |
| Scorer point par point | ✓ | — |
| Corriger (jeux±/sets±/serveur/inversion côtés) | ✓ | ✓ |
| Terminer (auto sur balle de match + manuel) | ✓ | ✓ |
| Forfait / Abandon / Annulation | ✓ | ✓ |
| **Rouvrir un match terminé** | ✗ | ✓ (seul) |

---

## `order_index` : la place au calendrier persiste

Le match **garde son `order_index`** en passant `LIVE` puis `FINISHED` : un match
joué **reste à sa place** dans la journée (verrouillé), les heures estimées aval se
recalant sur son heure réelle (voir [[planning]] et [[admin-matchs]]). Seuls
l'**annulation** et le **renvoi à la pile « à planifier »** effacent l'`order_index`.

---

## Champs de données

| Champ | État actuel | Cible |
|---|---|---|
| `Match.status` (SCHEDULED/LIVE/FINISHED/CANCELED) | ✓ présent | inchangé (pas de statut WARMUP — phase dérivée) |
| `Match.warmup_started_at` (DateTime, nullable) | à créer | posé à l'entrée en `LIVE` d'un match jamais lancé ; exposé `warmupStartedAt` dans `_pack_match` |
| `Match.play_started_at` (DateTime, nullable) | à créer | posé au choix du serveur ; exposé `playStartedAt` dans `_pack_match` ; nul = phase d'échauffement |
| `Match.winner_side` (A/B) | ✓ présent | inchangé |
| `Match.is_walkover` | ✓ présent | conservé (compat), câblé en parallèle de `end_reason=WALKOVER` |
| `Match.end_reason` (NORMAL / WALKOVER / RETIREMENT) | ✓ présent (migration `0022_match_end_reason`) | NORMAL câblé (`mark_finished()` + balle de match auto tie-break/set classique), WALKOVER câblé (`withdraw_entry`) et RETIREMENT **câblé** via le service `finish_match_manual` (`live/admin_views.py`), utilisé par l'action `finish_winner` (`live/referee_views.py`) avec `retirement=True` (ticket #281). Exposé dans `_pack_match` sous `endReason` |
| `formatLabel` dans `_pack_match` | ✓ présent | packer `_format_label` (`live/api_views.py:191-196`), inclus dans `_pack_match` (`live/api_views.py:238`, clé `"formatLabel": _format_label(m)`) |

> `CANCELED` n'a pas besoin de `end_reason` : l'absence de vainqueur + le statut
> suffisent, et le classement l'ignore.

---

## Concurrence & temps réel

- L'invariant « un seul `LIVE` par édition » limite les collisions : un seul match
  est activement scoré.
- Le partage admin ⇄ arbitre sur le même match est en **dernière-écriture-gagne**
  via le polling (pas de verrou) — acceptable au grain mono-court. Les corrections
  passent par des actions atomiques distinctes (jeu±, set±), pas par un état global.
- Polling : ~2 s sur le match arbitré/scoreboard, ~5 s sur la file et le calendrier
  (voir [[arbitre-match]], [[arbitre-home]], [[planning]]).

---

## Récapitulatif : ce qui est neuf côté backend

| Élément | Nature |
|---|---|
| Action `démarrer` exposée aussi côté **admin** | service partagé (existe côté arbitre) |
| Phase d'échauffement (`warmup_started_at` / `play_started_at`, refus du scoring en échauffement, action « lancer le jeu ») | migration + évolution de `mark_live` / `referee_action` (retours TV 2026-07-08) |
| Garde « slot non résolu » sur `démarrer` (matchs de tableau) | garde de service (retours TV 2026-07-08) |
| `end_reason` (NORMAL/WALKOVER/RETIREMENT) | migration + câblage terminer/forfait faits (#279) ; câblage abandon (RETIREMENT) fait via `finish_match_manual` / action `finish_winner` (#281) |
| Forfait / abandon / annulation **scopés au match** | services neufs (le walkover d'entry existe côté épreuve) |
| `reopen` **conservant `set_scores`** et repassant `LIVE` | correction de bug |
| `order_index` **persistant** à travers `LIVE`/`FINISHED` | correction (sprint 15) |
