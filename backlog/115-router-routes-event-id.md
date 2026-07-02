# 115 — Router : migrer les routes admin vers `/admin/events/:eventId/...`

**Sévérité :** 🟠 Majeure
**Fichier(s) :** `frontend/app/src/router/index.ts`
**Spec source :** `specs/technical/routing-context.md`
**Infra partagée :** oui — réservé à l'orchestrateur

## Description

La spec définit les routes dépendantes d'une épreuve avec un segment `:eventId` :
`/admin/events/:eventId/inscriptions`, `/admin/events/:eventId/groups`,
`/admin/events/:eventId/matches`, `/admin/events/:eventId/bracket`.

Le code actuel les expose sans ce segment : `/admin/inscriptions`, `/admin/groups`,
`/admin/matches`, `/admin/bracket`. L'URL ne porte pas l'épreuve active, ce qui
rend le rechargement de page et le partage de liens non fonctionnels (l'épreuve
retombe toujours sur `events[0]`).

## Correction

Dans `router/index.ts`, sous la route `/admin`, ajouter une route imbriquée :

```ts
{
  path: 'events/:eventId',
  children: [
    { path: 'inscriptions', component: () => import('@/views/admin/AdminInscriptions.vue') },
    { path: 'groups',       component: () => import('@/views/admin/AdminGroups.vue') },
    { path: 'matches',      component: () => import('@/views/admin/AdminMatches.vue') },
    { path: 'bracket',      component: () => import('@/views/admin/AdminBracket.vue') },
  ],
},
```

Les anciennes routes plates (`/admin/inscriptions`, etc.) peuvent être supprimées ou
gardées comme redirections pendant la transition — supprimer est préférable pour éviter
la confusion.

**Dépendances :** ce ticket est prérequis de #116, #117, #118, #119.
