<script setup lang="ts">
import { computed } from 'vue'
import { useEventStore } from '@/stores/event'
import { usePolling } from '@/composables/usePolling'
import type { BracketSlot } from '@/types'

const eventStore = useEventStore()
usePolling(async () => {
  await eventStore.fetchEditions()
  if (eventStore.activeEventId) {
    await eventStore.fetchBracket(eventStore.activeEventId)
  }
}, 10000)

const bracket = computed(() => eventStore.bracket)

// ── Layout constants (portées depuis bracket.jsx) ──────────────────────
const LB = {
  qfX: 80,  sfX: 540, fX: 1000, trX: 1420,
  cardW: 380, finalW: 380, trW: 420,
  cardH: 120, finalH: 128, trH: 186,
  qf: [70, 230, 580, 740],
  sf: [150, 660],
  f: 401,
  tr: 372,
}

const STAGE_H = 928  // 1080 - 96 header - 56 footer

function elbowPath(fromX: number, fromY: number, toX: number, toY: number): string {
  if (fromY === toY) return `M ${fromX} ${fromY} H ${toX}`
  const midX = fromX + (toX - fromX) / 2
  return `M ${fromX} ${fromY} H ${midX} V ${toY} H ${toX}`
}

// Chemins SVG connecteurs QF→SF
const qfSfPaths = computed(() => [
  elbowPath(LB.qfX + LB.cardW, LB.qf[0] + LB.cardH / 2, LB.sfX, LB.sf[0] + LB.cardH / 2),
  elbowPath(LB.qfX + LB.cardW, LB.qf[1] + LB.cardH / 2, LB.sfX, LB.sf[0] + LB.cardH / 2),
  elbowPath(LB.qfX + LB.cardW, LB.qf[2] + LB.cardH / 2, LB.sfX, LB.sf[1] + LB.cardH / 2),
  elbowPath(LB.qfX + LB.cardW, LB.qf[3] + LB.cardH / 2, LB.sfX, LB.sf[1] + LB.cardH / 2),
])

// Chemins SVG SF→F
const sfFPaths = computed(() => [
  elbowPath(LB.sfX + LB.cardW, LB.sf[0] + LB.cardH / 2, LB.fX, LB.f + LB.finalH / 2),
  elbowPath(LB.sfX + LB.cardW, LB.sf[1] + LB.cardH / 2, LB.fX, LB.f + LB.finalH / 2),
])

// Chemin F→Trophée
const fTrPath = computed(() =>
  elbowPath(LB.fX + LB.finalW, LB.f + LB.finalH / 2, LB.trX, LB.tr + LB.trH / 2)
)

function slotName(slot: BracketSlot): string {
  return slot.match?.sideA?.player?.fullName
    ?? slot.match?.sideALabel
    ?? 'À désigner'
}

function slotNameB(slot: BracketSlot): string {
  return slot.match?.sideB?.player?.fullName
    ?? slot.match?.sideBLabel
    ?? 'À désigner'
}

function isLive(slot: BracketSlot): boolean {
  return slot.match?.status === 'LIVE'
}

function setScoreA(slot: BracketSlot): string {
  return slot.match?.setScores?.map((s) => s.a).join(' ') ?? ''
}

function setScoreB(slot: BracketSlot): string {
  return slot.match?.setScores?.map((s) => s.b).join(' ') ?? ''
}
</script>

