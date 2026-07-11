---
sprint: 40
nom: "Planning : journées repliables"
specs:
  - specs/screens/admin-matchs.md
modules:
  - frontend/app/src/views/admin/AdminMatches.vue
tickets-tag: sprint-40
branche: claude/sprint/40-planning-journees-repliables
branche-parent: main
log: backlog/sprints/40-planning-journees-repliables/log.md
---

# Sprint 40 — Planning : journées repliables

**Objectif :** les cartes de journée du calendrier deviennent
repliables/dépliables — journées entièrement jouées repliées par défaut,
en-tête replié à résumé riche (compteur joués/total, plage horaire, pastille
de capacité), et dépliage au survol (~600 ms) pendant un glisser-déposer.

> Origine : retours produit 2026-07-09 (problématique 1 — « faire en sorte que
> les jours puissent être pliés/dépliés »). Arbitrages rendus en session :
> passées repliées par défaut (état non persisté), survol déplie pendant un
> drag (pas de dépôt direct sur l'en-tête replié), résumé riche. La règle
> anti-`overflow: hidden` sur `.play-day` (#328) reste valable à l'état
> déplié.

## Définition de terminé

- Golden path : édition avec une journée finie, une en cours, une future →
  au chargement, la finie est repliée (« N/N · début → fin », pastille de
  capacité visible), les deux autres dépliées ; clic sur l'en-tête →
  repli/dépli ; drag d'une carte de la pile avec survol ~600 ms de l'en-tête
  replié → la journée se déplie, dépôt à une position précise → la séquence
  envoyée au serveur la reflète ; un dépôt direct sur l'en-tête replié ne
  planifie rien.
- Le scroll et l'édition d'heure de début en place fonctionnent comme avant à
  l'état déplié (pas de régression #306/#307/#328).
- `npx vue-tsc --noEmit` passe.
- Spec review `✅ Conforme` sur [[admin-matchs]].
- Aucune issue `sprint-40` ouverte.

## Specs ciblées

- [`specs/screens/admin-matchs.md`](../../../specs/screens/admin-matchs.md) — §Journées (modèle plié/déplié) et §Flux glisser-déposer (survol déplie)

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 40 — Planning : journées repliables »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#355](https://github.com/sirius911/moutilloux/issues/355) | Front : AdminMatches — journées repliables (défaut + en-tête résumé riche) | `AdminMatches.vue` | débloque #356 |
| [#356](https://github.com/sirius911/moutilloux/issues/356) | Front : AdminMatches — drag vers journée repliée : dépliage au survol | `AdminMatches.vue` | après #355 (même fichier) |

### 🟡 Mineures

Aucune.

---

## Périmètre backend

Aucun — pur UI d'écran, le modèle ([[planning]]) ne change pas.

## Fichiers partagés (orchestrateur uniquement)

Aucun.

## Ordre d'exécution suggéré

1. #355 puis #356 — même fichier, même agent, strictement séquentiel
   (le comportement de drag s'appuie sur l'état replié posé par #355).
