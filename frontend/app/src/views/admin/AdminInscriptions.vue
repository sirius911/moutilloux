<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useEventStore } from '@/stores/event'
import CreateTeamModal from '@/components/modals/CreateTeamModal.vue'
import ConfirmModal from '@/components/ui/ConfirmModal.vue'

const eventStore = useEventStore()
const search = ref('')
const showCreateTeam = ref(false)
const busy = ref(false)
const error = ref('')
const confirmState = ref<{ show: boolean; entryId: number; name: string }>({ show: false, entryId: 0, name: '' })

const activeEvent = computed(() =>
  eventStore.events.find((e) => e.id === eventStore.activeEventId) ?? null,
)
const isDouble = computed(() => activeEvent.value?.categoryMode === 'D')

const inscribedPlayerIds = computed(
  () => new Set(eventStore.players.map((e) => e.player?.id).filter((id): id is number => id != null)),
)

const availablePlayers = computed(() => {
  const pool = eventStore.allPlayers.filter((p) => !inscribedPlayerIds.value.has(p.id))
  const q = search.value.trim().toLowerCase()
  return q ? pool.filter((p) => p.fullName.toLowerCase().includes(q)) : pool
})

async function reload() {
  if (!eventStore.activeEventId) return
  await Promise.all([
    eventStore.fetchPlayers(eventStore.activeEventId),
    eventStore.fetchAllPlayers(),
  ])
}

onMounted(reload)
watch(() => eventStore.activeEventId, reload)

async function inscrire(playerId: number) {
  if (!eventStore.activeEventId) return
  busy.value = true
  error.value = ''
  try {
    await eventStore.addRegistration(eventStore.activeEventId, playerId)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Erreur inconnue.'
  } finally {
    busy.value = false
  }
}

async function inscrireTout() {
  if (!eventStore.activeEventId) return
  const ids = availablePlayers.value.map((p) => p.id)
  if (ids.length === 0) return
  busy.value = true
  error.value = ''
  try {
    await eventStore.addRegistrationsBulk(eventStore.activeEventId, ids)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Erreur inconnue.'
  } finally {
    busy.value = false
  }
}

function setActiveEvent(id: string) {
  const numId = parseInt(id, 10)
  if (!isNaN(numId)) eventStore.activeEventId = numId
}

function retirer(entryId: number, name: string) {
  if (!eventStore.activeEventId) return
  confirmState.value = { show: true, entryId, name }
}

async function executeRetrait() {
  confirmState.value.show = false
  if (!eventStore.activeEventId) return
  busy.value = true
  error.value = ''
  try {
    await eventStore.removeRegistration(eventStore.activeEventId, confirmState.value.entryId)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Erreur inconnue.'
  } finally {
    busy.value = false
  }
}

const AVATAR_COLORS = ['#FFE48A', '#A7E8E2', '#F2B0B0', '#C4B5FD', '#BBF7D0', '#FED7AA']

function avatarColor(name: string): string {
  let hash = 0
  for (const c of name) hash = (hash * 31 + c.charCodeAt(0)) % AVATAR_COLORS.length
  return AVATAR_COLORS[hash]
}

