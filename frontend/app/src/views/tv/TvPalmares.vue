<script setup lang="ts">
import { ref, computed } from 'vue'
import { useLiveStore } from '@/stores/live'
import { usePolling } from '@/composables/usePolling'
import { sideName } from '@/utils/participants'
import type { Match } from '@/types'

const live = useLiveStore()

// Index de rotation par épreuve — une slide palmarès montre poules ET
// tableau de la même épreuve simultanément (pas deux slides séparées, voir
// plan #374), contrairement à TvIdle qui a un index par nature de slide.
const eventIndex = ref(0)

const currentEvent = computed(() => {
  const list = live.events
  if (list.length === 0) return null
  return list[eventIndex.value % list.length]
})

usePolling(async () => {
  eventIndex.value = (eventIndex.value + 1) % Math.max(live.events.length, 1)
}, 10000)

// Score par sets d'un côté, chiffres dans l'ordre chronologique des sets :
// sets clos (setScores) + set en cours si le match est encore en jeu
// (dupliqué depuis TvIdle.vue — pas d'import croisé entre SFC).
function sideSetScore(m: Match | null | undefined, side: 'A' | 'B'): string {
  if (!m) return ''
  const closed = (m.setScores ?? []).map(s => String(side === 'A' ? s.a : s.b))
  if (m.status === 'LIVE' && m.playStartedAt) {
    closed.push(String(side === 'A' ? m.gamesA : m.gamesB))
  }
  return closed.join(' ')
}

// Vainqueur mis en avant, dérivé du match de finale (bracket.f[0]).
const finalMatch = computed(() => currentEvent.value?.bracket?.f[0]?.match ?? null)

const winnerName = computed(() => {
  const m = finalMatch.value
  if (!m || !m.winnerSide) return null
  return m.winnerSide === 'A'
    ? (m.sideA?.player?.fullName ?? m.sideALabel ?? null)
    : (m.sideB?.player?.fullName ?? m.sideBLabel ?? null)
})
</script>

