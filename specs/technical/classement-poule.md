---
type: technical
module: classement-poule
fichiers:
  - competition/standings.py
  - live/models.py
  - live/admin_views.py
---

# Spec technique — Classement de poule

> Documente l'algorithme de `recalc_one_group` (`competition/standings.py`), qui
> calcule le classement d'une poule à chaque match de poule terminé et déclenche
> en sortie la synchronisation du tableau final (`sync_final_bracket_for_event`,
> `standings.py:76-80`). Décide donc directement des qualifiés. Aucune spec ne
> couvrait cet algorithme jusqu'ici ; ce document décrit **l'existant**, pas une
> cible — deux points de vigilance connus sont documentés tels quels en fin de
> fichier plutôt que « corrigés ».

## Périmètre du calcul

`recalc_one_group(group_id)` ne prend en compte que les matchs :
- `stage = Match.Stage.GROUP`
- `status = Match.Status.FINISHED`
- dont les deux côtés (`side_a`, `side_b`) appartiennent à la poule

(`standings.py:30-36`). Les matchs `CANCELED` sont **exclus** : le filtre ne
porte que sur `FINISHED`, donc un match annulé est simplement absent du calcul,
sans traitement spécial. Ce n'est pas un bug — c'est le comportement attendu et
il n'y a rien de plus à documenter dessus.

Le classement est recalculé poule par poule. `recalc_event_groups(event_id)`
(`standings.py:83-97`) trouve tous les groupes d'une édition ayant au moins un
match de poule `FINISHED` et rappelle `recalc_one_group` pour chacun.

> **Classement ≠ qualification.** Les rangs produits ici existent dès le
> **premier** match terminé de la poule (classement intermédiaire). Le statut
> de **qualifié** (badge Q, placement dans le tableau final), lui, n'est défini
> que lorsque la poule est **terminée** — plus aucun match `SCHEDULED`/`LIVE`.
> Règle cible et surfaces concernées : [[cycle-de-vie-epreuve]].

## Victoire / défaite

Le vainqueur d'un match est déduit de la comparaison des jeux, **pas** du champ
`winner_side` :

```python
if m.games_a > m.games_b:
    a.wins += 1
    b.losses += 1
elif m.games_b > m.games_a:
    b.wins += 1
    a.losses += 1
else:
    continue
```

(`standings.py:51-58`). Cas `games_a == games_b` : la ligne `continue` ne
comptabilise **ni victoire ni défaite** pour aucune des deux entries. C'est un
bug latent documenté tel quel — le tennis n'a pas de match nul, donc ce cas ne
devrait survenir que si le score a été mal renseigné (voir la section édition
manuelle admin plus bas, seul chemin qui peut produire cette situation).

## Points

2 points par victoire, 0 sinon (`standings.py:60-63`) :

```python
for s in standings.values():
    s.points = s.wins * 2
    s.save()
```

Pas de point de défaite, pas de bonus (jeux gagnés, série de victoires, etc.).

## Tie-break (ordre de tri)

Le classement trie par tuple décroissant `(points, games_won, games_won -
games_lost)` (`standings.py:66-70`) :

```python
ordered = sorted(
    standings.values(),
    key=lambda s: (s.points, s.games_won, (s.games_won - s.games_lost)),
    reverse=True
)
```

**Aucune confrontation directe (head-to-head)** n'est appliquée à aucun niveau
du départage. En cas d'égalité totale sur les trois critères pour 3 équipes ou
plus, `sorted` (stable en Python) retombe sur l'ordre d'itération du dict
`standings`, lui-même construit dans l'ordre d'insertion de
`GroupMembership.objects.filter(...)` — donc un ordre qui dépend de l'ordre de
création des inscriptions en poule, **non déterministe du point de vue
métier**. Comportement réel à documenter tel quel, pas une règle voulue (voir
« Point de vigilance » ci-dessous).

## Walkover (`withdraw_entry`)

