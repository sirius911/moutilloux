<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useEventStore } from '@/stores/event'
import AutoFillModal from '@/components/modals/AutoFillModal.vue'
import ConfirmModal from '@/components/ui/ConfirmModal.vue'
import ModalShell from '@/components/ui/ModalShell.vue'
import type { Entry } from '@/types'

const eventStore = useEventStore()
const route = useRoute()
const router = useRouter()
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
  return entry.displayName
}

function setActiveEvent(id: string) {
  const numId = parseInt(id, 10)
  if (!isNaN(numId)) router.push({ params: { ...route.params, eventId: numId } })
}

const dropError = ref('')
const createGroupBusy = ref(false)

const nextGroupLetter = computed(() => {
  const used = new Set(eventStore.groups.map((g) => g.name.toUpperCase()))
  for (let code = 'A'.charCodeAt(0); code <= 'Z'.charCodeAt(0); code++) {
    const letter = String.fromCharCode(code)
    if (!used.has(letter)) return letter
  }
  return 'A'
})

async function createGroup() {
  if (!eventStore.activeEventId || createGroupBusy.value) return
  createGroupBusy.value = true
  dropError.value = ''
  try {
    await eventStore.createGroup(eventStore.activeEventId, nextGroupLetter.value)
  } catch (e) {
    dropError.value = apiErrorMessage(e, 'Erreur lors de la création de la poule.')
  } finally {
    createGroupBusy.value = false
  }
}

// ── Ajustements (épreuve EN_COURS) ────────────────────────────────────────

const activeEvent = computed(() =>
  eventStore.events.find((e) => e.id === eventStore.activeEventId) ?? null
)

const inscribedPlayerIds = computed(
  () => new Set(eventStore.players.map((e) => e.player?.id).filter((id): id is number => id != null))
)

const availablePlayers = computed(() =>
  eventStore.allPlayers.filter((p) => !inscribedPlayerIds.value.has(p.id))
)

watch(() => eventStore.groupsLocked, (locked) => {
  if (locked) eventStore.fetchAllPlayers()
}, { immediate: true })

const adjustBusy = ref(false)
const adjustError = ref('')
const overCapacityNotice = ref('')

const confirmState = ref<{ show: boolean; entryId: number; name: string; action: 'forfait' | 'retrait' }>({
  show: false, entryId: 0, name: '', action: 'forfait',
})
const replaceState = ref<{ show: boolean; entryId: number; name: string }>({
  show: false, entryId: 0, name: '',
})
const addLateState = ref<{ show: boolean; groupId: number; groupName: string }>({
  show: false, groupId: 0, groupName: '',
})
const selectedReplacePlayerId = ref<number | null>(null)
const selectedAddPlayerId = ref<number | null>(null)

function openForfait(entryId: number, name: string) {
  confirmState.value = { show: true, entryId, name, action: 'forfait' }
}

function openRetrait(entryId: number, name: string) {
  confirmState.value = { show: true, entryId, name, action: 'retrait' }
}

async function executeWithdraw() {
  confirmState.value.show = false
  adjustBusy.value = true
  adjustError.value = ''
  try {
    await eventStore.withdrawEntry(confirmState.value.entryId, confirmState.value.action === 'retrait')
  } catch (e) {
    adjustError.value = apiErrorMessage(e, 'Erreur lors du forfait.')
  } finally {
    adjustBusy.value = false
  }
}

function openReplace(entryId: number, name: string) {
  selectedReplacePlayerId.value = null
  adjustError.value = ''
  replaceState.value = { show: true, entryId, name }
}

async function executeReplace() {
  if (!selectedReplacePlayerId.value) return
  adjustBusy.value = true
  adjustError.value = ''
  try {
    await eventStore.replacePlayer(replaceState.value.entryId, { player: selectedReplacePlayerId.value })
    replaceState.value.show = false
  } catch (e) {
    adjustError.value = apiErrorMessage(e, 'Erreur lors du remplacement.')
  } finally {
    adjustBusy.value = false
  }
}

function openAddLate(groupId: number, groupName: string) {
  selectedAddPlayerId.value = null
  adjustError.value = ''
  addLateState.value = { show: true, groupId, groupName }
}

