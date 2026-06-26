<script setup lang="ts">
import { computed, watch, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useEventStore } from '@/stores/event'
import type { BracketSlot, Entry } from '@/types'

const eventStore = useEventStore()

watch(() => eventStore.activeEventId, (id) => {
  if (id) {
    eventStore.fetchBracket(id)
    eventStore.fetchGroups(id)
    eventStore.fetchPlayers(id)
  }
}, { immediate: true })

const bracket = computed(() => eventStore.bracket)
const error = ref('')

// Un tableau existe dès qu'au moins un slot porte un match.
const hasBracket = computed(() =>
  [...(bracket.value?.qf ?? []), ...(bracket.value?.sf ?? []), ...(bracket.value?.f ?? [])]
    .some((s) => s.match),
)

function extractError(e: unknown): string {
  const raw = e instanceof Error ? e.message : String(e)
  const sep = raw.indexOf('— ')
  const tail = sep >= 0 ? raw.slice(sep + 2) : raw
  try {
    const parsed = JSON.parse(tail)
    if (parsed && typeof parsed.error === 'string') return parsed.error
  } catch { /* message non-JSON : on retombe sur le générique */ }
  return 'Action impossible.'
}

async function createOrRecreate() {
  if (!eventStore.activeEventId) return
  // Étape de départ dérivée du nombre de poules : 4 poules → quarts, sinon demies.
  const startStage = eventStore.groups.length >= 4 ? 'QF' : 'SF'
  if (hasBracket.value && !confirm('Recréer le tableau effacera les matchs planifiés actuels. Continuer ?')) return
  try {
    await eventStore.createBracket(eventStore.activeEventId, startStage, hasBracket.value)
    error.value = ''
  } catch (e) {
    error.value = extractError(e)
  }
}

// Qualifiés disponibles (rang 1 et 2 de chaque poule)
const qualifiedEntries = computed((): Entry[] => {
  return eventStore.groups.flatMap((g) =>
    g.standings
      .filter((row) => row.qualified)
      .map((row) => {
        const entry = eventStore.players.find((e) => e.id === row.entryId)
        return entry ?? null
      })
      .filter((ent): ent is Entry => ent !== null)
  )
})

function slotLabel(slot: BracketSlot, side: 'A' | 'B'): string {
  const m = slot.match
  if (!m) return 'Vide'
  if (side === 'A') return m.sideA?.player?.fullName ?? m.sideALabel ?? 'À désigner'
  return m.sideB?.player?.fullName ?? m.sideBLabel ?? 'À désigner'
}

// Drag & drop
let draggingEntryId: number | null = null

function onDragStart(entryId: number) {
  draggingEntryId = entryId
}

async function onDropToSlot(slot: BracketSlot, side: 'A' | 'B') {
  if (draggingEntryId === null || !slot.match || !eventStore.activeEventId) return
  try {
    await eventStore.assignBracket(eventStore.activeEventId, slot.match.id, side, draggingEntryId)
    error.value = ''
  } catch (e) {
    error.value = extractError(e)
  } finally {
    draggingEntryId = null
  }
}

async function clearSlot(slot: BracketSlot, side: 'A' | 'B') {
  if (!slot.match || !eventStore.activeEventId) return
  try {
    await eventStore.clearBracket(eventStore.activeEventId, slot.match.id, side)
    error.value = ''
  } catch (e) {
    error.value = extractError(e)
  }
}
</script>