<template>
  <div class="bracket-screen">
    <!-- Header -->
    <header class="brk-header">
      <div class="brk-logo">
        <span class="logo-badge">M</span>
        <span class="logo-title">TABLEAU FINAL</span>
      </div>
      <div class="brk-stages">
        <span>QUARTS</span>
        <span class="stage-sep">→</span>
        <span>DEMI-FINALES</span>
        <span class="stage-sep">→</span>
        <span>FINALE</span>
        <span class="stage-sep">→</span>
        <span class="accent-text">VAINQUEUR</span>
      </div>
    </header>

    <!-- Corps bracket -->
    <div class="brk-body">
      <svg
        class="brk-svg"
        :viewBox="`0 0 1920 ${STAGE_H}`"
        preserveAspectRatio="none"
      >
        <!-- Connecteurs QF → SF -->
        <path
          v-for="(d, i) in qfSfPaths"
          :key="`qf-sf-${i}`"
          :d="d"
          fill="none"
          stroke="rgba(255,255,255,0.22)"
          stroke-width="2"
          vector-effect="non-scaling-stroke"
          stroke-linecap="round"
        />

        <!-- Connecteurs SF → F -->
        <path
          v-for="(d, i) in sfFPaths"
          :key="`sf-f-${i}`"
          :d="d"
          fill="none"
          stroke="rgba(255,255,255,0.22)"
          stroke-width="2"
          vector-effect="non-scaling-stroke"
          stroke-linecap="round"
        />

        <!-- Connecteur F → Trophée -->
        <path
          :d="fTrPath"
          fill="none"
          stroke="rgba(255,255,255,0.22)"
          stroke-width="2"
          vector-effect="non-scaling-stroke"
          stroke-linecap="round"
        />
      </svg>

      <!-- Cards en absolute -->
      <template v-if="bracket">
        <!-- QF -->
        <div
          v-for="(slot, i) in bracket.qf"
          :key="slot.slot"
          class="brk-match"
          :class="{ live: isLive(slot) }"
          :style="{ left: `${LB.qfX}px`, top: `${LB.qf[i]}px`, width: `${LB.cardW}px` }"
        >
          <span v-if="isLive(slot)" class="live-pill">EN DIRECT</span>
          <div class="bm-row" :class="{ winner: slot.match?.winnerSide === 'A' }">
            <span class="bm-seed">{{ slot.match?.sideA?.seedHint ?? '—' }}</span>
            <span class="bm-name">{{ slotName(slot) }}</span>
            <span class="bm-score tab">{{ setScoreA(slot) }}</span>
          </div>
          <div class="bm-row" :class="{ winner: slot.match?.winnerSide === 'B' }">
            <span class="bm-seed">{{ slot.match?.sideB?.seedHint ?? '—' }}</span>
            <span class="bm-name">{{ slotNameB(slot) }}</span>
            <span class="bm-score tab">{{ setScoreB(slot) }}</span>
          </div>
        </div>

        <!-- SF -->
        <div
          v-for="(slot, i) in bracket.sf"
          :key="slot.slot"
          class="brk-match"
          :class="{ live: isLive(slot) }"
          :style="{ left: `${LB.sfX}px`, top: `${LB.sf[i]}px`, width: `${LB.cardW}px` }"
        >
          <span v-if="isLive(slot)" class="live-pill">EN DIRECT</span>
          <div class="bm-row" :class="{ winner: slot.match?.winnerSide === 'A' }">
            <span class="bm-seed">{{ slot.match?.sideA?.seedHint ?? '—' }}</span>
            <span class="bm-name">{{ slotName(slot) }}</span>
          </div>
          <div class="bm-row" :class="{ winner: slot.match?.winnerSide === 'B' }">
            <span class="bm-seed">{{ slot.match?.sideB?.seedHint ?? '—' }}</span>
            <span class="bm-name">{{ slotNameB(slot) }}</span>
          </div>
        </div>

        <!-- Finale -->
        <div
          v-for="slot in bracket.f"
          :key="slot.slot"
          class="brk-match brk-match--final"
          :class="{ live: isLive(slot) }"
          :style="{ left: `${LB.fX}px`, top: `${LB.f}px`, width: `${LB.finalW}px`, height: `${LB.finalH}px` }"
        >
          <span v-if="isLive(slot)" class="live-pill">EN DIRECT</span>
          <div class="bm-row" :class="{ winner: slot.match?.winnerSide === 'A' }">
            <span class="bm-seed">{{ slot.match?.sideA?.seedHint ?? '—' }}</span>
            <span class="bm-name">{{ slotName(slot) }}</span>
          </div>
          <div class="bm-row" :class="{ winner: slot.match?.winnerSide === 'B' }">
            <span class="bm-seed">{{ slot.match?.sideB?.seedHint ?? '—' }}</span>
            <span class="bm-name">{{ slotNameB(slot) }}</span>
          </div>
        </div>

        <!-- Trophée vainqueur -->
        <div
          class="brk-winner"
          :style="{ left: `${LB.trX}px`, top: `${LB.tr}px`, width: `${LB.trW}px`, height: `${LB.trH}px` }"
        >
          <svg class="trophy-icon" viewBox="0 0 48 48" fill="none">
            <path d="M24 32c-8 0-14-6-14-14V8h28v10c0 8-6 14-14 14z" stroke="var(--accent)" stroke-width="2.5" stroke-linecap="round"/>
            <path d="M34 8h6v6c0 3-2 6-6 6M14 8H8v6c0 3 2 6 6 6" stroke="var(--accent)" stroke-width="2.5" stroke-linecap="round"/>
            <path d="M24 32v6M18 38h12" stroke="var(--accent)" stroke-width="2.5" stroke-linecap="round"/>
          </svg>
          <span class="winner-label">VAINQUEUR</span>
          <span class="winner-name">{{ bracket.f[0]?.match?.winnerSide ? (bracket.f[0].match.winnerSide === 'A' ? slotName(bracket.f[0]) : slotNameB(bracket.f[0])) : 'À DÉSIGNER' }}</span>
          <span class="winner-footer">COUPE MOUTILLOUX</span>
        </div>
      </template>
    </div>

    <!-- Footer -->
    <footer class="brk-footer">
      <span class="brk-footer-text">TABLEAU FINAL · MOUTILLOUX</span>
    </footer>
  </div>
