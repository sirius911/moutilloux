<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useLiveStore } from '@/stores/live'
import { usePolling } from '@/composables/usePolling'
import { useScale } from '@/composables/useScale'
import { useApi } from '@/composables/useApi'
import type { Match } from '@/types'

const props = defineProps<{ matchId: number }>()
const router = useRouter()
const { get, post } = useApi()
const live = useLiveStore()

// Polling du match arbitré (et non plus le hero global) — 2s
usePolling(() => live.fetchMatch(props.matchId), 2000)

const match = computed(() => live.match)

const TARGET_W = 834
const TARGET_H = 1112

const containerRef = ref<HTMLElement | null>(null)
const { scale, offsetX, offsetY } = useScale(containerRef, TARGET_W, TARGET_H)

// Modal de confirmation générique (reset_all)
const confirmModal = ref<{ action: string; label: string } | null>(null)

// Modal de fin de match — sélection du vainqueur
interface FinishCandidate {
  winner: 'A' | 'B'
  name: string
  isLeading: boolean
}
const finishModal = ref(false)
const retirement = ref(false)

// Modal de forfait — désigner le joueur présent (SCHEDULED uniquement)
const forfaitModal = ref(false)

async function confirmForfait(winner: 'A' | 'B') {
  const ok = await sendAction('forfait', { winner })
  if (ok) forfaitModal.value = false
}

// Tiroir « Corrections » — jeux±, sets±, serveur, inversion d'affichage
const correctionsOpen = ref(false)

// Affichage swap — état local, en lock-step avec le flag de session back (voir plan #283)
const swapped = ref(false)

function sideAt(pos: 'left' | 'right'): 'A' | 'B' {
  const base: 'A' | 'B' = pos === 'left' ? 'A' : 'B'
  if (!swapped.value) return base
  return base === 'A' ? 'B' : 'A'
}
const leftModelSide = computed(() => sideAt('left'))
const rightModelSide = computed(() => sideAt('right'))

function playerName(side: 'A' | 'B'): string {
  if (!match.value) return side === 'A' ? 'Joueur A' : 'Joueur B'
  return side === 'A'
    ? (match.value.sideA?.player?.fullName ?? match.value.sideALabel ?? 'Joueur A')
    : (match.value.sideB?.player?.fullName ?? match.value.sideBLabel ?? 'Joueur B')
}
function sideSets(side: 'A' | 'B'): number {
  return side === 'A' ? (match.value?.setsA ?? 0) : (match.value?.setsB ?? 0)
}
function sideGames(side: 'A' | 'B'): number {
  return side === 'A' ? (match.value?.gamesA ?? 0) : (match.value?.gamesB ?? 0)
}
function sidePoints(side: 'A' | 'B'): number {
  return side === 'A' ? (match.value?.pointsA ?? 0) : (match.value?.pointsB ?? 0)
}
function sideTbPoints(side: 'A' | 'B'): number {
  return side === 'A' ? (match.value?.tbPointsA ?? 0) : (match.value?.tbPointsB ?? 0)
}

async function handleSwap() {
  const ok = await sendAction('swap')
  if (ok) swapped.value = !swapped.value
}

// Toast d'erreur (action refusée par le moteur de score → message JSON renvoyé)
const error = ref('')
let errorTimer: ReturnType<typeof setTimeout> | null = null
function showError(msg: string) {
  error.value = msg
  if (errorTimer) clearTimeout(errorTimer)
  errorTimer = setTimeout(() => { error.value = '' }, 4000)
}

function extractError(e: unknown): string {
  const raw = e instanceof Error ? e.message : String(e)
  const sep = raw.indexOf('— ')
  const tail = sep >= 0 ? raw.slice(sep + 2) : raw
  try {
    const parsed = JSON.parse(tail)
    if (parsed && typeof parsed.error === 'string') return parsed.error
  } catch { /* corps non-JSON : on garde le fallback */ }
  return 'Action impossible.'
}

async function sendAction(action: string, extra: Record<string, unknown> = {}): Promise<boolean> {
  try {
    await post(`/arbitre/match/${props.matchId}/action/`, { action, ...extra })
    // Le moteur renvoie {ok:true} sans l'état → on rafraîchit tout de suite
    // (sans attendre le tick de polling) pour un retour immédiat.
    await live.fetchMatch(props.matchId)
    return true
  } catch (e) {
    showError(extractError(e))
    return false
  }
}

