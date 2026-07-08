import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'
import type { Edition, Event, Entry, Group, KanbanData, Bracket, Player, Category, Court, CategoryMode, CalendarData, PlayDay, Break } from '@/types'

export interface PlayerEditPayload {
  first_name?: string
  last_name?: string
  gender?: 'M' | 'F' | 'O'
  birth_year?: number
  phone?: string
  email?: string
  license_number?: string
}

export interface MatchEditPayload {
  status?: string
  scheduled_time?: string | null
  court?: string | null
  server?: 'A' | 'B' | null
  sets_a?: number
  sets_b?: number
  games_a?: number
  games_b?: number
  tb_active?: boolean
  tb_points_a?: number
  tb_points_b?: number
  winner_side?: 'A' | 'B' | null
}

// ── Payloads Phase 9 (configuration) — clés snake_case attendues par l'API ──
export interface EditionPayload {
  name?: string
  year?: number
  start_dt?: string | null
  end_dt?: string | null
  activate?: boolean
}

export interface CategoryPayload {
  name?: string
  mode?: CategoryMode
}

export interface EventConfigPayload {
  category_id?: number
  group_size_default?: number
  qualified_per_group?: number
  notes?: string
}

// ── Payloads Sprint 12 (ajustements en cours de jeu) ─────────────────────────

export interface AddLateEntryPayload {
  group_id: number
  player?: number
  team?: number
}

export interface ReplacePlayerPayload {
  player?: number
  team?: number
}

// ── Payloads Sprint 08 (calendrier) ──────────────────────────────────────────

export interface PlayDayPayload {
  date: string
  startTime: string
  targetEndTime: string
}

export interface BreakCreatePayload {
  durationMin: number
  label?: string
  orderIndex?: number
}

export interface BreakEditPayload {
  durationMin?: number
  label?: string
  orderIndex?: number
}

export interface CalendarReorderItem {
  type: 'match' | 'break'
  id: number
}

export interface CalendarReorderPayload {
  playDays: Array<{ playDayId: number; items: CalendarReorderItem[] }>
}

