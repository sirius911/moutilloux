import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'
import type { Match, TvState, TvStake, TvIdleData, TvStats, TvEvent, TvProgramme, TvAnnouncement } from '@/types'

export const useLiveStore = defineStore('live', () => {
  const { get } = useApi()

  // État chaud (GET /api/tv/state/) — seul écrivain de `next`
  const hero = ref<Match | null>(null)
  const next = ref<Match | null>(null)
  const now = ref<string>('')
  const editionYear = ref<number | null>(null)
  const stake = ref<TvStake | null>(null)

  // Contenu froid du carousel (GET /api/tv/idle/)
  const stats = ref<TvStats | null>(null)
  const recentResults = ref<Match[]>([])
  const events = ref<TvEvent[]>([])
  const programme = ref<TvProgramme>({ day: 'finished', playDay: null, upcoming: [] })
  const announcements = ref<TvAnnouncement[]>([])

  // Match unique (écran arbitre) — polling de /api/matches/<id>/
  const match = ref<Match | null>(null)

  async function fetchTvState() {
    const data = await get<TvState>('/api/tv/state/')
    hero.value = data.hero
    next.value = data.next
    now.value = data.now
    editionYear.value = data.editionYear
    stake.value = data.stake
  }

  async function fetchTvIdle() {
    const data = await get<TvIdleData>('/api/tv/idle/')
    stats.value = data.stats
    recentResults.value = data.recentResults
    events.value = data.events
    programme.value = data.programme
    announcements.value = data.announcements
  }

  async function fetchMatch(matchId: number | string) {
    const data = await get<{ match: Match }>(`/api/matches/${matchId}/`)
    match.value = data.match
  }

  return {
    hero, next, now, editionYear, stake,
    stats, recentResults, events, programme, announcements,
    match, fetchTvState, fetchTvIdle, fetchMatch,
  }
})
