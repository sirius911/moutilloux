---
type: transverse
module: erreurs-api
fichiers:
  - frontend/app/src/composables/useApi.ts
  - frontend/app/src/lib/apiError.ts
---

# Spec transverse — Erreurs API

> Comment un appel API en échec est détecté, traduit en message lisible et affiché,
> pour tous les écrans admin et arbitre. Référencée par [[admin-shell]] (session
> expirée) et applicable à tout écran qui appelle `useApi()`.

## Contrats d'erreur serveur

Les endpoints `/api/...` renvoient un corps JSON en cas d'échec :

| Statut | Cas | Corps |
|---|---|---|
| `400` | Requête invalide (champ manquant, JSON illisible) | `{ "error": "message" }` ou `{ "error": "...", "fields": {...} }` (erreurs de formulaire par champ, `__all__` pour les erreurs non liées à un champ précis) |
| `401` | Non authentifié (`/api/me/`) ou identifiants incorrects (`/api/auth/login/`) | `{ "error": "message" }` |
| `409` | Conflit métier (action impossible dans l'état courant, ex. changer le service en cours de jeu) | `{ "error": "message" }` |

Une session expirée sur un endpoint protégé par `@login_required` /
`superuser_required` ne renvoie **pas** ce contrat JSON : Django redirige vers
`/accounts/login/` en HTML (voir « Session expirée » ci-dessous).

## `useApi` — détection des échecs

`apiFetch` (dans `useApi.ts`) lève une exception sur tout statut non-2xx :
`new Error('[<status>] <path> — <body brut>')`.

Deux cas déclenchent une redirection vers `/login`, gérés **dans `useApi`**, avant
que l'exception ne remonte à l'écran appelant :

1. **Redirection HTML Django** (`res.redirected` vers `/accounts/login`) — cas
   historique, un `@login_required` a intercepté une session expirée.
2. **401 JSON** — un endpoint a renvoyé `{"error": ...}` avec le statut `401`.

**Exception** : les endpoints d'authentification eux-mêmes (`/api/me/`,
`/api/auth/login/`) renvoient un 401 **attendu** (utilisateur non connecté,
identifiants incorrects) — ce cas ne doit **pas** rediriger, sinon la page
`/login` boucle sur elle-même ou l'erreur de saisie ne peut jamais s'afficher.
`useApi` exclut ces deux chemins de la redirection automatique ; l'appelant
(`auth.ts`, `LoginView.vue`) gère lui-même ce 401 comme aujourd'hui.

Dans tous les autres cas de 401, la redirection est identique au cas HTML :
`window.location.href = '/login'` (rechargement complet, réinitialise tout
l'état front).

## Extraction du message pour l'affichage

**`extractApiError(e, fallback)`** (`lib/apiError.ts`) est la **seule** fonction à
utiliser pour transformer l'exception de `useApi` en message affichable :

1. Parse le corps JSON de l'exception.
2. Si `fields.__all__` est présent (tableau de chaînes) → le joindre (erreur
   métier la plus précise, ex. contrainte de service).
3. Sinon si `error` est une chaîne → la retourner telle quelle (message serveur).
4. Sinon (corps non-JSON, erreur réseau) → retourner `fallback`.

Toute autre implémentation locale ou dupliquée (ex. l'ancienne `apiErrorMessage`
de `useApi.ts`, ou un `extractError` propre à un composant) est une dérive à
corriger : un seul point de vérité pour ce mapping.

## Convention d'affichage

- Ne **jamais** afficher le message brut de l'exception (`[400] /api/... — {...}`)
  à l'utilisateur : toujours passer par `extractApiError`.
- Le message extrait s'affiche dans la zone d'erreur de l'écran ou de la modale
  concernée (bandeau/texte existant), pas via `alert()`.
- `fallback` est un message générique adapté à l'action tentée (ex. « Action
  impossible. », « Impossible de charger les données. »).

## Journalisation

Aucun `console.log`/`console.error` de débogage dans `useApi.ts` en usage normal
(CSRF token, statut de chaque requête) : ce sont des traces de mise au point, pas
un comportement transverse à conserver. Une erreur réseau réellement inattendue
peut être loguée par l'appelant s'il le juge utile, pas systématiquement par le
composable.

## Hors périmètre

- Retentative automatique (retry) sur erreur réseau : non couvert, l'utilisateur
  relance l'action manuellement.
- Notifications globales (toasts) : l'affichage reste local à l'écran/la modale,
  pas de système de notification transverse pour l'instant.
