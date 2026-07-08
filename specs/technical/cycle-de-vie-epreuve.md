---
type: technical
module: cycle-de-vie
fichiers:
  - competition/models.py
  - live/models.py
  - live/bracket.py
  - live/admin_views.py
  - live/api_views.py
  - frontend/app/src/types/index.ts
  - frontend/app/src/stores/event.ts
  - frontend/app/src/views/admin/AdminTournoi.vue
  - frontend/app/src/views/admin/AdminGroups.vue
  - frontend/app/src/views/admin/AdminMatches.vue
  - frontend/app/src/views/admin/AdminBracket.vue
---

# Spec technique — Cycle de vie d'une épreuve

> Comment une **épreuve** progresse de l'inscription à la phase finale : un statut
> stocké, des transitions explicites, et les règles métier qui en découlent
> (verrouillage des poules, forfait, tableau au fil de l'eau, seeding). Source de
> vérité du « déroulement » d'une épreuve. Les specs d'écran ([[admin-tournoi]],
> [[admin-poules]], [[admin-matchs]], [[admin-tableau-final]]) décrivent l'UI ;
> celle-ci décrit les états et les règles communes. Complète [[planning]] (le
> calendrier) et [[routing-context]] (le contexte d'épreuve dans l'URL).

## Principe

Aujourd'hui l'avancement d'une épreuve est **dérivé** et **implicite** : aucun
statut n'est stocké, et les poules se verrouillent comme effet de bord dès qu'un
match existe. Cette spec rend l'avancement **explicite** : un statut stocké sur
l'épreuve, deux transitions décidées par l'admin, et une frontière nette entre
« on place les joueurs » et « on joue ».

**La granularité est l'épreuve, pas l'édition.** Chaque épreuve (Simple Homme,
Double Mixte…) a son propre cycle : on peut jouer une épreuve pendant qu'une autre
recrute encore. Le modèle de données impose déjà ce grain (poules, matchs et
tableau sont par `Event`).

---

## La machine à états

Statut stocké sur `Event` — **champ présent** : `status`
(`competition/models.py:38-40`, `Event.Status` = INSCRIPTION/EN_COURS/TERMINEE,
défaut INSCRIPTION).

```
  INSCRIPTION  ──[Débuter]──►  EN_COURS  ──[finale jouée]──►  TERMINÉE
  placement libre              poules + tableau              archive
```

| Statut | Ce qu'on peut faire | Ce qui est figé |
|---|---|---|
| **INSCRIPTION** | inscrire des joueurs, composer/recomposer les poules (DnD), remplir auto | aucun match n'existe encore |
| **EN_COURS** | jouer les matchs, planifier (calendrier), remplir le tableau ; **ajustements ponctuels** (forfait, remplacement, ajout, retrait) | la **structure** des poules (qui est dans quelle poule, nombre de matchs) |
| **TERMINÉE** | consultation, archive | tout |

### Badge d'avancement (dérivé, pour l'affichage)

L'écran Tournoi ([[admin-tournoi]]) garde un libellé d'avancement plus fin que le
statut brut, **dérivé** de `status` + structure :

| Affichage | Règle |
|---|---|
| « À préparer » | `INSCRIPTION` et aucune poule créée |
| « Inscription » | `INSCRIPTION` et au moins une poule composée |
| « Poules » | `EN_COURS` et aucun match de tableau commencé |
| « Phase finale » | `EN_COURS` et au moins un match de tableau `LIVE`/`FINISHED` |
| « Terminée » | `TERMINÉE` |

> Le libellé dérivé remplace l'actuel (« À préparer / Poules / Phase finale » de
> [[admin-tournoi]], qui se basait sur l'existence de poules / d'un tableau). On
> ajoute la vérité stockée dessous sans perdre la finesse visuelle.

---

## Transition « Débuter »

