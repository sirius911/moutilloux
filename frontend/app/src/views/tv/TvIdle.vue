<script setup lang="ts">
import { ref, computed } from 'vue'
import { useLiveStore } from '@/stores/live'
import { usePolling } from '@/composables/usePolling'
import type { Match } from '@/types'

const live = useLiveStore()
usePolling(() => live.fetchTvIdle(), 10000)

// Index de rotation par épreuve, indépendants de l'index de slide global.
const groupsEventIndex = ref(0)
const bracketEventIndex = ref(0)

// La slide "Programme terminé" ne doit s'afficher qu'une seule fois puis
// être sautée aux rotations suivantes tant qu'elle reste `finished`.
const programmeFinishedShown = ref(false)

type SlideKind = 'tournoi' | 'results' | 'groups' | 'bracket' | 'programme' | 'announces' | 'poster'

interface SlideDef {
  kind: SlideKind
}

const eventsWithGroups = computed(() =>
  live.events.filter(e => e.groups.length > 0)
)

const eventsWithBracket = computed(() =>
  live.events.filter(e => e.bracket !== null)
)

const currentGroupsEvent = computed(() => {
  const list = eventsWithGroups.value
  if (list.length === 0) return null
  return list[groupsEventIndex.value % list.length]
})

const currentBracketEvent = computed(() => {
  const list = eventsWithBracket.value
  if (list.length === 0) return null
  return list[bracketEventIndex.value % list.length]
})

const programmeVisible = computed(() => {
  const p = live.programme
  if (p.day === 'finished') {
    return p.upcoming.length > 0 || !programmeFinishedShown.value
  }
  return p.upcoming.length > 0
})

const programmeTitle = computed(() => {
  switch (live.programme.day) {
    case 'tomorrow': return 'PROGRAMME DE DEMAIN'
    case 'finished': return 'PROGRAMME TERMINÉ'
    default: return 'PROCHAINS MATCHS'
  }
})

// Liste des slides réellement affichables à l'instant courant (contenu non
// vide), calculée dynamiquement — le pager et la rotation ne portent que sur
// celles-ci. Cette liste est recalculée à chaque poll `tv/idle`, mais elle ne
// doit JAMAIS, à elle seule, changer la slide affichée : voir `displayed`
// ci-dessous, qui fige la slide courante entre deux appels à `advance()`.
const SLIDES = computed<SlideDef[]>(() => {
  const list: SlideDef[] = [{ kind: 'tournoi' }]
  if (live.recentResults.length > 0) list.push({ kind: 'results' })
  if (currentGroupsEvent.value) list.push({ kind: 'groups' })
  if (currentBracketEvent.value) list.push({ kind: 'bracket' })
  if (programmeVisible.value) list.push({ kind: 'programme' })
  if (live.announcements.length > 0) list.push({ kind: 'announces' })
  if (live.next?.posterUrl) list.push({ kind: 'poster' })
  return list
})

// Slide actuellement affichée, identifiée par sa nature (kind) — figée entre
// deux ticks de rotation (`advance()`), indépendamment des recalculs de
// SLIDES déclenchés par le polling `tv/idle`. Un rafraîchissement de données
// ne change donc jamais la slide en cours de lecture (spec tv-live §Cadre).
const displayedKind = ref<SlideKind>('tournoi')

// Compteur technique incrémenté à chaque tick de rotation ou clic `goTo`,
// utilisé comme clé de la pastille de progression : contrairement à
// `displayedKind`, il change même quand la slide affichée reste la même
// (composition à une seule slide), pour que le remplissage reparte de zéro
// à chaque cycle de 8 s (voir spec tv-live §Cadre, pastille de progression).
const pagerTick = ref(0)

const currentSlide = computed<SlideKind>(() => displayedKind.value)

// Position de la slide affichée dans la liste fraîche, pour le pager — par
// recherche de kind, jamais par index brut.
const displayedIndex = computed(() => {
  const i = SLIDES.value.findIndex(s => s.kind === displayedKind.value)
  return i === -1 ? 0 : i
})

