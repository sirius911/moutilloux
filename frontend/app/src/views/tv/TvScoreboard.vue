<script setup lang="ts">
import { useLiveStore } from '@/stores/live'
import { usePolling } from '@/composables/usePolling'
import TvIdle from './TvIdle.vue'

const live = useLiveStore()
usePolling(() => live.fetchTvState(), 2000)
</script>

<template>
  <div class="scoreboard">
    <!-- Fond de scène : affiche du match si disponible, sinon fond de court CSS -->
    <div
      v-if="live.hero?.posterUrl"
      class="hero-poster-bg"
      :style="{ backgroundImage: `url(${live.hero.posterUrl})` }"
    />
    <div v-else class="court-bg" />

    <!-- ── État vide → carrousel TvIdle ─────────────────────────────────── -->
    <TvIdle v-if="!live.hero" />

    <!-- ── Match en cours ────────────────────────────────────────────────── -->
    <template v-else>
      <!-- Zone d'enjeu (centre de l'écran) — classement de poule ou mini-tableau -->
      <div v-if="live.stake" class="stake-panel">
        <!-- Enjeu : poule -->
        <div v-if="live.stake.kind === 'group'" class="stake-group">
          <h2 class="stake-title">
            POULE {{ live.stake.groupName }}
            <span class="stake-title-sep">·</span>
            {{ live.stake.eventName }}
          </h2>
          <div class="stake-group-rows">
            <div class="stake-group-row stake-group-row-head">
              <span>JOUEUR</span><span>V</span><span>D</span><span>PTS</span>
            </div>
            <div
              v-for="s in live.stake.standings"
              :key="s.entryId"
              :class="['stake-group-row', {
                q: s.qualified,
                hl: s.entryId === live.hero.sideA?.id || s.entryId === live.hero.sideB?.id,
              }]"
            >
              <span class="stake-group-name">
                <em class="stake-group-rank">{{ s.rank }}</em>
                {{ s.name }}
                <i v-if="s.qualified" class="stake-group-q">Q</i>
              </span>
              <span class="tab">{{ s.wins }}</span>
              <span class="tab">{{ s.losses }}</span>
              <span class="tab stake-group-pts">{{ s.points }}</span>
            </div>
          </div>
        </div>

        <!-- Enjeu : tableau -->
        <div v-else-if="live.stake.kind === 'bracket'" class="stake-bracket">
          <h2 class="stake-title">
            TABLEAU
            <span class="stake-title-sep">·</span>
            {{ live.stake.eventName }}
          </h2>
          <div class="stake-mini-bracket">
            <div class="stake-mini-col">
              <div class="stake-mini-col-head">QUARTS</div>
              <div
                v-for="slot in live.stake.bracket.qf"
                :key="slot.slot"
                :class="['stake-mini-match', { current: slot.match?.id === live.hero.id }]"
              >
                <div :class="['stake-mini-slot', { win: slot.match?.winnerSide === 'A' }]">
                  <span class="stake-mini-name">{{ slot.match?.sideA?.player?.fullName ?? slot.match?.sideALabel ?? 'À désigner' }}</span>
                </div>
                <div :class="['stake-mini-slot', { win: slot.match?.winnerSide === 'B' }]">
                  <span class="stake-mini-name">{{ slot.match?.sideB?.player?.fullName ?? slot.match?.sideBLabel ?? 'À désigner' }}</span>
                </div>
              </div>
            </div>
            <div class="stake-mini-col">
              <div class="stake-mini-col-head">DEMIES</div>
              <div
                v-for="slot in live.stake.bracket.sf"
                :key="slot.slot"
                :class="['stake-mini-match', { current: slot.match?.id === live.hero.id }]"
              >
                <div :class="['stake-mini-slot', { win: slot.match?.winnerSide === 'A' }]">
                  <span class="stake-mini-name">{{ slot.match?.sideA?.player?.fullName ?? slot.match?.sideALabel ?? 'À désigner' }}</span>
                </div>
                <div :class="['stake-mini-slot', { win: slot.match?.winnerSide === 'B' }]">
                  <span class="stake-mini-name">{{ slot.match?.sideB?.player?.fullName ?? slot.match?.sideBLabel ?? 'À désigner' }}</span>
                </div>
              </div>
            </div>
            <div class="stake-mini-col">
              <div class="stake-mini-col-head">FINALE</div>
              <div
                v-for="slot in live.stake.bracket.f"
                :key="slot.slot"
                :class="['stake-mini-match', 'final', { current: slot.match?.id === live.hero.id }]"
              >
                <div :class="['stake-mini-slot', { win: slot.match?.winnerSide === 'A' }]">
                  <span class="stake-mini-name">{{ slot.match?.sideA?.player?.fullName ?? slot.match?.sideALabel ?? 'À désigner' }}</span>
                </div>
                <div :class="['stake-mini-slot', { win: slot.match?.winnerSide === 'B' }]">
                  <span class="stake-mini-name">{{ slot.match?.sideB?.player?.fullName ?? slot.match?.sideBLabel ?? 'À désigner' }}</span>
                </div>
              </div>
            </div>
            <div v-if="live.stake.bracket.p3?.length" class="stake-mini-col">
              <div class="stake-mini-col-head">3E PLACE</div>
              <div
                v-for="slot in live.stake.bracket.p3"
                :key="slot.slot"
                :class="['stake-mini-match', { current: slot.match?.id === live.hero.id }]"
              >
                <div :class="['stake-mini-slot', { win: slot.match?.winnerSide === 'A' }]">
                  <span class="stake-mini-name">{{ slot.match?.sideA?.player?.fullName ?? slot.match?.sideALabel ?? 'À désigner' }}</span>
                </div>
                <div :class="['stake-mini-slot', { win: slot.match?.winnerSide === 'B' }]">
                  <span class="stake-mini-name">{{ slot.match?.sideB?.player?.fullName ?? slot.match?.sideBLabel ?? 'À désigner' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bandeau haut (fin) -->
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

        <div class="sb-header-status">
          <span v-if="live.hero.stageLabel" class="sb-header-stage">{{ live.hero.stageLabel }}</span>
          <span class="live-dot" />
          <span class="sb-header-live">EN DIRECT</span>
          <span v-if="live.hero.tbActive" class="tb-badge">JEU DÉCISIF</span>
        </div>
      </header>

      <!-- Bandeau « À suivre » — inchangé dans ce ticket (repositionnement #330) -->
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

      <!-- Centre editorial : jeux du set en cours en très grand -->
      <div class="sb-ed-numbers">
        <div class="sb-ed-num tab accent-text">{{ live.hero.gamesA }}</div>
        <div class="sb-ed-num-sep">—</div>
        <div class="sb-ed-num tab">{{ live.hero.gamesB }}</div>
      </div>
      <div class="sb-ed-label">JEUX · SET {{ live.hero.setScores.length + 1 }}</div>

      <div class="sb-ed-bottom">
        <!-- Côté A -->
        <div class="sb-ed-line">
          <span v-if="live.hero.server === 'A'" class="serve-ball">
            <svg viewBox="0 0 24 24" width="26" height="26" style="filter: drop-shadow(0 0 6px #E8F35A)">
              <circle cx="12" cy="12" r="10" fill="#E8F35A"/>
              <path d="M2.5 12c4-1 8.5-1 12.5 3 1.5 1.5 4.5 2.5 6.5 2.5M2.5 12c4 1 8.5 1 12.5-3 1.5-1.5 4.5-2.5 6.5-2.5" fill="none" stroke="rgba(0,0,0,0.5)" stroke-width="0.8"/>
            </svg>
          </span>
          <span v-else class="serve-ball-spacer" style="width: 26px; height: 26px" />
          <span class="sb-ed-name">
            {{ live.hero.sideA?.player?.fullName ?? live.hero.sideALabel ?? '—' }}
          </span>
          <span v-if="live.hero.sideA?.seedHint" class="sb-ed-seed">[{{ live.hero.sideA.seedHint }}]</span>
          <span class="sb-ed-rule" />
          <span
            class="sb-ed-pts tab"
            :class="{ 'accent-text': !live.hero.tbActive && live.hero.displayPointA === 'AV' }"
          >
            {{ live.hero.tbActive ? live.hero.tbPointsA : live.hero.displayPointA }}
          </span>
          <span class="sb-ed-mini">SETS&nbsp;<b class="tab">{{ live.hero.setScores.filter(s => s.a > s.b).length }}</b></span>
        </div>

        <!-- Côté B -->
        <div class="sb-ed-line">
          <span v-if="live.hero.server === 'B'" class="serve-ball">
            <svg viewBox="0 0 24 24" width="26" height="26" style="filter: drop-shadow(0 0 6px #E8F35A)">
              <circle cx="12" cy="12" r="10" fill="#E8F35A"/>
              <path d="M2.5 12c4-1 8.5-1 12.5 3 1.5 1.5 4.5 2.5 6.5 2.5M2.5 12c4 1 8.5 1 12.5-3 1.5-1.5 4.5-2.5 6.5-2.5" fill="none" stroke="rgba(0,0,0,0.5)" stroke-width="0.8"/>
            </svg>
          </span>
          <span v-else class="serve-ball-spacer" style="width: 26px; height: 26px" />
          <span class="sb-ed-name">
            {{ live.hero.sideB?.player?.fullName ?? live.hero.sideBLabel ?? '—' }}
          </span>
          <span v-if="live.hero.sideB?.seedHint" class="sb-ed-seed">[{{ live.hero.sideB.seedHint }}]</span>
          <span class="sb-ed-rule" />
          <span
            class="sb-ed-pts tab"
            :class="{ 'accent-text': !live.hero.tbActive && live.hero.displayPointB === 'AV' }"
          >
            {{ live.hero.tbActive ? live.hero.tbPointsB : live.hero.displayPointB }}
          </span>
          <span class="sb-ed-mini">SETS&nbsp;<b class="tab">{{ live.hero.setScores.filter(s => s.b > s.a).length }}</b></span>
        </div>
      </div>

      <!-- Pied discret -->
      <div class="sb-foot-discreet">
        <span v-if="live.hero.court">COURT · {{ live.hero.court }}</span>
        <span v-if="live.hero.clock">DURÉE · {{ live.hero.clock }}</span>
        <span>{{ live.now }}</span>
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

/* ── Fond de scène : affiche du match (sprint 24) ─────────────────────── */
.hero-poster-bg {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center top;
  background-repeat: no-repeat;
  background-color: var(--bg-0);
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

.sb-header-status {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.18em;
  color: var(--ink-2);
  text-transform: uppercase;
}

.sb-header-stage {
  color: var(--ink-2);
}

.sb-header-live {
  color: var(--danger);
  font-weight: 700;
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

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--danger);
  animation: pulse 1.5s ease-in-out infinite;
}

.tb-badge {
  background: var(--accent-soft);
  color: var(--accent);
  padding: 2px 8px;
  border-radius: var(--r-xs);
  font-size: 10px;
}

/* ── Centre editorial (porté depuis scoreboard.css .sb-ed-*) ─────────── */
.sb-ed-numbers {
  position: absolute;
  left: 50%;
  top: 42%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  gap: 80px;
  font-feature-settings: "tnum";
  z-index: 4;
}

.sb-ed-num {
  font-size: 320px;
  line-height: 0.85;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--ink-0);
  text-shadow: 0 8px 40px rgba(0, 0, 0, 0.7);
}

.sb-ed-num-sep {
  font-size: 200px;
  color: var(--ink-3);
  font-weight: 200;
  line-height: 0.85;
}

.sb-ed-label {
  position: absolute;
  left: 50%;
  top: calc(42% + 170px);
  transform: translateX(-50%);
  font-size: 13px;
  letter-spacing: 0.3em;
  color: var(--ink-3);
  z-index: 4;
}

.sb-ed-bottom {
  position: absolute;
  left: 64px;
  right: 64px;
  bottom: 72px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  z-index: 4;
}

.sb-ed-line {
  display: flex;
  align-items: baseline;
  gap: 20px;
  padding-bottom: 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.sb-ed-line:last-child { border-bottom: 0; }

.sb-ed-name {
  font-size: 64px;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--ink-0);
}

.sb-ed-seed {
  font-size: 22px;
  color: var(--ink-3);
}

.sb-ed-rule {
  flex: 1;
  height: 1px;
  background: rgba(255, 255, 255, 0.18);
  margin: 0 12px;
  align-self: center;
}

.sb-ed-pts {
  font-size: 80px;
  font-weight: 800;
  color: var(--ink-1);
  text-shadow: 0 0 30px var(--accent-glow);
  letter-spacing: -0.02em;
  min-width: 130px;
  text-align: right;
}

.sb-ed-mini {
  font-size: 14px;
  color: var(--ink-3);
  letter-spacing: 0.18em;
}

.sb-ed-mini b {
  color: var(--ink-0);
  font-weight: 700;
  font-size: 20px;
  margin-left: 4px;
}

.accent-text { color: var(--accent); }

.serve-ball {
  display: flex;
  align-items: center;
  animation: serveFloat 1.8s ease-in-out infinite;
}

.serve-ball-spacer {
  display: inline-block;
  visibility: hidden;
}

/* ── Zone d'enjeu (centre de l'écran) ───────────────────────────────── */
.stake-panel {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 5;
  max-width: 1100px;
  width: 90%;
  max-height: 620px;
  overflow: hidden;
  background: rgba(5, 6, 8, 0.7);
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  padding: 28px 40px;
  backdrop-filter: blur(4px);
}

.stake-title {
  margin: 0 0 20px;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.2em;
  color: var(--ink-2);
  text-transform: uppercase;
}

.stake-title-sep { color: var(--line-3); margin: 0 8px; }

/* Enjeu : poule */
.stake-group-rows {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stake-group-row {
  display: grid;
  grid-template-columns: 1fr 48px 48px 60px;
  padding: 10px 14px;
  border-radius: var(--r-sm);
  align-items: center;
  gap: 10px;
  font-size: 18px;
  color: var(--ink-1);
}

.stake-group-row-head {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
  color: var(--ink-3);
  text-transform: uppercase;
}

.stake-group-row.q {
  background: linear-gradient(90deg, rgba(255,200,61,0.08), transparent);
}

.stake-group-row.hl {
  background: rgba(255,200,61,0.14);
  border: 1px solid var(--accent-soft);
}

.stake-group-name {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  color: var(--ink-0);
}

.stake-group-rank {
  font-style: normal;
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--ink-3);
  min-width: 18px;
}

.stake-group-q {
  font-style: normal;
  font-size: 11px;
  font-weight: 700;
  background: var(--accent);
  color: #000;
  padding: 1px 6px;
  border-radius: 3px;
}

.stake-group-pts { color: var(--accent); font-weight: 700; }

/* Enjeu : mini-tableau */
.stake-mini-bracket {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.stake-mini-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stake-mini-col-head {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
  color: var(--ink-3);
  text-transform: uppercase;
  margin-bottom: 6px;
}

.stake-mini-match {
  background: var(--bg-2);
  border: 1px solid var(--line-2);
  border-radius: var(--r-sm);
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stake-mini-match.final { border-color: var(--accent-soft); }

.stake-mini-match.current {
  border-color: var(--accent);
  background: rgba(255,200,61,0.1);
}

.stake-mini-slot {
  font-size: 13px;
  color: var(--ink-2);
}

.stake-mini-slot.win { color: var(--ink-0); font-weight: 700; }

.stake-mini-name {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Pied discret ────────────────────────────────────────────────────── */
.sb-foot-discreet {
  position: absolute;
  bottom: 20px;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
  padding: 0 48px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.16em;
  color: var(--ink-3);
  text-transform: uppercase;
  z-index: 4;
}
</style>
