# 118 — Garde de route : résolution et validation de `:eventId`

**Sévérité :** 🟠 Majeure
**Fichier(s) :** `frontend/app/src/router/index.ts`
**Spec source :** `specs/technical/routing-context.md`
**Infra partagée :** oui — réservé à l'orchestrateur

## Description

La spec définit quatre cas à gérer à l'entrée d'une route dépendante d'une épreuve :

1. **`:eventId` absent** → rediriger vers la première épreuve de l'édition active.
2. **`:eventId` inconnu** (n'appartient pas aux épreuves de l'édition active) → rediriger
   vers la première épreuve (lien périmé rattrapé silencieusement).
3. **Aucune épreuve dans l'édition active** → laisser passer (état vide géré par les
   écrans — ticket #119).
4. **`:eventId` valide** → laisser passer.

Actuellement, aucune garde ne couvre ces cas : si on navigue vers
`/admin/events/999/groups` avec un `eventId` inexistant, le store garde
son `activeEventId` précédent et l'écran se comporte de façon incohérente.

## Correction

Dans `router/index.ts`, ajouter une garde `beforeEnter` sur la route parent
`/admin/events/:eventId` (ou dans le `beforeEach` global en filtrant sur la présence
de `params.eventId`) :

```ts
async function resolveEventId(to, _from, next) {
  const eventStore = useEventStore()
  if (!eventStore.editions.length) {
    await eventStore.fetchEditions()
  }
  const events = eventStore.events
  const requestedId = Number(to.params.eventId)

  if (!requestedId || !events.find(e => e.id === requestedId)) {
    // Absent ou inconnu → premier de la liste, ou état vide
    const defaultEvent = events[0]
    if (defaultEvent) {
      return next({ ...to, params: { ...to.params, eventId: String(defaultEvent.id) }, replace: true })
    }
    // Aucune épreuve → laisser passer (état vide géré par l'écran)
    return next()
  }
  return next()
}
```

Attacher cette garde à la route parent `/admin/events/:eventId` via `beforeEnter`.

**Dépend de :** #115 (la route parent doit exister)
**Dépend de :** le store `event.ts` doit exposer `fetchEditions` + `events` (déjà le cas)
