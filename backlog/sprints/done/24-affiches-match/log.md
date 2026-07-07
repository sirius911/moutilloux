# Log — Sprint 24 : Affiches de match

| # | Date | Verdict spec | Dérives | Nouvelles issues | Issues sprint restantes |
|---|------|-------------|---------|-----------------|------------------------|
| — | 2026-07-04 | — | Sprint planifié (specs affiche-match du brainstorm 2026-07-04 ; intègre la PR #1) | #263-272 | 10 |
| #96 | 2026-07-05 | ✅ Conforme | 0 dérive (toutes les exigences des 4 specs couvertes par #264-272 ; #263 fait au setup) | 0 nouvelle issue | 9 |
| #97 | 2026-07-05 | ✅ Conforme | 0 dérive (fondations #263-265 fidèles aux 4 specs ; reste correctement en attente de #266-272) | 0 nouvelle issue | 7 |
| #98 | 2026-07-06 | ✅ Conforme | 0 dérive (upload photo #268 conforme à `admin-joueurs.md`/`affiche-match.md` — format, taille, contrat `_pack_player` non cassé ; reste correctement en attente de #266/#267/#269-272) | 0 nouvelle issue | 6 |
| #99 | 2026-07-06 | ✅ Conforme | 0 dérive (endpoints poster #266 + posterUrl/type Match #267 fidèles aux 4 specs ; reste correctement en attente de #269-272) | 0 nouvelle issue | 4 |
| #100 | 2026-07-07 | ⚠️ Dérive mineure | 1 dérive 🟡 (`admin-matchs.md` : onglet Affiche d'`EditMatchPanel.vue` ne gère pas le Double — 2 champs attitude fixes A/B, backend prêt pour 4 joueurs ; bug connu #270 saved/fermeture panneau revérifié, non re-signalé) | 1 nouvelle issue (#286) | 4 |
| #101 | 2026-07-07 | ⚠️ Dérive mineure | 1 dérive 🟡 (`affiche-match.md` : bouton « Générer 2 propositions » d'`EditMatchPanel.vue` ne teste pas la présence de `photoUrl` avant activation — garde côté serveur seule ; `admin-joueurs.md`/`tv-live.md` ✅ Conforme, `admin-matchs.md` dérive déjà connue #286 non re-signalée) | 1 nouvelle issue (#287) | 3 |
| #102 | 2026-07-07 | ✅ Conforme | 0 nouvelle dérive (4 specs relues point par point ; #287 confirmée toujours présente dans `EditMatchPanel.vue:201-208`, non re-signalée ; 2 suggestions annexes hors-périmètre — redirection 401 sur upload photo multipart, `transaction.atomic()` manquant sur `select_poster_candidate`/`_purge_job` — déjà couvertes par le TODO général 401 du CLAUDE.md, non ticketées) | 0 nouvelle issue | 1 |
