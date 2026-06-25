<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import draggable from 'vuedraggable'
import { useEventStore } from '@/stores/event'
import type { CalendarReorderPayload } from '@/stores/event'
import { usePolling } from '@/composables/usePolling'
import EditMatchPanel from '@/components/modals/EditMatchPanel.vue'
import GenerateMatchesModal from '@/components/modals/GenerateMatchesModal.vue'
import type { Match, CalendarDay } from '@/types'

const eventStore = useEventStore()

const editingMatch = ref<Match | null>(null)
const showGenerateMatches = ref(false)
const bannerError = ref('')
const arranging = ref(false)

// ── Polling calendrier ─────────────────────────────────────────────────────

usePolling(() => eventStore.fetchCalendar(), 2000)

watch(
  () => eventStore.activeEventId,
  () => eventStore.fetchCalendar(),
)

// ── État local DnD (miroir du store, muté par vuedraggable) ───────────────

const dragging = ref(false)
// Pile : groupée par poule (une entrée par groupe)
const unscheduledByGroupDnd = ref<Record<string, Match[]>>({})
// Journées : matchs ordonnés par playDayId
const dayMatchesDnd = ref<Record<number, Match[]>>({})

function syncFromStore() {
  if (dragging.value) return
  const cal = eventStore.calendar
  if (!cal) {
    unscheduledByGroupDnd.value = {}
    dayMatchesDnd.value = {}
    return
  }
  const newGroups: Record<string, Match[]> = {}
  for (const m of cal.unscheduled.filter((m) => m.eventId === eventStore.activeEventId)) {
    const g = groupName(m) || '?'
    ;(newGroups[g] ??= []).push(m)
  }
  unscheduledByGroupDnd.value = newGroups

  const days: Record<number, Match[]> = {}
  for (const day of cal.playDays) {
    days[day.id] = day.matches.filter((m) => m.eventId === eventStore.activeEventId)
  }
  dayMatchesDnd.value = days
}

watch(() => eventStore.calendar, () => { if (!dragging.value) syncFromStore() }, { deep: true, immediate: true })

// ── Données de structure (journées depuis le store, matchs depuis DnD local) ─

const calendarDays = computed<CalendarDay[]>(() => {
  if (!eventStore.calendar) return []
  return eventStore.calendar.playDays.map((day) => ({
    ...day,
    matches: dayMatchesDnd.value[day.id] ?? [],
  }))
})

const unscheduledTotal = computed(() =>
  Object.values(unscheduledByGroupDnd.value).reduce((s, arr) => s + arr.length, 0),
)

const totalScheduledMatches = computed(() =>
  Object.values(dayMatchesDnd.value).reduce((s, arr) => s + arr.length, 0),
)

// ── Helpers ────────────────────────────────────────────────────────────────

function groupName(match: Match): string {
  const parts = match.stageLabel.split(' — Poule ')
  return parts[1] ?? ''
}

function playerLabel(match: Match, side: 'A' | 'B'): string {
  if (side === 'A') return match.sideA?.player?.fullName ?? match.sideALabel ?? 'TBD'
  return match.sideB?.player?.fullName ?? match.sideBLabel ?? 'TBD'
}

// Identifiant du seul match "Next" — lu depuis l'état DnD local
const nextMatchId = computed<number | null>(() => {
  const allMatches = Object.values(dayMatchesDnd.value).flat()
  const liveMatch = allMatches.find((m) => m.status === 'LIVE')
  const pivotIndex = liveMatch?.orderIndex ?? -Infinity
  const candidates = allMatches
    .filter((m) => m.status === 'SCHEDULED' && (m.orderIndex ?? -1) > pivotIndex)
    .sort((a, b) => (a.orderIndex ?? 0) - (b.orderIndex ?? 0))
  return candidates[0]?.id ?? null
})

type DisplayState = 'live' | 'next' | 'scheduled' | 'finished' | 'canceled'

function displayState(match: Match): DisplayState {
  if (match.status === 'LIVE') return 'live'
  if (match.status === 'FINISHED') return 'finished'
  if (match.status === 'CANCELED') return 'canceled'
  if (match.id === nextMatchId.value) return 'next'
  return 'scheduled'
}

function stateLabel(state: DisplayState): string {
  return { live: 'En cours', next: 'Next', scheduled: 'Planifié', finished: 'Terminé', canceled: 'Annulé' }[state]
}

function timeToMin(t: string): number {
  const normalized = t.replace('h', ':')
  const [h, m] = normalized.split(':').map(Number)
  return h * 60 + (m || 0)
}

