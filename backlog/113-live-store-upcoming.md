# 113 — live.ts : fetchUpcoming + upcoming[] [infra sprint 09]

**Sévérité :** 🟠 Majeure
**Fichier(s) :** `frontend/app/src/stores/live.ts`
**Spec source :** `specs/screens/tv-programme.md`

## Description

La spec [[tv-programme]] requiert que la slide "Programme" (TvIdle) et le bandeau
"À suivre" (TvScoreboard) consomment les **N prochains matchs planifiés** via
`GET /api/tv/upcoming/` (Sprint 07, livré).

Le store `live.ts` n'expose ni `upcoming: Match[]` ni `currentPlayDay: PlayDay | null`
ni l'action `fetchUpcoming()`. Les tickets #101 et #102 ne peuvent pas se brancher sur
cette donnée.

**Ce que dit la spec :**
- Source : packer calendrier / état TV enrichi — le *next* et les *N prochains* sont
  exposés par `/api/tv/upcoming/` (champs `next`, `upcoming`, `currentPlayDay`).
- Polling TV ~4 s.

**Ce que fait le code :**
- `live.ts` n'a que `fetchScoreState()` → `/api/score_state/` (hero + next + now).
- Aucune action pour `/api/tv/upcoming/`.

## Correction

Dans `frontend/app/src/stores/live.ts` (fichier partagé — orchestrateur uniquement) :

1. Ajouter le type `TvUpcoming` dans `types/index.ts` :
   ```ts
   export interface TvUpcoming {
     next: Match | null
     upcoming: Match[]
     currentPlayDay: PlayDay | null
   }
   ```

2. Ajouter dans le store :
   ```ts
   const upcoming = ref<Match[]>([])
   const currentPlayDay = ref<PlayDay | null>(null)

   async function fetchUpcoming(n = 5) {
     const data = await get<TvUpcoming>(`/api/tv/upcoming/?n=${n}`)
     upcoming.value = data.upcoming
     currentPlayDay.value = data.currentPlayDay
     if (data.next) next.value = data.next   // sync avec hero next
   }
   ```

3. Exposer : `return { ..., upcoming, currentPlayDay, fetchUpcoming }`

> Fichier partagé — câblé par l'orchestrateur. Les agents #101 et #102
> peuvent supposer que `live.upcoming` et `live.fetchUpcoming` existent.
