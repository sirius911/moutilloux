<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePolling } from '@/composables/usePolling'
import { useApi } from '@/composables/useApi'
import type { Match } from '@/types'

const router = useRouter()
const authStore = useAuthStore()
const { get } = useApi()

const matches = ref<Match[]>([])
const filter = ref<'all' | 'live' | 'soon' | 'done'>('all')
const syncTime = ref('')

function updateClock() {
  const now = new Date()
  syncTime.value = now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

usePolling(async () => {
  matches.value = await get<Match[]>('/api/arbitre/matches/')
  updateClock()
}, 5000)

const liveCount = computed(() => matches.value.filter(m => m.status === 'LIVE').length)
const soonCount = computed(() => matches.value.filter(m => m.status === 'SCHEDULED').length)
const doneCount = computed(() => matches.value.filter(m => m.status === 'FINISHED').length)

const filtered = computed(() => {
  if (filter.value === 'live') return matches.value.filter(m => m.status === 'LIVE')
  if (filter.value === 'soon') return matches.value.filter(m => m.status === 'SCHEDULED')
  if (filter.value === 'done') return matches.value.filter(m => m.status === 'FINISHED')
  return matches.value
})

const tabs = computed(() => [
  { id: 'all' as const,  label: 'Tous',      count: matches.value.length },
  { id: 'live' as const, label: 'En direct', count: liveCount.value,  hot: true },
  { id: 'soon' as const, label: 'À venir',   count: soonCount.value },
  { id: 'done' as const, label: 'Terminés',  count: doneCount.value },
])

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

    <!-- Tabs -->
    <div class="arh-tabs">
      <button
        v-for="t in tabs"
        :key="t.id"
        :class="['arh-tab', { on: filter === t.id }]"
        type="button"
        @click="filter = t.id"
      >
        <span v-if="t.hot && liveCount > 0" class="arh-tab-hot" />
        {{ t.label }}
        <em class="tab">{{ t.count }}</em>
      </button>
    </div>

    <!-- Liste de matchs -->
    <div class="arh-list">
      <p v-if="filtered.length === 0" class="arh-empty">Aucun match dans cette catégorie.</p>

      <button
        v-for="m in filtered"
        :key="m.id"
        :class="['arh-match', `arh-match-${m.status.toLowerCase()}`]"
        type="button"
        @click="router.push(`/arbitre/${m.id}`)"
      >
        <div class="arh-match-stripe" :style="{ background: stripeColor(m.status) }" />

        <div class="arh-match-body">
          <div class="arh-match-top">
            <span :class="['arh-match-status', m.status.toLowerCase()]">
              <i v-if="m.status === 'LIVE'" class="arh-live-dot" />
              {{ m.status === 'LIVE' ? 'EN DIRECT' : m.status === 'FINISHED' ? 'TERMINÉ' : 'PRÉVU' }}
            </span>
            <span v-if="m.scheduledTime" class="arh-match-time tab">{{ m.scheduledTime }}</span>
            <span v-if="m.court" class="arh-match-court">{{ m.court }}</span>
          </div>

          <div class="arh-match-players">
            <span>{{ playerName(m, 'A') }}</span>
            <em>vs</em>
            <span>{{ playerName(m, 'B') }}</span>
          </div>

          <div class="arh-match-bottom">
            <span class="arh-match-event">{{ m.stageLabel }}</span>
            <span v-if="m.status === 'LIVE' && scoreDisplay(m)" class="arh-match-score tab">
              {{ scoreDisplay(m) }}
            </span>
            <span class="arh-match-go">
              {{ goLabel(m.status) }}
              <svg viewBox="0 0 24 24" width="14" height="14">
                <path d="M5 12h14m0 0l-5-5m5 5l-5 5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </div>
        </div>
      </button>
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

/* Tabs */
.arh-tabs {
  display: flex;
  gap: 6px;
  padding: 16px 32px;
  border-bottom: 1px solid var(--line-1);
  flex-shrink: 0;
}

.arh-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: var(--r-md);
  background: transparent;
  border: 1px solid var(--line-2);
  font-size: 14px;
  font-weight: 500;
  color: var(--ink-2);
  position: relative;
  transition: background 150ms, color 150ms, border-color 150ms;
}

.arh-tab:hover { background: var(--bg-3); color: var(--ink-1); }

.arh-tab.on {
  background: var(--accent);
  color: #000;
  border-color: var(--accent);
  font-weight: 600;
}

.arh-tab em {
  font-style: normal;
  font-family: var(--font-mono);
  font-size: 12px;
  opacity: 0.7;
}

.arh-tab-hot {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--danger);
  animation: pulse 1.5s ease-in-out infinite;
}

/* Liste */
.arh-list {
  flex: 1;
  padding: 20px 32px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
}

.arh-empty {
  text-align: center;
  color: var(--ink-3);
  font-size: 15px;
  margin-top: 40px;
}

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

.arh-match-status.live     { background: var(--danger-soft); color: var(--danger); }
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
