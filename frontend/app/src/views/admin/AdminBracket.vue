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

// Un tableau existe dès qu'au moins un slot porte un match (y compris P3).
const hasBracket = computed(() =>
  [...(bracket.value?.qf ?? []), ...(bracket.value?.sf ?? []),
   ...(bracket.value?.f ?? []), ...(bracket.value?.p3 ?? [])]
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

// ── Qualifiés disponibles ──────────────────────────────────────────────────

interface QualifiedItem {
  entry: Entry
  label: string  // "A1", "B2", etc.
}

const qualifiedItems = computed((): QualifiedItem[] => {
  return eventStore.groups.flatMap((g) =>
    g.standings
      .filter((row) => row.qualified)
      .map((row) => {
        const entry = eventStore.players.find((e) => e.id === row.entryId)
        if (!entry) return null
        return { entry, label: `${g.name}${row.rank}` }
      })
      .filter((item): item is QualifiedItem => item !== null)
  )
})

// Entrées déjà placées + slot où elles sont placées
const placedEntrySlots = computed((): Map<number, string> => {
  const map = new Map<number, string>()
  const b = bracket.value
  if (!b) return map
  for (const slot of [...(b.qf ?? []), ...(b.sf ?? []), ...(b.f ?? []), ...(b.p3 ?? [])]) {
    if (slot.match?.sideA?.id) map.set(slot.match.sideA.id, slot.slot)
    if (slot.match?.sideB?.id) map.set(slot.match.sideB.id, slot.slot)
  }
  return map
})

const placedEntryIds = computed((): Set<number> => new Set(placedEntrySlots.value.keys()))

function slotLabel(slot: BracketSlot, side: 'A' | 'B'): string {
  const m = slot.match
  if (!m) return 'Vide'
  if (side === 'A') return m.sideA?.player?.fullName ?? m.sideALabel ?? 'À désigner'
  return m.sideB?.player?.fullName ?? m.sideBLabel ?? 'À désigner'
}

// ── Reseeding — édition locale des étiquettes ─────────────────────────────

const editingSlot = ref<{ matchId: number; sideALabel: string; sideBLabel: string } | null>(null)

function startEdit(slot: BracketSlot) {
  if (!slot.match || slot.match.status !== 'SCHEDULED') return
  editingSlot.value = {
    matchId: slot.match.id,
    sideALabel: slot.match.sideALabel ?? '',
    sideBLabel: slot.match.sideBLabel ?? '',
  }
}

async function saveEdit() {
  if (!editingSlot.value || !eventStore.activeEventId) return
  try {
    await eventStore.updateBracketLabels(
      eventStore.activeEventId,
      editingSlot.value.matchId,
      editingSlot.value.sideALabel,
      editingSlot.value.sideBLabel,
    )
    editingSlot.value = null
    error.value = ''
  } catch (e) {
    error.value = extractError(e)
  }
}

function cancelEdit() {
  editingSlot.value = null
}

// ── Drag & drop ───────────────────────────────────────────────────────────

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
            <div v-if="bracket.qf?.length" class="stage-col">
              <h3 class="stage-title">Quarts</h3>
              <div
                v-for="slot in bracket.qf"
                :key="slot.slot"
                class="bracket-slot"
              >
                <div class="slot-header">
                  <span class="slot-label">{{ slot.slot }}</span>
                  <button
                    v-if="slot.match?.status === 'SCHEDULED' && editingSlot?.matchId !== slot.match?.id"
                    class="slot-edit-btn"
                    type="button"
                    :title="'Modifier étiquettes'"
                    @click="startEdit(slot)"
                  >&#9998;</button>
                </div>

                <!-- Mode édition -->
                <template v-if="editingSlot?.matchId === slot.match?.id">
                  <div class="slot-edit-form">
                    <label class="slot-edit-label">
                      <span class="slot-edit-side">A</span>
                      <input v-model="editingSlot.sideALabel" class="slot-edit-input" type="text" placeholder="ex. A1" />
                    </label>
                    <label class="slot-edit-label">
                      <span class="slot-edit-side">B</span>
                      <input v-model="editingSlot.sideBLabel" class="slot-edit-input" type="text" placeholder="ex. B2" />
                    </label>
                    <div class="slot-edit-actions">
                      <button class="adm-btn primary slot-edit-save" type="button" @click="saveEdit">Valider</button>
                      <button class="adm-btn slot-edit-cancel" type="button" @click="cancelEdit">Annuler</button>
                    </div>
                  </div>
                </template>

                <!-- Affichage normal -->
                <template v-else>
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
                </template>
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
                <div class="slot-header">
                  <span class="slot-label">{{ slot.slot }}</span>
                  <button
                    v-if="slot.match?.status === 'SCHEDULED' && editingSlot?.matchId !== slot.match?.id"
                    class="slot-edit-btn"
                    type="button"
                    :title="'Modifier étiquettes'"
                    @click="startEdit(slot)"
                  >&#9998;</button>
                </div>

                <!-- Mode édition -->
                <template v-if="editingSlot?.matchId === slot.match?.id">
                  <div class="slot-edit-form">
                    <label class="slot-edit-label">
                      <span class="slot-edit-side">A</span>
                      <input v-model="editingSlot.sideALabel" class="slot-edit-input" type="text" placeholder="ex. A1" />
                    </label>
                    <label class="slot-edit-label">
                      <span class="slot-edit-side">B</span>
                      <input v-model="editingSlot.sideBLabel" class="slot-edit-input" type="text" placeholder="ex. B2" />
                    </label>
                    <div class="slot-edit-actions">
                      <button class="adm-btn primary slot-edit-save" type="button" @click="saveEdit">Valider</button>
                      <button class="adm-btn slot-edit-cancel" type="button" @click="cancelEdit">Annuler</button>
                    </div>
                  </div>
                </template>

                <!-- Affichage normal -->
                <template v-else>
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
                </template>
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
                <div class="slot-header">
                  <span class="slot-label">{{ slot.slot }}</span>
                  <button
                    v-if="slot.match?.status === 'SCHEDULED' && editingSlot?.matchId !== slot.match?.id"
                    class="slot-edit-btn"
                    type="button"
                    :title="'Modifier étiquettes'"
                    @click="startEdit(slot)"
                  >&#9998;</button>
                </div>

                <!-- Mode édition -->
                <template v-if="editingSlot?.matchId === slot.match?.id">
                  <div class="slot-edit-form">
                    <label class="slot-edit-label">
                      <span class="slot-edit-side">A</span>
                      <input v-model="editingSlot.sideALabel" class="slot-edit-input" type="text" placeholder="ex. A1" />
                    </label>
                    <label class="slot-edit-label">
                      <span class="slot-edit-side">B</span>
                      <input v-model="editingSlot.sideBLabel" class="slot-edit-input" type="text" placeholder="ex. B2" />
                    </label>
                    <div class="slot-edit-actions">
                      <button class="adm-btn primary slot-edit-save" type="button" @click="saveEdit">Valider</button>
                      <button class="adm-btn slot-edit-cancel" type="button" @click="cancelEdit">Annuler</button>
                    </div>
                  </div>
                </template>

                <!-- Affichage normal -->
                <template v-else>
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
                </template>
              </div>
            </div>

            <!-- Petite finale (P3) — uniquement si un match P3 existe en base -->
            <div v-if="bracket.p3?.some(s => s.match)" class="stage-col">
              <h3 class="stage-title">Petite finale</h3>
              <div
                v-for="slot in bracket.p3"
                :key="slot.slot"
                class="bracket-slot"
              >
                <div class="slot-header">
                  <span class="slot-label">{{ slot.slot }}</span>
                  <button
                    v-if="slot.match?.status === 'SCHEDULED' && editingSlot?.matchId !== slot.match?.id"
                    class="slot-edit-btn"
                    type="button"
                    :title="'Modifier étiquettes'"
                    @click="startEdit(slot)"
                  >&#9998;</button>
                </div>

                <!-- Mode édition -->
                <template v-if="editingSlot?.matchId === slot.match?.id">
                  <div class="slot-edit-form">
                    <label class="slot-edit-label">
                      <span class="slot-edit-side">A</span>
                      <input v-model="editingSlot.sideALabel" class="slot-edit-input" type="text" placeholder="ex. LSF1" />
                    </label>
                    <label class="slot-edit-label">
                      <span class="slot-edit-side">B</span>
                      <input v-model="editingSlot.sideBLabel" class="slot-edit-input" type="text" placeholder="ex. LSF2" />
                    </label>
                    <div class="slot-edit-actions">
                      <button class="adm-btn primary slot-edit-save" type="button" @click="saveEdit">Valider</button>
                      <button class="adm-btn slot-edit-cancel" type="button" @click="cancelEdit">Annuler</button>
                    </div>
                  </div>
                </template>

                <!-- Affichage normal -->
                <template v-else>
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
                </template>
              </div>
            </div>
          </template>
        </div>

        <!-- Qualifiés disponibles -->
        <div class="qualified-panel">
          <div class="qp-header">
            <span class="qp-title">Qualifiés disponibles</span>
            <span class="qp-count">{{ qualifiedItems.length }}</span>
          </div>
          <div class="qp-list">
            <div
              v-for="item in qualifiedItems"
              :key="item.entry.id"
              class="qualified-pill"
              :class="{ 'qualified-pill--placed': placedEntryIds.has(item.entry.id) }"
              :draggable="!placedEntryIds.has(item.entry.id)"
              @dragstart="!placedEntryIds.has(item.entry.id) && onDragStart(item.entry.id)"
            >
              <span class="qp-seed">{{ item.label }}</span>
              <span class="qp-name">{{ item.entry.player?.fullName ?? `Équipe ${item.entry.id}` }}</span>
              <span v-if="placedEntryIds.has(item.entry.id)" class="qp-placed">Placé en {{ placedEntrySlots.get(item.entry.id) }}</span>
              <span v-else class="grip">&#8942;&#8942;</span>
            </div>
            <div v-if="qualifiedItems.length === 0" class="qp-empty">
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
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
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

.slot-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: var(--bg-3);
  border-bottom: 1px solid var(--line-1);
}

