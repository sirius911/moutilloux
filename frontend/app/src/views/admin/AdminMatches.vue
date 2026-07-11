<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import draggable from 'vuedraggable'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useEventStore } from '@/stores/event'
import type { CalendarReorderPayload } from '@/stores/event'
import { usePolling } from '@/composables/usePolling'
import EditMatchPanel from '@/components/modals/EditMatchPanel.vue'
import PlayDayModal from '@/components/modals/PlayDayModal.vue'
import ConfirmModal from '@/components/ui/ConfirmModal.vue'
import type { Match, Break, CalendarDay } from '@/types'

// ── Type union local ───────────────────────────────────────────────────────
type DayItem =
  | { kind: 'match'; data: Match }
  | { kind: 'break'; data: Break }

const eventStore = useEventStore()
const route = useRoute()
const router = useRouter()

const editingMatch = ref<Match | null>(null)
const editingMatchInitialTab = ref<'score' | 'format' | 'planning' | 'poster'>('score')
const showPlayDayModal = ref(false)
const bannerError = ref('')
const arranging = ref(false)

const editingStartDayId = ref<number | null>(null)
const editingStartValue = ref('')
const savingStart = ref<Record<number, boolean>>({})
const startError = ref<Record<number, string>>({})

function openMatchPanel(match: Match, initialTab: 'score' | 'format' | 'planning' | 'poster' = 'score') {
  editingMatch.value = match
  editingMatchInitialTab.value = initialTab
}

const activeEvent = computed(() =>
  eventStore.events.find((e) => e.id === eventStore.activeEventId),
)

// ── Polling calendrier ─────────────────────────────────────────────────────

usePolling(() => eventStore.fetchCalendar(), 2000)

watch(
  () => eventStore.activeEventId,
  () => eventStore.fetchCalendar(),
)

// ── État local DnD (miroir du store, muté par vuedraggable) ───────────────

const dragging = ref(false)
// Pile : groupée par poule (une entrée par groupe, wrappée en DayItem)
const unscheduledByGroupDnd = ref<Record<string, DayItem[]>>({})
// Journées : items unifiés (matchs + pauses) ordonnés par playDayId
const dayItemsDnd = ref<Record<number, DayItem[]>>({})

// ── Repli des journées (défaut jouées repliées, état non persisté) ────────
const collapsedDays = ref<Record<number, boolean>>({})

function isDayFullyPlayed(day: CalendarDay): boolean {
  return day.matches.length > 0 && day.matches.every((m) => m.status !== 'SCHEDULED' && m.status !== 'LIVE')
}

function toggleDay(dayId: number) {
  collapsedDays.value[dayId] = !collapsedDays.value[dayId]
}

// ── Dépliage au survol pendant un drag (journée repliée = cible masquée) ──
// Objet non réactif : simples handles de timer, pas d'affichage lié.
const collapsedHoverTimers: Record<number, ReturnType<typeof setTimeout>> = {}

function onHeaderMouseEnter(dayId: number) {
  if (!dragging.value || !collapsedDays.value[dayId]) return
  clearTimeout(collapsedHoverTimers[dayId])
  collapsedHoverTimers[dayId] = setTimeout(() => {
    collapsedDays.value[dayId] = false
  }, 600)
}

function onHeaderMouseLeave(dayId: number) {
  clearTimeout(collapsedHoverTimers[dayId])
  delete collapsedHoverTimers[dayId]
}

function playedCount(day: CalendarDay): number {
  return day.matches.filter((m) => m.status === 'FINISHED').length
}

function syncFromStore() {
  if (dragging.value) return
  const cal = eventStore.calendar
  if (!cal) {
    unscheduledByGroupDnd.value = {}
    dayItemsDnd.value = {}
    return
  }

  // Pile : toute l'édition, groupée par épreuve + poule. Ne PAS filtrer par
  // épreuve : le payload de reorder doit couvrir la séquence complète de
  // l'édition, sinon le serveur dé-planifie les matchs absents (specs planning).
  const newGroups: Record<string, DayItem[]> = {}
  for (const m of cal.unscheduled) {
    ;(newGroups[pileGroupKey(m)] ??= []).push({ kind: 'match', data: m })
  }
  unscheduledByGroupDnd.value = newGroups

  // Journées : merge + tri par orderIndex (toute l'édition, même contrainte)
  const days: Record<number, DayItem[]> = {}
  for (const day of cal.playDays) {
    const matchItems: DayItem[] = day.matches
      .map((m) => ({ kind: 'match', data: m }))
    const breakItems: DayItem[] = day.breaks.map((b) => ({ kind: 'break', data: b }))
    days[day.id] = [...matchItems, ...breakItems].sort((a, b) => {
      const ao = a.kind === 'match' ? (a.data.orderIndex ?? 99999) : a.data.orderIndex
      const bo = b.kind === 'match' ? (b.data.orderIndex ?? 99999) : b.data.orderIndex
      return ao - bo
    })
  }
  dayItemsDnd.value = days
}

watch(() => eventStore.calendar, () => { if (!dragging.value) syncFromStore() }, { deep: true, immediate: true })

// ── Données de structure (journées depuis le store, matchs depuis DnD local) ─