export const useEventStore = defineStore('event', () => {
  const { get, post } = useApi()

  // ── Sélection active ───────────────────────────────────────────────────
  const activeEdition = ref<Edition | null>(null)
  const editions = ref<Edition[]>([])
  const events = ref<Event[]>([])
  const activeEventId = ref<number | null>(null)

  // ── Données de l'événement actif ──────────────────────────────────────
  const allPlayers = ref<Player[]>([])
  const players = ref<Entry[]>([])
  const groups = ref<Group[]>([])
  const groupsLocked = ref(false)
  const kanban = ref<KanbanData | null>(null)
  const calendar = ref<CalendarData | null>(null)
  const bracket = ref<Bracket | null>(null)

  // ── Référentiels de configuration (Phase 9) ───────────────────────────
  const categories = ref<Category[]>([])
  const courts = ref<Court[]>([])

  // ── Fetch ──────────────────────────────────────────────────────────────

  async function fetchEditions() {
    const data = await get<{ activeEdition: Edition | null; events: Event[]; editions: Edition[] }>('/api/editions/')
    activeEdition.value = data.activeEdition
    events.value = data.events
    editions.value = data.editions ?? []
    if (!activeEventId.value && data.events.length > 0) {
      activeEventId.value = data.events[0].id
    }
  }

  async function fetchCategories() {
    categories.value = await get<Category[]>('/api/categories/')
  }

  async function fetchCourts() {
    courts.value = await get<Court[]>('/api/courts/')
  }

  async function fetchAllPlayers() {
    allPlayers.value = await get<Player[]>('/api/players/')
  }

  async function fetchPlayers(eventId?: number) {
    const id = eventId ?? activeEventId.value
    if (!id) return
    players.value = await get<Entry[]>(`/api/events/${id}/players/`)
  }

  async function fetchGroups(eventId?: number) {
    const id = eventId ?? activeEventId.value
    if (!id) return
    const data = await get<{ locked: boolean; groups: Group[] }>(`/api/events/${id}/groups/`)
    groups.value = data.groups
    groupsLocked.value = data.locked
  }

  async function fetchMatches(eventId?: number) {
    const id = eventId ?? activeEventId.value
    if (!id) return
    kanban.value = await get<KanbanData>(`/api/events/${id}/matches/`)
  }

  async function fetchCalendar(editionId?: number) {
    const id = editionId ?? activeEdition.value?.id
    if (!id) return
    calendar.value = await get<CalendarData>(`/api/editions/${id}/calendar/`)
  }

  async function fetchBracket(eventId?: number) {
    const id = eventId ?? activeEventId.value
    if (!id) return
    bracket.value = await get<Bracket>(`/api/events/${id}/bracket/`)
  }

  // ── Mutations — Phase 2 (inscriptions) ────────────────────────────────

  async function editPlayer(playerId: number, payload: PlayerEditPayload) {
    await post(`/api/players/${playerId}/edit/`, payload)
    await fetchAllPlayers()
  }

  async function createTeam(
    eventId: number,
    player1: number,
    player2: number,
    name?: string,
  ) {
    await post(`/api/events/${eventId}/teams/create/`, { player1, player2, name })
    await fetchPlayers(eventId)
  }

  async function addRegistration(eventId: number, playerId: number) {
    await post(`/api/events/${eventId}/registrations/add/`, { player: playerId })
    await fetchPlayers(eventId)
  }

  async function addRegistrationsBulk(eventId: number, playerIds: number[]) {
    const res = await post<{ created: Entry[]; skipped: number[] }>(
      `/api/events/${eventId}/registrations/add-bulk/`,
      { player_ids: playerIds },
    )
    await fetchPlayers(eventId)
    return res
  }

  async function removeRegistration(eventId: number, entryId: number) {
    await post(`/api/events/${eventId}/registrations/${entryId}/remove/`, {})
    await fetchPlayers(eventId)
  }

  // ── Mutations (réutilisent les endpoints admin existants) ─────────────

  async function assignGroup(eventId: number, entryId: number, groupId: number | null) {
    if (groupId === null) {
      await post(`/api/events/${eventId}/groups/unassign/`, { entry_id: entryId })
    } else {
      await post(`/api/events/${eventId}/groups/assign/`, { entry_id: entryId, group_id: groupId })
    }
    await fetchGroups(eventId)
    await fetchPlayers(eventId)
  }

  async function createGroup(eventId: number, name: string) {
    await post(`/api/events/${eventId}/groups/create/`, { name })
    await fetchGroups(eventId)
  }

  async function autofillGroups(
    eventId: number,
    shuffle: boolean,
    groupSize: 3 | 4,
    numGroups?: number,
  ) {
    await post(`/api/events/${eventId}/groups/autofill/`, {
      shuffle,
      group_size: groupSize,
      num_groups: numGroups,
    })
    await fetchGroups(eventId)
    await fetchPlayers(eventId)
  }

  async function generateMatches(eventId: number) {
    await post(`/api/events/${eventId}/matches/generate/`, {})
    await fetchMatches(eventId)
    await fetchGroups(eventId)
  }

  async function editMatch(eventId: number, matchId: number, payload: MatchEditPayload) {
    await post(`/api/matches/${matchId}/edit/`, payload)
    await fetchMatches(eventId)
  }

  async function reorderMatches(eventId: number, orderedIds: number[]) {
    await post(`/api/events/${eventId}/matches/reorder/`, { queue: orderedIds })
    await fetchMatches(eventId)
  }

  async function featureMatch(eventId: number, matchId: number) {
    await post(`/api/matches/${matchId}/feature/`, {})
    await fetchMatches(eventId)
  }

  // ── Mutations — Sprint 08 (calendrier) ────────────────────────────────

  async function createPlayDay(editionId: number, payload: PlayDayPayload) {
    await post(`/api/editions/${editionId}/play-days/create/`, payload)
    await fetchCalendar(editionId)
  }

  async function updatePlayDay(playDayId: number, payload: Partial<PlayDayPayload>) {
    const editionId = activeEdition.value?.id
    await post(`/api/play-days/${playDayId}/edit/`, payload)
    await fetchCalendar(editionId)
  }

  async function deletePlayDay(playDayId: number) {
    const editionId = activeEdition.value?.id
    await post(`/api/play-days/${playDayId}/delete/`, {})
    await fetchCalendar(editionId)
  }

  async function createBreak(playDayId: number, payload: BreakCreatePayload) {
    const editionId = activeEdition.value?.id
    await post(`/api/play-days/${playDayId}/breaks/create/`, payload)
    await fetchCalendar(editionId)
  }

  async function updateBreak(breakId: number, payload: BreakEditPayload) {
    const editionId = activeEdition.value?.id
    await post(`/api/breaks/${breakId}/edit/`, payload)
    await fetchCalendar(editionId)
  }

  async function deleteBreak(breakId: number) {
    const editionId = activeEdition.value?.id
    await post(`/api/breaks/${breakId}/delete/`, {})
    await fetchCalendar(editionId)
  }

  async function reorderCalendar(editionId: number, payload: CalendarReorderPayload) {
    await post(`/api/editions/${editionId}/calendar/reorder/`, payload)
    await fetchCalendar(editionId)
  }

  async function autoArrangeMatches(eventId: number) {
    const editionId = activeEdition.value?.id
    const result = await post<{ placed: number }>(`/api/events/${eventId}/matches/auto-arrange/`, {})
    await fetchCalendar(editionId)
    return result
  }

  // ── Mutations — Phase 7 (bracket) ─────────────────────────────────────

  async function createBracket(
    eventId: number,
    startStage: 'QF' | 'SF' | 'F',
    force = false,
  ) {
    // L'endpoint renvoie la structure du bracket : on l'applique directement.
    bracket.value = await post<Bracket>(`/api/events/${eventId}/bracket/create/`, {
      start_stage: startStage,
      force,
    })
  }

  async function updateBracketLabels(
    eventId: number,
    matchId: number,
    sideALabel: string,
    sideBLabel: string,
  ) {
    await post(`/api/matches/${matchId}/bracket-labels/`, {
      side_a_label: sideALabel,
      side_b_label: sideBLabel,
    })
    await fetchBracket(eventId)
  }

  // assign / clear : réutilisent les endpoints JSON déjà exposés par le panel admin.
  async function assignBracket(eventId: number, matchId: number, side: 'A' | 'B', entryId: number) {
    await post(`/api/events/${eventId}/bracket/assign/`, { match_id: matchId, entry_id: entryId, side })
    await fetchBracket(eventId)
  }

  async function clearBracket(eventId: number, matchId: number, side: 'A' | 'B') {
    await post(`/api/events/${eventId}/bracket/clear/`, { match_id: matchId, side })
    await fetchBracket(eventId)
  }

  // ── Mutations — Sprint 11 (cycle de vie) ──────────────────────────────

  async function startEvent(eventId: number) {
    await post(`/api/events/${eventId}/start/`, {})
    await fetchEditions()
    if (activeEventId.value === eventId) await fetchGroups(eventId)
  }

  async function closeEvent(eventId: number) {
    await post(`/api/events/${eventId}/close/`, {})
    await fetchEditions()
  }

  async function reopenEvent(eventId: number) {
    await post(`/api/events/${eventId}/reopen/`, {})
    await fetchEditions()
  }

  // ── Mutations — Sprint 12 (ajustements en cours de jeu) ──────────────

  async function withdrawEntry(entryId: number) {
    await post(`/api/entries/${entryId}/withdraw/`, {})
    const id = activeEventId.value
    if (!id) return
    await fetchGroups(id)
    await fetchPlayers(id)
    await fetchMatches(id)
    await fetchBracket(id)
  }

  async function addLateEntry(eventId: number, payload: AddLateEntryPayload) {
    await post(`/api/events/${eventId}/entries/late/`, payload)
    await fetchGroups(eventId)
    await fetchPlayers(eventId)
  }

  async function replacePlayer(entryId: number, payload: ReplacePlayerPayload) {
    await post(`/api/entries/${entryId}/replace/`, payload)
    const id = activeEventId.value
    if (!id) return
    await fetchPlayers(id)
    await fetchGroups(id)
  }

  // ── Mutations — Phase 9 (configuration) ───────────────────────────────
  // Éditions, catégories, courts, épreuves. Chaque action recâble vers le ref
  // concerné (fetchEditions rafraîchit aussi events + compteurs d'épreuves).

  async function createEdition(payload: EditionPayload) {
    await post('/api/editions/create/', payload)
    await fetchEditions()
  }

  async function editEdition(id: number, payload: EditionPayload) {
    await post(`/api/editions/${id}/edit/`, payload)
    await fetchEditions()
  }

  async function activateEdition(id: number) {
    await post(`/api/editions/${id}/activate/`, {})
    await fetchEditions()
  }

  async function deleteEdition(id: number) {
    await post(`/api/editions/${id}/delete/`, {})
    await fetchEditions()
  }

  async function createCategory(payload: CategoryPayload): Promise<Category> {
    const created = await post<Category>('/api/categories/create/', payload)
    await fetchCategories()
    return created
  }

  async function editCategory(id: number, payload: CategoryPayload) {
    await post(`/api/categories/${id}/edit/`, payload)
    await fetchCategories()
  }

  async function deleteCategory(id: number) {
    await post(`/api/categories/${id}/delete/`, {})
    await fetchCategories()
  }

  async function createCourt(name: string) {
    await post('/api/courts/create/', { name })
    await fetchCourts()
  }

  async function editCourt(id: number, name: string) {
    await post(`/api/courts/${id}/edit/`, { name })
    await fetchCourts()
  }

  async function deleteCourt(id: number) {
    await post(`/api/courts/${id}/delete/`, {})
    await fetchCourts()
  }

  async function createEvent(editionId: number, payload: EventConfigPayload) {
    await post(`/api/editions/${editionId}/events/create/`, payload)
    await fetchEditions()
  }

  async function editEvent(eventId: number, payload: EventConfigPayload) {
    await post(`/api/events/${eventId}/edit/`, payload)
    await fetchEditions()
  }

  async function deleteEvent(eventId: number) {
    await post(`/api/events/${eventId}/delete/`, {})
    await fetchEditions()
  }

  return {
    // State
    activeEdition, editions, events, activeEventId,
    allPlayers, players, groups, groupsLocked, kanban, calendar, bracket,
    categories, courts,
    // Fetch
    fetchEditions, fetchAllPlayers, fetchPlayers, fetchGroups, fetchMatches, fetchCalendar, fetchBracket,
    fetchCategories, fetchCourts,
    // Mutations — P2 inscriptions
    editPlayer, createTeam, addRegistration, addRegistrationsBulk, removeRegistration,
    // Mutations — P3 poules
    assignGroup, createGroup, autofillGroups, generateMatches,
    // Mutations — P4 planning
    editMatch, reorderMatches, featureMatch,
    // Mutations — Sprint 08 calendrier
    createPlayDay, updatePlayDay, deletePlayDay,
    createBreak, updateBreak, deleteBreak,
    reorderCalendar, autoArrangeMatches,
    // Mutations — P7 bracket
    createBracket, updateBracketLabels, assignBracket, clearBracket,
    // Mutations — Sprint 11 cycle de vie
    startEvent, closeEvent, reopenEvent,
    // Mutations — Sprint 12 ajustements en cours de jeu
    withdrawEntry, addLateEntry, replacePlayer,
    // Mutations — P9 configuration
    createEdition, editEdition, activateEdition, deleteEdition,
    createCategory, editCategory, deleteCategory,
    createCourt, editCourt, deleteCourt,
    createEvent, editEvent, deleteEvent,
  }
})