<template>
  <div class="admin-page">
    <header class="page-header">
      <div>
        <p class="breadcrumb">Tournoi · {{ eventStore.events.find(e => e.id === eventStore.activeEventId)?.name ?? '—' }}</p>
        <h1 class="page-title">Tableau final</h1>
        <p class="page-sub">Glissez les qualifiés dans les slots du bracket</p>
      </div>
      <div class="header-actions">
        <button v-if="hasBracket" class="adm-btn" type="button" @click="createOrRecreate">Recréer le tableau</button>
      </div>
    </header>

    <div v-if="eventStore.events.length === 0" class="empty-state">
      <p>Aucune épreuve active.</p>
      <RouterLink to="/admin/tournoi">Créer une épreuve dans Tournoi →</RouterLink>
    </div>

    <div v-else class="page-content">
      <p v-if="error" class="bracket-error" role="alert">{{ error }}</p>

      <div v-if="!hasBracket" class="bracket-empty bracket-empty--cta">
        <p>Aucun tableau final créé pour cette épreuve.</p>
        <button class="adm-btn primary" type="button" @click="createOrRecreate">Créer le tableau</button>
      </div>

      <div v-else class="bracket-layout">
        <!-- Aperçu du bracket -->
        <div class="bracket-preview">
          <template v-if="bracket">
            <!-- Quarts -->
            <div class="stage-col">
              <h3 class="stage-title">Quarts</h3>
              <div
                v-for="slot in bracket.qf"
                :key="slot.slot"
                class="bracket-slot"
              >
                <div class="slot-label">{{ slot.slot }}</div>
                <div
                  class="slot-side"
                  :class="{ empty: !slot.match?.sideA, winner: slot.match?.winnerSide === 'A' }"
                  @dragover.prevent
                  @drop="onDropToSlot(slot, 'A')"
                >
                  <span>{{ slotLabel(slot, 'A') }}</span>
                  <button v-if="slot.match?.sideA" class="slot-clear" @click="clearSlot(slot, 'A')">✕</button>
                </div>
                <div
                  class="slot-side"
                  :class="{ empty: !slot.match?.sideB, winner: slot.match?.winnerSide === 'B' }"
                  @dragover.prevent
                  @drop="onDropToSlot(slot, 'B')"
                >
                  <span>{{ slotLabel(slot, 'B') }}</span>
                  <button v-if="slot.match?.sideB" class="slot-clear" @click="clearSlot(slot, 'B')">✕</button>
                </div>
              </div>
            </div>

            <!-- Demi-finales -->
            <div class="stage-col">
              <h3 class="stage-title">Demi-finales</h3>
              <div
                v-for="slot in bracket.sf"
                :key="slot.slot"
                class="bracket-slot"
              >
                <div class="slot-label">{{ slot.slot }}</div>
                <div
                  class="slot-side"
                  :class="{ empty: !slot.match?.sideA, winner: slot.match?.winnerSide === 'A' }"
                  @dragover.prevent
                  @drop="onDropToSlot(slot, 'A')"
                >
                  <span>{{ slotLabel(slot, 'A') }}</span>
                </div>
                <div
                  class="slot-side"
                  :class="{ empty: !slot.match?.sideB, winner: slot.match?.winnerSide === 'B' }"
                  @dragover.prevent
                  @drop="onDropToSlot(slot, 'B')"
                >
                  <span>{{ slotLabel(slot, 'B') }}</span>
                </div>
              </div>
            </div>

            <!-- Finale -->
            <div class="stage-col">
              <h3 class="stage-title">Finale</h3>
              <div
                v-for="slot in bracket.f"
                :key="slot.slot"
                class="bracket-slot bracket-slot--final"
              >
                <div class="slot-label">{{ slot.slot }}</div>
                <div
                  class="slot-side"
                  :class="{ empty: !slot.match?.sideA, winner: slot.match?.winnerSide === 'A' }"
                  @dragover.prevent
                  @drop="onDropToSlot(slot, 'A')"
                >
                  <span>{{ slotLabel(slot, 'A') }}</span>
                </div>
                <div
                  class="slot-side"
                  :class="{ empty: !slot.match?.sideB, winner: slot.match?.winnerSide === 'B' }"
                  @dragover.prevent
                  @drop="onDropToSlot(slot, 'B')"
                >
                  <span>{{ slotLabel(slot, 'B') }}</span>
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- Qualifiés disponibles -->
        <div class="qualified-panel">
          <div class="qp-header">
            <span class="qp-title">Qualifiés disponibles</span>
            <span class="qp-count">{{ qualifiedEntries.length }}</span>
          </div>
          <div class="qp-list">
            <div
              v-for="entry in qualifiedEntries"
              :key="entry.id"
              class="qualified-pill"
              draggable="true"
              @dragstart="onDragStart(entry.id)"
            >
              <span class="qp-seed">{{ entry.seedHint ?? '—' }}</span>
              <span class="qp-name">{{ entry.player?.fullName ?? `Équipe ${entry.id}` }}</span>
              <span class="grip">⋮⋮</span>
            </div>
            <div v-if="qualifiedEntries.length === 0" class="qp-empty">
              Aucun qualifié encore
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