Quand une entry se retire (`withdraw_entry`, `admin_views.py:850-864`), les
matchs non terminés de cette entry reçoivent un score de convention posé en
cohérence avec `winner_side` :

```python
if m.side_a_id == entry.id:
    m.winner_side = Match.WinnerSide.B
    m.games_a = 0
    m.games_b = m.games_to_win
else:
    m.winner_side = Match.WinnerSide.A
    m.games_a = m.games_to_win
    m.games_b = 0
```

Ici `games_a > games_b` (ou l'inverse) et `winner_side` **concordent toujours**
par construction : ce chemin ne peut pas produire de divergence pour
`standings.py`, qui ignore `winner_side` mais retombe sur le même résultat.

## Édition manuelle admin (`MatchEditForm`)

`MatchEditForm` (`admin_views.py:95-112`) expose `winner_side`, `games_a` et
`games_b` comme des champs de formulaire **indépendants**, librement
modifiables par l'admin :

```python
fields = [
    "status", "order_index", "is_featured",
    "match_format", "games_to_win", "tb_at", "best_of",
    "tb_points_to_win", "tb_win_by_two",
    "deciding_set_mode", "deciding_tb_points_to_win",
    "server", "points_a", "points_b",
    "sets_a", "sets_b", "games_a", "games_b",
    "tb_active", "tb_points_a", "tb_points_b",
    "winner_side",
]
```

Rien n'empêche d'enregistrer un match `FINISHED` où `winner_side` diverge de
`games_a`/`games_b` (ex. `winner_side = A` mais `games_a < games_b`). Comme
`standings.py` ignore `winner_side` et ne regarde que `games_a`/`games_b`, le
classement de poule peut alors s'appuyer sur un résultat qui **contredit** le
vainqueur affiché ailleurs dans l'app — les autres surfaces (scoreboard TV,
historique, calcul de vainqueur/perdant du bracket) utilisent `winner_side`,
pas les jeux : `live/views.py:390-404` (`_winner_score_text`) et
`live/bracket.py:276-288` (`_winner_entry`/`_loser_entry`) tranchent tous les
deux sur `m.winner_side == "A"` / `"B"`.

---

## Points de vigilance (documentés, non corrigés)

Ces deux comportements sont volontairement **documentés tels quels**, sans
correctif de code. Le ticket #217 est un ticket de documentation ; changer
l'un ou l'autre serait une décision de design nouvelle (quel critère de
départage ajouter ? que faire si `winner_side` est `None` sur un vieux match ?
), hors périmètre.

1. **Égalité totale à 3 équipes ou plus, sans head-to-head.** Le tri
   `(points, games_won, games_won - games_lost)` n'a pas de quatrième critère.
   Si trois entries ou plus finissent parfaitement à égalité sur les trois
   valeurs, l'ordre final dépend de l'ordre d'insertion des `GroupMembership`
   en base — un artefact d'implémentation, pas une règle métier. Aucun
   comportement d'affichage ne doit supposer que cet ordre est stable ou
   « voulu » dans ce cas précis.

2. **Divergence `winner_side` / score via l'édition manuelle admin.** Les deux
   chemins de mutation normaux (score live via l'arbitre, walkover via
   `withdraw_entry`) garantissent la concordance entre `winner_side` et
   `games_a`/`games_b`. Seule l'édition manuelle admin (`MatchEditForm`), un
   outil de correction a posteriori et non un flux normal, permet de casser
   cette concordance. Si elle est cassée sur un match `FINISHED` de poule, le
   classement (`standings.py`, basé sur les jeux) et les autres surfaces de
   l'app (basées sur `winner_side`) peuvent afficher des vainqueurs
   différents pour le même match. À garder en tête pour tout admin qui corrige
   un score a posteriori : renseigner `winner_side` et `games_a`/`games_b` de
   façon cohérente à la main, l'application ne le vérifie pas pour lui.