function handleTap(side: 'left' | 'right') {
  const action = side === 'left' ? 'point_left' : 'point_right'
  sendAction(action)
}

function handleUndo() {
  sendAction('reset_points')
}

function askConfirm(action: string, label: string) {
  confirmModal.value = { action, label }
}

async function confirm() {
  if (!confirmModal.value) return
  const ok = await sendAction(confirmModal.value.action)
  if (ok) confirmModal.value = null
}

function cancel() {
  confirmModal.value = null
}

// Fin de match — vainqueur explicite
function openFinishModal() {
  retirement.value = false
  finishModal.value = true
}

async function confirmFinish(winner: 'A' | 'B') {
  const ok = await sendAction('finish_winner', { winner, retirement: retirement.value })
  if (ok) finishModal.value = false
}

function closeFinishModal() {
  retirement.value = false
  finishModal.value = false
}

const finishCandidates = computed((): { a: FinishCandidate; b: FinishCandidate } | null => {
  if (!match.value) return null
  const m = match.value

  const nameA = m.sideA?.player?.fullName ?? m.sideALabel ?? 'Joueur A'
  const nameB = m.sideB?.player?.fullName ?? m.sideBLabel ?? 'Joueur B'

  // Déduction du meneur dans le repère modèle (A/B fixes, indépendamment du swap)
  const aLeads = m.setsA > m.setsB || (m.setsA === m.setsB && m.gamesA > m.gamesB)
  const bLeads = m.setsB > m.setsA || (m.setsA === m.setsB && m.gamesB > m.gamesA)

  return {
    a: { winner: 'A', name: nameA, isLeading: aLeads },
    b: { winner: 'B', name: nameB, isLeading: bLeads },
  }
})

function pointDisplay(n: number, inTb: boolean): string {
  if (inTb) return String(n)
  const map: Record<number, string> = { 0: '0', 1: '15', 2: '30', 3: '40' }
  return map[n] ?? '40'
}

const statusLabel = computed(() => {
  if (!match.value) return ''
  if (match.value.status === 'SCHEDULED') return 'PRÉVU'
  if (match.value.status === 'CANCELED') return 'ANNULÉ'
  if (match.value.tbActive) return 'JEU DÉCISIF'
  if (match.value.status === 'FINISHED') return 'TERMINÉ'
  return 'EN COURS'
})

const isFinished = computed(() => match.value?.status === 'FINISHED')
const isScheduled = computed(() => match.value?.status === 'SCHEDULED')
const isLive = computed(() => match.value?.status === 'LIVE')
const isCanceled = computed(() => match.value?.status === 'CANCELED')
const isReadOnly = computed(() => isFinished.value || isCanceled.value)

async function handleStart() {
  try {
    const others = await get<Match[]>('/api/arbitre/matches/')
    const anotherLive = others.some((m) => m.id !== props.matchId && m.status === 'LIVE')
    if (anotherLive) {
      askConfirm('start', 'Démarrer le match ?')
    } else {
      await sendAction('start')
    }
  } catch {
    // Si la vérification échoue (réseau), on retombe sur l'action directe :
    // le back est idempotent et gère l'invariant mono-LIVE de toute façon.
    await sendAction('start')
  }
}
</script>

