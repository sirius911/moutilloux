# Log — Sprint 27 : Poules : suivi & suppression

| # | Date | Verdict spec | Dérives | Nouvelles issues | Issues sprint restantes |
|---|------|-------------|---------|-----------------|------------------------|
| — | 2026-07-07 | — | Sprint planifié (revue produit 2026-07-07, décision 29) | #292-296 | 5 |
| #111 | 2026-07-08 | ❌ Dérive bloquante (attendu, sprint pas démarré) | 3 dérives confirmées dans le code réel (`AdminGroups.vue` : aucune action « Supprimer la poule » en `INSCRIPTION` ; `api_event_groups` — `live/api_views.py:484-` — expose standings + grille croisée mais aucun détail des matchs par poule ; aucune légende du badge Q ni des états), toutes déjà couvertes par #292-296 | 0 | 5 |
| #112 | 2026-07-08 | ❌ Dérive bloquante (attendu, 2/5 tickets traités jusqu'ici) | 3 dérives confirmées dans `AdminGroups.vue` : aucune action « Supprimer la poule » en `INSCRIPTION` (#293) ; mode suivi absent — aucun rang/V-D/points ni matchs de poule affichés malgré `matches` désormais exposé par `api_event_groups` (#294 ✅ côté back) et `StandingRow.rank/wins/losses/points` déjà typés (#295) ; aucune légende du badge Q ni des états (#296). Toutes déjà couvertes par les issues ouvertes du sprint | 0 | 3 |
