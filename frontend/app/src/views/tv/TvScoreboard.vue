<script setup lang="ts">
import { useLiveStore } from '@/stores/live'
import { usePolling } from '@/composables/usePolling'
import TvIdle from './TvIdle.vue'

const live = useLiveStore()
usePolling(() => live.fetchScoreState(), 2000)

function pointLabel(n: number, inTb: boolean): string {
  if (inTb) return String(n)
  const map: Record<number, string> = { 0: '0', 1: '15', 2: '30', 3: '40' }
  return map[n] ?? '40'
}
</script>

<template>
  <div class="scoreboard">
    <!-- Backdrop court CSS (défini dans tokens.css) -->
    <div class="court-bg" />

    <!-- ── État vide → carrousel TvIdle ─────────────────────────────────── -->
    <TvIdle v-if="!live.hero" />

    <!-- ── Match en cours ────────────────────────────────────────────────── -->
    <template v-else>
      <!-- Header -->
      <header class="sb-header">
        <!-- Logo balle de tennis SVG -->
        <div class="sb-logo">
          <div class="tv-tournament-mark">
            <svg viewBox="0 0 24 24" width="36" height="36" style="color: var(--accent)">
              <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="1.4"/>
              <path d="M2 9c5 2.5 15 2.5 20 0M2 15c5-2.5 15-2.5 20 0" fill="none" stroke="currentColor" stroke-width="1.4"/>
            </svg>
          </div>
          <div class="logo-text">
            <span class="logo-title">OPEN DE MOUTILLOUX</span>
            <span class="logo-sub">ÉDITION {{ live.editionYear }}</span>
          </div>
        </div>

      </header>

      <!-- Bandeau « À suivre » — positionné juste au-dessus du sb-band -->
      <div v-if="live.next" class="sb-next-band">
        <span class="sb-next-lbl">À SUIVRE</span>
        <span class="sb-next-dash">—</span>
        <span class="sb-next-players">
          {{ live.next.sideA?.player?.fullName ?? live.next.sideALabel ?? '?' }}
          <em class="sb-next-vs">vs</em>
          {{ live.next.sideB?.player?.fullName ?? live.next.sideBLabel ?? '?' }}
        </span>
        <span v-if="live.next.stageLabel" class="sb-next-stage">· {{ live.next.stageLabel }}</span>
        <span class="sb-next-call">
          <i class="sb-next-dot" />
          Joueurs suivants, présentez-vous au juge-arbitre
        </span>
      </div>

      <!-- Bandeau score bas -->
      <div class="sb-band">
        <!-- Ligne titre -->
        <div class="sb-band-title">
          <span class="live-dot" />
          EN DIRECT
          <span class="band-sep">·</span>
          {{ live.hero.stageLabel }}
          <span v-if="live.hero.tbActive" class="tb-badge">JEU DÉCISIF</span>
        </div>

        <!-- Score principal -->
        <div class="sb-score-grid">
          <!-- Côté A -->
          <div class="sb-player" :class="{ serving: live.hero.server === 'A' }">
            <div class="player-bar accent" />
            <div class="player-info">
              <!-- Balle de service SVG -->
              <span v-if="live.hero.server === 'A'" class="serve-ball">
                <svg viewBox="0 0 24 24" width="20" height="20" style="filter: drop-shadow(0 0 6px #E8F35A)">
                  <circle cx="12" cy="12" r="10" fill="#E8F35A"/>
                  <path d="M2.5 12c4-1 8.5-1 12.5 3 1.5 1.5 4.5 2.5 6.5 2.5M2.5 12c4 1 8.5 1 12.5-3 1.5-1.5 4.5-2.5 6.5-2.5" fill="none" stroke="rgba(0,0,0,0.5)" stroke-width="0.8"/>
                </svg>
              </span>
              <span class="player-name">
                {{ live.hero.sideA?.player?.fullName ?? live.hero.sideALabel ?? '—' }}
              </span>
              <span v-if="live.hero.sideA?.seedHint" class="seed-badge">{{ live.hero.sideA.seedHint }}</span>
            </div>
            <div class="player-scores">
              <div class="score-sets">
                <span v-for="set in live.hero.setScores" :key="set.a + '-' + set.b" class="set-box">{{ set.a }}</span>
              </div>
              <span class="score-games tab">{{ live.hero.gamesA }}</span>
              <span class="score-points tab accent-text">
                {{ live.hero.tbActive ? live.hero.tbPointsA : pointLabel(live.hero.pointsA, false) }}
              </span>
            </div>
          </div>

          <!-- Séparateur -->
          <div class="sb-divider" />

          <!-- Côté B -->
          <div class="sb-player sb-player--right" :class="{ serving: live.hero.server === 'B' }">
            <div class="player-scores player-scores--right">
              <span class="score-points tab">
                {{ live.hero.tbActive ? live.hero.tbPointsB : pointLabel(live.hero.pointsB, false) }}
              </span>
              <span class="score-games tab">{{ live.hero.gamesB }}</span>
              <div class="score-sets">
                <span v-for="set in live.hero.setScores" :key="set.a + '-' + set.b" class="set-box">{{ set.b }}</span>
              </div>
            </div>
            <div class="player-info player-info--right">
              <span class="player-name">
                {{ live.hero.sideB?.player?.fullName ?? live.hero.sideBLabel ?? '—' }}
              </span>
              <span v-if="live.hero.sideB?.seedHint" class="seed-badge">{{ live.hero.sideB.seedHint }}</span>
              <span v-if="live.hero.server === 'B'" class="serve-ball">
                <svg viewBox="0 0 24 24" width="20" height="20" style="filter: drop-shadow(0 0 6px #E8F35A)">
                  <circle cx="12" cy="12" r="10" fill="#E8F35A"/>
                  <path d="M2.5 12c4-1 8.5-1 12.5 3 1.5 1.5 4.5 2.5 6.5 2.5M2.5 12c4 1 8.5 1 12.5-3 1.5-1.5 4.5-2.5 6.5-2.5" fill="none" stroke="rgba(0,0,0,0.5)" stroke-width="0.8"/>
                </svg>
              </span>
            </div>
            <div class="player-bar white" />
          </div>
        </div>

        <!-- Pied de bande -->
        <div class="sb-band-footer">
          <span v-if="live.hero.court">COURT · {{ live.hero.court }}</span>
          <span v-if="live.hero.clock">DURÉE · {{ live.hero.clock }}</span>
          <span>{{ live.now }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.scoreboard {
  position: relative;
  width: 1920px;
  height: 1080px;
  overflow: hidden;
  background: var(--bg-0);
}

/* ── Header ─────────────────────────────────────────────────────────── */
.sb-header {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 96px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 48px;
  z-index: 10;
}

.sb-logo {
  display: flex;
  align-items: center;
  gap: 16px;
}

.tv-tournament-mark {
  animation: serveFloat 3s ease-in-out infinite;
}

.logo-title {
  display: block;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.20em;
  color: var(--ink-0);
}

.logo-sub {
  display: block;
  font-size: 12px;
  font-weight: 400;
  letter-spacing: 0.18em;
  color: var(--ink-2);
  text-transform: uppercase;
}

/* ── Bandeau « À suivre » ────────────────────────────────────── */
.sb-next-band {
  position: absolute;
  bottom: 240px;
  left: 0;
  right: 0;
  height: 56px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 48px;
  background: rgba(5, 6, 8, 0.88);
  border-top: 1px solid var(--accent-soft);
  border-bottom: 1px solid var(--line-2);
  z-index: 10;
}

.sb-next-lbl {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.2em;
  color: var(--accent);
  text-transform: uppercase;
  flex-shrink: 0;
}

.sb-next-dash {
  color: var(--ink-3);
  flex-shrink: 0;
}

.sb-next-players {
  font-size: 18px;
  font-weight: 700;
  color: var(--ink-0);
  display: flex;
  align-items: center;
  gap: 10px;
}

.sb-next-vs {
  font-style: normal;
  font-size: 12px;
  font-weight: 400;
  color: var(--ink-3);
  letter-spacing: 0.08em;
}

.sb-next-stage {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-2);
  letter-spacing: 0.06em;
}

