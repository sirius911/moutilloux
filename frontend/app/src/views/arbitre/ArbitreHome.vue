<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePolling } from '@/composables/usePolling'
import { useApi } from '@/composables/useApi'
import type { ArbitreProgramme, Match, Break, CalendarDay } from '@/types'

// ── Type union local (fusion match + pause, lecture seule) ─────────────────
type DayItem =
  | { kind: 'match'; data: Match }
  | { kind: 'break'; data: Break }

const router = useRouter()
const authStore = useAuthStore()
const { get } = useApi()

const programme = ref<ArbitreProgramme>({ playDays: [], next: null })
const syncTime = ref('')

// ── État replié/déplié par journée ──────────────────────────────────────────
const expandedDays = ref<Set<number>>(new Set())
const seenDayIds = new Set<number>()
let initialized = false

function updateClock() {
  const now = new Date()
  syncTime.value = now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function toggleDay(id: number) {
  const next = new Set(expandedDays.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  expandedDays.value = next
}

usePolling(async () => {
  programme.value = await get<ArbitreProgramme>('/api/arbitre/matches/')
  updateClock()

  const currentLiveDayId = programme.value.playDays.find(
    (day) => day.matches.some((m) => m.status === 'LIVE'),
  )?.id

  if (!initialized) {
    const next = new Set<number>()
    for (const day of programme.value.playDays) {
      if (isToday(day.date) || day.id === currentLiveDayId) next.add(day.id)
      seenDayIds.add(day.id)
    }
    expandedDays.value = next
    initialized = true
    return
  }

  // Nouvelles journées jamais vues : auto-expand si aujourd'hui ou LIVE.
  let changed = false
  const next = new Set(expandedDays.value)
  for (const day of programme.value.playDays) {
    if (seenDayIds.has(day.id)) continue
    seenDayIds.add(day.id)
    if (isToday(day.date) || day.id === currentLiveDayId) {
      next.add(day.id)
      changed = true
    }
  }
  if (changed) expandedDays.value = next
}, 5000)

// ── Données dérivées ────────────────────────────────────────────────────────

const allMatches = computed(() => programme.value.playDays.flatMap((d) => d.matches))
const liveCount = computed(() => allMatches.value.filter((m) => m.status === 'LIVE').length)
const liveMatch = computed(() => allMatches.value.find((m) => m.status === 'LIVE') ?? null)
const nextMatch = computed(() => programme.value.next)
const heroMatch = computed(() => liveMatch.value ?? nextMatch.value)
const heroKind = computed(() => (liveMatch.value ? 'live' : 'next'))

function mergeItems(day: CalendarDay): DayItem[] {
  const matchItems: DayItem[] = day.matches.map((m) => ({ kind: 'match', data: m }))
  const breakItems: DayItem[] = day.breaks.map((b) => ({ kind: 'break', data: b }))
  return [...matchItems, ...breakItems].sort((a, b) => {
    const ao = a.kind === 'match' ? (a.data.orderIndex ?? 99999) : a.data.orderIndex
    const bo = b.kind === 'match' ? (b.data.orderIndex ?? 99999) : b.data.orderIndex
    return ao - bo
  })
}

const dayGroups = computed(() =>
  programme.value.playDays.map((day) => ({ day, items: mergeItems(day) })),
)

// Compare `dateStr` (YYYY-MM-DD) à la date locale du jour — construction
// locale, pas UTC/`toISOString` (cohérent avec AdminMatches.vue).
function isToday(dateStr: string): boolean {
  const now = new Date()
  const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  return dateStr === todayStr
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })
}

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}

function goLabel(status: string): string {
  if (status === 'LIVE')     return 'Reprendre'
  if (status === 'FINISHED') return 'Voir'
  return 'Démarrer'
}

function stripeColor(status: string): string {
  if (status === 'LIVE') return 'var(--accent)'
  if (status === 'FINISHED') return 'var(--ink-4)'
  return 'var(--ink-3)'
}

function playerName(m: Match, side: 'A' | 'B'): string {
  if (side === 'A') return m.sideA?.player?.fullName ?? m.sideALabel ?? 'TBD'
  return m.sideB?.player?.fullName ?? m.sideBLabel ?? 'TBD'
}

function scoreDisplay(m: Match): string {
  const sets = m.setScores?.map(s => `${s.a}-${s.b}`).join(' ') ?? ''
  const current = m.status === 'LIVE' ? ` (${m.gamesA}-${m.gamesB})` : ''
  return (sets + current).trim()
}