<template>
  <div ref="containerRef" class="arb-container">
    <div
      class="arb-stage"
      :style="{
        width: `${TARGET_W}px`,
        height: `${TARGET_H}px`,
        transform: `translate(${offsetX}px, ${offsetY}px) scale(${scale})`,
        transformOrigin: 'top left',
      }"
    >
      <!-- Header -->
      <header class="arb-header">
        <button class="btn-back" @click="router.push('/arbitre')">←</button>
        <div class="arb-header-center">
          <span class="arb-category">{{ match?.stageLabel ?? '—' }}</span>
          <span v-if="match?.formatLabel" class="arb-format">{{ match.formatLabel }}</span>
          <span class="arb-status-badge" :class="{ tb: match?.tbActive, finished: isFinished, scheduled: isScheduled, canceled: isCanceled }">
            {{ statusLabel }}
          </span>
        </div>
        <div style="width: 44px" />
      </header>

      <!-- Bloc score -->
      <div class="arb-score-block">
        <!-- Joueur (côté gauche affiché) -->
        <div class="arb-score-player">
          <span class="arb-player-label">{{ playerName(leftModelSide) }}</span>
          <div class="arb-player-meta">
            <span>SETS {{ sideSets(leftModelSide) }}</span>
            <span>JEUX {{ sideGames(leftModelSide) }}</span>
            <span v-if="match?.server === leftModelSide" class="serve-indicator">●</span>
          </div>
        </div>

        <!-- Score central -->
        <div class="arb-score-center">
          <span class="score-label">{{ match?.tbActive ? 'JEU DÉCISIF' : 'POINT' }}</span>
          <div class="score-nums tab">
            <span class="score-a">
              {{ match ? (match.tbActive ? sideTbPoints(leftModelSide) : pointDisplay(sidePoints(leftModelSide), false)) : '0' }}
            </span>
            <span class="score-sep">·</span>
            <span class="score-b">
              {{ match ? (match.tbActive ? sideTbPoints(rightModelSide) : pointDisplay(sidePoints(rightModelSide), false)) : '0' }}
            </span>
          </div>
        </div>

        <!-- Joueur (côté droit affiché) -->
        <div class="arb-score-player arb-score-player--right">
          <span class="arb-player-label">{{ playerName(rightModelSide) }}</span>
          <div class="arb-player-meta">
            <span v-if="match?.server === rightModelSide" class="serve-indicator">●</span>
            <span>SETS {{ sideSets(rightModelSide) }}</span>
            <span>JEUX {{ sideGames(rightModelSide) }}</span>
          </div>
        </div>
      </div>

      <!-- Zones de tap -->
      <div class="arb-tap-area" :class="{ disabled: !isLive }">
        <button class="tap-zone tap-zone--a" :disabled="!isLive" @click="handleTap('left')">
          <span class="tap-player-name">{{ playerName(leftModelSide) }}</span>
          <span class="tap-cta">+ POINT</span>
          <span class="tap-hint">TAP ICI</span>
        </button>
        <button class="tap-zone tap-zone--b" :disabled="!isLive" @click="handleTap('right')">
          <span class="tap-player-name">{{ playerName(rightModelSide) }}</span>
          <span class="tap-cta">+ POINT</span>
          <span class="tap-hint">TAP ICI</span>
        </button>
      </div>

      <!-- Footer actions -->
      <footer class="arb-footer">
        <template v-if="isScheduled">
          <button
            class="action-btn action-btn--primary"
            title="Démarrer le match"
            :disabled="!match?.sideA || !match?.sideB"
            @click="handleStart"
          >
            <span class="action-icon">▶</span>
            <span class="action-label">Démarrer le match</span>
          </button>
          <button class="action-btn" title="Déclarer forfait" @click="forfaitModal = true">
            <span class="action-icon">⚑</span>
            <span class="action-label">Forfait</span>
          </button>
          <button
            class="action-btn action-btn--danger-ghost"
            title="Annuler le match"
            @click="askConfirm('annuler', 'Annuler le match ?')"
          >
            <span class="action-icon">✕</span>
            <span class="action-label">Annuler</span>
          </button>
        </template>
        <template v-else>
          <button class="action-btn" title="Remettre les points à 0-0" :disabled="isReadOnly" @click="handleUndo">
            <span class="action-icon">↩</span>
            <span class="action-label">0 pts</span>
          </button>
          <button class="action-btn" title="Corrections" :disabled="isReadOnly" @click="correctionsOpen = true">
            <span class="action-icon">✎</span>
            <span class="action-label">Corrections</span>
          </button>
          <button
            v-if="!isReadOnly"
            class="action-btn action-btn--danger"
            title="Terminer le match"
            @click="openFinishModal"
          >
            <span class="action-icon">■</span>
            <span class="action-label">Terminer</span>
          </button>
          <button
            class="action-btn action-btn--danger-ghost"
            title="Réinitialiser"
            :disabled="isReadOnly"
            @click="askConfirm('reset_all', 'Réinitialiser le match ?')"
          >
            <span class="action-icon">↺</span>
            <span class="action-label">Reset</span>
          </button>
        </template>
      </footer>
    </div>

    <!-- Toast d'erreur -->
    <Teleport to="body">
      <div v-if="error" class="arb-toast" role="alert">{{ error }}</div>
    </Teleport>

    <!-- Modal de confirmation générique (reset_all, etc.) -->
    <Teleport to="body">
      <div v-if="confirmModal" class="modal-backdrop" @click.self="cancel">
        <div class="modal-card">
          <div class="modal-icon">⚠</div>
          <h3 class="modal-title">{{ confirmModal.label }}</h3>
          <p class="modal-body">
            {{ confirmModal.action === 'start'
              ? 'Un autre match est en cours — le démarrer le mettra en pause.'
              : 'Cette action est irréversible.' }}
          </p>
          <div class="modal-actions">
            <button class="btn-secondary" @click="cancel">Annuler</button>
            <button class="btn-danger" @click="confirm">Confirmer</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Modal de fin de match — sélection du vainqueur -->
    <Teleport to="body">
      <div v-if="finishModal" class="modal-backdrop" @click.self="closeFinishModal">
        <div class="modal-card">
          <div class="modal-icon modal-icon--trophy">🏆</div>
          <h3 class="modal-title">Déclarer vainqueur</h3>
          <p class="modal-body">Choisissez le vainqueur du match. Cette action est irréversible.</p>

          <label class="finish-retirement-toggle">
            <input v-model="retirement" type="checkbox" />
            <span>Abandon adverse</span>
          </label>

          <div class="modal-actions modal-actions--vertical">
            <button
              class="btn-finish"
              :class="{ 'btn-finish--leading': finishCandidates?.a.isLeading }"
              @click="confirmFinish('A')"
            >
              <span>{{ finishCandidates?.a.name }}</span>
              <span v-if="finishCandidates?.a.isLeading" class="leading-badge">Mène</span>
            </button>

            <button
              class="btn-finish"
              :class="{ 'btn-finish--leading': finishCandidates?.b.isLeading }"
              @click="confirmFinish('B')"
            >
              <span>{{ finishCandidates?.b.name }}</span>
              <span v-if="finishCandidates?.b.isLeading" class="leading-badge">Mène</span>
            </button>

            <button class="btn-secondary" @click="closeFinishModal">Annuler</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Modal de forfait — désigner le joueur présent -->
    <Teleport to="body">
      <div v-if="forfaitModal" class="modal-backdrop" @click.self="forfaitModal = false">
        <div class="modal-card">
          <div class="modal-icon">⚑</div>
          <h3 class="modal-title">Déclarer forfait</h3>
          <p class="modal-body">Qui est présent ? Le joueur choisi est déclaré vainqueur.</p>

          <div class="modal-actions modal-actions--vertical">
            <button class="btn-finish" @click="confirmForfait('A')">
              <span>{{ playerName('A') }}</span>
            </button>
            <button class="btn-finish" @click="confirmForfait('B')">
              <span>{{ playerName('B') }}</span>
            </button>
            <button class="btn-secondary" @click="forfaitModal = false">Annuler</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Tiroir « Corrections » — jeux±, sets±, serveur, inversion d'affichage -->
    <Teleport to="body">
      <div v-if="correctionsOpen" class="modal-backdrop" @click.self="correctionsOpen = false">
        <div class="modal-card corrections-card">
          <h3 class="modal-title">Corrections</h3>
          <p class="modal-body">Format : {{ match?.formatLabel ?? '—' }} (lecture seule)</p>

          <div class="corrections-group">
            <span class="corrections-group-label">Jeux</span>
            <div class="corrections-row">
              <span class="corrections-row-name">{{ playerName(leftModelSide) }}</span>
              <button class="corrections-btn" @click="sendAction('game_left_minus')">−</button>
              <span class="corrections-val tab">{{ sideGames(leftModelSide) }}</span>
              <button class="corrections-btn" @click="sendAction('game_left_plus')">+</button>
            </div>
            <div class="corrections-row">
              <span class="corrections-row-name">{{ playerName(rightModelSide) }}</span>
              <button class="corrections-btn" @click="sendAction('game_right_minus')">−</button>
              <span class="corrections-val tab">{{ sideGames(rightModelSide) }}</span>
              <button class="corrections-btn" @click="sendAction('game_right_plus')">+</button>
            </div>
          </div>

          <div class="corrections-group">
            <span class="corrections-group-label">Sets</span>
            <div class="corrections-row">
              <span class="corrections-row-name">{{ playerName(leftModelSide) }}</span>
              <button class="corrections-btn" @click="sendAction('set_left_minus')">−</button>
              <span class="corrections-val tab">{{ sideSets(leftModelSide) }}</span>
              <button class="corrections-btn" @click="sendAction('set_left_plus')">+</button>
            </div>
            <div class="corrections-row">
              <span class="corrections-row-name">{{ playerName(rightModelSide) }}</span>
              <button class="corrections-btn" @click="sendAction('set_right_minus')">−</button>
              <span class="corrections-val tab">{{ sideSets(rightModelSide) }}</span>
              <button class="corrections-btn" @click="sendAction('set_right_plus')">+</button>
            </div>
          </div>

          <div class="corrections-group">
            <span class="corrections-group-label">Service</span>
            <button class="btn-secondary" @click="sendAction('toggle_service')">Changer le serveur</button>
          </div>

          <div class="corrections-group">
            <span class="corrections-group-label">Affichage</span>
            <button class="btn-secondary" @click="handleSwap">Inverser les côtés</button>
          </div>

          <div class="modal-actions">
            <button class="btn-secondary" @click="correctionsOpen = false">Fermer</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.arb-container {
  position: fixed;
  inset: 0;
  background: var(--bg-1);
  overflow: hidden;
}

