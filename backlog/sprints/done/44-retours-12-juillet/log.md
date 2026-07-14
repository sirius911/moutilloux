# Log — Sprint 44 : Correctifs retours du 12 juillet

| # | Date | Verdict spec | Dérives | Nouvelles issues | Issues sprint restantes |
|---|------|-------------|---------|-----------------|------------------------|
| — | 2026-07-12 | — | Sprint planifié | #383, #384, #385, #386, #387, #388, #389, #390, #391 | 9 |
| #171 | 2026-07-12 | ❌ | 15 dérives (0 spec ✅, 2 ⚠️, 4 ❌) — toutes correspondent aux 9 issues déjà ouvertes | 0 | 9 |
| #172 | 2026-07-12 | ❌ | 7 dérives (2 spec ✅, 1 ⚠️, 3 ❌) — toutes correspondent aux 7 issues déjà ouvertes (#385/#387 confirmés clos) | 0 | 7 |
| #173 | 2026-07-13 | ❌ | 5 dérives (2 spec ✅, 1 ⚠️, 3 ❌) — 4 correspondent aux issues déjà ouvertes (#383, #384, #388, #390 ; #386/#389 confirmés clos), 1 note non ticketée (artefact rédactionnel non fonctionnel sur cycle-de-vie-epreuve.md) | 0 | 5 |
| #174 | 2026-07-13 | ⚠️ | 3 dérives (4 spec ✅, 2 ⚠️, 0 ❌) — toutes correspondent exactement aux 3 issues déjà ouvertes (#388, #390, #391) ; #383/#384/#385/#386/#387/#389 confirmés clos et conformes | 0 | 3 |
| #175 | 2026-07-13 | ⚠️ | 1 dérive neuve non ticketée (5 spec ✅, 1 ⚠️, 0 ❌) — `AdminBracket.vue:560` (panneau Qualifiés disponibles) lit encore `entry.player?.fullName` au lieu de `entry.displayName`, hors périmètre du sweep #388, reproduit la classe de bug "TBD" pour le Double ; reste `#391` déjà ouvert (store event.ts) | 1 (#393) | 2 |
| #176 | 2026-07-13 | ✅ | 0 dérive — 6 spec ✅ Conforme, correction #393 confirmée présente (`AdminBracket.vue:560`), aucune occurrence résiduelle du motif fautif dans le sweep, `npx vue-tsc --noEmit` 0 erreur | 0 | 0 |
