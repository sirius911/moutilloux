# Log — Sprint 20 : Transverse : erreurs API & routing

| # | Date | Verdict spec | Dérives | Nouvelles issues | Issues sprint restantes |
|---|------|-------------|---------|-----------------|------------------------|
| — | 2026-07-02 | — | Sprint planifié (audit admin) | #207-210 (+ #17, #20, #177 réutilisées) | 7 |
| #1 | 2026-07-03 | ⚠️ Dérive mineure | `routing-context.md` : 1 (« Sélectionner » Tournoi mute le store, #208) ; `admin-shell.md` : 2 (compteurs sidebar à 0 avant chargement #209 ; lien mort `[[useapi-401]]` #207) | 0 nouvelle issue (7 déjà ticketées) | 4 (après clôture #207, #20, #17 cette session) |
| #2 | 2026-07-03 | ⚠️ Dérive mineure | `routing-context.md` : 1 (idem #208, confirmée à `AdminTournoi.vue:229`) ; `admin-shell.md` : 1 (idem #209, confirmée `AdminLayout.vue:56-59` — portée un peu plus large que le libellé initial : 4 compteurs sur 6 touchés, pas seulement un) ; aucun lien mort résiduel | 0 nouvelle issue (dérives déjà ticketées) | 4 (avant traitement des tickets de cette session) |
| #3 | 2026-07-04 | ⚠️ Dérive mineure | `routing-context.md` : ✅ Conforme (URL fait foi, watcher store, sélecteur navigue via `router.push` sur les 4 écrans dépendants — confirmé) ; `admin-shell.md` : 1 (idem #209, confirmée : `bracketCount` compte toujours 7 slots (4+2+1) au lieu des matchs réels ; `events.length`/`allPlayers.length` affichent 0 avant chargement) | 0 nouvelle issue (dérive déjà ticketée #209) | 1 (#209) |