const calendarDays = computed<CalendarDay[]>(() => {
  if (!eventStore.calendar) return []
  return eventStore.calendar.playDays.map((day) => ({
    ...day,
    matches: (dayItemsDnd.value[day.id] ?? [])
      .filter((i): i is { kind: 'match'; data: Match } => i.kind === 'match')
      .map((i) => i.data),
  }))
})

const unscheduledTotal = computed(() =>
  Object.values(unscheduledByGroupDnd.value).reduce((s, arr) => s + arr.length, 0),
)

// Initialisation du repli une fois par journée (jamais re-forcée sur un
// repli/dépli manuel en cours de session, même au fil du polling).
watch(
  calendarDays,
  (days) => {
    for (const day of days) {
      if (!(day.id in collapsedDays.value)) collapsedDays.value[day.id] = isDayFullyPlayed(day)
    }
  },
  { immediate: true },
)

// ── Groupage épreuve + poule (pile et annulés) ─────────────────────────────

function pileGroupKey(m: Match): string {
  return `${pileGroupLetter(m)}|${m.eventId}`
}

function eventName(eventId: number): string {
  return eventStore.events.find((e) => e.id === eventId)?.name ?? `Épreuve ${eventId}`
}

function isForeign(m: Match): boolean {
  return m.eventId !== eventStore.activeEventId
}

// Plusieurs épreuves représentées au calendrier ? → afficher le nom d'épreuve
// sur les groupes de pile et les lignes de journée (mise en évidence).
const multiEvent = computed(() => {
  const cal = eventStore.calendar
  if (!cal) return false
  const ids = new Set<number>()
  for (const m of cal.unscheduled) ids.add(m.eventId)
  for (const d of cal.playDays) for (const m of d.matches) ids.add(m.eventId)
  for (const m of cal.canceled) ids.add(m.eventId)
  return ids.size > 1
})

interface PileGroup { key: string; letter: string; eventId: number; eventName: string }

function parsePileKey(key: string): PileGroup {
  const sep = key.lastIndexOf('|')
  const eventId = Number(key.slice(sep + 1))
  return { key, letter: key.slice(0, sep), eventId, eventName: eventName(eventId) }
}

// Poules triées alphabétiquement, groupe « Tableau » toujours en dernier
// (ordre du cycle de vie d'une épreuve : poules puis QF → SF → F/P3, déjà
// garanti par le tri serveur à l'intérieur du groupe Tableau lui-même).
function groupSortKey(letter: string): string {
  return letter === 'Tableau' ? '￿' : letter
}

const pileGroups = computed<PileGroup[]>(() =>
  Object.keys(unscheduledByGroupDnd.value)
    .map(parsePileKey)
    .sort((a, b) =>
      a.eventName.localeCompare(b.eventName) ||
      groupSortKey(a.letter).localeCompare(groupSortKey(b.letter)),
    ),
)

// ── Colonne « Annulés » (lecture seule) ────────────────────────────────────
interface CanceledGroup extends PileGroup { matches: Match[] }

const canceledGroups = computed<CanceledGroup[]>(() => {
  const cal = eventStore.calendar
  if (!cal) return []
  const byKey: Record<string, Match[]> = {}
  for (const m of cal.canceled) {
    ;(byKey[pileGroupKey(m)] ??= []).push(m)
  }
  return Object.entries(byKey)
    .map(([key, matches]) => ({ ...parsePileKey(key), matches }))
    .sort((a, b) =>
      a.eventName.localeCompare(b.eventName) ||
      groupSortKey(a.letter).localeCompare(groupSortKey(b.letter)),
    )
})

const canceledCount = computed(() =>
  canceledGroups.value.reduce((s, g) => s + g.matches.length, 0),
)

const totalScheduledMatches = computed(() =>
  Object.values(dayItemsDnd.value).reduce(
    (s, items) => s + items.filter((i) => i.kind === 'match').length, 0,
  ),
)

// ── Pauses ─────────────────────────────────────────────────────────────────
const addingPause = ref<Record<number, boolean>>({})
const deletingBreak = ref<Record<number, boolean>>({})
const starting = ref<Record<number, boolean>>({})

async function addPause(dayId: number) {
  addingPause.value[dayId] = true
  bannerError.value = ''
  try {
    await eventStore.createBreak(dayId, { durationMin: 15 })
  } catch (e) {
    bannerError.value = e instanceof Error ? e.message : 'Erreur lors de l\'ajout de la pause.'
  } finally {
    addingPause.value[dayId] = false
  }
}

async function deletePause(breakId: number) {
  deletingBreak.value[breakId] = true
  bannerError.value = ''
  try {
    await eventStore.deleteBreak(breakId)
  } catch (e) {
    bannerError.value = e instanceof Error ? e.message : 'Erreur lors de la suppression de la pause.'
  } finally {
    deletingBreak.value[breakId] = false
  }
}

function openStartEdit(day: CalendarDay) {
  editingStartDayId.value = day.id
  editingStartValue.value = day.startTime
  startError.value[day.id] = ''
}

function cancelStartEdit() {
  editingStartDayId.value = null
}