function minToTime(min: number): string {
  return `${String(Math.floor(min / 60)).padStart(2, '0')}:${String(min % 60).padStart(2, '0')}`
}

function dayEndEstimate(day: CalendarDay, filteredMatches: Match[]): string | null {
  if (filteredMatches.length === 0) return null
  const last = filteredMatches[filteredMatches.length - 1]
  if (!last.scheduledTime) return null
  const dur = eventStore.activeEdition?.defaultMatchDurationMin ?? 30
  return minToTime(timeToMin(last.scheduledTime) + dur)
}

function capacityOver(day: CalendarDay, filteredMatches: Match[]): boolean {
  const end = dayEndEstimate(day, filteredMatches)
  if (!end) return false
  return timeToMin(end) > timeToMin(day.targetEndTime)
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })
}

// ── Actions ────────────────────────────────────────────────────────────────

async function onMatchesGenerated() {
  showGenerateMatches.value = false
  await eventStore.fetchCalendar()
}

async function preArrange() {
  if (!eventStore.activeEventId) return
  arranging.value = true
  bannerError.value = ''
  try {
    await eventStore.autoArrangeMatches(eventStore.activeEventId)
  } catch (e) {
    bannerError.value = e instanceof Error ? e.message : 'Erreur lors de la pré-pose.'
  } finally {
    arranging.value = false
  }
}

function onMatchSaved() {
  editingMatch.value = null
  eventStore.fetchCalendar()
}

// ── Drag-and-drop ──────────────────────────────────────────────────────────

// Guard contre le double @end lors des drags inter-listes (SortableJS peut
// émettre end sur source ET destination pour un même glissement).
let reorderPending = false

function onDragStart() {
  dragging.value = true
}

function checkMove(evt: { draggedContext: { element: Match } }): boolean {
  return evt.draggedContext.element.status !== 'LIVE'
}

function buildReorderPayload(): CalendarReorderPayload {
  const playDays = eventStore.calendar?.playDays ?? []
  return {
    playDays: playDays.map((day) => ({
      playDayId: day.id,
      items: [
        ...(dayMatchesDnd.value[day.id] ?? []).map((m) => ({ type: 'match' as const, id: m.id })),
        ...day.breaks.map((b) => ({ type: 'break' as const, id: b.id })),
      ],
    })),
  }
}

async function onDragEnd() {
  if (reorderPending) return
  reorderPending = true
  const editionId = eventStore.activeEdition?.id
  if (!editionId || !eventStore.calendar) {
    dragging.value = false
    reorderPending = false
    return
  }
  bannerError.value = ''
  try {
    await eventStore.reorderCalendar(editionId, buildReorderPayload())
  } catch (e) {
    bannerError.value = e instanceof Error ? e.message : 'Erreur lors du réordonnancement.'
    await eventStore.fetchCalendar()
  } finally {
    dragging.value = false
    reorderPending = false
    syncFromStore()
  }
}
</script>