</template>

<style scoped>
.bracket-screen {
  width: 1920px;
  height: 1080px;
  background: var(--bg-1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── Header ─────────────────────────────────────────────────────────── */
.brk-header {
  height: 96px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 56px;
  border-bottom: 1px solid var(--line-1);
  flex-shrink: 0;
}

.brk-logo {
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo-badge {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--accent);
  color: #000;
  font-size: 20px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-title {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.20em;
  color: var(--ink-0);
  text-transform: uppercase;
}

.brk-stages {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.18em;
  color: var(--ink-2);
  text-transform: uppercase;
}

.stage-sep { color: var(--line-3); }
.accent-text { color: var(--accent); }

/* ── Body ─────────────────────────────────────────────────────────────── */
.brk-body {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.brk-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

/* ── Match cards ─────────────────────────────────────────────────────── */
.brk-match {
  position: absolute;
  background: var(--bg-2);
  border: 1px solid var(--line-2);
  border-radius: 14px;
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.brk-match.live {
  border-color: var(--accent-soft);
  box-shadow: var(--glow);
}

.brk-match--final {
  background: linear-gradient(135deg, var(--bg-2), var(--bg-3));
}

.live-pill {
  position: absolute;
  top: -11px;
  left: 14px;
  background: var(--danger);
  color: white;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  padding: 2px 8px;
  border-radius: 99px;
}

.bm-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
}

.bm-row + .bm-row {
  border-top: 1px dashed var(--line-1);
}

.bm-row.winner .bm-name {
  font-weight: 700;
  color: var(--ink-0);
}

.bm-row.winner .bm-seed {
  background: var(--accent);
  color: #000;
}

.bm-seed {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: var(--r-xs);
  background: var(--bg-4);
  color: var(--ink-2);
  min-width: 28px;
  text-align: center;
}

.bm-name {
  flex: 1;
  font-size: 16px;
  color: var(--ink-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bm-score {
  font-size: 14px;
  color: var(--ink-2);
}

/* ── Winner card ─────────────────────────────────────────────────────── */
.brk-winner {
  position: absolute;
  background: linear-gradient(135deg, rgba(255,200,61,0.08), rgba(255,200,61,0.02));
  border: 1px solid var(--accent-soft);
  border-radius: var(--r-xl);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: var(--glow);
}

.trophy-icon {
  width: 52px;
  height: 52px;
  filter: drop-shadow(0 0 8px var(--accent-glow));
}

.winner-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.22em;
  color: var(--ink-3);
  text-transform: uppercase;
}

.winner-name {
  font-size: 20px;
  font-weight: 800;
  color: var(--accent);
  text-align: center;
}

.winner-footer {
  font-size: 10px;
  color: var(--ink-4);
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

/* ── Footer ──────────────────────────────────────────────────────────── */
.brk-footer {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 56px;
  border-top: 1px solid var(--line-1);
  flex-shrink: 0;
}

.brk-footer-text {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.18em;
  color: var(--ink-3);
  text-transform: uppercase;
}
</style>