async function confirmStartEdit(day: CalendarDay) {
  if (editingStartDayId.value !== day.id) return
  if (editingStartValue.value === day.startTime) {
    cancelStartEdit()
    return
  }
  savingStart.value[day.id] = true
  startError.value[day.id] = ''
  try {
    await eventStore.updatePlayDay(day.id, { startTime: editingStartValue.value })
    editingStartDayId.value = null
  } catch (e) {
    startError.value[day.id] = e instanceof Error ? e.message : 'Erreur lors de la mise à jour.'
  } finally {
    savingStart.value[day.id] = false
  }
}

const pendingStartMatchId = ref<number | null>(null)

function hasOtherLiveMatch(matchId: number): boolean {
  const allMatches = eventStore.calendar?.playDays.flatMap((d) => d.matches) ?? []
  return allMatches.some((m) => m.status === 'LIVE' && m.id !== matchId)
}

async function doStartMatch(matchId: number) {
  starting.value[matchId] = true
  bannerError.value = ''
  try {
    await eventStore.startMatch(matchId)
  } catch (e) {
    bannerError.value = e instanceof Error ? e.message : 'Erreur lors du démarrage du match.'
  } finally {
    starting.value[matchId] = false
  }
}

async function startMatch(matchId: number) {
  if (hasOtherLiveMatch(matchId)) {
    pendingStartMatchId.value = matchId
    return
  }
  await doStartMatch(matchId)
}

async function confirmStartMatch() {
  const matchId = pendingStartMatchId.value
  pendingStartMatchId.value = null
  if (matchId !== null) await doStartMatch(matchId)
}

// ── Helpers ────────────────────────────────────────────────────────────────

function groupName(match: Match): string {
  const parts = match.stageLabel.split(' — Poule ')
  return parts[1] ?? ''
}

// Lettre de groupement de la pile / Annulés : lettre de poule pour un match
// de poule, groupe unique « Tableau » pour tout stage de tableau final
// (QF/SF/F/P3) — cf. spec « la pile … groupés par épreuve puis par poule —
// les matchs de tableau … forment un groupe "Tableau" »).
function pileGroupLetter(match: Match): string {
  if (match.stage === 'GROUP') return groupName(match) || '?'
  return 'Tableau'
}

// Pastille affichée sur une carte/ligne : lettre de poule, ou pastille
// d'étape (bracketSlot, ex. « QF1 », « SF2 ») pour un match de tableau.
function stagePillLabel(match: Match): string {
  if (match.stage === 'GROUP') return groupName(match) || match.stageLabel
  return match.bracketSlot ?? match.stage
}

function playerLabel(match: Match, side: 'A' | 'B'): string {
  if (side === 'A') return match.sideA?.player?.fullName ?? match.sideALabel ?? 'TBD'
  return match.sideB?.player?.fullName ?? match.sideBLabel ?? 'TBD'
}

// Identifiant du seul match "Next" — lu depuis l'état DnD local.
// Scope à la journée du match en cours quand un match est LIVE (spec planning §États dérivés).
const nextMatchId = computed<number | null>(() => {
  const allMatchItems = Object.values(dayItemsDnd.value)
    .flat()
    .filter((i): i is { kind: 'match'; data: Match } => i.kind === 'match')
  const allMatches = allMatchItems.map((i) => i.data)
  const liveMatch = allMatches.find((m) => m.status === 'LIVE')

  let candidates: Match[]
  if (liveMatch) {
    const liveDayItems =
      Object.values(dayItemsDnd.value).find((items) =>
        items.some((i) => i.kind === 'match' && i.data.id === liveMatch.id),
      ) ?? []
    const liveDayMatches = liveDayItems
      .filter((i): i is { kind: 'match'; data: Match } => i.kind === 'match')
      .map((i) => i.data)
    candidates = liveDayMatches.filter(
      (m) => m.status === 'SCHEDULED' && (m.orderIndex ?? -1) > (liveMatch.orderIndex ?? -1),
    )
  } else {
    candidates = allMatches.filter((m) => m.status === 'SCHEDULED')
  }

  candidates.sort((a, b) => (a.orderIndex ?? 0) - (b.orderIndex ?? 0))
  return candidates[0]?.id ?? null
})