function advance() {
  const list = SLIDES.value
  if (list.length === 0) return

  // Position (dans la liste fraîche) de la slide actuellement affichée ; si
  // elle a disparu de la composition (devenue vide), on avance depuis la
  // position qu'elle occuperait pour rester cohérent avec l'ordre déclaré.
  const currentIndex = list.findIndex(s => s.kind === displayedKind.value)

  const nextIndex = (currentIndex + 1) % list.length
  const upcomingKind = list[nextIndex].kind

  if (upcomingKind === 'groups') {
    groupsEventIndex.value = (groupsEventIndex.value + 1) % Math.max(eventsWithGroups.value.length, 1)
  }
  if (upcomingKind === 'bracket') {
    bracketEventIndex.value = (bracketEventIndex.value + 1) % Math.max(eventsWithBracket.value.length, 1)
  }
  if (upcomingKind === 'programme' && live.programme.day === 'finished') {
    programmeFinishedShown.value = true
  }

  displayedKind.value = upcomingKind
  pagerTick.value++
}

function goTo(i: number) {
  const target = SLIDES.value[i]
  if (!target) return
  displayedKind.value = target.kind
  pagerTick.value++
}

usePolling(async () => {
  advance()
}, 8000)

function nextPlayerName(side: 'A' | 'B'): string {
  if (!live.next) return 'À désigner'
  if (side === 'A') return live.next.sideA?.player?.fullName ?? live.next.sideALabel ?? 'À désigner'
  return live.next.sideB?.player?.fullName ?? live.next.sideBLabel ?? 'À désigner'
}

// Score par sets d'un côté, chiffres dans l'ordre chronologique des sets :
// sets clos (setScores) + set en cours si le match est encore en jeu.
function sideSetScore(m: Match | null | undefined, side: 'A' | 'B'): string {
  if (!m) return ''
  const closed = (m.setScores ?? []).map(s => String(side === 'A' ? s.a : s.b))
  if (m.status === 'LIVE' && m.playStartedAt) {
    closed.push(String(side === 'A' ? m.gamesA : m.gamesB))
  }
  return closed.join(' ')
}
</script>

