# 117 — Sélecteur d'épreuve : `router.push` au lieu de mutation store (3 écrans)

**Sévérité :** 🟠 Majeure
**Fichier(s) :** `frontend/app/src/views/admin/AdminInscriptions.vue`, `frontend/app/src/views/admin/AdminGroups.vue`, `frontend/app/src/views/admin/AdminMatches.vue`
**Spec source :** `specs/technical/routing-context.md`

## Description

La spec exige que le sélecteur d'épreuve en en-tête de page **navigue** vers le même
écran avec un `:eventId` différent (`router.push`), au lieu de muter directement
`eventStore.activeEventId`. Le changement de store doit être piloté par le watcher
de route du shell (#116), pas par le sélecteur.

**État actuel par écran :**

- `AdminInscriptions.vue` : `setActiveEvent(id)` → `eventStore.activeEventId = numId`
- `AdminGroups.vue` : `setActiveEvent(id)` → `eventStore.activeEventId = numId`
- `AdminMatches.vue` : `@change` inline → `eventStore.activeEventId = Number(...)`

Ces trois mutations contournent l'URL et cassent le bookmark/rechargement.

## Correction

Dans chacun des 3 écrans, remplacer la mutation par une navigation :

```ts
import { useRouter, useRoute } from 'vue-router'
const router = useRouter()
const route = useRoute()

function setActiveEvent(id: string) {
  const numId = parseInt(id, 10)
  if (!isNaN(numId)) {
    // Naviguer vers le même écran avec le nouvel eventId
    router.push({ params: { ...route.params, eventId: numId } })
  }
}
```

Supprimer l'initialisation par `watch(activeEventId)` au montage si elle était
présente pour compenser la mutation directe — le watcher de route du shell (#115)
s'en charge désormais.

**Dépend de :** #115 (routes `:eventId`), #116 (watcher de route dans le shell)
