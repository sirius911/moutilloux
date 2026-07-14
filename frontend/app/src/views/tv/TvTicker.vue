<script setup lang="ts">
import { computed } from 'vue'
import { useLiveStore } from '@/stores/live'
import { sideName } from '@/utils/participants'
import type { Match } from '@/types'

const live = useLiveStore()

interface TickerItem {
  key: string
  text: string
}

function winnerLoserNames(m: Match): { winner: string; loser: string } {
  const a = m.sideA?.displayName ?? m.sideALabel ?? '—'
  const b = m.sideB?.displayName ?? m.sideBLabel ?? '—'
  return m.winnerSide === 'A' ? { winner: a, loser: b } : { winner: b, loser: a }
}

function resultScore(m: Match): string {
  return m.setScores?.map(s => `${s.a}-${s.b}`).join(' ') ?? `${m.gamesA}-${m.gamesB}`
}

// Liste plate : annonces actives → derniers résultats → prochains matchs
// (ordre imposé par la spec tv-live §Banderole d'information).
const items = computed<TickerItem[]>(() => {
  const list: TickerItem[] = []

  for (const a of live.announcements) {
    list.push({ key: `a-${a.id}`, text: a.message })
  }

  for (const m of live.recentResults) {
    const { winner, loser } = winnerLoserNames(m)
    list.push({ key: `r-${m.id}`, text: `${m.stageLabel} · ${winner} bat ${loser} ${resultScore(m)}` })
  }

  for (const m of live.programme.upcoming) {
    const a = sideName(m.sideA, m.sideALabel)
    const b = sideName(m.sideB, m.sideBLabel)
    list.push({ key: `p-${m.id}`, text: `À venir ~${m.scheduledTime ?? '—'} · ${a} vs ${b}` })
  }

  return list
})

// Piste doublée pour une boucle sans à-coup (translateX 0 → -50%).
const loopItems = computed<TickerItem[]>(() => {
  const base = items.value
  return [...base, ...base].map((it, i) => ({ ...it, key: `${it.key}-${i}` }))
})

// Durée de l'animation proportionnelle au nombre d'items, bornée pour éviter
// un défilement trop rapide (peu d'items) ou trop lent (beaucoup d'items).
const scrollDurationS = computed(() => {
  const n = items.value.length
  if (n === 0) return 0
  return Math.min(60, Math.max(14, n * 4.5))
})
</script>

<template>
  <div class="tv-ticker" :class="{ 'tv-ticker--empty': items.length === 0 }">
    <div class="tv-ticker-fixed">
      <span v-if="live.hero?.court">COURT · {{ live.hero.court }}</span>
      <span v-if="live.hero?.clock">DURÉE · {{ live.hero.clock }}</span>
      <span>{{ live.now }}</span>
    </div>

    <span v-if="items.length > 0" class="tv-ticker-divider" />

    <div v-if="items.length > 0" class="tv-ticker-track-wrap">
      <div class="tv-ticker-track" :style="{ animationDuration: `${scrollDurationS}s` }">
        <span v-for="it in loopItems" :key="it.key" class="tv-ticker-item">{{ it.text }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── Banderole d'information (ticker) ─────────────────────────────────
   Ancrée en bas de la scène, sous la bande de score (.sb-ed-bottom
   commence à bottom: 72px) : bottom 12px + height 44px = haut à 56px,
   marge de sécurité de 16px. Même plan que l'ancien .sb-foot-discreet. */
.tv-ticker {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 12px;
  height: 44px;
  z-index: 4;
  display: flex;
  align-items: center;
  gap: 28px;
  padding: 0 48px;
  overflow: hidden;
}

.tv-ticker--empty {
  justify-content: center;
}

.tv-ticker-fixed {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 32px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.16em;
  color: var(--ink-3);
  text-transform: uppercase;
  white-space: nowrap;
}

.tv-ticker-divider {
  flex-shrink: 0;
  width: 1px;
  height: 18px;
  background: rgba(255, 255, 255, 0.15);
}

.tv-ticker-track-wrap {
  flex: 1;
  min-width: 0;
  height: 100%;
  overflow: hidden;
  display: flex;
  align-items: center;
  -webkit-mask-image: linear-gradient(to right, transparent 0, black 32px, black calc(100% - 32px), transparent 100%);
  mask-image: linear-gradient(to right, transparent 0, black 32px, black calc(100% - 32px), transparent 100%);
}

.tv-ticker-track {
  display: flex;
  align-items: center;
  white-space: nowrap;
  animation-name: tv-ticker-scroll;
  animation-timing-function: linear;
  animation-iteration-count: infinite;
  will-change: transform;
}

.tv-ticker-item {
  position: relative;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--ink-2);
  padding: 0 28px;
}

.tv-ticker-item::after {
  content: '·';
  position: absolute;
  right: 0;
  color: var(--ink-4);
}

@keyframes tv-ticker-scroll {
  from { transform: translateX(0); }
  to { transform: translateX(-50%); }
}
</style>