function endReasonLabel(m: Match): string {
  if (m.status !== 'FINISHED') return ''
  if (m.endReason === 'WALKOVER') return 'Forfait'
  if (m.endReason === 'RETIREMENT') return 'Abandon'
  return ''
}

// Puce d'état visuelle par ligne : NEXT est purement d'affichage (le statut
// réel du match reste SCHEDULED) et ne remplace jamais la pastille LIVE.
function rowStatusLabel(m: Match, isNext: boolean): string {
  if (m.status === 'LIVE') return 'EN DIRECT'
  if (isNext) return 'NEXT'
  if (m.status === 'FINISHED') return 'TERMINÉ'
  return 'PRÉVU'
}

function rowStatusClass(m: Match, isNext: boolean): string {
  if (m.status === 'LIVE') return 'live'
  if (isNext) return 'next'
  if (m.status === 'FINISHED') return 'finished'
  return 'scheduled'
}

function formatIsoTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }).replace(':', 'h')
}

// ETA simplifiée V1 (cf. plan #311) : scheduledTime est une donnée figée
// renvoyée par le backend (position planifiée), pas recalculée dynamiquement
// en cas de retard (contrairement au moteur ETA de AdminMatches.vue).
function matchTimeLabel(m: Match): string {
  if (m.status === 'FINISHED') {
    const iso = m.startedAt ?? m.finishedAt
    return iso ? formatIsoTime(iso) : (m.scheduledTime ? `~${m.scheduledTime}` : '—')
  }
  return m.scheduledTime ? `~${m.scheduledTime}` : '—'
}
</script>

<template>
  <div class="arh">
    <div class="arh-bg" />

    <!-- Header -->
    <header class="arh-header">
      <div class="arh-greeting">
        <div class="arh-greeting-hi">
          Bonjour {{ authStore.user?.username ?? 'Arbitre' }},
        </div>
        <div class="arh-greeting-sub">
          Vous êtes l'arbitre désigné · {{ liveCount }} match{{ liveCount > 1 ? 's' : '' }} en cours
        </div>
      </div>
      <button class="arh-logout" type="button" @click="handleLogout">
        <svg viewBox="0 0 24 24" width="16" height="16">
          <path d="M15 4h3a2 2 0 012 2v12a2 2 0 01-2 2h-3M10 17l5-5-5-5M3 12h12" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </header>

    <!-- Bloc « À l'instant » -->
    <div v-if="heroMatch" class="arh-hero">
      <div :class="['arh-hero-card', `arh-hero-card-${heroKind}`]">
        <span class="arh-hero-label">
          <i v-if="heroKind === 'live'" class="arh-live-dot" />
          {{ heroKind === 'live' ? 'En direct' : 'Prochain match' }}
        </span>

        <div class="arh-hero-players">
          <span>{{ playerName(heroMatch, 'A') }}</span>
          <em>vs</em>
          <span>{{ playerName(heroMatch, 'B') }}</span>
        </div>

        <div class="arh-hero-meta">
          <span class="arh-hero-stage">{{ heroMatch.stageLabel }}</span>
          <span v-if="heroKind === 'live' && scoreDisplay(heroMatch)" class="arh-hero-score tab">
            {{ scoreDisplay(heroMatch) }}
          </span>
          <span v-else-if="heroKind === 'next'" class="arh-hero-time tab">
            {{ matchTimeLabel(heroMatch) }}
          </span>
        </div>

        <button
          class="arh-hero-action"
          type="button"
          @click="router.push(`/arbitre/${heroMatch.id}`)"
        >
          {{ heroKind === 'live' ? 'Reprendre' : 'Démarrer' }}
          <svg viewBox="0 0 24 24" width="16" height="16">
            <path d="M5 12h14m0 0l-5-5m5 5l-5 5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Journées -->
    <div class="arh-days">
      <p v-if="programme.playDays.length === 0" class="arh-empty">Aucun programme pour le moment.</p>

      <section
        v-for="{ day, items } in dayGroups"
        :key="day.id"
        class="arh-day"
      >
        <header
          :class="['arh-day-header', { 'is-today': isToday(day.date) }]"
          @click="toggleDay(day.id)"
        >
          <div class="arh-day-header-left">
            <span class="arh-day-date">{{ formatDate(day.date) }}</span>
            <span class="arh-day-count">{{ day.matches.length }} match{{ day.matches.length !== 1 ? 's' : '' }}</span>
          </div>
          <div class="arh-day-header-right">
            <span class="arh-day-start">début {{ day.startTime }}</span>
            <span :class="['arh-day-chevron', { open: expandedDays.has(day.id) }]">
              <svg viewBox="0 0 24 24" width="16" height="16">
                <path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </div>
        </header>

        <div v-show="expandedDays.has(day.id)" class="arh-day-body">
          <p v-if="items.length === 0" class="arh-day-empty">Aucun match ce jour-là.</p>

          <template v-for="item in items" :key="`${item.kind}-${item.data.id}`">
            <div v-if="item.kind === 'break'" class="arh-break-row">
              <span class="arh-break-icon">⏸</span>
              <span class="arh-break-label">{{ item.data.label || 'Pause' }} · {{ item.data.durationMin }} min</span>
            </div>

            <button
              v-else
              :class="[
                'arh-match',
                `arh-match-${item.data.status.toLowerCase()}`,
                { 'arh-match-finished': item.data.status === 'FINISHED' },
              ]"
              type="button"
              @click="router.push(`/arbitre/${item.data.id}`)"
            >
              <div class="arh-match-stripe" :style="{ background: stripeColor(item.data.status) }" />

              <div class="arh-match-body">
                <div class="arh-match-top">
                  <span :class="['arh-match-status', rowStatusClass(item.data, item.data.id === programme.next?.id)]">
                    <i v-if="item.data.status === 'LIVE'" class="arh-live-dot" />
                    {{ rowStatusLabel(item.data, item.data.id === programme.next?.id) }}
                  </span>
                  <span class="arh-match-time tab">{{ matchTimeLabel(item.data) }}</span>
                  <span v-if="item.data.court" class="arh-match-court">{{ item.data.court }}</span>
                </div>

                <div class="arh-match-players">
                  <span>{{ playerName(item.data, 'A') }}</span>
                  <em>vs</em>
                  <span>{{ playerName(item.data, 'B') }}</span>
                </div>

                <div class="arh-match-bottom">
                  <span class="arh-match-event">{{ item.data.stageLabel }}</span>
                  <span v-if="item.data.status === 'LIVE' && scoreDisplay(item.data)" class="arh-match-score tab">
                    {{ scoreDisplay(item.data) }}
                  </span>
                  <span v-else-if="endReasonLabel(item.data)" class="arh-match-score">
                    {{ endReasonLabel(item.data) }}
                  </span>
                  <span class="arh-match-go">
                    {{ goLabel(item.data.status) }}
                    <svg viewBox="0 0 24 24" width="14" height="14">
                      <path d="M5 12h14m0 0l-5-5m5 5l-5 5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </span>
                </div>
              </div>
            </button>
          </template>
        </div>
      </section>
    </div>

    <!-- Footer -->
    <footer class="arh-foot">
      <i class="arh-foot-dot" />
      Synchronisé · {{ syncTime }}
    </footer>
  </div>