.arb-stage {
  position: absolute;
  top: 0;
  left: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-1);
}

/* ── Header ─────────────────────────────────────────────────────────── */
.arb-header {
  height: 96px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid var(--line-1);
  flex-shrink: 0;
}

.btn-back {
  width: 44px;
  height: 44px;
  border-radius: var(--r-md);
  background: var(--bg-3);
  border: none;
  color: var(--ink-1);
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.arb-header-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.arb-category {
  font-size: 15px;
  font-weight: 600;
  color: var(--ink-1);
  letter-spacing: 0.04em;
}

.arb-format {
  font-size: 12px;
  font-weight: 500;
  color: var(--ink-2);
  letter-spacing: 0.02em;
}

.arb-status-badge {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  padding: 3px 12px;
  border-radius: 99px;
  background: var(--accent-soft);
  color: var(--accent);
  text-transform: uppercase;
}

.arb-status-badge.tb {
  background: rgba(255, 200, 61, 0.2);
  color: var(--gold);
}

.arb-status-badge.finished {
  background: var(--danger-soft);
  color: var(--danger);
}

.arb-status-badge.scheduled {
  background: var(--bg-4);
  color: var(--ink-3);
}

.arb-status-badge.canceled {
  background: var(--bg-4);
  color: var(--ink-3);
}

/* ── Score block ─────────────────────────────────────────────────────── */
.arb-score-block {
  height: 280px;
  display: grid;
  grid-template-columns: 1fr 320px 1fr;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid var(--line-1);
  flex-shrink: 0;
}

.arb-score-player {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.arb-score-player--right {
  align-items: flex-end;
}

.arb-player-label {
  font-size: 28px;
  font-weight: 700;
  color: var(--ink-0);
  letter-spacing: -0.01em;
}

.arb-player-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.1em;
  color: var(--ink-3);
  text-transform: uppercase;
}

.serve-indicator {
  color: var(--ball-yellow);
  animation: serveFloat 1.8s ease-in-out infinite;
  font-size: 14px;
}

.arb-score-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.score-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.22em;
  color: var(--ink-3);
  text-transform: uppercase;
}