.sb-next-call {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--ink-3);
  letter-spacing: 0.06em;
}

.sb-next-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  animation: pulse 1.5s ease-in-out infinite;
  display: inline-block;
  flex-shrink: 0;
}

/* ── Bandeau bas ─────────────────────────────────────────────────────── */
.sb-band {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 240px;
  background: rgba(5, 6, 8, 0.96);
  border-top: 1px solid var(--line-2);
  display: flex;
  flex-direction: column;
  z-index: 10;
}

.sb-band-title {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 48px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.18em;
  color: var(--ink-2);
  text-transform: uppercase;
  border-bottom: 1px solid var(--line-1);
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--danger);
  animation: pulse 1.5s ease-in-out infinite;
}

.band-sep { color: var(--line-3); }

.tb-badge {
  background: var(--accent-soft);
  color: var(--accent);
  padding: 2px 8px;
  border-radius: var(--r-xs);
  font-size: 10px;
}

/* ── Score grid ──────────────────────────────────────────────────────── */
.sb-score-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 2px 1fr;
  align-items: center;
  padding: 0 48px;
  gap: 32px;
}

.sb-player {
  display: flex;
  align-items: center;
  gap: 20px;
}

.sb-player--right { flex-direction: row-reverse; }

.player-bar {
  width: 4px;
  height: 64px;
  border-radius: 2px;
  flex-shrink: 0;
}

.player-bar.accent { background: var(--accent); }
.player-bar.white  { background: rgba(255,255,255,0.4); }

.player-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.player-info--right { flex-direction: row-reverse; }

.serve-ball {
  display: flex;
  align-items: center;
  animation: serveFloat 1.8s ease-in-out infinite;
}

.player-name {
  font-size: 36px;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: var(--ink-0);
}

.seed-badge {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  background: var(--accent-soft);
  color: var(--accent);
  padding: 3px 8px;
  border-radius: var(--r-xs);
}

.player-scores {
  display: flex;
  align-items: center;
  gap: 16px;
}

.player-scores--right { flex-direction: row-reverse; }

.score-sets {
  display: flex;
  gap: 6px;
}

.set-box {
  font-size: 22px;
  font-weight: 700;
  width: 36px;
  height: 36px;
  border-radius: var(--r-xs);
  background: var(--bg-3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-1);
}

.score-games {
  font-size: 60px;
  font-weight: 700;
  color: var(--ink-0);
  min-width: 72px;
  text-align: center;
}

.score-points {
  font-size: 64px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--ink-1);
  min-width: 80px;
  text-align: center;
}

.accent-text { color: var(--accent); }

.sb-divider {
  background: var(--line-2);
  height: 80px;
  align-self: center;
}

/* ── Pied ────────────────────────────────────────────────────────────── */
.sb-band-footer {
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 10px 48px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.16em;
  color: var(--ink-3);
  text-transform: uppercase;
  border-top: 1px solid var(--line-1);
}
</style>
