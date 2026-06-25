<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useEventStore } from '@/stores/event'
import AddPlayerModal from '@/components/modals/AddPlayerModal.vue'
import type { Player } from '@/types'

const eventStore = useEventStore()
const search = ref('')
const showAddPlayer = ref(false)
const editingPlayer = ref<Player | null>(null)

function openEdit(p: Player) {
  editingPlayer.value = p
}

function closeModal() {
  showAddPlayer.value = false
  editingPlayer.value = null
}

onMounted(() => {
  eventStore.fetchAllPlayers()
})

const filtered = computed(() => {
  if (!search.value.trim()) return eventStore.allPlayers
  const q = search.value.toLowerCase()
  return eventStore.allPlayers.filter((p) =>
    p.fullName.toLowerCase().includes(q)
  )
})

const AVATAR_COLORS = ['#FFE48A', '#A7E8E2', '#F2B0B0', '#C4B5FD', '#BBF7D0', '#FED7AA']

function avatarColor(name: string): string {
  let hash = 0
  for (const c of name) hash = (hash * 31 + c.charCodeAt(0)) % AVATAR_COLORS.length
  return AVATAR_COLORS[hash]
}

function initials(name: string): string {
  return name.split(' ').map(p => p[0]).join('').toUpperCase().slice(0, 2)
}

function genderLabel(g: string | undefined | null) {
  return g === 'M' ? 'Homme' : g === 'F' ? 'Femme' : g === 'O' ? 'Autre' : '—'
}
</script>

<template>
  <div class="admin-page">
    <header class="page-header">
      <div>
        <p class="breadcrumb">Tournoi</p>
        <h1 class="page-title">Joueurs</h1>
        <p class="page-sub">{{ eventStore.allPlayers.length }} joueurs dans le registre</p>
      </div>
      <button class="adm-btn primary" type="button" @click="showAddPlayer = true">
        <svg viewBox="0 0 24 24" width="16" height="16">
          <path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        Ajouter un joueur
      </button>
    </header>

    <AddPlayerModal
      v-if="showAddPlayer || editingPlayer"
      :editing="editingPlayer"
      @close="closeModal"
      @saved="closeModal"
    />

    <div class="page-content">
      <div class="card">
        <!-- Toolbar -->
        <div class="toolbar">
          <div class="search-wrap">
            <svg viewBox="0 0 24 24" width="14" height="14" class="search-icon">
              <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="1.8"/>
              <path d="M20 20l-3-3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
            <input
              v-model="search"
              type="text"
              placeholder="Rechercher un joueur…"
              class="search-input"
            />
          </div>
        </div>

        <!-- Table -->
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Joueur</th>
                <th>Genre</th>
                <th>Né(e) en</th>
                <th class="col-actions-h">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in filtered" :key="p.id">
                <td class="col-player">
                  <div class="avatar" :style="{ background: avatarColor(p.fullName) }">
                    {{ initials(p.fullName) }}
                  </div>
                  <span class="player-name">{{ p.fullName }}</span>
                </td>
                <td>
                  <span class="player-meta">{{ genderLabel(p.gender) }}</span>
                </td>
                <td>
                  <span class="player-meta">{{ p.birthYear ?? '—' }}</span>
                </td>
                <td class="col-actions">
                  <button class="row-btn" type="button" @click="openEdit(p)">Éditer</button>
                </td>
              </tr>
              <tr v-if="filtered.length === 0 && !search.trim()">
                <td colspan="4" class="empty-row">Aucun joueur dans le registre. Ajoutez votre premier joueur.</td>
              </tr>
              <tr v-else-if="filtered.length === 0">
                <td colspan="4" class="empty-row">Aucun joueur trouvé</td>
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

.card {
  background: var(--bg-2);
  border: 1px solid var(--line-1);
  border-radius: var(--r-lg);
  overflow: hidden;
}

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

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

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

.col-player {
  display: flex;
  align-items: center;
  gap: 12px;
}

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

.empty-row {
  text-align: center;
  padding: 48px !important;
  color: var(--ink-3);
}
</style>