<template>
  <div class="tv-palmares">
    <div class="tv-idle-bg" />
    <div class="tv-idle-glow" />

    <!-- Header : marque + horloge (pas de barre « PROCHAIN MATCH » ni de pastilles, spec ligne 213) -->
    <header class="tv-idle-top">
      <div class="tv-idle-mark">
        <svg viewBox="0 0 24 24" width="48" height="48" style="color: var(--accent)">
          <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="1.4"/>
          <path d="M2 9c5 2.5 15 2.5 20 0M2 15c5-2.5 15-2.5 20 0" fill="none" stroke="currentColor" stroke-width="1.4"/>
        </svg>
      </div>
      <div>
        <div class="tv-idle-tournament">OPEN DE MOUTILLOUX</div>
        <div class="tv-idle-edition">ÉDITION {{ live.editionYear }}</div>
      </div>
      <div class="tv-idle-clock tab">{{ live.now }}</div>
    </header>

    <!-- Corps : poules à gauche, tableau final à droite (par épreuve) -->
    <main class="tv-palmares-main">
      <div v-if="currentEvent" class="tv-palmares-body">
        <h2 class="tv-palmares-title">
          PALMARÈS
          <em>{{ currentEvent.name }}</em>
        </h2>

        <div class="tv-palmares-columns">
          <!-- Poules -->
          <section class="tv-palmares-groups">
            <h3 class="tv-palmares-col-title">Poules</h3>
            <div v-if="currentEvent.groups.length" class="tv-groups">
              <div v-for="g in currentEvent.groups" :key="g.id" class="tv-group">
                <div class="tv-group-head">
                  <span class="tv-group-letter">{{ g.name }}</span>
                  <span class="tv-group-title">Poule {{ g.name }}</span>
                </div>
                <div class="tv-group-rows">
                  <div class="tv-group-row tv-group-row-head">
                    <span>JOUEUR</span><span>V</span><span>D</span><span>PTS</span>
                  </div>
                  <div
                    v-for="(s, i) in g.standings"
                    :key="s.entryId"
                    :class="['tv-group-row', { q: s.qualified }]"
                  >
                    <span class="tv-group-name">
                      <em class="tv-group-rank">{{ i + 1 }}</em>
                      {{ s.name }}
                      <i v-if="s.qualified" class="tv-group-q">Q</i>
                    </span>
                    <span class="tab">{{ s.wins }}</span>
                    <span class="tab">{{ s.losses }}</span>
                    <span class="tab tv-group-pts">{{ s.points }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="tv-empty">Aucune poule disponible</div>
          </section>

          <!-- Tableau final -->
          <section class="tv-palmares-bracket">
            <h3 class="tv-palmares-col-title">Tableau final</h3>
            <div v-if="currentEvent.bracket" class="tv-mini-bracket">
              <!-- QF -->
              <div v-if="currentEvent.bracket.qf?.some(s => s.match)" class="tv-mini-col">
                <div class="tv-mini-col-head">QUARTS</div>
                <div
                  v-for="slot in currentEvent.bracket.qf"
                  :key="slot.slot"
                  :class="['tv-mini-match', { done: slot.match?.winnerSide, live: slot.match?.status === 'LIVE' }]"
                >
                  <span v-if="slot.match?.status === 'LIVE'" class="tv-mini-live">EN DIRECT</span>
                  <div :class="['tv-mini-slot', { win: slot.match?.winnerSide === 'A' }]">
                    <span class="tv-mini-seed" :class="{ 'tv-mini-seed--win': slot.match?.winnerSide === 'A' }">{{ slot.match?.sideA?.seedHint ?? '' }}</span>
                    <span class="tv-mini-name">{{ sideName(slot.match?.sideA, slot.match?.sideALabel) }}</span>
                    <span v-if="sideSetScore(slot.match, 'A')" class="tv-mini-score tab">{{ sideSetScore(slot.match, 'A') }}</span>
                  </div>
                  <div :class="['tv-mini-slot', { win: slot.match?.winnerSide === 'B' }]">
                    <span class="tv-mini-seed">{{ slot.match?.sideB?.seedHint ?? '' }}</span>
                    <span class="tv-mini-name">{{ sideName(slot.match?.sideB, slot.match?.sideBLabel) }}</span>
                    <span v-if="sideSetScore(slot.match, 'B')" class="tv-mini-score tab">{{ sideSetScore(slot.match, 'B') }}</span>
                  </div>
                </div>
              </div>
              <!-- SF -->
              <div v-if="currentEvent.bracket.sf?.some(s => s.match)" class="tv-mini-col">
                <div class="tv-mini-col-head">DEMI-FINALES</div>
                <div style="height: 24px" />
                <div
                  v-for="(slot, i) in currentEvent.bracket.sf"
                  :key="slot.slot"
                  :class="['tv-mini-match', { live: slot.match?.status === 'LIVE' }]"
                  :style="{ marginTop: i > 0 ? '60px' : '0' }"
                >
                  <div :class="['tv-mini-slot', { win: slot.match?.winnerSide === 'A' }]">
                    <span class="tv-mini-seed">{{ slot.match?.sideA?.seedHint ?? '' }}</span>
                    <span class="tv-mini-name">{{ sideName(slot.match?.sideA, slot.match?.sideALabel) }}</span>
                    <span v-if="sideSetScore(slot.match, 'A')" class="tv-mini-score tab">{{ sideSetScore(slot.match, 'A') }}</span>
                  </div>
                  <div :class="['tv-mini-slot', { win: slot.match?.winnerSide === 'B' }]">
                    <span class="tv-mini-seed">{{ slot.match?.sideB?.seedHint ?? '' }}</span>
                    <span class="tv-mini-name">{{ sideName(slot.match?.sideB, slot.match?.sideBLabel) }}</span>
                    <span v-if="sideSetScore(slot.match, 'B')" class="tv-mini-score tab">{{ sideSetScore(slot.match, 'B') }}</span>
                  </div>
                </div>
              </div>
              <!-- F -->
              <div v-if="currentEvent.bracket.f?.some(s => s.match)" class="tv-mini-col">
                <div class="tv-mini-col-head">FINALE</div>
                <div style="height: 80px" />
                <div v-for="slot in currentEvent.bracket.f" :key="slot.slot" class="tv-mini-match final">
                  <div :class="['tv-mini-slot', { win: slot.match?.winnerSide === 'A' }]">
                    <span class="tv-mini-seed">{{ slot.match?.sideA?.seedHint ?? '' }}</span>
                    <span class="tv-mini-name">{{ slot.match?.sideA?.player?.fullName ?? slot.match?.sideALabel ?? 'Vainqueur SF1' }}</span>
                    <span v-if="sideSetScore(slot.match, 'A')" class="tv-mini-score tab">{{ sideSetScore(slot.match, 'A') }}</span>
                  </div>
                  <div :class="['tv-mini-slot', { win: slot.match?.winnerSide === 'B' }]">
                    <span class="tv-mini-seed">{{ slot.match?.sideB?.seedHint ?? '' }}</span>
                    <span class="tv-mini-name">{{ slot.match?.sideB?.player?.fullName ?? slot.match?.sideBLabel ?? 'Vainqueur SF2' }}</span>
                    <span v-if="sideSetScore(slot.match, 'B')" class="tv-mini-score tab">{{ sideSetScore(slot.match, 'B') }}</span>
                  </div>
                </div>

                <!-- 3e place (seulement si activée), à l'intérieur de la colonne Finale -->
                <template v-if="currentEvent.bracket.p3?.some(s => s.match)">
                  <div class="tv-mini-col-head" style="margin-top: 16px">3E PLACE</div>
                  <div v-for="slot in currentEvent.bracket.p3" :key="slot.slot" class="tv-mini-match">
                    <div :class="['tv-mini-slot', { win: slot.match?.winnerSide === 'A' }]">
                      <span class="tv-mini-seed">{{ slot.match?.sideA?.seedHint ?? '' }}</span>
                      <span class="tv-mini-name">{{ sideName(slot.match?.sideA, slot.match?.sideALabel) }}</span>
                      <span v-if="sideSetScore(slot.match, 'A')" class="tv-mini-score tab">{{ sideSetScore(slot.match, 'A') }}</span>
                    </div>
                    <div :class="['tv-mini-slot', { win: slot.match?.winnerSide === 'B' }]">
                      <span class="tv-mini-seed">{{ slot.match?.sideB?.seedHint ?? '' }}</span>
                      <span class="tv-mini-name">{{ sideName(slot.match?.sideB, slot.match?.sideBLabel) }}</span>
                      <span v-if="sideSetScore(slot.match, 'B')" class="tv-mini-score tab">{{ sideSetScore(slot.match, 'B') }}</span>
                    </div>
                  </div>
                </template>
              </div>
              <!-- Trophée : vainqueur mis en avant (nom réel, dérivé de bracket.f[0].match.winnerSide) -->
              <div class="tv-mini-col tv-mini-trophy-col">
                <div class="tv-mini-col-head" style="color: var(--accent)">VAINQUEUR</div>
                <div style="height: 60px" />
                <div class="tv-mini-trophy">
                  <svg viewBox="0 0 32 32" width="56" height="56" style="color: var(--accent)">
                    <path d="M6 4h20v6a8 8 0 01-8 8h-4a8 8 0 01-8-8V4zm0 0H2v3a3 3 0 003 3M26 4h4v3a3 3 0 01-3 3M12 18v4M20 18v4M9 26h14v2H9z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
                  </svg>
                  <div :class="['tv-mini-trophy-lbl', { won: winnerName }]">{{ winnerName ?? 'À DÉSIGNER' }}</div>
                </div>
              </div>
            </div>
            <div v-else class="tv-empty">Tableau final non disponible</div>
          </section>
        </div>
      </div>
      <div v-else class="tv-empty">Aucune épreuve disponible</div>
    </main>
  </div>
</template>

<style scoped>
.tv-palmares {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tv-idle-bg {
  position: absolute;
  inset: 0;
  background: var(--bg-0);
}

.tv-idle-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse 60% 40% at 50% 50%, rgba(255,200,61,0.08), transparent 70%);
  pointer-events: none;
}

