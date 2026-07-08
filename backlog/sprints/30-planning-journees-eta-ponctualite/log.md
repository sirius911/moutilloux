# Log — Sprint 30 : Planning : journées, ETA monotone & ponctualité

| # | Date | Verdict spec | Dérives | Nouvelles issues | Issues sprint restantes |
|---|------|-------------|---------|-----------------|------------------------|
| — | 2026-07-07 | — | Sprint planifié (revue produit 2026-07-07, décisions 31-32 + bug scroll) | #302-307 | 6 |
| #119 | 2026-07-08 | ❌ | 6 dérives attendues (sprint pas démarré) toutes déjà ticketées : pas d'endpoint `play-days/generate/` (#302), pas de bouton « Générer depuis l'édition » dans `PlayDayModal.vue` (#303), moteur ETA existant non-monotone sur le cas match fini en avance — `computedETAs` avance le curseur sur `finishedAt` seul au lieu de `max(t+durée, finished_at)` (#304), aucune teinte de ponctualité rouge/orange/vert ni légende (#305), heure de début de journée non éditable en place (#306), bug de scroll des journées confirmé côté ticket (#307) | 0 | 6 |