.bracket-error {
  margin: 0 0 16px;
  padding: 10px 14px;
  border: 1px solid var(--danger);
  border-radius: var(--r-md);
  color: var(--danger);
  font-size: 13px;
  font-weight: 600;
}

.bracket-empty--cta {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.breadcrumb { margin: 0 0 4px; font-size: 12px; color: var(--ink-3); letter-spacing: 0.06em; }
.page-title { margin: 0 0 4px; font-size: 26px; font-weight: 700; color: var(--ink-0); }
.page-sub { margin: 0; font-size: 13px; color: var(--ink-2); }

.page-content { padding: 24px 40px; }

/* ── Layout ──────────────────────────────────────────────────────────── */
.bracket-layout {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 20px;
  align-items: start;
}

.bracket-preview {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 20px;
}

.bracket-empty {
  text-align: center;
  color: var(--ink-3);
  padding: 60px;
  grid-column: span 3;
}

/* ── Stages ──────────────────────────────────────────────────────────── */
.stage-col {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stage-title {
  margin: 0 0 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
  color: var(--ink-3);
  text-transform: uppercase;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line-1);
}

/* ── Bracket slot ────────────────────────────────────────────────────── */
.bracket-slot {
  background: var(--bg-2);
  border: 1px solid var(--line-1);
  border-radius: var(--r-md);
  overflow: hidden;
}

.bracket-slot--final {
  border-color: var(--accent-soft);
}

.slot-label {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.1em;
  color: var(--ink-4);
  padding: 6px 12px;
  background: var(--bg-3);
  border-bottom: 1px solid var(--line-1);
  text-transform: uppercase;
}

.slot-side {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  font-size: 13px;
  color: var(--ink-1);
  min-height: 40px;
  border-bottom: 1px dashed var(--line-1);
  transition: background 150ms;
  cursor: default;
}

.slot-side:last-child { border-bottom: none; }

.slot-side:hover { background: var(--bg-3); }

.slot-side.empty {
  font-style: italic;
  color: var(--ink-4);
}

.slot-side.winner {
  font-weight: 700;
  color: var(--accent);
  background: var(--accent-soft);
}

.slot-clear {
  background: none;
  border: none;
  color: var(--ink-4);
  font-size: 12px;
  padding: 0;
  cursor: pointer;
  opacity: 0;
  transition: opacity 150ms, color 150ms;
}

.slot-side:hover .slot-clear { opacity: 1; }
.slot-clear:hover { color: var(--danger); }

/* ── Qualifiés ───────────────────────────────────────────────────────── */
.qualified-panel {
  background: var(--bg-2);
  border: 1px solid var(--line-1);
  border-radius: var(--r-lg);
  overflow: hidden;
}

.qp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--line-1);
}

.qp-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-0);
}

.qp-count {
  font-size: 12px;
  font-weight: 700;
  color: var(--ink-3);
  background: var(--bg-4);
  padding: 2px 8px;
  border-radius: 99px;
}

.qp-list {
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.qualified-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: var(--r-sm);
  padding: 8px 10px;
  cursor: grab;
}

.qualified-pill:active { cursor: grabbing; }

.qp-seed {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  background: var(--accent-soft);
  color: var(--accent);
  padding: 2px 8px;
  border-radius: var(--r-xs);
  min-width: 32px;
  text-align: center;
}

.qp-name {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--ink-0);
}

.grip {
  font-size: 12px;
  color: var(--ink-4);
  letter-spacing: -2px;
}

.qp-empty {
  text-align: center;
  color: var(--ink-4);
  font-size: 13px;
  padding: 24px;
  font-style: italic;
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
</style>