**Où.** Action principale sur la carte d'épreuve de l'écran Tournoi quand
`status = INSCRIPTION` (miroir possible en en-tête de l'écran Poules). Une épreuve
à la fois.

**Garde.** Au moins une poule jouable (≥ 2 entries). Les inscrits non placés sont
**exclus** du tournoi avec un avertissement explicite avant confirmation (ils ne
joueront pas tant qu'on ne revient pas les ajouter — voir Ajustements).

**Effets (atomiques) :**
1. **Génère le round-robin** de chaque poule (service existant
   `generate_group_matches_for_event`, déjà **idempotent et additif** —
   `admin_views.py:255`). Matchs en `SCHEDULED`, sans `order_index` (= « à
   planifier », voir [[planning]]).
2. **Verrouille la structure** des poules : composition en lecture seule
   (le verrouillage ne dépend plus de « un match existe » mais de `status ≥ EN_COURS`).
3. **Crée le squelette du tableau** (vide, étiquettes de provenance — voir
   *Le tableau final*). Ses matchs naissent `SCHEDULED` sans `order_index` :
   ils rejoignent la **pile « à planifier »** du calendrier au même titre que
   les matchs de poule (étiquetés « A1 vs D2 » tant que non résolus — voir
   [[planning]], « Matchs de tableau au calendrier »).
4. **Ouvre la planification** : le calendrier ([[planning]]) n'accepte des matchs
   que pour les épreuves `EN_COURS`.
5. Passe `status = EN_COURS`.

> **Changement vs existant.** Aujourd'hui c'est la *génération des matchs* (écran
> Matchs) qui verrouille les poules, comme action séparée. Désormais « Débuter »
> fait les deux d'un geste, et la génération n'est plus une action libre.

---

## Transition « Clôturer »

- **Automatique** dès que le match de finale (`F1`) passe `FINISHED` →
  `status = TERMINÉE`.
- **Rouvrir** : action d'urgence admin (`TERMINÉE → EN_COURS`) pour corriger un
  score après coup. Pas de retour à `INSCRIPTION` (voir Réversibilité).

---

## Ajustements en phase de jeu

En `EN_COURS`, la structure est figée mais quatre ajustements ponctuels restent
possibles. Règle transversale : **un match déjà commencé (`LIVE`/`FINISHED`) n'est
jamais réécrit par un ajustement** ; seuls les matchs `SCHEDULED` sont touchés.

| Ajustement | Mécanique | Coût |
|---|---|---|
| **Remplacer un joueur** | échange le `player`/`team` porté par l'`Entry`, **même place** en poule. Aucun match touché, résultats déjà joués conservés. | faible |
| **Ajout tardif** | nouvelle `Entry` + `GroupMembership` dans une poule **sous l'effectif** ; re-run de la génération (additive) → crée **uniquement** les matchs manquants du nouveau venu. Avertissement si l'effectif dépasse `group_size_default`. | faible–moyen |
| **Forfait** | voir ci-dessous (walkover). | présent — `withdraw_entry` (live/admin_views.py:589) |
| **Retrait sans remplaçant** | = forfait, **plus** retrait de l'affichage poule. Forfaits en cascade sur tous ses matchs non joués. | présent — `withdraw_entry` (live/admin_views.py:589) |

### Forfait / walkover (logique neuve)

Aujourd'hui un abandon est un `CANCELED` **sans vainqueur** ([[planning]]) — ce
n'est pas un walkover. À créer :

- **`Entry.withdrawn`** (bool, **champ présent**, `competition/models.py:62`) :
  l'inscription abandonne.
- **`Match.is_walkover`** (bool, **champ présent**, `live/models.py:140`) : marque
  une victoire par forfait.
- Au déclenchement du forfait sur une entry : tous ses matchs **non terminés**
  passent `FINISHED`, `winner_side` = l'adversaire, `is_walkover = True`, score de
  convention (adversaire `games_to_win`, partant 0). Ces matchs **restent à leur
  place** dans le calendrier (verrouillés, libellé « Forfait ») : leur `order_index`
  est conservé, ils ne disparaissent pas de la journée (voir [[planning]]).
- Le reste se recâble sur l'existant : **classements recalculés**, et le tableau
  auto-rempli **avance l'adversaire** si le forfait touche un qualifié
  (propagation des vainqueurs, `bracket.py:241`).
- **Les matchs déjà joués restent acquis** (on ne réécrit pas le palmarès des
  adversaires précédents).

### Réversibilité

Pas de « retour en inscription » : une fois `EN_COURS`, on n'efface pas la
structure. Les imprévus passent par les ajustements ci-dessus (et, en dernier
recours, l'admin Django). C'est le choix « ajustements ponctuels permis » plutôt
que « rollback global ».

---

## Planification (calque optionnel)

La planification ([[planning]]) est un **calque d'organisation, pas une barrière** :

- un match généré est **jouable même non planifié** (l'arbitre peut le lancer) ;
  le calendrier sert à ordonner courts/journées et estimer les heures. Seule
  exception : un match de tableau aux slots **non résolus** refuse `démarrer`
  (garde serveur, [[cycle-de-vie-match]]).
- Deux horizons, **tous deux planifiables dès « Débuter »** : les **matchs de
  poule** (joueurs connus) et les **slots de tableau** (joueurs TBD → on
  planifie le *créneau*, les étiquettes de provenance « A1/C2 » s'affichent
  jusqu'à résolution). Règles dans [[planning]], « Matchs de tableau au
  calendrier ».
- Un ajustement qui crée des matchs (ajout tardif) les fait retomber dans la pile
  « à planifier ».

---

## Le tableau final

### Poule terminée : la frontière de la qualification

> Une poule est **terminée** quand plus aucun de ses matchs n'est `SCHEDULED`
> ou `LIVE` — tous sont `FINISHED` (walkovers compris) ou `CANCELED`. Les
> **qualifiés d'une poule ne sont définis qu'à ce moment-là** : tant qu'elle
> joue, son classement intermédiaire (rang, V/D, points) reste visible partout,
> mais **sans statut de qualification** — aucun badge Q ([[admin-poules]],
> [[tv-live]]), aucune apparition dans « Qualifiés disponibles » et aucun
> placement dans le tableau ([[admin-tableau-final]]).

La granularité reste **la poule**, pas l'épreuve : on n'attend pas que toutes
les poules soient finies — chaque poule libère ses qualifiés dès qu'elle est
terminée, au fil de l'eau.

> **Écart résolu** (#289, #290). `_resolve_label_to_entry` ne résout plus une
> étiquette `A1`/`C2` sur un classement intermédiaire : le helper partagé
> `group_is_finished` (`live/bracket.py:5-11`) garde à la fois la résolution
> d'étiquette bracket et le flag `qualified` exposé par `live/views.py` et
> `live/api_views.py` — les deux ne se déclenchent que poule terminée.

### Au fil de l'eau

Le tableau se **remplit progressivement** : un slot reçoit ses joueurs dès que la
ou les poules dont il dépend sont **terminées** (`sync_final_bracket_for_event`,
`bracket.py:242`). Un quart peut donc **se jouer dès que ses deux qualifiés sont
connus**, même si d'autres poules de l'épreuve jouent encore.

> **Conséquence sur le seeding.** « Au fil de l'eau » impose un seeding **par
> position de poule** (étiquettes `A1`/`C2`, résolues poule par poule), et **exclut**
> un seeding par classement global (qui exigerait toutes les poules finies pour
> connaître le seed 1). Le cas « 3 poules » actuel (`S1..S6` globaux,
> `bracket.py:118`) est donc remplacé par un placement positionnel.

### Seeding : séparation maximale

Principe retenu : pas d'ELO par joueur — **c'est l'admin qui équilibre les poules**.
Le tableau, lui, applique un placement déterministe avec **séparation maximale** :

> Les **deux qualifiés d'une même poule** (1er et 2e) sont placés dans des
> **moitiés opposées** du tableau : ils ne peuvent se rencontrer **qu'en finale**.

À cela s'ajoute : chaque match de 1er tour oppose autant que possible un **1er à un
2e** d'une **autre** poule.

#### Cas 4 poules × 2 qualifiés (tableau de 8)

```
   QF1   A1 ─┐
         C2 ─┴─┐
              SF1 ─┐
   QF2   D1 ─┐    │
         B2 ─┴─┘  │
                 FINALE
   QF3   B1 ─┐    │
         A2 ─┴─┐  │
              SF2 ┘
   QF4   C1 ─┐
         D2 ─┘
```

| Slot | Affiche | Moitié |
|---|---|---|
| QF1 | A1 vs C2 | haute |
| QF2 | D1 vs B2 | haute |
| QF3 | B1 vs A2 | basse |
| QF4 | C1 vs D2 | basse |
| SF1 | WQF1 vs WQF2 | — |
| SF2 | WQF3 vs WQF4 | — |
| F1  | WSF1 vs WSF2 | — |

A1 est en haut, A2 en bas → ils ne se croisent qu'en finale (idem B, C, D).

> **Changement vs existant.** Le code actuel (`bracket.py:98`) est déjà à
> séparation maximale mais avec d'autres affiches (A1 vs D2…). On adopte les
> affiches ci-dessus (1er d'une poule contre 2e de la poule « suivante »).

#### Cas 2 poules × 2 (tableau de 4)

`SF1 = A1 vs B2`, `SF2 = B1 vs A2`, `F1 = WSF1 vs WSF2`. (Inchangé,
`bracket.py:111`.)

#### Petits tableaux

- **2 poules × 1** → finale sèche `A1 vs B1`.
- **4 poules × 1** → demies `A1 vs D1` / `B1 vs C1`, puis finale.
- **1 poule** → pas de tableau ; au plus une finale `A1 vs A2` si 2 qualifiés.

### Byes (configs variables)

Les épreuves ont des tailles variables : le nombre de qualifiés
`Q = nb_poules × qualified_per_group` n'est pas toujours une puissance de 2.

- Taille de tableau `B` = puissance de 2 ≥ `Q` ; **byes** = `B − Q`.
- Les byes sont attribués aux **vainqueurs de poule**, par ordre de poule (A, B, C…)
  **par défaut**, et **modifiables à la main** (cohérent avec « pas de config en
  plus, l'humain rattrape »).
- Un bye place directement le qualifié au tour suivant (pas de match de 1er tour
  pour lui), en respectant la séparation maximale.
- Dans les configs impaires, un match de 1er tour peut opposer deux 2e (inévitable
  quand il manque des 1ers) — accepté.

**Exemple 3 poules × 2 (6 qualifiés, tableau de 8, 2 byes) :**

| Slot | Affiche |
|---|---|
| (bye) | A1 → SF1 |
| (bye) | B1 → SF2 |
| QF1 | C1 vs B2 → SF1 |
| QF2 | C2 vs A2 → SF2 |
| F1 | WSF1 vs WSF2 |

Séparation respectée (A1/A2, B1/B2, C1/C2 en moitiés opposées).

**Règle générale (N poules)** : placer les vainqueurs (`X1`) aux positions de tête
maximalement espacées ; placer chaque second (`X2`) dans la **moitié opposée** à
son propre vainqueur, face à une autre poule ; attribuer les byes aux premiers
vainqueurs par ordre de poule. Tout slot reste **corrigeable à la main** tant que
le match n'a pas commencé. (Templates explicites au-delà de 4 poules : à figer
quand le besoin se présente.)

### Reseeding manuel

Le placement automatique est **rattrapable** : l'admin peut réorganiser une place
(drag / vider) tant que le match concerné est `SCHEDULED`, notamment en cas de
forfait ou d'arbitrage. Même geste que le remplissage manuel existant
([[admin-tableau-final]]).

### Petite finale (optionnelle)

- **`Event.has_third_place`** (bool, **champ présent**, `competition/models.py:37`) :
  active un match pour la 3e place.
- **`Match.Stage.P3`** (« 3e place », **valeur présente**) : un slot `P3`
  opposant les **perdants** des deux demi-finales (`live/bracket.py:186-197` pour la
  création du slot, `live/bracket.py:363-395`, fonction `sync_p3_losers_for_event`,
  pour la propagation des perdants).
- La propagation des perdants existe désormais (`sync_p3_losers_for_event`,
  `live/bracket.py:363-395`), en complément de la propagation des vainqueurs
  (`sync_final_winners_for_event`). Proposable uniquement quand le tableau
  a deux vraies demi-finales.

---

## Récapitulatif : ce qui est neuf côté backend

Cette spec dépassait le « exposer / brancher » — l'essentiel de la logique
métier est maintenant livré ; seule la généralisation du tableau au-delà de
4 poules reste à faire si le besoin se présente.

| Élément | Nature |
|---|---|
| `Event.status` + transitions Débuter/Clôturer | livré (`competition/models.py:38-40` ; `live/admin_views.py:311` `start_event`, `:351` `close_event`, `:373` réouverture) |
| `Event.has_third_place` | livré (`competition/models.py:37`) |
| `Entry.withdrawn`, `Match.is_walkover` | livré (`competition/models.py:62` ; `live/models.py:140`) |
| Service forfait (cascade walkover + recalcul) | livré (`withdraw_entry`, `live/admin_views.py:589-681`) |
| Généralisation du tableau (N poules, byes, séparation) | livré pour N ≤ 4 (`bracket.py:_bracket_layout`) ; N > 4 reste non templé — à faire si besoin |
| Propagation des **perdants** (3e place) | livré (`sync_p3_losers_for_event`, `live/bracket.py:363-395`) |
| Ajout tardif post-Débuter (déverrouillage ciblé + re-génération additive) | livré (`add_late_entry`, `live/admin_views.py:682-715`) |

> La généralisation du tableau au-delà de 4 poules reste la seule brique à
> **spécifier puis implémenter** comme logique métier neuve ; le reste est
> désormais de l'exposition/branchement sur des services existants.

---

## Impacts sur les specs existantes (réconciliées)

- **[[admin-poules]]** : le verrouillage n'est plus « dès qu'un match existe » mais
  « dès `status = EN_COURS` ». Le bandeau de verrouillage référence « Débuter ».
- **[[admin-matchs]] / [[planning]]** : « générer les matchs » n'est plus une action
  libre de l'écran Matchs — elle est absorbée par « Débuter ». Le forfait n'est plus
  un simple `CANCELED` mais un walkover avec vainqueur.
- **[[admin-tableau-final]]** : le squelette est créé à « Débuter » (plus à la
  demande) ; le remplissage des qualifiés est **automatique** (au fil de l'eau) avec
  correction manuelle, au lieu d'un drag-drop d'amorce ; seeding à séparation
  maximale généralisé ; petite finale optionnelle.
- **[[admin-tournoi]]** : la carte d'épreuve porte l'action « Débuter » (et
  « Rouvrir »), le badge d'avancement se dérive de `status`, et la modale Épreuve
  porte l'option « petite finale ».
- **[[admin-inscriptions]]** : le retrait **sec** d'une inscription reste réservé à
  la phase d'inscription ; une fois l'épreuve débutée, sortir un joueur passe par le
  forfait / retrait en cours de jeu.

---

## Hors périmètre

- **Têtes de série par performance / ELO** : écarté (incompatible avec « au fil de
  l'eau », et l'équilibrage est humain au niveau des poules). Le champ
  `Entry.seed_hint` (déjà présent, inutilisé) reste un crochet pour un éventuel
  besoin futur.
- **Démarrage global d'édition** (« tout démarrer ») : le grain reste l'épreuve.
- **Templates de tableau > 4 poules** : la règle générale est posée ; les schémas
  explicites seront figés au premier besoin réel.