async function executeAddLate() {
  if (!selectedAddPlayerId.value || !eventStore.activeEventId) return
  adjustBusy.value = true
  adjustError.value = ''
  const groupName = addLateState.value.groupName
  try {
    const result = await eventStore.addLateEntry(eventStore.activeEventId, {
      group_id: addLateState.value.groupId,
      player: selectedAddPlayerId.value,
    })
    addLateState.value.show = false
    overCapacityNotice.value = result?.overCapacity
      ? `Poule ${groupName} au-delà de l'effectif prévu — vérifiez la composition.`
      : ''
  } catch (e) {
    adjustError.value = apiErrorMessage(e, "Erreur lors de l'ajout.")
  } finally {
    adjustBusy.value = false
  }
}

function apiErrorMessage(e: unknown, fallback: string): string {
  if (!(e instanceof Error)) return fallback
  const match = e.message.match(/— (.+)$/)
  if (match) {
    try { const p = JSON.parse(match[1]); if (p.error) return p.error } catch {}
  }
  return e.message
}

// Drag state
let draggingEntryId: number | null = null

function onDragStart(entryId: number) {
  if (eventStore.groupsLocked) return
  draggingEntryId = entryId
}

async function onDropToGroup(groupId: number) {
  if (draggingEntryId === null || eventStore.groupsLocked) return
  const id = draggingEntryId
  draggingEntryId = null
  try {
    await assign(id, groupId)
    dropError.value = ''
  } catch (e) {
    dropError.value = apiErrorMessage(e, 'Erreur lors de l\'assignation.')
  }
}

async function onDropToUnassigned() {
  if (draggingEntryId === null || eventStore.groupsLocked) return
  const id = draggingEntryId
  draggingEntryId = null
  try {
    await unassign(id)
    dropError.value = ''
  } catch (e) {
    dropError.value = apiErrorMessage(e, 'Erreur lors du retrait.')
  }
}
</script>