// ── Détection repos insuffisant ────────────────────────────────────────────
// Deux matchs adjacents dans la séquence partageant un joueur → ⚠ (spec planning §repos).
// Les pauses sont ignorées pour ce calcul.
// Best-effort sur matchs de tableau non résolus (sideA/sideB null) : un slot
// non résolu n'ajoute aucun id à currIds, donc ne peut jamais déclencher de
// faux ⚠ ni faire planter le calcul (chaînage optionnel). Le ⚠ apparaît
// naturellement au recalcul du computed une fois le slot résolu par le polling.
const restWarnings = computed<Set<number>>(() => {
  const warnings = new Set<number>()

  for (const day of calendarDays.value) {
    const seq = (dayItemsDnd.value[day.id] ?? [])
      .filter((item): item is { kind: 'match'; data: Match } =>
        item.kind === 'match' && item.data.status !== 'CANCELED')
      .map((item) => item.data)

    for (let i = 0; i < seq.length; i++) {
      const curr = seq[i]
      const currIds = new Set<number>()
      if (curr.sideA?.player?.id != null) currIds.add(curr.sideA.player.id)
      if (curr.sideB?.player?.id != null) currIds.add(curr.sideB.player.id)

      const sharesPlayer = (other: Match): boolean => {
        if (other.sideA?.player?.id != null && currIds.has(other.sideA.player.id)) return true
        if (other.sideB?.player?.id != null && currIds.has(other.sideB.player.id)) return true
        return false
      }

      const prev = i > 0 ? seq[i - 1] : null
      const next = i < seq.length - 1 ? seq[i + 1] : null
      if ((prev && sharesPlayer(prev)) || (next && sharesPlayer(next))) {
        warnings.add(curr.id)
      }
    }
  }

  return warnings
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

function isoToMin(iso: string): number {
  const d = new Date(iso)
  return d.getHours() * 60 + d.getMinutes()
}

// Compare `dateStr` (YYYY-MM-DD) à la date locale du jour — même convention que
// `formatDate` (construction locale, pas UTC/`toISOString`). L'ancrage sur
// « maintenant » ne doit s'appliquer qu'à la journée en cours (spec planning
// §journées indépendantes).
function isToday(dateStr: string): boolean {
  const now = new Date()
  const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  return dateStr === todayStr
}

// ── Moteur ETA frontal ─────────────────────────────────────────────────────
// Durée par étape (constantes applicatives, pas de config — spec planning
// §Algorithme d'estimation des heures) : poule = défaut d'édition (~30 min
// par défaut) ; QF/SF ~30-35 min (formats à un set, `_fmt_for_stage` :
// QF_SET5_TB_5_5 / NORMAL_1SET) ; finale/3e place ~45 min (BO3, plus long).
const ETA_DUR_QF_SF_MIN = 35
const ETA_DUR_FINAL_MIN = 45

function durFor(match: Match): number {
  const editionDefault = eventStore.activeEdition?.defaultMatchDurationMin ?? 30
  if (match.stage === 'QF' || match.stage === 'SF') return ETA_DUR_QF_SF_MIN
  if (match.stage === 'F' || match.stage === 'P3') return ETA_DUR_FINAL_MIN
  return editionDefault
}

// Calcule les heures estimées pour chaque match et pause de chaque journée.
// Clés : m-{id} (match), b-{id} (pause), day-end-{id} (fin de journée).
// Les pauses obtiennent leur ETA à leur position réelle dans la séquence unifiée.
const etaEngine = computed<{ display: Map<string, string>; plannedMin: Map<number, number> }>(() => {
  const result = new Map<string, string>()
  const plannedMin = new Map<number, number>()
  const now = new Date()
  const nowMin = now.getHours() * 60 + now.getMinutes()

  for (const day of calendarDays.value) {
    const items = dayItemsDnd.value[day.id] ?? []
    let cursor = timeToMin(day.startTime)
    const anchorNow = isToday(day.date)

    for (const item of items) {
      if (item.kind === 'match') {
        const m = item.data
        const dur = durFor(m)
        plannedMin.set(m.id, cursor)
        if (m.status === 'FINISHED' && m.finishedAt) {
          const displayMin = m.startedAt ? isoToMin(m.startedAt) : isoToMin(m.finishedAt)
          result.set(`m-${m.id}`, minToTime(displayMin))
          const ft = isoToMin(m.finishedAt)
          cursor = Math.max(cursor + dur, ft)
        } else if (m.status === 'LIVE') {
          const displayMin = m.startedAt ? isoToMin(m.startedAt) : cursor
          result.set(`m-${m.id}`, minToTime(displayMin))
          const liveEnd = m.startedAt ? isoToMin(m.startedAt) + dur : cursor + dur
          cursor = anchorNow ? Math.max(cursor + dur, liveEnd, nowMin) : Math.max(cursor + dur, liveEnd)
        } else {
          result.set(`m-${m.id}`, `~${minToTime(cursor)}`)
          cursor += dur
        }
      } else {
        result.set(`b-${item.data.id}`, `~${minToTime(cursor)}`)
        cursor += item.data.durationMin
      }
    }

    result.set(`day-end-${day.id}`, minToTime(cursor))
  }

  return { display: result, plannedMin }
})

const computedETAs = computed(() => etaEngine.value.display)
const plannedEtaMin = computed(() => etaEngine.value.plannedMin)

type Punctuality = 'red' | 'orange' | 'green'

const punctualityByMatchId = computed<Map<number, Punctuality>>(() => {
  const result = new Map<number, Punctuality>()
  const now = new Date()
  const nowMin = now.getHours() * 60 + now.getMinutes()

  for (const day of calendarDays.value) {
    if (!isToday(day.date)) continue
    for (const item of dayItemsDnd.value[day.id] ?? []) {
      if (item.kind !== 'match') continue
      const m = item.data
      const planned = plannedEtaMin.value.get(m.id)
      if (planned === undefined) continue
      const dur = durFor(m)

      if (m.status === 'SCHEDULED') {
        if (nowMin > planned + 5) result.set(m.id, 'red')
      } else if (m.status === 'LIVE') {
        const startedMin = m.startedAt ? isoToMin(m.startedAt) : null
        const lateStart = startedMin !== null && startedMin > planned + 5
        const overrun = startedMin !== null && nowMin > startedMin + dur + 5
        result.set(m.id, lateStart || overrun ? 'orange' : 'green')
      }
      // FINISHED / CANCELED : aucune entrée → aucune teinte.
    }
  }
  return result
})

function punctualityClass(matchId: number): string {
  const p = punctualityByMatchId.value.get(matchId)
  return p ? `punct--${p}` : ''
}

function dayEndEstimate(day: CalendarDay): string | null {
  return computedETAs.value.get(`day-end-${day.id}`) ?? null
}

function capacityOver(day: CalendarDay): boolean {
  const end = dayEndEstimate(day)
  if (!end) return false
  return timeToMin(end) > timeToMin(day.targetEndTime)
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })
}

