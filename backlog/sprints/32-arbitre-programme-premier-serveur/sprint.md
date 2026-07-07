---
sprint: 32
nom: "Arbitre : programme du jour & premier serveur"
specs:
  - specs/screens/arbitre-home.md
  - specs/screens/arbitre-match.md
modules:
  - live/api_views.py
  - live/referee_views.py
  - frontend/app/src/views/arbitre/ArbitreHome.vue
  - frontend/app/src/views/arbitre/ArbitreMatch.vue
tickets-tag: sprint-32
branche: claude/sprint/32-arbitre-programme-premier-serveur
branche-parent: main
log: backlog/sprints/32-arbitre-programme-premier-serveur/log.md
---

# Sprint 32 — Arbitre : programme du jour & premier serveur

**Objectif :** la refonte de l'accueil arbitre (miroir lecture du calendrier :
bloc « À l'instant », toutes les journées, plus d'onglets) et la user story
« premier serveur » : le démarrage d'un match impose de choisir qui sert.

> Origine : revue produit 2026-07-07 (page Arbitre : « une vue simplifiée du
> calendrier pour voir et démarrer le bon match », « la première action avant
> le point devrait être de définir le premier serveur »). S'appuie sur le
> packer calendrier et la définition unique du next (sprints 22-23) sans les
> redupliquer.

## Définition de terminé

- Golden path programme : 2 journées planifiées, un match `LIVE` → il occupe le
  bloc « À l'instant » avec Reprendre ; le terminer → le next prend le bloc
  avec Démarrer ; les journées s'affichent dans l'ordre, terminés atténués à
  leur place, journées non courantes repliables.
- Golden path serveur : Démarrer → le modal exige le choix du serveur (Confirmer
  grisé sans choix) → choisir B → au premier point, l'indicateur ● est côté B ;
  si un autre match est LIVE, l'avertissement apparaît dans le même modal.
- Spec review `✅ Conforme` sur [[arbitre-home]] et [[arbitre-match]].
- Aucune issue `sprint-32` ouverte.

## Specs ciblées

- [`specs/screens/arbitre-home.md`](../../../specs/screens/arbitre-home.md) — programme (refonte complète)
- [`specs/screens/arbitre-match.md`](../../../specs/screens/arbitre-match.md) — flux « démarrer un match »

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 32 — Arbitre : programme du jour & premier serveur »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#310](https://github.com/sirius911/moutilloux/issues/310) | Back : api_arbitre_matches — lecture calendrier (journées + séquence + next) | `live/api_views.py` | débloque #311 |
| [#311](https://github.com/sirius911/moutilloux/issues/311) | Front : ArbitreHome — refonte programme (bloc « À l'instant » + journées) | `ArbitreHome.vue` | dépend de #310 |
| [#312](https://github.com/sirius911/moutilloux/issues/312) | Back : action start avec paramètre server (A/B) | `live/referee_views.py` | débloque #313 |
| [#313](https://github.com/sirius911/moutilloux/issues/313) | Front : ArbitreMatch — modal de démarrage avec choix obligatoire du serveur | `ArbitreMatch.vue` | dépend de #312 |

---

## Périmètre backend

Deux briques indépendantes : lecture calendrier arbitre (réutilise
`api_edition_calendar` + next unique) et paramètre `server` de l'action `start`
(`start_match(match, server=None)`).

## Fichiers partagés (orchestrateur uniquement)

Aucun (`live/urls.py` non touché — routes existantes).

## Ordre d'exécution suggéré

Deux chaînes parallèles (fichiers disjoints) :
- **Programme** : #310 (back) → #311 (front).
- **Serveur** : #312 (back) → #313 (front).