<template>
  <div class="admin-page">
    <!-- ── En-tête ──────────────────────────────────────────────────────── -->
    <header class="page-header">
      <div class="header-left">
        <select
          class="event-selector"
          :value="eventStore.activeEventId"
          @change="eventStore.activeEventId = Number(($event.target as HTMLSelectElement).value)"
        >
          <option v-for="ev in eventStore.events" :key="ev.id" :value="ev.id">
            {{ ev.name }}
          </option>
        </select>
        <div>
          <h1 class="page-title">Calendrier des matchs</h1>
          <p class="page-sub">Qui joue, quand, contre qui</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="adm-btn" type="button" @click="showGenerateMatches = true">
          Générer les matchs de poule
        </button>
        <button
          class="adm-btn primary"
          type="button"
          :disabled="unscheduledTotal === 0 || arranging"
          @click="preArrange"
        >
          {{ arranging ? 'Pré-pose…' : 'Pré-poser' }}
        </button>
      </div>
    </header>

    <!-- Bandeau d'erreur global -->
    <div v-if="bannerError" class="error-banner">{{ bannerError }}</div>

    <!-- Modales -->
    <GenerateMatchesModal
      v-if="showGenerateMatches"
      @close="showGenerateMatches = false"
      @saved="onMatchesGenerated"
    />
    <EditMatchPanel
      v-if="editingMatch"
      :match="editingMatch"
      @close="editingMatch = null"
      @saved="onMatchSaved"
    />

    <!-- ── Corps ────────────────────────────────────────────────────────── -->
    <div class="cal-layout">
      <!-- Pile à planifier -->
      <aside class="cal-pile">
        <div class="pile-head">
          <span class="pile-title">À planifier</span>
          <span class="pile-count">{{ unscheduledTotal }}</span>
        </div>

        <div v-if="unscheduledTotal === 0 && totalScheduledMatches === 0" class="pile-done">
          Générez d'abord les matchs de poule.
        </div>
        <div v-else-if="unscheduledTotal === 0" class="pile-done">
          Tout est planifié
        </div>
        <template v-else>
          <template v-for="g in Object.keys(unscheduledByGroupDnd).sort()" :key="g">
            <div class="pile-group-hd">Poule {{ g }}</div>
            <draggable
              v-model="unscheduledByGroupDnd[g]"
              item-key="id"
              :group="{ name: 'matches', pull: true, put: true }"
              :move="checkMove"
              @start="onDragStart"
              @end="onDragEnd"
            >
              <template #item="{ element: m }">
                <div class="pile-card" @click="editingMatch = m">
                  <span class="poule-pill">{{ g }}</span>
                  <span class="pile-card-players">
                    {{ playerLabel(m, 'A') }} <em class="vs">vs</em> {{ playerLabel(m, 'B') }}
                  </span>
                  <span class="drag-handle">⋮⋮</span>
                </div>
              </template>
            </draggable>
          </template>
        </template>
      </aside>

      <!-- Journées -->
      <main class="cal-days">
        <div v-if="calendarDays.length === 0" class="cal-empty">
          <p>Aucune journée configurée.</p>
          <p class="cal-empty-sub">Créez les journées de jeu via l'administration Django.</p>
        </div>

        <section
          v-for="day in calendarDays"
          :key="day.id"
          class="play-day"
        >
          <!-- En-tête de journée -->
          <header class="pd-header">
            <div class="pd-header-left">
              <span class="pd-date">{{ formatDate(day.date) }}</span>
              <span class="pd-match-count">{{ day.matches.length }} match{{ day.matches.length !== 1 ? 's' : '' }}</span>
            </div>
            <div class="pd-header-right">
              <span class="pd-times">
                Court central · début {{ day.startTime }} · fin estimée
                ~{{ dayEndEstimate(day, day.matches) ?? '—' }}
              </span>
              <span
                v-if="dayEndEstimate(day, day.matches)"
                :class="['pd-capacity', capacityOver(day, day.matches) ? 'over' : '']"
              >
                {{ capacityOver(day, day.matches)
                  ? `Dépasse ${dayEndEstimate(day, day.matches)}`
                  : `Cible ${day.targetEndTime}` }}
              </span>
            </div>
          </header>

          <!-- Lignes (matchs draggables + pauses statiques) -->
          <div class="pd-rows">
            <template v-if="(dayMatchesDnd[day.id] ?? []).length === 0 && day.breaks.length === 0">
              <div class="pd-empty">Aucun match pour cette journée.</div>
            </template>
            <template v-else>
              <draggable
                v-model="dayMatchesDnd[day.id]"
                item-key="id"
                :group="{ name: 'matches', pull: true, put: true }"
                :move="checkMove"
                ghost-class="cal-row--ghost"
                drag-class="cal-row--dragging"
                @start="onDragStart"
                @end="onDragEnd"
              >
                <template #item="{ element: m }">
                  <div
                    class="cal-row"
                    :class="[`state--${displayState(m)}`, { 'no-drag': m.status === 'LIVE' }]"
                    role="button"
                    tabindex="0"
                    @click="editingMatch = m"
                    @keydown.enter="editingMatch = m"
                  >
                    <span class="cal-time">
                      {{ m.status === 'FINISHED' && m.startedAt ? '' : '~' }}{{ m.scheduledTime ?? '—' }}
                    </span>
                    <span
                      class="cal-dot"
                      :class="`dot--${displayState(m)}`"
                      :title="stateLabel(displayState(m))"
                    />
                    <span class="poule-pill">{{ groupName(m) || m.stageLabel }}</span>
                    <span class="cal-players">
                      {{ playerLabel(m, 'A') }} <em class="vs">vs</em> {{ playerLabel(m, 'B') }}
                    </span>
                    <span
                      v-if="m.isFeatured"
                      class="featured-badge"
                      title="Match mis en avant sur la TV"
                    >★ EN AVANT</span>
                    <span
                      class="drag-handle"
                      :class="{ 'drag-handle--locked': m.status === 'LIVE' }"
                    >⋮⋮</span>
                  </div>
                </template>
                <template #footer>
                  <div
                    v-for="brk in day.breaks"
                    :key="`b-${brk.id}`"
                    class="cal-row cal-row--break"
                  >
                    <span class="cal-time">—</span>
                    <span class="break-icon">⏸</span>
                    <span class="break-label">
                      {{ brk.label || 'Pause' }} · {{ brk.durationMin }} min
                    </span>
                    <span class="drag-handle drag-handle--locked">⋮⋮</span>
                  </div>
                </template>
              </draggable>
            </template>
          </div>

          <!-- Action pause (placeholder #98) -->
          <button class="add-pause-btn" type="button" disabled title="Bientôt disponible (#98)">
            + pause
          </button>
        </section>
      </main>
    </div>

    <!-- ── Légende ──────────────────────────────────────────────────────── -->
    <footer class="cal-legend">
      <div class="legend-item"><span class="cal-dot dot--live" /> En cours</div>
      <div class="legend-item"><span class="cal-dot dot--next" /> Next</div>
      <div class="legend-item"><span class="cal-dot dot--scheduled" /> Planifié</div>
      <div class="legend-item"><span class="cal-dot dot--finished" /> Terminé</div>
      <div class="legend-item"><span class="cal-dot dot--canceled" /> Annulé</div>
    </footer>
  </div>
</template>

<style scoped>
/* ── Layout global ────────────────────────────────────────────────────────── */
.admin-page { display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

/* ── En-tête ─────────────────────────────────────────────────────────────── */
.page-header {
  padding: 24px 40px 20px;
  border-bottom: 1px solid var(--line-1);
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-shrink: 0;
}

.header-left { display: flex; flex-direction: column; gap: 6px; }

.event-selector {
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-2);
  cursor: pointer;
  font-family: inherit;
  max-width: 220px;
}

.event-selector:focus { outline: none; border-color: var(--accent); }

.page-title { margin: 0; font-size: 22px; font-weight: 700; color: var(--ink-0); }
.page-sub { margin: 2px 0 0; font-size: 13px; color: var(--ink-3); }

.header-actions { display: flex; gap: 8px; flex-shrink: 0; }

.adm-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
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
.adm-btn.primary { background: var(--accent); border-color: var(--accent); color: #000; }
.adm-btn.primary:hover { opacity: 0.9; }
.adm-btn:disabled { opacity: 0.45; cursor: not-allowed; }

/* Bandeau d'erreur */
.error-banner {
  padding: 10px 40px;
  background: var(--danger-soft);
  color: var(--danger);
  font-size: 13px;
  border-bottom: 1px solid var(--danger);
  flex-shrink: 0;
}

/* ── Corps : pile + journées ─────────────────────────────────────────────── */
.cal-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  gap: 0;
}

/* ── Pile à planifier ────────────────────────────────────────────────────── */
.cal-pile {
  width: 260px;
  flex-shrink: 0;
  border-right: 1px solid var(--line-1);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 16px 12px;
  gap: 0;
}

.pile-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line-1);
}