// ── Actions ────────────────────────────────────────────────────────────────

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

function onPosterUpdated() {
  eventStore.fetchCalendar()
}

function setActiveEvent(id: string) {
  const numId = parseInt(id, 10)
  if (!isNaN(numId)) router.push({ params: { ...route.params, eventId: numId } })
}

// ── Drag-and-drop ──────────────────────────────────────────────────────────

// Guard contre le double @end lors des drags inter-listes (SortableJS peut
// émettre end sur source ET destination pour un même glissement).
let reorderPending = false

function onDragStart() {
  dragging.value = true
}

function checkMove(evt: { draggedContext: { element: DayItem }; to: Element }): boolean {
  const el = evt.draggedContext.element
  if (el.kind === 'match' && el.data.status !== 'SCHEDULED') return false
  if (el.kind === 'break' && evt.to.classList.contains('pile-draggable')) return false
  return true
}

function buildReorderPayload(): CalendarReorderPayload {
  const playDays = eventStore.calendar?.playDays ?? []
  return {
    playDays: playDays.map((day) => ({
      playDayId: day.id,
      items: (dayItemsDnd.value[day.id] ?? []).map((item) =>
        item.kind === 'match'
          ? { type: 'match' as const, id: item.data.id }
          : { type: 'break' as const, id: item.data.id },
      ),
    })),
  }
}

