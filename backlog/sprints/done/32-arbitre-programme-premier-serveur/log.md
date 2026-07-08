# Log — Sprint 32 : Arbitre : programme du jour & premier serveur

| # | Date | Verdict spec | Dérives | Nouvelles issues | Issues sprint restantes |
|---|------|-------------|---------|-----------------|------------------------|
| — | 2026-07-07 | — | Sprint planifié (revue produit 2026-07-07) | #310-313 | 4 |
| #124 | 2026-07-08 | ⚠️ Dérive mineure | 2 dérives (UI onglets ArbitreHome + démarrage sans choix serveur ArbitreMatch — déjà couvertes par #310-313, 0 nouvelle issue) | 0 nouvelles issues | 4 |
| #125 | 2026-07-08 | ⚠️ Dérive mineure | `arbitre-home.md` ✅ Conforme (refonte #311 vérifiée : bloc « À l'instant », journées repliables, plus d'onglets) ; `arbitre-match.md` toujours ⚠️ (démarrage sans choix du serveur — couverte par #312/#313, 0 nouvelle issue) | 0 nouvelles issues | 2 |
| #125 | 2026-07-08 | ✅ Conforme | Backlog engine session #125 : #312 (back, `start_match(match, server=None)`) et #313 (front, modal de démarrage avec choix obligatoire du serveur) implémentés et approuvés. `arbitre-match.md` repassé ✅ Conforme (dérive du début de session résorbée). Bug pré-existant corrigé au passage : `handleStart()` consommait `/api/arbitre/matches/` comme tableau plat alors qu'il renvoie `{playDays, next}` depuis #310. | 0 nouvelles issues | 0 |