.slot-label {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.1em;
  color: var(--ink-4);
  text-transform: uppercase;
}

.slot-edit-btn {
  background: none;
  border: none;
  color: var(--ink-4);
  font-size: 13px;
  padding: 0 2px;
  cursor: pointer;
  line-height: 1;
  transition: color 150ms;
}

.slot-edit-btn:hover { color: var(--accent); }

/* ── Édition inline ──────────────────────────────────────────────────── */
.slot-edit-form {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.slot-edit-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.slot-edit-side {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  color: var(--ink-3);
  width: 14px;
  flex-shrink: 0;
}

.slot-edit-input {
  flex: 1;
  padding: 5px 8px;
  font-size: 13px;
  border: 1px solid var(--line-2);
  border-radius: var(--r-sm);
  background: var(--bg-1);
  color: var(--ink-0);
  font-family: inherit;
}

.slot-edit-input:focus {
  outline: none;
  border-color: var(--accent);
}

.slot-edit-actions {
  display: flex;
  gap: 6px;
}

.slot-edit-save,
.slot-edit-cancel {
  padding: 5px 12px;
  font-size: 12px;
}

/* ── Slot sides ──────────────────────────────────────────────────────── */
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

.qualified-pill--placed {
  opacity: 0.45;
  cursor: default;
}

.qp-placed {
  font-size: 11px;
  color: var(--ink-3);
  font-style: italic;
}

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
