<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useEventStore } from '@/stores/event'
import AutoFillModal from '@/components/modals/AutoFillModal.vue'
import type { Entry } from '@/types'

const eventStore = useEventStore()
const showAutoFill = ref(false)

watch(() => eventStore.activeEventId, (id) => {
  if (id) {
    eventStore.fetchPlayers(id)
    eventStore.fetchGroups(id)
  }
}, { immediate: true })

// Rattrapage : si activeEventId était null au montage (fetchEditions pas encore répondu)
watch(() => eventStore.events, () => {
  const id = eventStore.activeEventId
  if (id && eventStore.groups.length === 0 && eventStore.players.length === 0) {
    eventStore.fetchPlayers(id)
    eventStore.fetchGroups(id)
  }
}, { once: true })

// Joueurs non assignés
const unassigned = computed(() =>
  eventStore.players.filter((e) => !e.groupId)
)

async function assign(entryId: number, groupId: number) {
  if (!eventStore.activeEventId) return
  await eventStore.assignGroup(eventStore.activeEventId, entryId, groupId)
}

async function unassign(entryId: number) {
  if (!eventStore.activeEventId) return
  await eventStore.assignGroup(eventStore.activeEventId, entryId, null)
}

function entryDisplayName(entry: Entry): string {
  return entry.player?.fullName ?? `Équipe ${entry.id}`
}

const dropError = ref('')

// Drag state
let draggingEntryId: number | null = null

function onDragStart(entryId: number) {
  draggingEntryId = entryId
}

async function onDropToGroup(groupId: number) {
  if (draggingEntryId === null) return
  const id = draggingEntryId
  draggingEntryId = null
  try {
    await assign(id, groupId)
    dropError.value = ''
  } catch {
    dropError.value = 'Erreur lors de l\'assignation.'
  }
}

async function onDropToUnassigned() {
  if (draggingEntryId === null) return
  const id = draggingEntryId
  draggingEntryId = null
  try {
    await unassign(id)
    dropError.value = ''
  } catch {
    dropError.value = 'Erreur lors du retrait.'
  }
}
</script>

<template>
  <div class="admin-page">
    <header class="page-header">
      <div>
        <p class="breadcrumb">Tournoi · {{ eventStore.events.find(e => e.id === eventStore.activeEventId)?.name }}</p>
        <h1 class="page-title">Poules</h1>
        <p class="page-sub">Glissez-déposez les joueurs dans leur groupe</p>
      </div>
      <div class="header-actions">
        <button class="adm-btn" type="button" @click="showAutoFill = true">Auto-remplir</button>
      </div>
    </header>

    <AutoFillModal v-if="showAutoFill" @close="showAutoFill = false" @saved="showAutoFill = false" />

    <div class="page-content">
      <p v-if="dropError" class="adm-error">{{ dropError }}</p>
      <div class="groups-layout">
        <!-- Non assignés -->
        <div
          class="group-card group-card--unassigned"
          @dragover.prevent
          @drop="onDropToUnassigned"
        >
          <div class="gc-header">
            <span class="gc-title">Non assignés</span>
            <span class="gc-count">{{ unassigned.length }}</span>
          </div>

          <div v-if="unassigned.length === 0" class="gc-empty">
            <span>✓</span>
            <p>Tous les joueurs sont placés</p>
          </div>

          <div v-else class="gc-list">
            <div
              v-for="entry in unassigned"
              :key="entry.id"
              class="player-pill"
              draggable="true"
              @dragstart="onDragStart(entry.id)"
            >
              <span class="grip">⋮⋮</span>
              <span class="pill-name">{{ entryDisplayName(entry) }}</span>
            </div>
          </div>
        </div>

        <!-- Groupes -->
        <div class="groups-grid">
          <div
            v-for="group in eventStore.groups"
            :key="group.id"
            class="group-card"
            @dragover.prevent
            @drop="onDropToGroup(group.id)"
          >
            <div class="gc-header">
              <span class="gc-letter">{{ group.name }}</span>
              <span class="gc-title">Poule {{ group.name }}</span>
              <span class="gc-count">{{ group.standings.length }}</span>
            </div>

            <div class="gc-list">
              <div
                v-for="row in group.standings"
                :key="row.entryId"
                class="player-pill"
                draggable="true"
                @dragstart="onDragStart(row.entryId)"
              >
                <span class="grip">⋮⋮</span>
                <span class="pill-name">{{ row.name }}</span>
                <span v-if="row.qualified" class="q-badge">Q</span>
                <button class="pill-remove" @click="unassign(row.entryId)" @mousedown.stop>✕</button>
              </div>
            </div>

            <div v-if="group.standings.length === 0" class="gc-empty gc-empty--small">
              Glissez un joueur ici
            </div>
          </div>
        </div>
      </div>
    </div>
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
  gap: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.adm-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
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

.adm-btn.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #000;
}

.adm-btn.primary:hover { opacity: 0.9; }

.breadcrumb { margin: 0 0 4px; font-size: 12px; color: var(--ink-3); letter-spacing: 0.06em; }
.page-title { margin: 0 0 4px; font-size: 26px; font-weight: 700; color: var(--ink-0); }
.page-sub { margin: 0; font-size: 13px; color: var(--ink-2); }

.page-content { padding: 24px 40px; }

.groups-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
  align-items: start;
}

.groups-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

/* ── Group card ──────────────────────────────────────────────────────── */
.group-card {
  background: var(--bg-2);
  border: 1px solid var(--line-1);
  border-radius: var(--r-lg);
  overflow: hidden;
  transition: border-color 150ms;
}

.group-card[dragover],
.group-card:has(*[dragover]) {
  border-color: var(--accent);
}

.group-card--unassigned {
  min-height: 200px;
}

.gc-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--line-1);
}

.gc-letter {
  font-size: 24px;
  font-weight: 800;
  color: var(--accent);
  background: var(--accent-soft);
  width: 36px;
  height: 36px;
  border-radius: var(--r-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.gc-title {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-0);
}

.gc-count {
  font-size: 12px;
  font-weight: 700;
  color: var(--ink-3);
  background: var(--bg-4);
  padding: 2px 8px;
  border-radius: 99px;
}

.gc-list {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 60px;
}

.gc-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 20px;
  color: var(--ink-3);
  font-size: 13px;
  text-align: center;
}

.gc-empty span { font-size: 28px; color: var(--success); }
.gc-empty p { margin: 0; }

.gc-empty--small {
  padding: 16px 20px;
  font-size: 12px;
  font-style: italic;
}

/* ── Player pill ─────────────────────────────────────────────────────── */
.player-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: var(--r-sm);
  padding: 8px 10px;
  cursor: grab;
  transition: background 150ms;
}

.player-pill:hover { background: var(--bg-4); }
.player-pill:active { cursor: grabbing; }

.grip {
  font-size: 12px;
  color: var(--ink-4);
  letter-spacing: -2px;
  flex-shrink: 0;
}

.pill-name {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--ink-0);
}

.q-badge {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  background: var(--accent);
  color: #000;
  padding: 2px 6px;
  border-radius: var(--r-xs);
}

.pill-remove {
  background: none;
  border: none;
  color: var(--ink-4);
  font-size: 14px;
  padding: 0 2px;
  line-height: 1;
  transition: color 150ms;
}

.pill-remove:hover { color: var(--danger); }
</style>
