<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useEventStore } from '@/stores/event'
import { extractApiError } from '@/lib/apiError'
import CategoryModal from '@/components/modals/CategoryModal.vue'
import CourtModal from '@/components/modals/CourtModal.vue'
import type { Category, Court } from '@/types'

const eventStore = useEventStore()

const tab = ref<'categories' | 'courts'>('categories')
const error = ref('')

const categories = computed(() => eventStore.categories)
const courts = computed(() => eventStore.courts)

// Modales : un seul état, discriminé par `kind`.
type ModalState =
  | { kind: 'category'; editing: Category | null }
  | { kind: 'court'; editing: Court | null }
const modal = ref<ModalState | null>(null)

onMounted(() => {
  eventStore.fetchCategories()
  eventStore.fetchCourts()
})

async function removeCategory(c: Category) {
  if (!confirm(`Supprimer la catégorie « ${c.name} » ?`)) return
  error.value = ''
  try {
    await eventStore.deleteCategory(c.id)
  } catch (e) {
    error.value = extractApiError(e)
  }
}

async function removeCourt(c: Court) {
  if (!confirm(`Supprimer le court « ${c.name} » ?`)) return
  error.value = ''
  try {
    await eventStore.deleteCourt(c.id)
  } catch (e) {
    error.value = extractApiError(e)
  }
}
</script>

<template>
  <div class="admin-page">
    <header class="page-header">
      <div>
        <p class="breadcrumb">Administration</p>
        <h1 class="page-title">Configuration</h1>
        <p class="page-sub">Référentiels partagés entre les éditions</p>
      </div>
    </header>

    <div class="page-content">
      <!-- Onglets -->
      <div class="cfg-tabs">
        <button :class="['cfg-tab', { on: tab === 'categories' }]" type="button" @click="tab = 'categories'">
          Catégories
        </button>
        <button :class="['cfg-tab', { on: tab === 'courts' }]" type="button" @click="tab = 'courts'">
          Courts
        </button>
      </div>

      <p v-if="error" class="cfg-error">{{ error }}</p>

      <!-- Catégories -->
      <section v-show="tab === 'categories'" class="adm-card">
        <div class="adm-card-head">
          <h3>Catégories</h3>
          <button class="adm-btn primary" type="button" @click="modal = { kind: 'category', editing: null }">
            + Nouvelle catégorie
          </button>
        </div>

        <div v-if="categories.length === 0" class="adm-empty">Aucune catégorie.</div>

        <table v-else class="adm-table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Mode</th>
              <th>Épreuves</th>
              <th class="ta-r">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in categories" :key="c.id">
              <td><span class="adm-name">{{ c.name }}</span></td>
              <td>
                <span class="adm-pill adm-pill-ghost">{{ c.mode === 'S' ? 'Simple' : 'Double' }}</span>
              </td>
              <td class="tab">{{ c.eventsCount }}</td>
              <td class="ta-r">
                <button class="adm-btn" type="button" @click="modal = { kind: 'category', editing: c }">Modifier</button>
                <button class="adm-btn danger" type="button" @click="removeCategory(c)">Supprimer</button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- Courts -->
      <section v-show="tab === 'courts'" class="adm-card">
        <div class="adm-card-head">
          <h3>Courts</h3>
          <button class="adm-btn primary" type="button" @click="modal = { kind: 'court', editing: null }">
            + Nouveau court
          </button>
        </div>

        <div v-if="courts.length === 0" class="adm-empty">Aucun court.</div>

        <table v-else class="adm-table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Matchs rattachés</th>
              <th class="ta-r">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in courts" :key="c.id">
              <td><span class="adm-name">{{ c.name }}</span></td>
              <td class="tab">{{ c.matchCount }}</td>
              <td class="ta-r">
                <button class="adm-btn" type="button" @click="modal = { kind: 'court', editing: c }">Renommer</button>
                <button class="adm-btn danger" type="button" @click="removeCourt(c)">Supprimer</button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>

    <!-- Modales -->
    <CategoryModal
      v-if="modal?.kind === 'category'"
      :editing="modal.editing"
      @close="modal = null"
      @saved="error = ''"
    />
    <CourtModal
      v-if="modal?.kind === 'court'"
      :editing="modal.editing"
      @close="modal = null"
      @saved="error = ''"
    />
  </div>
</template>

<style scoped>
.admin-page { padding: 0; }

.page-header {
  padding: 32px 40px 24px;
  border-bottom: 1px solid var(--line-1);
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}
.breadcrumb { margin: 0 0 4px; font-size: 12px; color: var(--ink-3); letter-spacing: 0.06em; }
.page-title { margin: 0 0 4px; font-size: 26px; font-weight: 700; color: var(--ink-0); }
.page-sub { margin: 0; font-size: 13px; color: var(--ink-2); }

.page-content { padding: 24px 40px; display: flex; flex-direction: column; gap: 20px; }

/* Onglets */
.cfg-tabs { display: inline-flex; gap: 2px; background: var(--bg-3); border: 1px solid var(--line-2); border-radius: var(--r-md); padding: 3px; align-self: flex-start; }
.cfg-tab {
  padding: 8px 18px;
  border-radius: var(--r-sm);
  border: none;
  background: transparent;
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-2);
  cursor: pointer;
  font-family: inherit;
  transition: background 150ms, color 150ms;
}
.cfg-tab:hover { color: var(--ink-0); }
.cfg-tab.on { background: var(--accent); color: #000; }

.cfg-error { margin: 0; font-size: 13px; color: var(--danger); }

/* Cards */
.adm-card { background: var(--bg-2); border: 1px solid var(--line-1); border-radius: var(--r-lg); overflow: hidden; }
.adm-card-head { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--line-1); }
.adm-card-head h3 { margin: 0; font-size: 15px; font-weight: 700; color: var(--ink-0); }

/* Table */
.adm-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.adm-table th {
  padding: 10px 20px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.1em;
  color: var(--ink-3);
  text-transform: uppercase;
  border-bottom: 1px solid var(--line-1);
  background: var(--bg-3);
}
.adm-table td { padding: 14px 20px; border-bottom: 1px solid var(--line-1); color: var(--ink-1); vertical-align: middle; }
.adm-table tr:last-child td { border-bottom: none; }
.ta-r { text-align: right; }
.adm-name { font-size: 14px; font-weight: 600; color: var(--ink-0); }

/* Pills */
.adm-pill { display: inline-block; padding: 3px 10px; border-radius: var(--r-xs); font-size: 12px; font-weight: 600; background: var(--accent); color: #000; }
.adm-pill-ghost { background: var(--bg-4); color: var(--ink-2); border: 1px solid var(--line-2); }

.adm-empty { padding: 40px; text-align: center; color: var(--ink-3); font-size: 14px; }

/* Buttons */
.adm-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: var(--r-md);
  border: 1px solid var(--line-2);
  background: var(--bg-3);
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-1);
  cursor: pointer;
  transition: background 150ms;
  font-family: inherit;
}
.adm-btn:hover { background: var(--bg-4); }
.adm-btn + .adm-btn { margin-left: 8px; }
.adm-btn.primary { background: var(--accent); border-color: var(--accent); color: #000; }
.adm-btn.primary:hover { opacity: 0.9; }
.adm-btn.danger { color: var(--danger); }
.adm-btn.danger:hover { background: var(--danger); border-color: var(--danger); color: #fff; }

.tab { font-family: var(--font-mono); }
</style>
