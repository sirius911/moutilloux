import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'
import type { ScoreState, Match, PlayDay, TvUpcoming } from '@/types'

export const useLiveStore = defineStore('live', () => {
  const { get } = useApi()

  const hero = ref<Match | null>(null)
  const next = ref<Match | null>(null)
  const now = ref<string>('')
  const editionYear = ref<number | null>(null)

  const upcoming = ref<Match[]>([])
  const currentPlayDay = ref<PlayDay | null>(null)

  // Match unique (écran arbitre) — polling de /api/matches/<id>/
  const match = ref<Match | null>(null)

  async function fetchScoreState() {
    const data = await get<ScoreState>('/api/score_state/')
    hero.value = data.hero
    next.value = data.next
    now.value = data.now
    editionYear.value = data.editionYear
  }

  async function fetchUpcoming(n = 5) {
    const data = await get<TvUpcoming>(`/api/tv/upcoming/?n=${n}`)
    upcoming.value = data.upcoming
    currentPlayDay.value = data.currentPlayDay
    if (data.next) next.value = data.next
  }

  async function fetchMatch(matchId: number | string) {
    const data = await get<{ match: Match }>(`/api/matches/${matchId}/`)
    match.value = data.match
  }

  return { hero, next, now, editionYear, upcoming, currentPlayDay, match, fetchScoreState, fetchUpcoming, fetchMatch }
})
