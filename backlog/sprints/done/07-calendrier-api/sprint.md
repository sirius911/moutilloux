---
sprint: 7
nom: Calendrier — modèle & API
specs:
  - specs/technical/planning.md
modules:
  - live/models.py
  - live/api_views.py
  - live/admin_views.py
  - live/urls.py
tickets-tag: sprint-07
branche: claude/sprint/07-calendrier-api
branche-parent: claude/sprint/06-refacto-selecteur
log: backlog/sprints/07-calendrier-api/log.md
---

# Sprint 07 — Calendrier : modèle & API

**Objectif :** Mettre en place le backend complet du calendrier des matchs —
modèles `PlayDay` + `Break`, CRUD JSON, packer « calendrier », reorder évolué,
pré-pose automatique et enrichissement de l'état TV.

## Définition de terminé

- Modèles `PlayDay` et `Break` en base (migration OK)
- CRUD JSON PlayDay + Break exposés (`/api/`)
- Packer calendrier : matchs regroupés par journée + pile à planifier
- Reorder évolué : affectation journée + position, matchs et pauses
- Pré-pose : endpoint `POST /api/events/<id>/matches/auto-arrange/`
- État TV enrichi : N prochains matchs + `next`
- Spec review sur `specs/technical/planning.md` → verdict `✅ Conforme`
- Aucun ticket `sprint-07` ouvert dans GitHub Issues

> Les tickets sont gérés dans GitHub Issues (milestone "Sprint 07 — Calendrier : modèle & API").

## Specs ciblées

- [`specs/technical/planning.md`](../../../specs/technical/planning.md)
  → fichiers : `live/models.py`, `live/api_views.py`, `live/admin_views.py`

---

## Périmètre backend

Tous les nouveaux endpoints exposent des mutations dont la logique est dans
`admin_views.py` (fonctions de service). `live/urls.py` est câblé par
l'orchestrateur uniquement.

## Ordre d'exécution suggéré

1. #87 — Modèles PlayDay + Break (✅ terminé)
2. #88 — CRUD JSON PlayDay + Break
3. #89 — Packer « calendrier »
4. #90 — Reorder évolué
5. #91 — Pré-pose auto
6. #92 — État TV enrichi
7. #93 — Durée match par défaut (mineure)