</template>

<style scoped>
.arh {
  min-height: 100vh;
  background: var(--bg-1);
  display: flex;
  flex-direction: column;
  position: relative;
}

.arh-bg {
  position: fixed;
  inset: 0;
  background: radial-gradient(ellipse 60% 40% at 50% 0%, rgba(255,200,61,0.06), transparent 60%);
  pointer-events: none;
}

/* Header */
.arh-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28px 32px 20px;
  border-bottom: 1px solid var(--line-1);
  flex-shrink: 0;
  position: relative;
}

.arh-greeting-hi {
  font-size: 22px;
  font-weight: 700;
  color: var(--ink-0);
  letter-spacing: -0.01em;
}

.arh-greeting-sub {
  font-size: 13px;
  color: var(--ink-3);
  margin-top: 4px;
}

.arh-logout {
  width: 40px;
  height: 40px;
  border-radius: var(--r-md);
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  color: var(--ink-2);
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  transition: background 150ms;
}

.arh-logout:hover { background: var(--bg-4); color: var(--ink-0); }

/* Bloc « À l'instant » */
.arh-hero {
  padding: 20px 32px 4px;
  flex-shrink: 0;
}

.arh-hero-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 22px 26px;
  background: var(--bg-2);
  border: 1px solid var(--line-2);
  border-radius: var(--r-lg);
}

.arh-hero-card-live {
  border-color: var(--accent-soft);
  box-shadow: var(--glow);
}

.arh-hero-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--accent);
}

.arh-hero-players {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 28px;
  font-weight: 700;
  color: var(--ink-0);
}

.arh-hero-players em {
  font-style: normal;
  font-size: 14px;
  color: var(--ink-3);
  letter-spacing: 0.08em;
}

