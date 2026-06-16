# Backlog — Moutilloux Front-End

Généré par analyse automatique multi-agents (cartographie + revue de code par section).  
**30 tickets** — classés par sévérité.

## 🔴 Critiques (bloqueront la mise en production)

| # | Titre | Fichier(s) |
|---|-------|-----------|
| ~~[001](./001-bracket-routes-panel-cassees.md)~~ | ~~Routes `/panel/` cassées pour bracket (assignBracket/clearBracket)~~ | ✅ **Clôturé** — endpoints `/api/` créés, routes câblées, store mis à jour. Révisé et approuvé. |
| ~~[002](./002-arbitre-finish-left-en-dur.md)~~ | ~~ArbitreMatch : `finish_left` en dur → mauvais vainqueur possible~~ | ✅ **Clôturé** — action `finish_winner` (repère modèle A/B) + modale deux boutons nommés. Réservés mineurs : meneur ignore les points en cours, modale se ferme sur erreur. |
| ~~[003](./003-tvlayout-transform-ordre-incorrect.md)~~ | ~~TvLayout : ordre `translate`/`scale` incorrect → centrage cassé~~ | ✅ **Clôturé** — formule `useScale.ts` simplifiée + ordre transform inversé dans `TvLayout.vue` et `ArbitreMatch.vue`. Révisé et approuvé. |

## 🟠 Majeures (à corriger avant le sprint suivant)

| # | Titre | Fichier(s) |
|---|-------|-----------|
| [004](./004-router-guard-admin-routes-enfants.md) | Router : guard `requiresAdmin` ne couvre pas les routes enfants | `router/index.ts` |
| [005](./005-login-redirection-post-login-role.md) | LoginView : redirection post-login ignore le rôle réel | `LoginView.vue` |
| [006](./006-auth-store-logout-absent.md) | auth.ts : action `logout()` absente du store | `stores/auth.ts` |
| [007](./007-admin-tournoi-stats-toujours-zero.md) | AdminTournoi : dashboard de stats affiche toujours 0 | `AdminTournoi.vue` |
| [008](./008-admin-matches-event-bubbling-feature.md) | AdminMatches : clic "Mettre en avant" ouvre aussi le panneau d'édition | `AdminMatches.vue` |
| [009](./009-admin-groups-timing-navigation-directe.md) | AdminGroups : données non chargées sur navigation directe | `AdminGroups.vue` |
| [010](./010-admin-inscriptions-inscrire-tout-filtre.md) | AdminInscriptions : "Tout inscrire" applique le filtre de recherche | `AdminInscriptions.vue` |
| [011](./011-arbitre-match-polling-300ms.md) | ArbitreMatch + TvScoreboard : polling à 300 ms (cible 2 s) | `ArbitreMatch.vue`, `TvScoreboard.vue` |
| [012](./012-arbitre-match-boutons-footer-match-termine.md) | ArbitreMatch : boutons footer actifs sur match FINISHED | `ArbitreMatch.vue` |
| [013](./013-arbitre-match-annuler-semantique.md) | ArbitreMatch : bouton "Annuler" = `reset_points` ≠ undo | `ArbitreMatch.vue` |
| [014](./014-arbitre-home-onglet-termines-vide.md) | ArbitreHome : onglet "Terminés" toujours vide (API exclut FINISHED) | `ArbitreHome.vue`, `api_views.py` |
| [015](./015-arbitre-home-logout-get-csrf.md) | ArbitreHome : logout via GET non protégé par CSRF | `ArbitreHome.vue` |
| [016](./016-tvidle-await-manquant-fetchs-ignores.md) | TvIdle : `await` manquant → fetchs secondaires jamais exécutés | `TvIdle.vue` |
| [017](./017-tvpoules-events-zero-au-lieu-actif.md) | TvPoules : affiche `events[0]` au lieu de l'épreuve active | `TvPoules.vue` |
| [018](./018-tvlayout-navigation-onglets-absente.md) | TvLayout : aucune navigation entre les onglets TV | `TvLayout.vue` |
| [019](./019-useapi-401-non-geree.md) | useApi : redirection 401 non gérée → pas de renvoi vers le login | `composables/useApi.ts` |
| [020](./020-usepolling-pause-onglet-cache.md) | usePolling : pas de pause sur onglet caché | `composables/usePolling.ts` |
| [021](./021-editMatchPanel-format-silencieusement-ignore.md) | EditMatchPanel : onglet "Format" silencieusement ignoré à la sauvegarde | `EditMatchPanel.vue` |
| [022](./022-event-store-activeEventId-null-assertion.md) | event.ts : `activeEventId!` → URLs `/api/events/undefined/…` | `stores/event.ts` |

## 🟡 Mineures (backlog à planifier)

| # | Titre | Fichier(s) |
|---|-------|-----------|
| [023](./023-guard-role-arbitre-manquant.md) | Router : garde `isReferee` + prop `matchId: string` → `number` | `router/index.ts`, `ArbitreMatch.vue` |
| [024](./024-extract-api-error-incoherent.md) | `extractApiError` non utilisé dans 4+ modales + doublon AdminBracket | plusieurs modales |
| [025](./025-polling-tv-mal-calibre.md) | Polling TV mal calibré (TvPoules 5 s, TvBracket 10 s → cible 4 s) | `TvPoules.vue`, `TvBracket.vue` |
| [026](./026-etats-vides-absents.md) | États vides absents (TvBracket, TvPoules, ArbitreMatch loading) | plusieurs vues |
| [027](./027-useapi-logs-console-production.md) | useApi : logs de débogage laissés en production | `composables/useApi.ts` |
| [028](./028-modal-shell-escape-absent.md) | ModalShell : fermeture sur Escape non implémentée | `ModalShell.vue` |
| [029](./029-tvidle-donnees-figees-sans-polling.md) | TvIdle : données kanban/groups/bracket figées (polling absent) | `TvIdle.vue` |
| [030](./030-arbitre-match-finish-modal-ferme-sur-erreur.md) | ArbitreMatch : modale "Terminer" se ferme même si `sendAction` échoue | `ArbitreMatch.vue` |