async function onDragEnd() {
  for (const id of Object.keys(collapsedHoverTimers)) {
    clearTimeout(collapsedHoverTimers[Number(id)])
    delete collapsedHoverTimers[Number(id)]
  }
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
          @change="setActiveEvent(($event.target as HTMLSelectElement).value)"
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
        <button class="adm-btn" type="button" @click="showPlayDayModal = true">
          Gérer les journées
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
    <PlayDayModal v-if="showPlayDayModal" @close="showPlayDayModal = false" />
    <EditMatchPanel
      v-if="editingMatch"
      :match="editingMatch"
      :initial-tab="editingMatchInitialTab"
      @close="editingMatch = null"
      @saved="onMatchSaved"
      @poster-updated="onPosterUpdated"
    />
    <ConfirmModal
      v-if="pendingStartMatchId !== null"
      title="Démarrer ce match ?"
      body="Un autre match est en cours — le démarrer le mettra en pause (il repasse Prévu, score conservé)."
      confirm-label="Démarrer"
      :danger="false"
      @confirm="confirmStartMatch"
      @close="pendingStartMatchId = null"
    />

    <!-- ── Corps ────────────────────────────────────────────────────────── -->
    <div v-if="eventStore.events.length === 0" class="empty-state">
      <p>Aucune épreuve active.</p>
      <RouterLink to="/admin/tournoi">Créer une épreuve dans Tournoi →</RouterLink>
    </div>

    <div v-else-if="activeEvent?.status === 'INSCRIPTION'" class="empty-state">
      <p>L'épreuve n'a pas encore été débutée.</p>
      <RouterLink to="/admin/tournoi">Débuter depuis l'écran Tournoi →</RouterLink>
    </div>

    <template v-else>
      <div class="cal-layout">
      <!-- Pile à planifier -->
      <aside class="cal-pile">
        <div class="pile-head">
          <span class="pile-title">À planifier</span>
          <span class="pile-count">{{ unscheduledTotal }}</span>
        </div>

        <div v-if="unscheduledTotal === 0 && totalScheduledMatches === 0" class="pile-done">
          Aucun match à planifier.
        </div>
        <div v-else-if="unscheduledTotal === 0" class="pile-done">
          Tout est planifié
        </div>
        <template v-else>
          <template v-for="g in pileGroups" :key="g.key">
            <div class="pile-group-hd">
              {{ g.letter === 'Tableau' ? 'Tableau' : `Poule ${g.letter}` }}<span v-if="multiEvent" class="pile-group-ev"> · {{ g.eventName }}</span>
            </div>
            <draggable
              v-model="unscheduledByGroupDnd[g.key]"
              class="pile-draggable"
              :item-key="(item: DayItem) => item.kind + '-' + item.data.id"
              :group="{ name: 'matches', pull: true, put: true }"
              :move="checkMove"
              @start="onDragStart"
              @end="onDragEnd"
            >
              <template #item="{ element }">
                <div
                  class="pile-card"
                  :class="{ 'is-foreign': isForeign(element.data as Match) }"
                  @click="openMatchPanel(element.data as Match)"
                >
                  <span class="poule-pill">{{ stagePillLabel(element.data as Match) }}</span>
                  <span class="pile-card-players">
                    {{ playerLabel(element.data as Match, 'A') }} <em class="vs">vs</em> {{ playerLabel(element.data as Match, 'B') }}
                  </span>
                  <span class="drag-handle">⋮⋮</span>
                </div>
              </template>
            </draggable>
          </template>
        </template>
      </aside>

      <!-- Colonne Annulés (lecture seule) -->
      <aside v-if="canceledCount > 0" class="cal-pile cal-canceled">
        <div class="pile-head">
          <span class="pile-title">Annulés</span>
          <span class="pile-count">{{ canceledCount }}</span>
        </div>

        <template v-for="g in canceledGroups" :key="g.key">
          <div class="pile-group-hd">
            {{ g.letter === 'Tableau' ? 'Tableau' : `Poule ${g.letter}` }}<span v-if="multiEvent" class="pile-group-ev"> · {{ g.eventName }}</span>
          </div>
          <div
            v-for="m in g.matches"
            :key="m.id"
            class="pile-card pile-card--readonly"
            :class="{ 'is-foreign': isForeign(m) }"
            @click="openMatchPanel(m)"
          >
            <span class="poule-pill">{{ stagePillLabel(m) }}</span>
            <span class="pile-card-players">
              {{ playerLabel(m, 'A') }} <em class="vs">vs</em> {{ playerLabel(m, 'B') }}
            </span>
            <span class="canceled-badge" title="Match annulé">ANNULÉ</span>
          </div>
        </template>
      </aside>

      <!-- Journées -->
      <main class="cal-days">
        <div v-if="calendarDays.length === 0" class="cal-empty">
          <p>Aucune journée configurée.</p>
          <p class="cal-empty-sub">
            Créez une première journée via
            <button class="cal-empty-link" type="button" @click="showPlayDayModal = true">« Gérer les journées »</button>.
          </p>
        </div>

        <section
          v-for="day in calendarDays"
          :key="day.id"
          class="play-day"
        >
          <!-- En-tête de journée (repliable — clic sur l'en-tête entier) -->
          <header
            class="pd-header"
            role="button"
            tabindex="0"
            :aria-expanded="!collapsedDays[day.id]"
            @click="toggleDay(day.id)"
            @keydown.enter="toggleDay(day.id)"
            @mouseenter="onHeaderMouseEnter(day.id)"
            @mouseleave="onHeaderMouseLeave(day.id)"
          >
            <span
              class="pd-chevron"
              :class="{ 'pd-chevron--collapsed': collapsedDays[day.id] }"
            >▾</span>

            <!-- Repliée : résumé riche (joués/total, plage horaire) -->
            <template v-if="collapsedDays[day.id]">
              <div class="pd-header-left">
                <span class="pd-date">{{ formatDate(day.date) }}</span>
                <span class="pd-match-count">{{ playedCount(day) }}/{{ day.matches.length }} matchs</span>
              </div>
              <div class="pd-header-right">
                <span class="pd-times">
                  début {{ day.startTime }} → {{ isDayFullyPlayed(day) ? '' : '~' }}{{ dayEndEstimate(day) ?? '—' }}
                </span>
                <span
                  v-if="dayEndEstimate(day)"
                  :class="['pd-capacity', capacityOver(day) ? 'over' : '']"
                >
                  {{ capacityOver(day)
                    ? `Dépasse ${dayEndEstimate(day)}`
                    : `Cible ${day.targetEndTime}` }}
                </span>
              </div>
            </template>

            <!-- Dépliée : rendu actuel, inchangé -->
            <template v-else>
              <div class="pd-header-left">
                <span class="pd-date">{{ formatDate(day.date) }}</span>
                <span class="pd-match-count">{{ day.matches.length }} match{{ day.matches.length !== 1 ? 's' : '' }}</span>
              </div>
              <div class="pd-header-right">
                <span class="pd-times">
                  Court central ·
                  <button
                    v-if="editingStartDayId !== day.id"
                    type="button"
                    class="pd-start-trigger"
                    @click.stop="openStartEdit(day)"
                  >début {{ day.startTime }}</button>
                  <span v-else class="pd-start-edit" @click.stop>
                    début
                    <input
                      v-model="editingStartValue"
                      type="time"
                      class="pd-input pd-start-input"
                      :disabled="savingStart[day.id]"
                      autofocus
                      @keydown.enter="confirmStartEdit(day)"
                      @keydown.esc="cancelStartEdit"
                      @blur="confirmStartEdit(day)"
                      @click.stop
                    />
                  </span>
                  · fin estimée ~{{ dayEndEstimate(day) ?? '—' }}
                </span>
                <span v-if="startError[day.id]" class="pd-start-error">{{ startError[day.id] }}</span>
                <span
                  v-if="dayEndEstimate(day)"
                  :class="['pd-capacity', capacityOver(day) ? 'over' : '']"
                >
                  {{ capacityOver(day)
                    ? `Dépasse ${dayEndEstimate(day)}`
                    : `Cible ${day.targetEndTime}` }}
                </span>
              </div>
            </template>
          </header>

          <!-- Lignes matchs + pauses (liste unifiée DnD ↔ pile) -->
          <div v-if="!collapsedDays[day.id]" class="pd-rows">
            <draggable
              v-model="dayItemsDnd[day.id]"
              class="pd-droparea"
              :item-key="(item: DayItem) => item.kind + '-' + item.data.id"
              :group="{ name: 'matches', pull: true, put: true }"
              :move="checkMove"
              ghost-class="cal-row--ghost"
              drag-class="cal-row--dragging"
              @start="onDragStart"
              @end="onDragEnd"
            >
              <template #item="{ element }">
                <div
                  v-if="element.kind === 'match'"
                  class="cal-row"
                  :class="[
                    `state--${displayState(element.data as Match)}`,
                    {
                      'no-drag': (element.data as Match).status !== 'SCHEDULED',
                      'is-foreign': isForeign(element.data as Match),
                    },
                    punctualityClass((element.data as Match).id),
                  ]"
                  role="button"
                  tabindex="0"
                  @click="openMatchPanel(element.data as Match)"
                  @keydown.enter="openMatchPanel(element.data as Match)"
                >
                  <span class="cal-time">
                    {{ computedETAs.get(`m-${element.data.id}`) ?? '—' }}
                  </span>
                  <span
                    class="cal-dot"
                    :class="`dot--${displayState(element.data as Match)}`"
                    :title="stateLabel(displayState(element.data as Match))"
                  />
                  <span class="poule-pill">{{ stagePillLabel(element.data as Match) }}</span>
                  <span v-if="multiEvent" class="cal-event-tag">{{ eventName((element.data as Match).eventId) }}</span>
                  <span class="cal-players">
                    {{ playerLabel(element.data as Match, 'A') }} <em class="vs">vs</em> {{ playerLabel(element.data as Match, 'B') }}
                  </span>
                  <span class="cal-badges">
                    <button
                      v-if="(element.data as Match).status === 'SCHEDULED'"
                      class="row-start-btn"
                      type="button"
                      :disabled="starting[element.data.id]"
                      @click.stop="startMatch(element.data.id)"
                    >
                      {{ starting[element.data.id] ? 'Démarrage…' : 'Démarrer' }}
                    </button>
                    <span
                      v-if="restWarnings.has(element.data.id)"
                      class="rest-warning"
                      title="Repos insuffisant — ce joueur joue deux matchs consécutifs"
                    >⚠</span>
                    <span
                      v-if="(element.data as Match).isWalkover"
                      class="walkover-badge"
                      title="Victoire par forfait"
                    >FORFAIT</span>
                    <span
                      v-if="(element.data as Match).isFeatured"
                      class="featured-badge"
                      title="Match mis en avant sur la TV"
                    >★ EN AVANT</span>
                    <button
                      class="row-poster-btn"
                      type="button"
                      title="Voir / générer l'affiche de ce match"
                      @click.stop="openMatchPanel(element.data as Match, 'poster')"
                    >
                      <span v-if="(element.data as Match).posterUrl">Affiche</span>
                      <span v-else>+ Affiche</span>
                    </button>
                  </span>
                  <span
                    v-if="(element.data as Match).status === 'SCHEDULED'"
                    class="drag-handle"
                  >⋮⋮</span>
                </div>
                <div v-else class="cal-row cal-row--break">
                  <span class="cal-time">{{ computedETAs.get(`b-${element.data.id}`) ?? '—' }}</span>
                  <span class="break-icon">⏸</span>
                  <span class="break-label">
                    {{ (element.data as Break).label || 'Pause' }} · {{ (element.data as Break).durationMin }} min
                  </span>
                  <button
                    class="break-delete-btn"
                    type="button"
                    :disabled="deletingBreak[element.data.id]"
                    :title="deletingBreak[element.data.id] ? 'Suppression…' : 'Supprimer la pause'"
                    @click.stop="deletePause(element.data.id)"
                  >×</button>
                  <span class="drag-handle">⋮⋮</span>
                </div>
              </template>
            </draggable>
            <div
              v-if="(dayItemsDnd[day.id] ?? []).length === 0"
              class="pd-empty"
            >Glissez un match ici</div>
          </div>

          <!-- Action pause -->
          <button
            v-if="!collapsedDays[day.id]"
            class="add-pause-btn"
            type="button"
            :disabled="addingPause[day.id]"
            @click="addPause(day.id)"
          >
            {{ addingPause[day.id] ? 'Ajout…' : '+ pause' }}
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
        <div class="legend-item"><span class="walkover-badge" style="font-size:9px;padding:1px 5px">FORFAIT</span> Walkover</div>
        <div class="legend-item"><span class="rest-warning">⚠</span> Repos insuffisant</div>
        <div class="legend-item"><span class="legend-swatch legend-swatch--red" /> En retard</div>
        <div class="legend-item"><span class="legend-swatch legend-swatch--orange" /> Démarré en retard</div>
        <div class="legend-item"><span class="legend-swatch legend-swatch--green" /> À l'heure</div>
      </footer>
    </template>
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

/* ── Colonne Annulés (lecture seule) ─────────────────────────────────────── */
.cal-canceled { border-right: 1px solid var(--line-1); }
.pile-card--readonly { opacity: 0.7; }

.canceled-badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--danger, #e5484d);
  border: 1px solid var(--danger, #e5484d);
  padding: 2px 7px;
  border-radius: 99px;
  white-space: nowrap;
  flex-shrink: 0;
}

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

.cal-empty-link {
  background: none;
  border: none;
  padding: 0;
  font-size: inherit;
  color: var(--accent);
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  text-decoration: underline;
}

/* ── Journée (PlayDay) ───────────────────────────────────────────────────── */
.play-day {
  border: 1px solid var(--line-1);
  border-radius: var(--r-lg);
}

.pd-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  background: var(--bg-3);
  border-bottom: 1px solid var(--line-1);
  border-radius: var(--r-lg) var(--r-lg) 0 0;
  flex-wrap: wrap;
  cursor: pointer;
}

