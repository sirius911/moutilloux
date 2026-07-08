# Log — Sprint 31 : TV : rotation stable & pastille de progression

| # | Date | Verdict spec | Dérives | Nouvelles issues | Issues sprint restantes |
|---|------|-------------|---------|-----------------|------------------------|
| — | 2026-07-07 | — | Sprint planifié (revue produit 2026-07-07, décision 12 tv-map) | #308-309 | 2 |
| #1 | 2026-07-08 | ⚠️ Dérive mineure | 2 dérives (`SLIDES` computed recalculé à chaque poll `tv/idle`, index positionnel → rotation non stable ; pastille sans remplissage progressif) — les deux déjà couvertes par #308/#309 | 0 nouvelle issue | 2 |
| #1 (relecture post-implém.) | 2026-07-08 | ✅ Conforme | #308/#309 implémentés et revus (rotation par `displayedKind` figé + pastille `pagerTick` sur 8s) — relecture des § « Rotation stable » et « Pastille de progression » de `tv-live.md` contre le code final : 0 écart résiduel | 0 nouvelle issue | 0 |