.arh-hero-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
}

.arh-hero-stage { color: var(--ink-3); flex: 1; }
.arh-hero-score { font-weight: 700; color: var(--accent); font-size: 16px; }
.arh-hero-time { font-weight: 700; color: var(--accent); font-size: 16px; }

.arh-hero-action {
  align-self: flex-start;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 22px;
  border-radius: var(--r-md);
  background: var(--accent);
  border: 1px solid var(--accent);
  color: #000;
  font-size: 14px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: opacity 150ms;
}

.arh-hero-action:hover { opacity: 0.9; }

/* Journées */
.arh-days {
  flex: 1;
  padding: 20px 32px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.arh-empty {
  text-align: center;
  color: var(--ink-3);
  font-size: 15px;
  margin-top: 40px;
}

.arh-day {
  border: 1px solid var(--line-2);
  border-radius: var(--r-lg);
  overflow: hidden;
  background: var(--bg-2);
}

.arh-day-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  background: var(--bg-3);
  cursor: pointer;
  flex-wrap: wrap;
  transition: background 150ms;
}

.arh-day-header:hover { background: var(--bg-4); }

.arh-day-header.is-today {
  background: var(--accent-soft);
}

.arh-day-header-left { display: flex; align-items: center; gap: 12px; }

.arh-day-date {
  font-size: 14px;
  font-weight: 700;
  color: var(--ink-0);
  text-transform: capitalize;
}

.arh-day-count {
  font-size: 12px;
  color: var(--ink-3);
  background: var(--bg-4);
  padding: 2px 8px;
  border-radius: 99px;
  font-weight: 600;
}

.arh-day-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--ink-3);
}

.arh-day-chevron {
  display: flex;
  color: var(--ink-2);
  transition: transform 150ms;
}

.arh-day-chevron.open { transform: rotate(180deg); }

.arh-day-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 18px;
}

.arh-day-empty {
  text-align: center;
  color: var(--ink-4);
  font-size: 13px;
  margin: 8px 0;
}

.arh-break-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 16px;
  background: var(--bg-3);
  border: 1px solid var(--line-1);
  border-radius: var(--r-md);
  opacity: 0.8;
}

.arh-break-icon { font-size: 14px; color: var(--ink-3); }
.arh-break-label { font-size: 13px; color: var(--ink-2); }

.arh-match {
  display: flex;
  align-items: stretch;
  background: var(--bg-2);
  border: 1px solid var(--line-2);
  border-radius: var(--r-lg);
  overflow: hidden;
  text-align: left;
  font: inherit;
  color: inherit;
  transition: background 150ms, border-color 150ms;
}

.arh-match:hover { background: var(--bg-3); }

.arh-match-live {
  border-color: var(--accent-soft);
  box-shadow: var(--glow);
}

.arh-match-stripe {
  width: 4px;
  flex-shrink: 0;
}

.arh-match-body {
  flex: 1;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.arh-match-top {
  display: flex;
  align-items: center;
  gap: 10px;
}

.arh-match-status {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
  padding: 3px 10px;
  border-radius: 99px;
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: 5px;
}

.arh-match-status.live      { background: var(--danger-soft); color: var(--danger); }
.arh-match-status.next      { background: var(--bg-4); color: var(--ink-2); }
.arh-match-status.scheduled { background: var(--accent-soft); color: var(--accent); }
.arh-match-status.finished  { background: var(--bg-4); color: var(--ink-3); }

.arh-live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--danger);
  animation: pulse 1.5s ease-in-out infinite;
  display: inline-block;
}

.arh-match-time { font-size: 13px; font-weight: 700; color: var(--accent); }
.arh-match-court { font-size: 12px; color: var(--ink-3); margin-left: auto; }

.arh-match-players {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 19px;
  font-weight: 700;
  color: var(--ink-0);
}

.arh-match-players em {
  font-style: normal;
  font-size: 12px;
  color: var(--ink-3);
  letter-spacing: 0.08em;
}

.arh-match-bottom {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
}

.arh-match-event { color: var(--ink-3); flex: 1; }
.arh-match-score { font-weight: 700; color: var(--accent); }

.arh-match-go {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
  color: var(--ink-2);
}

.arh-match-finished { opacity: 0.65; }

/* Footer */
.arh-foot {
  padding: 14px 32px;
  border-top: 1px solid var(--line-1);
  font-size: 11px;
  font-weight: 500;
  color: var(--ink-4);
  letter-spacing: 0.04em;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.arh-foot-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--success);
  display: inline-block;
}
</style>