/* Header (dupliqué depuis TvIdle.vue .tv-idle-top) */
.tv-idle-top {
  position: relative;
  height: 96px;
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 0 56px;
  border-bottom: 1px solid var(--line-1);
  flex-shrink: 0;
  z-index: 1;
}

.tv-idle-mark { animation: serveFloat 3s ease-in-out infinite; }

.tv-idle-tournament {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.2em;
  color: var(--ink-0);
}

.tv-idle-edition {
  font-size: 12px;
  color: var(--ink-3);
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.tv-idle-clock {
  margin-left: auto;
  font-size: 28px;
  font-weight: 700;
  color: var(--ink-2);
  letter-spacing: 0.04em;
}

/* Corps */
.tv-palmares-main {
  flex: 1;
  position: relative;
  overflow: hidden;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tv-palmares-body {
  width: 100%;
  max-width: 1800px;
  padding: 0 40px;
}

.tv-palmares-title {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.22em;
  color: var(--ink-3);
  text-transform: uppercase;
  margin: 0 0 28px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.tv-palmares-title em {
  font-style: normal;
  color: var(--accent);
}

.tv-palmares-columns {
  display: flex;
  align-items: flex-start;
  gap: 56px;
}

.tv-palmares-groups {
  flex: 0 0 620px;
}

.tv-palmares-bracket {
  flex: 1;
  min-width: 0;
}

.tv-palmares-col-title {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: var(--ink-3);
  text-transform: uppercase;
  margin: 0 0 20px;
}

/* Classement poules (dupliqué depuis TvIdle.vue) — empilé verticalement,
   colonne de gauche plus étroite que la slide Poules du carousel. */
.tv-groups {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.tv-group-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.tv-group-letter {
  width: 40px;
  height: 40px;
  border-radius: var(--r-md);
  background: var(--accent);
  color: #000;
  font-size: 20px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tv-group-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--ink-0);
}

.tv-group-rows { display: flex; flex-direction: column; gap: 2px; }

.tv-group-row {
  display: grid;
  grid-template-columns: 1fr 36px 36px 46px;
  padding: 7px 12px;
  border-radius: var(--r-sm);
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--ink-1);
}

.tv-group-row-head {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.16em;
  color: var(--ink-3);
  text-transform: uppercase;
}

.tv-group-row.q {
  background: linear-gradient(90deg, rgba(255,200,61,0.08), transparent);
}

.tv-group-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--ink-0);
}