<template>
  <div class="tv-idle">
    <div class="tv-idle-bg" />
    <div class="tv-idle-glow" />

    <!-- Header -->
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

    <!-- Slides -->
    <main class="tv-idle-main">
      <!-- Slide : Tournoi -->
      <section :class="['tv-slide', { on: currentSlide === 'tournoi' }]">
        <div class="tv-idle-hero">
          <div class="tv-idle-ball">
            <svg viewBox="0 0 24 24" width="80" height="80">
              <circle cx="12" cy="12" r="10" fill="#E8F35A"/>
              <path d="M2.5 12c4-1 8.5-1 12.5 3 1.5 1.5 4.5 2.5 6.5 2.5M2.5 12c4 1 8.5 1 12.5-3 1.5-1.5 4.5-2.5 6.5-2.5" fill="none" stroke="rgba(0,0,0,0.4)" stroke-width="0.7"/>
            </svg>
          </div>
          <div class="tv-idle-status">EN ATTENTE DU PROCHAIN MATCH</div>
          <div class="tv-idle-hero-stats">
            <div class="tv-idle-hero-stat">
              <span>MATCHS JOUÉS</span>
              <b class="tab">{{ live.stats?.matchesFinished ?? 0 }} / {{ live.stats?.matchesTotal ?? 0 }}</b>
            </div>
            <div class="tv-idle-hero-stat">
              <span>INSCRITS</span>
              <b class="tab">{{ live.stats?.entriesCount ?? 0 }}</b>
            </div>
            <div class="tv-idle-hero-stat">
              <span>ÉPREUVES</span>
              <b class="tab">{{ live.stats?.eventsCount ?? 0 }}</b>
            </div>
          </div>
        </div>
      </section>

      <!-- Slide : Derniers résultats -->
      <section :class="['tv-slide', { on: currentSlide === 'results' }]">
        <div class="tv-rotate">
          <h2 class="tv-rotate-title">
            DERNIERS RÉSULTATS
          </h2>
          <div class="tv-results">
            <div
              v-for="m in live.recentResults"
              :key="m.id"
              class="tv-result-row"
            >
              <span class="tv-result-stage">{{ m.stageLabel }}</span>
              <div class="tv-result-match">
                <div :class="['tv-result-side', { win: m.winnerSide === 'A' }]">
                  <span v-if="m.sideA?.seedHint" class="tv-result-seed" :class="{ 'tv-result-seed--win': m.winnerSide === 'A' }">{{ m.sideA.seedHint }}</span>
                  <span class="tv-result-name">{{ m.sideA?.player?.fullName ?? m.sideALabel ?? 'À désigner' }}</span>
                </div>
                <div :class="['tv-result-side', { win: m.winnerSide === 'B' }]">
                  <span v-if="m.sideB?.seedHint" class="tv-result-seed" :class="{ 'tv-result-seed--win': m.winnerSide === 'B' }">{{ m.sideB.seedHint }}</span>
                  <span class="tv-result-name">{{ m.sideB?.player?.fullName ?? m.sideBLabel ?? 'À désigner' }}</span>
                </div>
              </div>
              <span class="tv-result-score tab">
                {{ m.setScores?.map(s => `${s.a}-${s.b}`).join(' ') ?? `${m.gamesA}-${m.gamesB}` }}
              </span>
              <span v-if="m.court" class="tv-result-court">{{ m.court }}</span>
            </div>
            <div v-if="live.recentResults.length === 0" class="tv-empty">Aucun résultat disponible</div>
          </div>
        </div>
      </section>

      <!-- Slide : Poules (rotation par épreuve) -->
      <section :class="['tv-slide', { on: currentSlide === 'groups' }]">
        <div class="tv-rotate">
          <h2 class="tv-rotate-title">
            CLASSEMENT DES POULES
            <em v-if="currentGroupsEvent">{{ currentGroupsEvent.name }}</em>
          </h2>
          <div v-if="currentGroupsEvent" class="tv-groups">
            <div v-for="g in currentGroupsEvent.groups" :key="g.id" class="tv-group">
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
        </div>
      </section>

      <!-- Slide : Tableau (rotation par épreuve) -->
      <section :class="['tv-slide', { on: currentSlide === 'bracket' }]">
        <div class="tv-rotate">
          <h2 class="tv-rotate-title">
            TABLEAU FINAL
            <em v-if="currentBracketEvent">{{ currentBracketEvent.name }}</em>
          </h2>
          <div v-if="currentBracketEvent?.bracket" class="tv-mini-bracket">
            <!-- QF -->
            <div class="tv-mini-col">
              <div class="tv-mini-col-head">QUARTS</div>
              <div
                v-for="slot in currentBracketEvent.bracket.qf"
                :key="slot.slot"
                :class="['tv-mini-match', { done: slot.match?.winnerSide, live: slot.match?.status === 'LIVE' }]"
              >
                <span v-if="slot.match?.status === 'LIVE'" class="tv-mini-live">EN DIRECT</span>
                <div :class="['tv-mini-slot', { win: slot.match?.winnerSide === 'A' }]">
                  <span class="tv-mini-seed" :class="{ 'tv-mini-seed--win': slot.match?.winnerSide === 'A' }">{{ slot.match?.sideA?.seedHint ?? '' }}</span>
                  <span class="tv-mini-name">{{ slot.match?.sideA?.player?.fullName ?? slot.match?.sideALabel ?? 'À désigner' }}</span>
                  <span v-if="sideSetScore(slot.match, 'A')" class="tv-mini-score tab">{{ sideSetScore(slot.match, 'A') }}</span>
                </div>
                <div :class="['tv-mini-slot', { win: slot.match?.winnerSide === 'B' }]">
                  <span class="tv-mini-seed">{{ slot.match?.sideB?.seedHint ?? '' }}</span>
                  <span class="tv-mini-name">{{ slot.match?.sideB?.player?.fullName ?? slot.match?.sideBLabel ?? 'À désigner' }}</span>
                  <span v-if="sideSetScore(slot.match, 'B')" class="tv-mini-score tab">{{ sideSetScore(slot.match, 'B') }}</span>
                </div>
              </div>
            </div>
            <!-- SF -->
            <div class="tv-mini-col">
              <div class="tv-mini-col-head">DEMI-FINALES</div>
              <div style="height: 24px" />
              <div
                v-for="(slot, i) in currentBracketEvent.bracket.sf"
                :key="slot.slot"
                :class="['tv-mini-match', { live: slot.match?.status === 'LIVE' }]"
                :style="{ marginTop: i > 0 ? '60px' : '0' }"
              >
                <div :class="['tv-mini-slot', { win: slot.match?.winnerSide === 'A' }]">
                  <span class="tv-mini-seed">{{ slot.match?.sideA?.seedHint ?? '' }}</span>
                  <span class="tv-mini-name">{{ slot.match?.sideA?.player?.fullName ?? slot.match?.sideALabel ?? 'À désigner' }}</span>
                  <span v-if="sideSetScore(slot.match, 'A')" class="tv-mini-score tab">{{ sideSetScore(slot.match, 'A') }}</span>
                </div>
                <div :class="['tv-mini-slot', { win: slot.match?.winnerSide === 'B' }]">
                  <span class="tv-mini-seed">{{ slot.match?.sideB?.seedHint ?? '' }}</span>
                  <span class="tv-mini-name">{{ slot.match?.sideB?.player?.fullName ?? slot.match?.sideBLabel ?? 'À désigner' }}</span>
                  <span v-if="sideSetScore(slot.match, 'B')" class="tv-mini-score tab">{{ sideSetScore(slot.match, 'B') }}</span>
                </div>
              </div>
            </div>
            <!-- F -->
            <div class="tv-mini-col">
              <div class="tv-mini-col-head">FINALE</div>
              <div style="height: 80px" />
              <div v-for="slot in currentBracketEvent.bracket.f" :key="slot.slot" class="tv-mini-match final">
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
            </div>
            <!-- 3e place (seulement si activée) -->
            <div v-if="currentBracketEvent.bracket.p3?.length" class="tv-mini-col">
              <div class="tv-mini-col-head">3E PLACE</div>
              <div style="height: 80px" />
              <div v-for="slot in currentBracketEvent.bracket.p3" :key="slot.slot" class="tv-mini-match">
                <div :class="['tv-mini-slot', { win: slot.match?.winnerSide === 'A' }]">
                  <span class="tv-mini-seed">{{ slot.match?.sideA?.seedHint ?? '' }}</span>
                  <span class="tv-mini-name">{{ slot.match?.sideA?.player?.fullName ?? slot.match?.sideALabel ?? 'À désigner' }}</span>
                  <span v-if="sideSetScore(slot.match, 'A')" class="tv-mini-score tab">{{ sideSetScore(slot.match, 'A') }}</span>
                </div>
                <div :class="['tv-mini-slot', { win: slot.match?.winnerSide === 'B' }]">
                  <span class="tv-mini-seed">{{ slot.match?.sideB?.seedHint ?? '' }}</span>
                  <span class="tv-mini-name">{{ slot.match?.sideB?.player?.fullName ?? slot.match?.sideBLabel ?? 'À désigner' }}</span>
                  <span v-if="sideSetScore(slot.match, 'B')" class="tv-mini-score tab">{{ sideSetScore(slot.match, 'B') }}</span>
                </div>
              </div>
            </div>
            <!-- Trophée -->
            <div class="tv-mini-col tv-mini-trophy-col">
              <div class="tv-mini-col-head" style="color: var(--accent)">VAINQUEUR</div>
              <div style="height: 60px" />
              <div class="tv-mini-trophy">
                <svg viewBox="0 0 32 32" width="44" height="44" style="color: var(--accent)">
                  <path d="M6 4h20v6a8 8 0 01-8 8h-4a8 8 0 01-8-8V4zm0 0H2v3a3 3 0 003 3M26 4h4v3a3 3 0 01-3 3M12 18v4M20 18v4M9 26h14v2H9z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
                </svg>
                <div class="tv-mini-trophy-lbl">À DÉSIGNER</div>
              </div>
            </div>
          </div>
          <div v-else class="tv-empty">Tableau final non disponible</div>
        </div>
      </section>

      <!-- Slide : Programme -->
      <section :class="['tv-slide', { on: currentSlide === 'programme' }]">
        <div class="tv-rotate">
          <h2 class="tv-rotate-title">{{ programmeTitle }}</h2>
          <div class="tv-programme">
            <div v-if="live.programme.upcoming.length === 0" class="tv-empty">
              Aucun match programmé
            </div>
            <div
              v-for="(m, i) in live.programme.upcoming"
              :key="m.id"
              :class="['tv-prog-row', { bientot: i === 0 }]"
            >
              <span class="tv-prog-time tab">~{{ m.scheduledTime ?? '—' }}</span>
              <div class="tv-prog-match">
                <span class="tv-prog-name">{{ m.sideA?.player?.fullName ?? m.sideALabel ?? 'À désigner' }}</span>
                <em class="tv-prog-vs">vs</em>
                <span class="tv-prog-name">{{ m.sideB?.player?.fullName ?? m.sideBLabel ?? 'À désigner' }}</span>
              </div>
              <span class="tv-prog-group">{{ m.stageLabel }}</span>
              <span v-if="i === 0" class="tv-prog-bientot">bientôt</span>
            </div>
          </div>
          <p class="tv-prog-disclaimer">
            Horaires estimés — susceptibles de bouger
          </p>
        </div>
      </section>

      <!-- Slide : Annonces -->
      <section :class="['tv-slide', { on: currentSlide === 'announces' }]">
        <div class="tv-rotate">
          <h2 class="tv-rotate-title">ANNONCES</h2>
          <div class="tv-announces">
            <div
              v-for="a in live.announcements"
              :key="a.id"
              class="tv-announce-row"
            >
              {{ a.message }}
            </div>
            <div v-if="live.announcements.length === 0" class="tv-empty">Aucune annonce</div>
          </div>
        </div>
      </section>

      <!-- Slide : Affiche du prochain match -->
      <section :class="['tv-slide', 'tv-slide-poster', { on: currentSlide === 'poster' }]">
        <div
          v-if="live.next?.posterUrl"
          class="tv-slide-poster-bg"
          :style="{ backgroundImage: `url(${live.next.posterUrl})` }"
        />
        <div v-if="live.next" class="tv-slide-poster-band">
          <span v-if="live.next.scheduledTime" class="tv-slide-poster-time tab">~{{ live.next.scheduledTime }}</span>
          <span class="tv-slide-poster-side">{{ nextPlayerName('A') }}</span>
          <em class="tv-slide-poster-vs">vs</em>
          <span class="tv-slide-poster-side">{{ nextPlayerName('B') }}</span>
        </div>
      </section>
    </main>

    <!-- Footer : prochain match + paginateur -->
    <footer class="tv-idle-foot">
      <div v-if="live.next" class="tv-idle-next-bar">
        <span class="tv-idle-next-bar-lbl">PROCHAIN MATCH</span>
        <span v-if="live.next.scheduledTime" class="tv-idle-next-bar-time tab">{{ live.next.scheduledTime }}</span>
        <span class="tv-idle-next-bar-sep" />
        <span class="tv-idle-next-bar-side">
          <em v-if="live.next.sideA?.seedHint" class="tv-idle-next-bar-seed">{{ live.next.sideA.seedHint }}</em>
          <b>{{ nextPlayerName('A') }}</b>
        </span>
        <span class="tv-idle-next-bar-vs">vs</span>
        <span class="tv-idle-next-bar-side">
          <em v-if="live.next.sideB?.seedHint" class="tv-idle-next-bar-seed">{{ live.next.sideB.seedHint }}</em>
          <b>{{ nextPlayerName('B') }}</b>
        </span>
        <span v-if="live.next.court" class="tv-idle-next-bar-sep" />
        <span v-if="live.next.court" class="tv-idle-next-bar-court">{{ live.next.court }}</span>
      </div>
      <div v-else class="tv-idle-next-bar tv-idle-next-bar--empty">
        Programme du tournoi en cours de préparation
      </div>

      <div class="tv-idle-foot-pager">
        <i
          v-for="(_, i) in SLIDES"
          :key="i"
          :class="{ on: i === displayedIndex }"
          @click="goTo(i)"
        >
          <em
            v-if="i === displayedIndex"
            :key="pagerTick"
            class="tv-idle-foot-pager-fill"
          />
        </i>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.tv-idle {
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

/* Header */
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

/* Main slides */
.tv-idle-main {
  flex: 1;
  position: relative;
  overflow: hidden;
  z-index: 1;
}

.tv-slide {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 600ms ease;
  pointer-events: none;
}

.tv-slide.on {
  opacity: 1;
  pointer-events: auto;
}

/* Slide Hero */
.tv-idle-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
}

