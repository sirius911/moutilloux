# 119 — Écrans dépendants : état vide « Aucune épreuve active »

**Sévérité :** 🟡 Mineure
**Fichier(s) :** `frontend/app/src/views/admin/AdminInscriptions.vue`, `frontend/app/src/views/admin/AdminGroups.vue`, `frontend/app/src/views/admin/AdminMatches.vue`, `frontend/app/src/views/admin/AdminBracket.vue`
**Spec source :** `specs/technical/routing-context.md`

## Description

La spec prévoit que si l'édition active ne contient aucune épreuve, les écrans
dépendants affichent un **état vide « Aucune épreuve active »** avec un lien vers
l'écran Tournoi (plutôt qu'un écran cassé ou vide sans explication).

Actuellement, si `eventStore.events` est vide, les sélecteurs affichent
« Aucune épreuve » (option désactivée) mais les corps d'écrans restent vides sans
message ni guide.

## Correction

Dans chacun des 4 écrans, ajouter un bloc d'état vide conditionnel au début du
`<template>` (avant la page principale) :

```vue
<template>
  <div v-if="eventStore.events.length === 0" class="empty-state">
    <p>Aucune épreuve active.</p>
    <RouterLink to="/admin/tournoi">Créer une épreuve dans Tournoi →</RouterLink>
  </div>
  <div v-else class="admin-page">
    <!-- contenu existant -->
  </div>
</template>
```

Le style `.empty-state` peut réutiliser les tokens CSS existants (centré, texte
`--ink-2`, lien en `--accent`).

**Dépend de :** #115, #118 (la garde laisse passer quand `events[]` est vide)