.pile-title {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--ink-2);
}

.pile-count {
  font-size: 11px;
  font-weight: 700;
  color: var(--ink-3);
  background: var(--bg-4);
  padding: 1px 7px;
  border-radius: 99px;
}

.pile-done {
  text-align: center;
  color: var(--ink-4);
  font-size: 13px;
  padding: 24px 0;
}

.pile-group-hd {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--ink-3);
  text-transform: uppercase;
  padding: 10px 4px 4px;
}

.pile-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  background: var(--bg-3);
  border: 1px solid var(--line-1);
  border-radius: var(--r-md);
  cursor: pointer;
  margin-bottom: 6px;
  transition: background 150ms;
}

.pile-card:hover { background: var(--bg-4); }
.pile-card--ghost { opacity: 0.35; background: var(--accent-soft); }

.pile-card-players {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  color: var(--ink-0);
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Zone journées ───────────────────────────────────────────────────────── */
.cal-days {
  flex: 1;
  overflow-y: auto;
  padding: 20px 32px 80px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.cal-empty {
  text-align: center;
  padding: 60px 24px;
  color: var(--ink-3);
}

.cal-empty p { margin: 0 0 6px; }
.cal-empty-sub { font-size: 12px; }

/* ── Journée (PlayDay) ───────────────────────────────────────────────────── */
.play-day {
  border: 1px solid var(--line-1);
  border-radius: var(--r-lg);
  overflow: hidden;
}

.pd-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  background: var(--bg-3);
  border-bottom: 1px solid var(--line-1);
  flex-wrap: wrap;
}

.pd-header-left { display: flex; align-items: center; gap: 12px; }

.pd-date {
  font-size: 14px;
  font-weight: 700;
  color: var(--ink-0);
  text-transform: capitalize;
}

.pd-match-count {
  font-size: 12px;
  color: var(--ink-3);
  background: var(--bg-4);
  padding: 2px 8px;
  border-radius: 99px;
  font-weight: 600;
}

.pd-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--ink-2);
}