.tv-group-rank {
  font-style: normal;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-3);
  min-width: 16px;
}

.tv-group-q {
  font-style: normal;
  font-size: 10px;
  font-weight: 700;
  background: var(--accent);
  color: #000;
  padding: 1px 5px;
  border-radius: 3px;
}

.tv-group-pts { color: var(--accent); font-weight: 700; }

/* Mini-bracket (dupliqué depuis TvIdle.vue) */
.tv-mini-bracket {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.tv-mini-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.tv-mini-col-head {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: var(--ink-3);
  text-transform: uppercase;
  margin-bottom: 8px;
}

.tv-mini-match {
  background: var(--bg-2);
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
}

.tv-mini-match.live { border-color: var(--accent-soft); }
.tv-mini-match.final { border-color: var(--accent-soft); }

.tv-mini-live {
  position: absolute;
  top: -10px;
  left: 10px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.1em;
  background: var(--danger);
  color: white;
  padding: 2px 6px;
  border-radius: 99px;
}

.tv-mini-slot {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--ink-2);
}

.tv-mini-slot.win { color: var(--ink-0); font-weight: 700; }

.tv-mini-seed {
  font-family: var(--font-mono);
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 3px;
  background: var(--bg-4);
  color: var(--ink-3);
}

.tv-mini-seed--win { background: var(--accent); color: #000; }
.tv-mini-name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.tv-mini-score {
  font-size: 12px;
  color: var(--ink-3);
  white-space: nowrap;
}
.tv-mini-slot.win .tv-mini-score { color: var(--ink-1); }

.tv-mini-trophy-col { align-items: center; }

.tv-mini-trophy {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.tv-mini-trophy-lbl {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--accent);
  text-align: center;
}

/* Vainqueur mis en avant : nom réel en grand/accent (remplace le libellé
   générique « À DÉSIGNER » de TvIdle.vue une fois la finale jouée). */
.tv-mini-trophy-lbl.won {
  font-size: 26px;
  font-weight: 800;
  letter-spacing: 0.02em;
  text-shadow: 0 0 20px var(--accent-glow);
}

.tv-empty {
  color: var(--ink-4);
  font-size: 16px;
  text-align: center;
  padding: 40px 0;
}
</style>
