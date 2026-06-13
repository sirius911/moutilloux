<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ModalShell from '@/components/ui/ModalShell.vue'
import { useEventStore } from '@/stores/event'
import type { Player } from '@/types'

const emit = defineEmits<{ close: []; saved: [] }>()

const eventStore = useEventStore()

const player1Id = ref<number | null>(null)
const player2Id = ref<number | null>(null)
const teamName = ref('')
const saving = ref(false)
const error = ref('')
const pickingSlot = ref<1 | 2 | null>(null)
const search = ref('')

onMounted(() => {
  if (eventStore.allPlayers.length === 0) eventStore.fetchAllPlayers()
})

function playerForId(id: number | null): Player | null {
  return eventStore.allPlayers.find((p) => p.id === id) ?? null
}

function filteredForSlot(slot: 1 | 2): Player[] {
  const otherId = slot === 1 ? player2Id.value : player1Id.value
  const q = search.value.toLowerCase()
  return eventStore.allPlayers.filter(
    (p) =>
      p.id !== otherId &&
      (!q || p.fullName.toLowerCase().includes(q)),
  )
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

async function save() {
  if (!eventStore.activeEventId || !player1Id.value || !player2Id.value) return
  saving.value = true
  error.value = ''
  try {
    await eventStore.createTeam(
      eventStore.activeEventId,
      player1Id.value,
      player2Id.value,
      teamName.value || undefined,
    )
    emit('saved')
    emit('close')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Erreur inconnue.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <ModalShell
    title="Créer une équipe"
    subtitle="Mode Double · sélectionnez deux joueurs du registre"
    size="md"
    @close="emit('close')"
  >
    <template #icon>
      <svg viewBox="0 0 24 24" width="20" height="20">
        <circle cx="8" cy="8" r="3.5" fill="none" stroke="currentColor" stroke-width="1.6"/>
        <circle cx="16" cy="9" r="3" fill="none" stroke="currentColor" stroke-width="1.6"/>
        <path d="M2 20c0-3 3-5 6-5s6 2 6 5M14 20c0-2 2-4 5-4s3 2 3 4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
      </svg>
    </template>

    <!-- Composition -->
    <div class="mdl-section">
      <h4>Composition</h4>
      <div class="team-build">
        <!-- Joueur 1 -->
        <div class="team-slot">
          <span class="team-slot-lbl">Joueur 1</span>
          <div :class="['team-picker', { dashed: !player1Id }]">
            <template v-if="playerForId(player1Id)">
              <div
                class="adm-avatar"
                :style="{ background: avatarColor(playerForId(player1Id)!.fullName) }"
              >
                {{ initials(playerForId(player1Id)!.fullName) }}
              </div>
              <div>
                <div class="adm-player-name">{{ playerForId(player1Id)!.fullName }}</div>
                <div class="adm-player-meta">Joueur</div>
              </div>
              <button class="adm-btn" type="button" @click="pickingSlot = 1; search = ''">Changer</button>
            </template>
            <template v-else>
              <div class="adm-avatar adm-avatar-empty">??</div>
              <div class="adm-player-meta">Sélectionnez un joueur</div>
              <button class="adm-btn primary" type="button" style="margin-left: auto" @click="pickingSlot = 1; search = ''">Choisir</button>
            </template>
          </div>
        </div>

        <div class="team-and">+</div>

        <!-- Joueur 2 -->
        <div class="team-slot">
          <span class="team-slot-lbl">Joueur 2</span>
          <div :class="['team-picker', { dashed: !player2Id }]">
            <template v-if="playerForId(player2Id)">
              <div
                class="adm-avatar"
                :style="{ background: avatarColor(playerForId(player2Id)!.fullName) }"
              >
                {{ initials(playerForId(player2Id)!.fullName) }}
              </div>
              <div>
                <div class="adm-player-name">{{ playerForId(player2Id)!.fullName }}</div>
                <div class="adm-player-meta">Joueur</div>
              </div>
              <button class="adm-btn" type="button" @click="pickingSlot = 2; search = ''">Changer</button>
            </template>
            <template v-else>
              <div class="adm-avatar adm-avatar-empty">??</div>
              <div class="adm-player-meta">Sélectionnez un joueur</div>
              <button class="adm-btn primary" type="button" style="margin-left: auto" @click="pickingSlot = 2; search = ''">Choisir</button>
            </template>
          </div>
        </div>
      </div>

      <!-- Picker dropdown -->
      <div v-if="pickingSlot" class="picker-drop">
        <input v-model="search" class="inp" placeholder="Rechercher…" autofocus />
        <div class="picker-list">
          <button
            v-for="p in filteredForSlot(pickingSlot)"
            :key="p.id"
            type="button"
            class="picker-item"
            @click="pickingSlot === 1 ? (player1Id = p.id) : (player2Id = p.id); pickingSlot = null"
          >
            <div class="adm-avatar adm-avatar-sm" :style="{ background: avatarColor(p.fullName) }">
              {{ initials(p.fullName) }}
            </div>
            <span>{{ p.fullName }}</span>
          </button>
          <p v-if="filteredForSlot(pickingSlot).length === 0" class="picker-empty">Aucun joueur trouvé</p>
        </div>
        <button class="adm-btn" type="button" @click="pickingSlot = null">Fermer</button>
      </div>
    </div>

    <!-- Identification -->
    <div class="mdl-section">
      <h4>Identification</h4>
      <div class="fld-grid">
        <label class="fld">
          <span class="fld-lbl">Nom d'équipe</span>
          <input v-model="teamName" class="inp" placeholder="ex. Les Foudres" />
          <span class="fld-hint">Optionnel — sinon généré depuis les deux joueurs</span>
        </label>
      </div>
    </div>

    <p v-if="error" class="mdl-error">{{ error }}</p>

    <template #footer>
      <button class="adm-btn" type="button" @click="emit('close')">Annuler</button>
      <button
        class="adm-btn primary"
        type="button"
        :disabled="!player1Id || !player2Id || saving"
        @click="save"
      >
        {{ saving ? 'Création…' : "Créer l'équipe" }}
      </button>
    </template>
  </ModalShell>
</template>

<style scoped>
.mdl-section h4 {
  margin: 0 0 14px;
  font-size: 13px;
  font-weight: 700;
  color: var(--ink-2);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.fld-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px 20px;
}

.mdl-error {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--danger);
}

.fld {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.fld-lbl {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-2);
  letter-spacing: 0.04em;
}

.fld-hint {
  font-size: 11px;
  color: var(--ink-3);
}

.inp {
  width: 100%;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  padding: 9px 12px;
  font-size: 14px;
  color: var(--ink-0);
  outline: none;
  transition: border-color 150ms;
  box-sizing: border-box;
  font-family: inherit;
}

.inp:focus { border-color: var(--accent); }

/* Team builder */
.team-build {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.team-and {
  text-align: center;
  font-size: 20px;
  font-weight: 700;
  color: var(--accent);
}

.team-slot-lbl {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--ink-3);
  text-transform: uppercase;
  display: block;
  margin-bottom: 6px;
}

.team-picker {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  padding: 12px 16px;
}

.team-picker.dashed {
  border-style: dashed;
  border-color: var(--line-3);
}

/* Avatars */
.adm-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #000;
  flex-shrink: 0;
}

.adm-avatar-sm {
  width: 28px;
  height: 28px;
  font-size: 10px;
}

.adm-avatar-empty {
  background: var(--bg-4);
  color: var(--ink-3);
}

.adm-player-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-0);
}

.adm-player-meta {
  font-size: 12px;
  color: var(--ink-3);
}

/* Picker */
.picker-drop {
  margin-top: 12px;
  background: var(--bg-2);
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.picker-list {
  max-height: 200px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.picker-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--r-sm);
  background: transparent;
  border: none;
  font: inherit;
  color: var(--ink-0);
  cursor: pointer;
  font-size: 14px;
  text-align: left;
}

.picker-item:hover { background: var(--bg-3); }

.picker-empty {
  text-align: center;
  color: var(--ink-3);
  font-size: 13px;
  padding: 8px;
}

/* Buttons */
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
.adm-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