function initials(name: string): string {
  return name.split(' ').map((p) => p[0]).join('').toUpperCase().slice(0, 2)
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
        <h1 class="page-title">Inscriptions</h1>
        <p class="page-sub">{{ eventStore.players.length }} inscrit{{ eventStore.players.length > 1 ? 's' : '' }}</p>
      </div>
      <button
        v-if="isDouble"
        class="adm-btn primary"
        type="button"
        :disabled="!eventStore.activeEventId"
        @click="showCreateTeam = true"
      >
        <svg viewBox="0 0 24 24" width="16" height="16">
          <circle cx="8" cy="8" r="3.5" fill="none" stroke="currentColor" stroke-width="1.6" />
          <circle cx="16" cy="9" r="3" fill="none" stroke="currentColor" stroke-width="1.6" />
          <path d="M2 20c0-3 3-5 6-5s6 2 6 5M14 20c0-2 2-4 5-4s3 2 3 4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
        </svg>
        Créer une équipe
      </button>
      <button
        v-else
        class="adm-btn primary"
        type="button"
        :disabled="busy || availablePlayers.length === 0"
        @click="inscrireTout"
      >
        Inscrire les {{ availablePlayers.length }} affichés
      </button>
    </header>

    <CreateTeamModal
      v-if="showCreateTeam"
      @close="showCreateTeam = false"
      @saved="showCreateTeam = false"
    />

    <ConfirmModal
      v-if="confirmState.show"
      :title="`Retirer ${confirmState.name} de l'épreuve ?`"
      body="L'historique du joueur est conservé."
      confirm-label="Retirer"
      @confirm="executeRetrait"
      @close="confirmState.show = false"
    />

    <div class="page-content">
      <p v-if="error" class="banner-error">{{ error }}</p>

      <!-- Inscrits -->
      <div class="card">
        <div class="card-head">
          <h3>Inscrits</h3>
          <em class="card-count">{{ eventStore.players.length }}</em>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Participant</th>
                <th>Poule</th>
                <th class="col-actions-h">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in eventStore.players" :key="e.id">
                <td class="col-player">
                  <div class="avatar" :style="{ background: avatarColor(e.displayName) }">
                    {{ initials(e.displayName) }}
                  </div>
                  <span class="player-name">{{ e.displayName }}</span>
                </td>
                <td>
                  <span class="player-meta">{{ e.groupName ?? '—' }}</span>
                </td>
                <td class="col-actions">
                  <button class="row-btn danger" type="button" :disabled="busy" @click="retirer(e.id, e.displayName)">
                    Retirer
                  </button>
                </td>
              </tr>
              <tr v-if="eventStore.players.length === 0">
                <td colspan="3" class="empty-row">Aucun inscrit pour cette épreuve</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Joueurs disponibles (Simple uniquement) -->
      <div v-if="!isDouble" class="card">
        <div class="card-head">
          <h3>Joueurs disponibles</h3>
          <em class="card-count">{{ availablePlayers.length }}</em>
        </div>
        <div class="toolbar">
          <div class="search-wrap">
            <svg viewBox="0 0 24 24" width="14" height="14" class="search-icon">
              <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="1.8" />
              <path d="M20 20l-3-3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
            </svg>
            <input v-model="search" type="text" placeholder="Rechercher un joueur…" class="search-input" />
          </div>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <tbody>
              <tr v-for="p in availablePlayers" :key="p.id">
                <td class="col-player">
                  <div class="avatar" :style="{ background: avatarColor(p.fullName) }">
                    {{ initials(p.fullName) }}
                  </div>
                  <span class="player-name">{{ p.fullName }}</span>
                </td>
                <td class="col-actions">
                  <button class="row-btn" type="button" :disabled="busy" @click="inscrire(p.id)">
                    Inscrire
                  </button>
                </td>
              </tr>
              <tr v-if="availablePlayers.length === 0">
                <td colspan="2" class="empty-row">Tous les joueurs du registre sont inscrits</td>
              </tr>
            </tbody>
          </table>
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

.page-content { padding: 24px 40px; display: flex; flex-direction: column; gap: 20px; }

.banner-error {
  margin: 0;
  padding: 12px 16px;
  border-radius: var(--r-md);
  background: color-mix(in srgb, var(--danger) 12%, transparent);
  border: 1px solid var(--danger);
  color: var(--danger);
  font-size: 13px;
}

.card {
  background: var(--bg-2);
  border: 1px solid var(--line-1);
  border-radius: var(--r-lg);
  overflow: hidden;
}

.card-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--line-1);
}

.card-head h3 { margin: 0; font-size: 15px; font-weight: 700; color: var(--ink-0); }
.card-count { font-style: normal; font-size: 12px; color: var(--ink-3); }

.toolbar {
  padding: 16px 20px;
  border-bottom: 1px solid var(--line-1);
}

.search-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: var(--r-sm);
  padding: 8px 12px;
  max-width: 320px;
}

.search-icon { color: var(--ink-3); flex-shrink: 0; }

.search-input {
  border: none;
  background: transparent;
  font-size: 14px;
  color: var(--ink-0);
  width: 100%;
  outline: none;
}

.search-input::placeholder { color: var(--ink-3); }

.table-wrap { overflow-x: auto; }

.data-table { width: 100%; border-collapse: collapse; font-size: 14px; }

.data-table th {
  padding: 10px 16px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.1em;
  color: var(--ink-3);
  text-transform: uppercase;
  border-bottom: 1px solid var(--line-1);
  background: var(--bg-3);
}

.data-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--line-1);
  color: var(--ink-1);
  vertical-align: middle;
}

.data-table tr:last-child td { border-bottom: none; }

.col-player { display: flex; align-items: center; gap: 12px; }

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #000;
  flex-shrink: 0;
}

.player-name { font-weight: 500; color: var(--ink-0); }
.player-meta { font-size: 13px; color: var(--ink-3); }

.col-actions-h { text-align: right; }
.col-actions { text-align: right; white-space: nowrap; }

.row-btn {
  padding: 6px 12px;
  border-radius: var(--r-sm);
  border: 1px solid var(--line-2);
  background: var(--bg-3);
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-1);
  cursor: pointer;
  transition: background 150ms, border-color 150ms;
  font-family: inherit;
}

.row-btn:hover { background: var(--bg-4); border-color: var(--accent); }
.row-btn.danger:hover { border-color: var(--danger); color: var(--danger); }
.row-btn:disabled { opacity: 0.5; cursor: not-allowed; }

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
  flex-shrink: 0;
}

.adm-btn.primary { background: var(--accent); border-color: var(--accent); color: #000; }
.adm-btn.primary:hover { opacity: 0.9; }
.adm-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.empty-row { text-align: center; padding: 48px !important; color: var(--ink-3); }
</style>