.pd-chevron {
  font-size: 12px;
  color: var(--ink-3);
  flex-shrink: 0;
  transition: transform 150ms;
  transform: rotate(0deg);
}

.pd-chevron--collapsed { transform: rotate(-90deg); }

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

.pd-start-trigger {
  background: none;
  border: none;
  padding: 0;
  font: inherit;
  color: inherit;
  text-decoration: underline dotted;
  cursor: pointer;
}
.pd-start-trigger:hover { color: var(--accent); }
.pd-start-edit { display: inline-flex; align-items: center; gap: 4px; }
.pd-start-input { padding: 1px 4px; font-size: inherit; }
.pd-start-error { color: var(--danger); font-size: 11px; margin-left: 4px; }

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

.pd-rows { display: flex; flex-direction: column; position: relative; }

/* Zone de dépôt toujours présente, même journée vide (cible DnD pile → journée) */
.pd-droparea { min-height: 44px; }

.pd-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px 18px;
  font-size: 13px;
  color: var(--ink-4);
  pointer-events: none; /* laisse passer le drop vers le draggable en dessous */
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

.cal-row.punct--red    { background: var(--danger-soft, rgba(255,48,82,0.14)); }
.cal-row.punct--orange { background: rgba(229,124,0,0.12); }
.cal-row.punct--green  { background: rgba(34,226,127,0.10); }

