---
sprint: 13
nom: Tableau — seeding général, byes & 3e place
specs:
  - specs/technical/cycle-de-vie-epreuve.md
modules:
  - competition/models.py
  - live/models.py
  - live/bracket.py
  - live/referee_views.py
  - live/api_views.py
  - live/urls.py
  - frontend/app/src/views/admin/AdminBracket.vue
  - frontend/app/src/components/modals/EventModal.vue
  - frontend/app/src/views/tv/TvBracket.vue
tickets-tag: sprint-13
branche: claude/sprint/13-tableau-seeding
branche-parent: claude/sprint/12-forfait-ajustements
log: backlog/sprints/13-tableau-seeding/log.md
---

# Sprint 13 — Tableau : seeding général, byes & 3e place

**Objectif :** Généraliser le tableau final pour des **configs variables**
(N poules, 1 ou 2 qualifiés) avec **byes** et **séparation maximale** (les deux
qualifiés d'une poule ne se croisent qu'en finale), remplissage **au fil de l'eau**,
et **petite finale** optionnelle. Refonte de `live/bracket.py` (cas figés actuels).

## Définition de terminé

- `live/bracket.py` produit un tableau correct pour 1/2/3/4/5/6… poules, avec byes
- `Event.has_third_place` + `Match.Stage.P3` en base (migration OK)
- **Golden path :** 5 poules × 2 → tableau de 16 avec byes, séparation maximale,
  qualifiés auto-placés au fil des résultats ; option 3e place → perdants des demies
  promus dans `P3`
- Spec review sur `specs/technical/cycle-de-vie-epreuve.md` (volet tableau)
  → verdict `✅ Conforme`
- Aucun ticket `sprint-13` ouvert dans GitHub Issues (hors `en-attente`)

## Specs ciblées

- [`specs/technical/cycle-de-vie-epreuve.md`](../../../specs/technical/cycle-de-vie-epreuve.md)
  → §§ Le tableau final (au fil de l'eau, seeding, byes, petite finale)
- Écrans impactés : [[admin-tableau-final]], [[admin-tournoi]] (modale Épreuve)

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 13 — Tableau : seeding général, byes & 3e place »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#138](https://github.com/sirius911/moutilloux/issues/138) | Refonte `bracket.py` : générateur général (N poules, byes, séparation maximale) | `bracket.py` | Dépend de S11 (squelette posé au Débuter) |
| [#139](https://github.com/sirius911/moutilloux/issues/139) | Étiquetage positionnel + résolution au fil de l'eau | `bracket.py` | Dépend de #138 |
| [#140](https://github.com/sirius911/moutilloux/issues/140) | Modèle `Event.has_third_place` + `Match.Stage.P3` + migration | `competition/models.py`, `live/models.py` | ⚠️ Infra — orchestrateur |
| [#142](https://github.com/sirius911/moutilloux/issues/142) | Endpoints : bracket create généralisé + config `has_third_place` | `api_views.py`, `urls.py` | ⚠️ Infra — orchestrateur. Dépend de #138, #140 |
| [#143](https://github.com/sirius911/moutilloux/issues/143) | AdminBracket : remplissage auto affiché + reseed des étiquettes | `AdminBracket.vue` | Dépend de #142 |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#141](https://github.com/sirius911/moutilloux/issues/141) | Propagation des **perdants** → match de 3e place | `bracket.py`, `referee_views.py` | Dépend de #138, #140 |
| [#144](https://github.com/sirius911/moutilloux/issues/144) | AdminBracket : colonne 3e place | `AdminBracket.vue` | Dépend de #142 |
| [#145](https://github.com/sirius911/moutilloux/issues/145) | EventModal : option « petite finale » (`has_third_place`) | `EventModal.vue` | Dépend de #142 |
| [#146](https://github.com/sirius911/moutilloux/issues/146) | TvBracket : affichage 3e place + calibrage polling | `TvBracket.vue` | Dépend de #142 |

---

## Périmètre backend

**Refonte** de `live/bracket.py` (algorithme de seeding général + byes, logique
neuve) et **propagation des perdants** (neuve). `live/urls.py` câblé par
l'orchestrateur.

## Ordre d'exécution suggéré

1. **#140 [infra]** — Modèle (`has_third_place`, `Stage.P3`). Indépendant, peut démarrer en premier.
2. **#138** — Générateur général (cœur du sprint).
3. **#139** — Étiquetage positionnel + résolution au fil de l'eau.
4. **#141** — Propagation des perdants (3e place).
5. **#142 [infra]** — Endpoints + `urls.py`.
6. **#143 / #144 / #145 / #146** — Front, fichiers disjoints → parallélisables.

**Parallélisme :** #140 en parallèle de #138/#139 ; front #143→#146 en parallèle
après #142.

> **Séquencement inter-sprint :** ce sprint peut précéder le Sprint 12 (ils sont
> indépendants). Tant qu'il n'est pas fait, « Débuter » (S11) crée le squelette via
> le `bracket.py` actuel (4/2/3 poules, 2 qualifiés) ; les autres configs ne
> produisent un tableau complet qu'après ce sprint.