<template>
  <div class="admin-page">
    <header class="page-header">
      <div>
        <select
          class="event-select"
          :value="eventStore.activeEventId ?? ''"
          :disabled="eventStore.events.length === 0"
          @change="setActiveEvent(($event.target as HTMLSelectElement).value)"
        >
          <option v-if="eventStore.events.length === 0" value="" disabled>Aucune épreuve</option>
          <option v-for="ev in eventStore.events" :key="ev.id" :value="ev.id">{{ ev.name }}</option>
        </select>
        <h1 class="page-title">Poules</h1>
        <p class="page-sub">Glissez-déposez les joueurs dans leur groupe</p>
      </div>
      <div class="header-actions">
        <button
          class="adm-btn"
          type="button"
          :disabled="eventStore.groupsLocked || createGroupBusy"
          @click="createGroup"
        >+ Nouvelle poule</button>
        <button class="adm-btn" type="button" :disabled="eventStore.groupsLocked" @click="showAutoFill = true">Remplir automatiquement</button>
      </div>
    </header>

    <AutoFillModal v-if="showAutoFill" @close="showAutoFill = false" @saved="showAutoFill = false" />

    <div v-if="eventStore.events.length === 0" class="empty-state">
      <p>Aucune épreuve active.</p>
      <RouterLink to="/admin/tournoi">Créer une épreuve dans Tournoi →</RouterLink>
    </div>

    <div v-else class="page-content">
      <div v-if="eventStore.groupsLocked" class="lock-banner">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
        </svg>
        L'épreuve est débutée — composition verrouillée.
        <RouterLink :to="`/admin/events/${eventStore.activeEventId}/matches`" class="lock-link">Voir le Calendrier</RouterLink>
      </div>
      <p v-if="dropError" class="adm-error">{{ dropError }}</p>
      <p v-if="adjustError" class="adm-error">{{ adjustError }}</p>
      <p v-if="overCapacityNotice" class="adm-warning">
        {{ overCapacityNotice }}
        <button type="button" class="adm-warning-dismiss" @click="overCapacityNotice = ''">✕</button>
      </p>
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
              :draggable="!eventStore.groupsLocked"
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
                :class="{
                  'player-pill--locked': eventStore.groupsLocked,
                  'player-pill--withdrawn': row.withdrawn,
                }"
                :draggable="!eventStore.groupsLocked"
                @dragstart="onDragStart(row.entryId)"
              >
                <span v-if="!eventStore.groupsLocked" class="grip">⋮⋮</span>
                <span class="pill-name" :class="{ 'pill-name--crossed': row.withdrawn }">{{ row.name }}</span>
                <span v-if="row.qualified" class="q-badge">Q</span>
                <span v-if="row.withdrawn" class="w-badge">WO</span>
                <!-- Actions déverrouillées : retrait libre -->
                <button v-if="!eventStore.groupsLocked" class="pill-remove" @click="unassign(row.entryId)" @mousedown.stop>✕</button>
                <!-- Ajustements en cours de jeu (épreuve EN_COURS) -->
                <template v-if="eventStore.groupsLocked && !row.withdrawn">
                  <button class="pill-action" type="button" :disabled="adjustBusy" @click.stop="openForfait(row.entryId, row.name)">Forfait</button>
                  <button class="pill-action" type="button" :disabled="adjustBusy" @click.stop="openReplace(row.entryId, row.name)">Remplacer</button>
                  <button class="pill-action danger" type="button" :disabled="adjustBusy" @click.stop="openRetrait(row.entryId, row.name)">Retirer</button>
                </template>
              </div>
            </div>

            <div v-if="group.standings.length === 0" class="gc-empty gc-empty--small">
              Glissez un joueur ici
            </div>

            <!-- Ajouter tardif : visible dès que l'épreuve est EN_COURS (dépassement d'effectif autorisé, avec avertissement) -->
            <div
              v-if="eventStore.groupsLocked && activeEvent"
              class="gc-add-late"
            >
              <button class="gc-add-late-btn" type="button" :disabled="adjustBusy" @click="openAddLate(group.id, group.name)">
                + Ajouter un tardif
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Modales ajustements ─────────────────────────────────────────────── -->
    <ConfirmModal
      v-if="confirmState.show"
      :title="confirmState.action === 'forfait' ? `Déclarer le forfait de ${confirmState.name} ?` : `Retirer ${confirmState.name} de l'épreuve ?`"
      :body="confirmState.action === 'forfait' ? 'Tous ses matchs non joués seront marqués comme walkover (victoire adverse).' : 'Déclenche un forfait en cascade sur tous ses matchs non joués. Action irréversible.'"
      :confirm-label="confirmState.action === 'forfait' ? 'Déclarer le forfait' : 'Retirer'"
      @confirm="executeWithdraw"
      @close="confirmState.show = false"
    />

    <ModalShell
      v-if="replaceState.show"
      :title="`Remplacer ${replaceState.name}`"
      subtitle="Choisissez le nouveau participant. Les résultats existants sont conservés."
      size="sm"
      @close="replaceState.show = false"
    >
      <div class="adj-form">
        <select v-model="selectedReplacePlayerId" class="adj-select">
          <option :value="null" disabled>Choisir un joueur…</option>
          <option v-for="p in availablePlayers" :key="p.id" :value="p.id">{{ p.fullName }}</option>
        </select>
        <p v-if="adjustError" class="adj-error">{{ adjustError }}</p>
      </div>
      <template #footer>
        <button class="adm-btn" type="button" @click="replaceState.show = false">Annuler</button>
        <button
          class="adm-btn primary"
          type="button"
          :disabled="!selectedReplacePlayerId || adjustBusy"
          @click="executeReplace"
        >
          {{ adjustBusy ? 'Remplacement…' : 'Remplacer' }}
        </button>
      </template>
    </ModalShell>

    <ModalShell
      v-if="addLateState.show"
      :title="`Ajouter un tardif — Poule ${addLateState.groupName}`"
      subtitle="Choisissez le participant à ajouter. Ses matchs manquants seront générés."
      size="sm"
      @close="addLateState.show = false"
    >
      <div class="adj-form">
        <select v-model="selectedAddPlayerId" class="adj-select">
          <option :value="null" disabled>Choisir un joueur…</option>
          <option v-for="p in availablePlayers" :key="p.id" :value="p.id">{{ p.fullName }}</option>
        </select>
        <p v-if="adjustError" class="adj-error">{{ adjustError }}</p>
      </div>
      <template #footer>
        <button class="adm-btn" type="button" @click="addLateState.show = false">Annuler</button>
        <button
          class="adm-btn primary"
          type="button"
          :disabled="!selectedAddPlayerId || adjustBusy"
          @click="executeAddLate"
        >
          {{ adjustBusy ? 'Ajout…' : 'Ajouter' }}
        </button>
      </template>
    </ModalShell>
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