.cal-row--break {
  grid-template-columns: 64px 16px 1fr 28px 20px;
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

.cal-badges {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.rest-warning {
  font-size: 13px;
  color: var(--warning, #e57c00);
  line-height: 1;
}

.walkover-badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--warning, #e57c00);
  border: 1px solid var(--warning, #e57c00);
  padding: 2px 7px;
  border-radius: 99px;
  white-space: nowrap;
  flex-shrink: 0;
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

.row-start-btn {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #000;
  background: var(--accent);
  border: 1px solid var(--accent);
  padding: 3px 10px;
  border-radius: var(--r-xs);
  white-space: nowrap;
  flex-shrink: 0;
  cursor: pointer;
  font-family: inherit;
  transition: opacity 150ms;
}

.row-start-btn:hover { opacity: 0.9; }
.row-start-btn:disabled { opacity: 0.45; cursor: not-allowed; }

.row-poster-btn {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--ink-2);
  background: var(--bg-4);
  border: 1px solid var(--line-2);
  padding: 3px 10px;
  border-radius: var(--r-xs);
  white-space: nowrap;
  flex-shrink: 0;
  cursor: pointer;
  font-family: inherit;
  transition: opacity 150ms, background 150ms;
}
.row-poster-btn:hover { background: var(--bg-3); }

.drag-handle {
  font-size: 14px;
  color: var(--ink-4);
  cursor: grab;
  user-select: none;
  flex-shrink: 0;
}

/* États DnD */
.cal-row--ghost { opacity: 0.35; background: var(--accent-soft); }
.cal-row--dragging { opacity: 0.9; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }

/* Break */
.break-icon { font-size: 14px; color: var(--ink-3); }
.break-label { font-size: 13px; color: var(--ink-2); }

.break-delete-btn {
  background: none;
  border: none;
  font-size: 14px;
  color: var(--ink-3);
  cursor: pointer;
  padding: 2px 4px;
  border-radius: var(--r-xs);
  line-height: 1;
  transition: color 100ms, background 100ms;
}

.break-delete-btn:hover { color: var(--danger); background: var(--danger-soft); }
.break-delete-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* Bouton pause */
.add-pause-btn {
  display: block;
  width: 100%;
  padding: 9px;
  background: none;
  border: none;
  border-top: 1px dashed var(--line-2);
  border-radius: 0 0 var(--r-lg) var(--r-lg);
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-3);
  cursor: pointer;
  font-family: inherit;
  text-align: center;
  letter-spacing: 0.04em;
  transition: color 100ms, background 100ms;
}

.add-pause-btn:hover { color: var(--ink-1); background: var(--bg-3); }
.add-pause-btn:disabled { opacity: 0.5; cursor: not-allowed; }

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

.legend-swatch {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

.legend-swatch--red    { background: var(--danger); }
.legend-swatch--orange { background: #e57c00; }
.legend-swatch--green  { background: var(--success); }

/* ── Mise en évidence de l'épreuve active ────────────────────────────────── */
/* Les matchs des autres épreuves restent visibles et déplaçables (le
   calendrier couvre toute l'édition), mais sont atténués. */
.cal-row.is-foreign,
.pile-card.is-foreign { opacity: 0.55; }
.cal-row.is-foreign:hover,
.pile-card.is-foreign:hover { opacity: 1; }

.pile-group-ev {
  font-weight: 600;
  color: var(--ink-4);
  text-transform: none;
  letter-spacing: 0;
}

.cal-event-tag {
  font-size: 10px;
  font-weight: 600;
  color: var(--ink-3);
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  padding: 1px 6px;
  border-radius: 99px;
  white-space: nowrap;
  flex-shrink: 0;
}
</style>