.score-nums {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-a {
  font-size: 100px;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--accent);
  line-height: 1;
}

.score-b {
  font-size: 100px;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--ink-0);
  line-height: 1;
}

.score-sep {
  font-size: 40px;
  color: var(--ink-4);
}

/* ── Zones de tap ────────────────────────────────────────────────────── */
.arb-tap-area {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  overflow: hidden;
}

.arb-tap-area.disabled {
  opacity: 0.4;
  pointer-events: none;
}

.tap-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border: none;
  cursor: pointer;
  transition: filter 150ms;
  position: relative;
}

.tap-zone:active {
  filter: brightness(1.3);
}

.tap-zone--a {
  background: var(--accent);
}

.tap-zone--b {
  background: var(--bg-3);
  border-left: 1px solid var(--line-2);
}

.tap-player-name {
  font-size: 32px;
  font-weight: 800;
  color: inherit;
  letter-spacing: -0.01em;
}

.tap-zone--a .tap-player-name { color: #000; }
.tap-zone--b .tap-player-name { color: var(--ink-0); }

.tap-cta {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.tap-zone--a .tap-cta { color: rgba(0,0,0,0.7); }
.tap-zone--b .tap-cta { color: var(--ink-2); }

.tap-hint {
  position: absolute;
  bottom: 20px;
  right: 20px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  opacity: 0.5;
}

.tap-zone--a .tap-hint { color: #000; }
.tap-zone--b .tap-hint { color: var(--ink-0); }

/* ── Footer ──────────────────────────────────────────────────────────── */
.arb-footer {
  height: 90px;
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 0 16px;
  border-top: 1px solid var(--line-1);
  flex-shrink: 0;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  padding: 12px 20px;
  color: var(--ink-1);
  min-width: 80px;
  transition: background 150ms;
}

.action-btn:hover { background: var(--bg-4); }

.action-btn--danger {
  background: var(--danger-soft);
  border-color: rgba(255,48,82,0.3);
  color: var(--danger);
}

.action-btn--danger-ghost {
  background: transparent;
  border-color: var(--line-2);
  color: var(--danger);
}

.action-btn--primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #000;
}

.action-icon {
  font-size: 20px;
}

.action-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

/* ── Toast d'erreur ──────────────────────────────────────────────────── */
.arb-toast {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 300;
  max-width: 90vw;
  padding: 14px 22px;
  border-radius: var(--r-md);
  background: var(--danger);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  text-align: center;
  box-shadow: var(--shadow-2);
}

/* ── Modal ───────────────────────────────────────────────────────────── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-card {
  background: var(--bg-2);
  border: 1px solid var(--line-2);
  border-radius: var(--r-xl);
  padding: 40px 48px;
  max-width: 460px;
  width: 90%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow-2);
}

.modal-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--danger-soft);
  color: var(--danger);
  font-size: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--ink-0);
  text-align: center;
}

.modal-body {
  margin: 0;
  font-size: 14px;
  color: var(--ink-2);
  text-align: center;
}

.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.btn-secondary {
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  padding: 12px 28px;
  color: var(--ink-1);
  font-size: 15px;
  font-weight: 600;
}

.btn-danger {
  background: var(--danger);
  border: none;
  border-radius: var(--r-md);
  padding: 12px 28px;
  color: white;
  font-size: 15px;
  font-weight: 600;
}

/* ── Modal fin de match ──────────────────────────────────────────────── */
.modal-icon--trophy {
  background: var(--accent-soft);
  color: var(--accent);
}

.modal-actions--vertical {
  flex-direction: column;
  width: 100%;
}

.btn-finish {
  width: 100%;
  padding: 14px 28px;
  border-radius: var(--r-md);
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  color: var(--ink-1);
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: background 150ms;
}

.btn-finish:hover {
  background: var(--bg-4);
}

.btn-finish--leading {
  background: var(--accent);
  border-color: var(--accent);
  color: #000;
}

.btn-finish--leading:hover {
  filter: brightness(1.1);
  background: var(--accent);
}

.leading-badge {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  opacity: 0.7;
}

.finish-retirement-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  align-self: flex-start;
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-1);
  cursor: pointer;
}

.finish-retirement-toggle input {
  width: 18px;
  height: 18px;
  accent-color: var(--accent);
}

/* ── Tiroir Corrections ──────────────────────────────────────────────── */
.corrections-card {
  align-items: stretch;
  max-width: 420px;
}

.corrections-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
}

.corrections-group-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-3);
}

.corrections-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.corrections-row-name {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.corrections-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--r-md);
  background: var(--bg-4);
  border: 1px solid var(--line-2);
  color: var(--ink-0);
  font-size: 18px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.corrections-btn:hover {
  filter: brightness(1.2);
}

.corrections-val {
  min-width: 24px;
  text-align: center;
  font-size: 16px;
  font-weight: 700;
  color: var(--ink-0);
}
</style>