.tv-idle-ball { animation: serveFloat 2s ease-in-out infinite; }

.tv-idle-status {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 0.22em;
  color: var(--accent);
  text-transform: uppercase;
}

.tv-idle-hero-stats {
  display: flex;
  gap: 80px;
}

.tv-idle-hero-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.tv-idle-hero-stat span {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.18em;
  color: var(--ink-3);
  text-transform: uppercase;
}

.tv-idle-hero-stat b {
  font-size: 48px;
  font-weight: 800;
  color: var(--ink-0);
}

/* Slide Résultats / Classement / Bracket */
.tv-rotate {
  width: 100%;
  max-width: 1760px;
  padding: 0 40px;
}

.tv-rotate-title {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.22em;
  color: var(--ink-3);
  text-transform: uppercase;
  margin: 0 0 32px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.tv-rotate-title em {
  font-style: normal;
  color: var(--accent);
}

/* Résultats */
.tv-results {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tv-result-row {
  display: flex;
  align-items: center;
  gap: 20px;
  background: var(--bg-2);
  border: 1px solid var(--line-1);
  border-radius: var(--r-md);
  padding: 14px 20px;
}

.tv-result-stage {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.12em;
  color: var(--ink-3);
  text-transform: uppercase;
  min-width: 160px;
}

.tv-result-match {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tv-result-side {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  color: var(--ink-2);
}

.tv-result-side.win { color: var(--ink-0); font-weight: 700; }

.tv-result-seed {
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 2px 6px;
  border-radius: var(--r-xs);
  background: var(--bg-4);
  color: var(--ink-2);
}

.tv-result-seed--win { background: var(--accent); color: #000; }

.tv-result-name { flex: 1; }

.tv-result-score {
  font-size: 20px;
  font-weight: 700;
  color: var(--ink-0);
  min-width: 100px;
  text-align: right;
}

.tv-result-court {
  font-size: 12px;
  color: var(--ink-3);
  min-width: 80px;
  text-align: right;
}

/* Classement poules */
.tv-groups {
  display: flex;
  gap: 40px;
}

.tv-group { flex: 1; }

.tv-group-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.tv-group-letter {
  width: 48px;
  height: 48px;
  border-radius: var(--r-md);
  background: var(--accent);
  color: #000;
  font-size: 24px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tv-group-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--ink-0);
}

.tv-group-rows { display: flex; flex-direction: column; gap: 2px; }

.tv-group-row {
  display: grid;
  grid-template-columns: 1fr 40px 40px 50px;
  padding: 8px 12px;
  border-radius: var(--r-sm);
  align-items: center;
  gap: 8px;
  font-size: 16px;
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
  font-size: 12px;
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

/* Mini-bracket */
.tv-mini-bracket {
  display: flex;
  gap: 32px;
  align-items: flex-start;
}

.tv-mini-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  font-size: 14px;
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
.tv-mini-name { flex: 1; }

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
  gap: 10px;
}

.tv-mini-trophy-lbl {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--accent);
}

/* Footer */
.tv-idle-foot {
  position: relative;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 56px;
  border-top: 1px solid var(--line-1);
  flex-shrink: 0;
  z-index: 1;
}

.tv-idle-next-bar {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 13px;
  color: var(--ink-2);
}

.tv-idle-next-bar--empty {
  color: var(--ink-4);
  font-style: italic;
}

.tv-idle-next-bar-lbl {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: var(--ink-3);
  text-transform: uppercase;
}

.tv-idle-next-bar-time {
  font-size: 15px;
  font-weight: 700;
  color: var(--accent);
}

.tv-idle-next-bar-sep {
  width: 1px;
  height: 20px;
  background: var(--line-2);
}

.tv-idle-next-bar-side {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--ink-0);
}

.tv-idle-next-bar-seed {
  font-style: normal;
  font-family: var(--font-mono);
  font-size: 11px;
  background: var(--accent);
  color: #000;
  padding: 2px 6px;
  border-radius: 3px;
}

.tv-idle-next-bar-vs {
  font-size: 11px;
  color: var(--ink-3);
  letter-spacing: 0.08em;
}

.tv-idle-next-bar-court {
  font-weight: 600;
  color: var(--ink-2);
}

.tv-idle-foot-pager {
  display: flex;
  gap: 6px;
  align-items: center;
}

.tv-idle-foot-pager i {
  position: relative;
  width: 20px;
  height: 4px;
  border-radius: 2px;
  background: var(--line-3);
  cursor: pointer;
  transition: background 300ms, width 300ms;
  display: block;
  overflow: hidden;
}

.tv-idle-foot-pager i.on {
  background: var(--line-3);
  width: 32px;
}

.tv-idle-foot-pager-fill {
  position: absolute;
  inset: 0;
  width: 0;
  background: var(--accent);
  border-radius: 2px;
  animation: pagerFill 8s linear forwards;
}

@keyframes pagerFill {
  from { width: 0; }
  to { width: 100%; }
}

.tv-empty {
  color: var(--ink-4);
  font-size: 16px;
  text-align: center;
  padding: 40px 0;
}

/* Slide Programme */
.tv-programme {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tv-prog-row {
  display: flex;
  align-items: center;
  gap: 20px;
  background: var(--bg-2);
  border: 1px solid var(--line-1);
  border-radius: var(--r-md);
  padding: 14px 20px;
  transition: border-color 300ms;
}

.tv-prog-row.bientot {
  border-color: var(--accent-soft);
  background: linear-gradient(90deg, rgba(255,200,61,0.08), transparent);
}

.tv-prog-time {
  font-size: 18px;
  font-weight: 700;
  color: var(--accent);
  min-width: 90px;
}

.tv-prog-match {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.tv-prog-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--ink-0);
}

.tv-prog-vs {
  font-style: normal;
  font-size: 12px;
  color: var(--ink-3);
  letter-spacing: 0.08em;
  flex-shrink: 0;
}

.tv-prog-group {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.12em;
  color: var(--ink-3);
  text-transform: uppercase;
  min-width: 160px;
  text-align: right;
}

.tv-prog-bientot {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  background: var(--accent);
  color: #000;
  padding: 3px 8px;
  border-radius: 99px;
  flex-shrink: 0;
}

.tv-prog-disclaimer {
  margin: 16px 0 0;
  font-size: 12px;
  color: var(--ink-4);
  font-style: italic;
  text-align: center;
}

/* Slide Annonces */
.tv-announces {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.tv-announce-row {
  background: var(--bg-2);
  border: 1px solid var(--accent-soft);
  border-radius: var(--r-md);
  padding: 28px 36px;
  font-size: 28px;
  font-weight: 700;
  color: var(--ink-0);
  text-align: center;
  line-height: 1.4;
}

/* Slide Affiche */
.tv-slide-poster {
  justify-content: flex-start;
  align-items: flex-end;
}

.tv-slide-poster-bg {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center top;
  background-repeat: no-repeat;
  background-color: var(--bg-0);
}

.tv-slide-poster-band {
  position: relative;
  z-index: 1;
  width: 100%;
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px 56px;
  background: linear-gradient(0deg, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.4) 70%, transparent 100%);
}

.tv-slide-poster-time {
  font-size: 20px;
  font-weight: 700;
  color: var(--accent);
}

.tv-slide-poster-side {
  font-size: 26px;
  font-weight: 700;
  color: var(--ink-0);
}

.tv-slide-poster-vs {
  font-style: normal;
  font-size: 14px;
  color: var(--ink-3);
  letter-spacing: 0.08em;
}
</style>
