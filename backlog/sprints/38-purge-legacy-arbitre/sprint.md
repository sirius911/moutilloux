---
sprint: 38
nom: "Arbitre : purge legacy & action API"
specs:
  - specs/technical/cycle-de-vie-match.md
  - specs/transverse/auth-matrice-acces.md
modules:
  - live/api_views.py
  - live/urls.py
  - live/referee_views.py
  - live/arbitre_urls.py
  - live/views.py
  - live/templates/live/
  - moutilloux/urls.py
  - frontend/app/src/views/arbitre/ArbitreMatch.vue
  - frontend/app/src/views/admin/AdminRegie.vue
  - frontend/app/vite.config.ts
tickets-tag: sprint-38
branche: claude/sprint/38-purge-legacy-arbitre
branche-parent: main
log: backlog/sprints/38-purge-legacy-arbitre/log.md
---

# Sprint 38 — Arbitre : purge legacy & action API

**Objectif :** migrer la mutation de score de `POST /arbitre/match/<id>/action/`
vers `POST /api/matches/<id>/action/`, puis supprimer les dernières vues
template legacy (`referee_home`/`referee_match`, `home.html`) et nettoyer le
proxy Vite — la SPA devient l'unique surface arbitre, le conflit de routage
`/arbitre` disparaît.

> Origine : retours produit 2026-07-09 (problématique 2 — « conflit de routage
> avec l'ancienne vue d'arbitrage, virer les anciennes vues »). Le proxy Vite
> renvoie tout `/arbitre` vers Django : un chargement direct ou un refresh sur
> `/arbitre` sert l'ancienne page template au lieu de la SPA. Les vues
> `panel_*` ont déjà été purgées (#219, sprint 21/23) ; `admin_views.py` est
> déjà un module de services pur ; ce sprint achève le nettoyage.
> **Attention** : `referee_action` (le moteur de score) et les services
> consommés par `api_views` (`get_hero_match`, `build_event_group_tables`)
> doivent survivre — on ne supprime que les vues template.

## Définition de terminé

- Golden path : saisie arbitre complète (démarrer → lancer → scorer → terminer)
  et une action de la régie mobile passent par `/api/matches/<id>/action/` ;
  une action invalide (scorer en échauffement) renvoie l'erreur JSON affichée
  en toast.
- En dev, un **refresh** sur `/arbitre` et `/arbitre/:matchId` sert la SPA
  (gardes de rôle incluses) ; `GET /arbitre/` sur :8000 renvoie 404.
- La suite de tests Django passe ; `npx vue-tsc --noEmit` passe.
- Spec review `✅ Conforme` sur [[cycle-de-vie-match]] et [[auth-matrice-acces]].
- Aucune issue `sprint-38` ouverte.

## Specs ciblées

- [`specs/technical/cycle-de-vie-match.md`](../../../specs/technical/cycle-de-vie-match.md) — contrat de l'endpoint d'action + note de migration
- [`specs/transverse/auth-matrice-acces.md`](../../../specs/transverse/auth-matrice-acces.md) — niveau d'accès Arbitre du nouvel endpoint

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 38 — Arbitre : purge legacy & action API »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#347](https://github.com/sirius911/moutilloux/issues/347) | Back : endpoint POST /api/matches/\<id\>/action/ — moteur de score exposé en JSON | `live/api_views.py`, `live/urls.py`, `live/referee_views.py` | `infra` — câblage urls.py orchestrateur ; débloque tout |
| [#348](https://github.com/sirius911/moutilloux/issues/348) | Front : recâbler les actions de score sur /api/matches/\<id\>/action/ | `ArbitreMatch.vue`, `AdminRegie.vue` | dépend de #347 |
| [#349](https://github.com/sirius911/moutilloux/issues/349) | Back : supprimer les vues template legacy (/arbitre/, home.html) | `referee_views.py`, `arbitre_urls.py`, `views.py`, `templates/live/`, `moutilloux/urls.py` | `infra` — après #348 uniquement |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#350](https://github.com/sirius911/moutilloux/issues/350) | Infra front : nettoyer le proxy Vite (/arbitre, /panel, /accounts) | `vite.config.ts`, `CLAUDE.md` | `infra` — après #348 ; met à jour CLAUDE.md §1 |

---

## Périmètre backend

#347 et #349 — un endpoint neuf (wrapper fin sur le moteur existant, zéro
logique dupliquée) et une suppression de vues. Aucune migration de données.

## Fichiers partagés (orchestrateur uniquement)

- `live/urls.py` et `moutilloux/urls.py` (#347, #349) — routes posées/retirées
  par l'orchestrateur.
- `frontend/app/vite.config.ts` (#350) — config partagée, orchestrateur.

## Ordre d'exécution suggéré

**Strictement séquentiel** (chaîne de dépendances, pas de fan-out) :

1. #347 — le endpoint `/api/` existe (l'ancien chemin fonctionne encore).
2. #348 — le front bascule (plus aucun appel `/arbitre/…`).
3. #349 — purge des vues template (plus rien ne les consomme).
4. #350 — nettoyage du proxy + CLAUDE.md.