.event-select {
  display: block;
  margin-bottom: 4px;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: var(--r-sm);
  padding: 5px 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-1);
  font-family: inherit;
  cursor: pointer;
  outline: none;
  max-width: 280px;
}

.event-select:focus { border-color: var(--accent); }
.event-select:disabled { opacity: 0.5; cursor: not-allowed; }

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

.player-pill--locked { cursor: default; flex-wrap: wrap; }
.player-pill--locked:hover { background: var(--bg-3); }
.player-pill--locked:active { cursor: default; }

.player-pill--withdrawn { opacity: 0.6; border-style: dashed; }

.pill-name--crossed { text-decoration: line-through; color: var(--ink-3); }

.w-badge {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  background: color-mix(in srgb, var(--danger) 15%, transparent);
  color: var(--danger);
  padding: 2px 6px;
  border-radius: var(--r-xs);
}

.pill-action {
  background: none;
  border: 1px solid var(--line-2);
  border-radius: var(--r-xs);
  color: var(--ink-2);
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  cursor: pointer;
  transition: background 100ms, color 100ms, border-color 100ms;
  font-family: inherit;
  white-space: nowrap;
}

.pill-action:hover { background: var(--bg-4); color: var(--ink-0); }
.pill-action.danger:hover { border-color: var(--danger); color: var(--danger); }
.pill-action:disabled { opacity: 0.4; cursor: not-allowed; }

.gc-add-late {
  padding: 8px 12px;
  border-top: 1px dashed var(--line-2);
}

.gc-add-late-btn {
  width: 100%;
  background: none;
  border: none;
  color: var(--accent);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  padding: 6px;
  border-radius: var(--r-sm);
  font-family: inherit;
  transition: background 100ms;
  text-align: center;
}

.gc-add-late-btn:hover { background: var(--accent-soft); }
.gc-add-late-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.adj-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 4px 0 8px;
}

.adj-select {
  width: 100%;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  padding: 9px 12px;
  font-size: 14px;
  color: var(--ink-0);
  outline: none;
  font-family: inherit;
  cursor: pointer;
  box-sizing: border-box;
}

.adj-select:focus { border-color: var(--accent); }

.adj-error {
  margin: 0;
  font-size: 13px;
  color: var(--danger);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 80px 40px;
  color: var(--ink-3);
  font-size: 14px;
  text-align: center;
}

.empty-state a {
  color: var(--accent);
  font-weight: 600;
  text-decoration: none;
}

.empty-state a:hover { text-decoration: underline; }

.lock-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: var(--r-md);
  background: color-mix(in srgb, var(--gold) 12%, transparent);
  border: 1px solid var(--gold);
  color: var(--ink-1);
  font-size: 13px;
  margin-bottom: 4px;
}

.lock-link {
  margin-left: 4px;
  color: var(--accent);
  font-weight: 600;
  text-decoration: none;
}

.lock-link:hover { text-decoration: underline; }

.adm-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.adm-error {
  margin: 0 0 8px;
  padding: 12px 16px;
  border-radius: var(--r-md);
  background: color-mix(in srgb, var(--danger) 12%, transparent);
  border: 1px solid var(--danger);
  color: var(--danger);
  font-size: 13px;
}

.adm-warning {
  margin: 0 0 8px;
  padding: 12px 16px;
  border-radius: var(--r-md);
  background: color-mix(in srgb, var(--gold) 12%, transparent);
  border: 1px solid var(--gold);
  color: var(--ink-1);
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.adm-warning-dismiss {
  background: none;
  border: none;
  color: var(--ink-3);
  font-size: 13px;
  cursor: pointer;
  padding: 0 2px;
  line-height: 1;
  flex-shrink: 0;
}

.adm-warning-dismiss:hover { color: var(--ink-0); }
</style>