.pd-times { color: var(--ink-3); }

.pd-capacity {
  padding: 3px 10px;
  border-radius: 99px;
  font-size: 11px;
  font-weight: 700;
  background: var(--success-soft);
  color: var(--success);
  border: 1px solid currentColor;
}

.pd-capacity.over {
  background: var(--danger-soft);
  color: var(--danger);
}

.pd-rows { display: flex; flex-direction: column; }

.pd-empty {
  padding: 20px 18px;
  font-size: 13px;
  color: var(--ink-4);
}

/* ── Ligne calendrier ────────────────────────────────────────────────────── */
.cal-row {
  display: grid;
  grid-template-columns: 64px 14px auto 1fr auto 20px;
  align-items: center;
  gap: 10px;
  padding: 11px 18px;
  border-bottom: 1px solid var(--line-1);
  cursor: pointer;
  transition: background 100ms;
}

.cal-row:last-child { border-bottom: none; }
.cal-row:hover { background: var(--bg-3); }

.cal-row.state--finished { opacity: 0.65; }
.cal-row.state--canceled { opacity: 0.45; }
.cal-row.state--live { background: var(--danger-soft, rgba(255,50,50,0.06)); }
.cal-row.state--next { background: var(--accent-soft, rgba(255,200,61,0.07)); }

.cal-row--break {
  grid-template-columns: 64px 16px 1fr 20px;
  cursor: default;
  background: var(--bg-3);
  opacity: 0.8;
}

.cal-row--break:hover { background: var(--bg-3); }

.cal-time {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-2);
  text-align: right;
}

/* État dot */
.cal-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot--live    { background: var(--danger); box-shadow: 0 0 0 3px var(--danger-soft); }
.dot--next    { background: var(--accent, #ffc83d); }
.dot--scheduled { background: var(--ink-3, #888); }
.dot--finished  { background: var(--success, #0a8a4a); }
.dot--canceled  { background: var(--line-3, #ccc); }

/* Poule pill */
.poule-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: var(--r-xs);
  background: var(--accent);
  color: #000;
  font-size: 11px;
  font-weight: 800;
  flex-shrink: 0;
}

.cal-players {
  font-size: 14px;
  font-weight: 500;
  color: var(--ink-0);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.vs {
  font-style: normal;
  font-size: 11px;
  color: var(--ink-3);
  margin: 0 4px;
  font-weight: 400;
}

.featured-badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--accent);
  border: 1px solid var(--accent);
  padding: 2px 7px;
  border-radius: 99px;
  white-space: nowrap;
  flex-shrink: 0;
}

.drag-handle {
  font-size: 14px;
  color: var(--ink-4);
  cursor: grab;
  user-select: none;
  flex-shrink: 0;
}

.drag-handle--locked {
  cursor: not-allowed;
  opacity: 0.3;
}

/* États DnD */
.cal-row--ghost { opacity: 0.35; background: var(--accent-soft); }
.cal-row--dragging { opacity: 0.9; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }

/* Break */
.break-icon { font-size: 14px; color: var(--ink-3); }
.break-label { font-size: 13px; color: var(--ink-2); }

/* Bouton pause */
.add-pause-btn {
  display: block;
  width: 100%;
  padding: 9px;
  background: none;
  border: none;
  border-top: 1px dashed var(--line-2);
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-3);
  cursor: not-allowed;
  font-family: inherit;
  text-align: center;
  letter-spacing: 0.04em;
}

/* ── Légende ─────────────────────────────────────────────────────────────── */
.cal-legend {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px 40px;
  border-top: 1px solid var(--line-1);
  font-size: 12px;
  color: var(--ink-3);
  flex-shrink: 0;
  background: var(--bg-2);
}

.legend-item { display: flex; align-items: center; gap: 6px; }
</style>
