# Log — Sprint 42 : TV : score broadcast et phase en grand

| # | Date | Verdict spec | Dérives | Nouvelles issues | Issues sprint restantes |
|---|------|-------------|---------|-----------------|------------------------|
| — | 2026-07-10 | — | Sprint planifié | #361, #362, #363, #364, #365 | 5 |
| #157 | 2026-07-10 | ⚠️ Dérive mineure | 3 dérives (bande de score encore centrée/une-seule-ligne au lieu de deux lignes par joueur ; `stake-panel` conserve la variante mini-tableau `kind: 'bracket'` en template ; `_pack_tv_stake` (`live/api_views.py:2140`) renvoie toujours cette variante bracket) | 0 nouvelle (correspondent exactement à #361/#362/#363) | 5 |
| #158 | 2026-07-10 | ⚠️ Dérive mineure | 1 dérive restante (`TvScoreboard.vue` conserve le bloc `v-else-if="live.stake.kind === 'bracket'"` / `.stake-mini-bracket`, désormais mort côté données depuis #363 mais toujours en template — pas de « phase en grand » centrée au-dessus de la bande pour remplacer l'ancien mini-tableau, seul un `stageLabel` discret subsiste dans `sb-header-stage`) | 0 nouvelle (correspond exactement à #362, déjà ouverte) | 3 |
