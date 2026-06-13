import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'
import type { Edition, Event, Entry, Group, KanbanData, Bracket, Player, Category, Court, CategoryMode } from '@/types'

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
  const kanban = ref<KanbanData | null>(null)
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
    groups.value = await get<Group[]>(`/api/events/${id}/groups/`)
  }

  async function fetchMatches(eventId?: number) {
    const id = eventId ?? activeEventId.value
    if (!id) return
    kanban.value = await get<KanbanData>(`/api/events/${id}/matches/`)
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
    allPlayers, players, groups, kanban, bracket,
    categories, courts,
    // Fetch
    fetchEditions, fetchAllPlayers, fetchPlayers, fetchGroups, fetchMatches, fetchBracket,
    fetchCategories, fetchCourts,
    // Mutations — P2 inscriptions
    editPlayer, createTeam, addRegistration, addRegistrationsBulk, removeRegistration,
    // Mutations — P3 poules
    assignGroup, createGroup, autofillGroups, generateMatches,
    // Mutations — P4 planning
    editMatch, reorderMatches, featureMatch,
    // Mutations — P7 bracket
    createBracket, updateBracketLabels, assignBracket, clearBracket,
    // Mutations — P9 configuration
    createEdition, editEdition, activateEdition, deleteEdition,
    createCategory, editCategory, deleteCategory,
    createCourt, editCourt, deleteCourt,
    createEvent, editEvent, deleteEvent,
  }
})
