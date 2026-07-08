# 116 — AdminLayout : liens de sidebar porteurs d'`:eventId` + watcher de route

**Sévérité :** 🟠 Majeure
**Fichier(s) :** `frontend/app/src/views/admin/AdminLayout.vue`
**Spec source :** `specs/technical/routing-context.md`
**Infra partagée :** oui — réservé à l'orchestrateur

## Description

Deux problèmes liés dans le shell admin :

1. **Liens de sidebar** : `navItems` pointe vers `/admin/inscriptions` etc. — après
   #115, ces routes n'existent plus. Ils doivent pointer vers
   `/admin/events/${activeEventId}/inscriptions` etc., et ne cibler ces routes que
   si `activeEventId` est résolu.

2. **Watcher de route absent** : aucun watcher ne synchronise `activeEventId` depuis
   `route.params.eventId`. La spec impose que l'URL soit la source de vérité :
   chaque navigation vers une route `:eventId` doit mettre à jour `activeEventId`
   dans le store. Sans ce watcher, changer de route ou recharger la page ne met pas
   à jour l'épreuve active.

## Correction

Dans `AdminLayout.vue` :

1. Importer `watch` (déjà importé), `useRoute` et `useRouter` (déjà présents).
   Ajouter un `watchEffect` ou `watch` sur `route.params.eventId` qui met à jour
   `eventStore.activeEventId` :

```ts
watch(
  () => route.params.eventId,
  (id) => {
    const numId = id ? Number(id) : null
    if (numId && eventStore.activeEventId !== numId) {
      eventStore.activeEventId = numId
    }
  },
  { immediate: true }
)
```

2. Mettre à jour `navItems` pour construire les chemins dynamiquement :

```ts
const eventId = computed(() => eventStore.activeEventId)

const navItems = computed(() => {
  const eid = eventId.value
  const base = eid ? `/admin/events/${eid}` : null
  return [
    { path: '/admin/tournoi',               label: 'Tournoi',       icon: '🏛', count: eventStore.events.length },
    { path: '/admin/players',               label: 'Joueurs',       icon: '👤', count: eventStore.allPlayers.length },
    { path: base ? `${base}/inscriptions` : null, label: 'Inscriptions',  icon: '📝', count: eventStore.players.length },
    { path: base ? `${base}/groups` : null,       label: 'Poules',        icon: '⊞',  count: eventStore.groups.length },
    { path: base ? `${base}/matches` : null,      label: 'Planning',      icon: '⚡', count: matchCount },
    { path: base ? `${base}/bracket` : null,      label: 'Tableau final', icon: '🏆', count: bracketCount },
  ]
})
```

Les liens avec `path: null` sont rendus désactivés (classe CSS `disabled`) en attendant
qu'une épreuve soit résolue.

**Dépend de :** #115 (routes avec `:eventId` doivent exister avant de cibler ces chemins)
