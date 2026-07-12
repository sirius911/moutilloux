<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useLiveStore } from '@/stores/live'
import { usePolling } from '@/composables/usePolling'
import { useScale } from '@/composables/useScale'
import { useApi } from '@/composables/useApi'
import { useViewport } from '@/composables/useViewport'
import { useWakeLock } from '@/composables/useWakeLock'
import type { ArbitreProgramme } from '@/types'

const props = defineProps<{ matchId: number }>()
const router = useRouter()
const { get, post } = useApi()
const live = useLiveStore()

// Polling du match arbitré (et non plus le hero global) — 2s
usePolling(() => live.fetchMatch(props.matchId), 2000)

const match = computed(() => live.match)

const { isMobile } = useViewport()

// Scène iPad (existante)
const TARGET_W = 834
const TARGET_H = 1112

// Scène mobile portrait (specs/screens/arbitre-match.md « Variante mobile »)
const MOBILE_TARGET_W = 390
const MOBILE_TARGET_H = 844

const containerRef = ref<HTMLElement | null>(null)
const { scale: scaleIpad, offsetX: offsetXIpad, offsetY: offsetYIpad } = useScale(containerRef, TARGET_W, TARGET_H)
const { scale: scaleMobile, offsetX: offsetXMobile, offsetY: offsetYMobile } = useScale(containerRef, MOBILE_TARGET_W, MOBILE_TARGET_H)

const scale = computed(() => (isMobile.value ? scaleMobile.value : scaleIpad.value))
const offsetX = computed(() => (isMobile.value ? offsetXMobile.value : offsetXIpad.value))
const offsetY = computed(() => (isMobile.value ? offsetYMobile.value : offsetYIpad.value))
const stageW = computed(() => (isMobile.value ? MOBILE_TARGET_W : TARGET_W))
const stageH = computed(() => (isMobile.value ? MOBILE_TARGET_H : TARGET_H))

// Verrou anti-tap (scène mobile) — local à l'écran, pas de persistance
// (specs/transverse/mobile.md « Verrou anti-tap »)
const locked = ref(false)
let unlockTimer: ReturnType<typeof setTimeout> | null = null
const UNLOCK_HOLD_MS = 600

function startUnlockHold() {
  if (!locked.value) return
  if (unlockTimer) clearTimeout(unlockTimer)
  unlockTimer = setTimeout(() => {
    locked.value = false
    unlockTimer = null
  }, UNLOCK_HOLD_MS)
}

function cancelUnlockHold() {
  if (unlockTimer) {
    clearTimeout(unlockTimer)
    unlockTimer = null
  }
}

function toggleLock() {
  // Le cadenas verrouille en un tap simple ; le déverrouillage se fait par
  // appui long (voir startUnlockHold/cancelUnlockHold branchés sur le bouton).
  if (!locked.value) locked.value = true
}

// Menu mobile — actions secondaires repliées (Corrections, Terminer, Forfait, Reset, Annuler)
const mobileMenuOpen = ref(false)

// Modal de confirmation générique (reset_all, annuler)
const confirmModal = ref<{ action: string; label: string } | null>(null)

// Modal « Lancer le jeu » — choix obligatoire du premier serveur
const launchModal = ref(false)
const chosenServer = ref<'A' | 'B' | null>(null)

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
    await post(`/api/matches/${props.matchId}/action/`, { action, ...extra })
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

function sideDisplayPoint(side: 'A' | 'B'): string {
  return side === 'A' ? (match.value?.displayPointA ?? '0') : (match.value?.displayPointB ?? '0')
}

const statusLabel = computed(() => {
  if (!match.value) return ''
  if (match.value.status === 'SCHEDULED') return 'PRÉVU'
  if (match.value.status === 'CANCELED') return 'ANNULÉ'
  if (isWarmup.value) return `ÉCHAUFFEMENT · ${warmupCountdown.value}`
  if (match.value.tbActive) return 'JEU DÉCISIF'
  if (match.value.status === 'FINISHED') {
    if (match.value.endReason === 'WALKOVER') return 'TERMINÉ · FORFAIT'
    if (match.value.endReason === 'RETIREMENT') return 'TERMINÉ · ABANDON'
    return 'TERMINÉ'
  }
  return 'EN COURS'
})

const isFinished = computed(() => match.value?.status === 'FINISHED')
const isScheduled = computed(() => match.value?.status === 'SCHEDULED')
const isWarmup = computed(() => match.value?.status === 'LIVE' && !match.value?.playStartedAt)
const isPlaying = computed(() => match.value?.status === 'LIVE' && !!match.value?.playStartedAt)
const isCanceled = computed(() => match.value?.status === 'CANCELED')
const isReadOnly = computed(() => isFinished.value || isCanceled.value)

// Écran non verrouillé pendant un match LIVE (specs/transverse/mobile.md § Wake-lock)
useWakeLock(computed(() => match.value?.status === 'LIVE'))

const WARMUP_DURATION_MS = 5 * 60 * 1000 // 5 min, constante indicative (cycle-de-vie-match.md)

const nowTick = ref(Date.now())
let tickTimer: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  tickTimer = setInterval(() => { nowTick.value = Date.now() }, 1000)
})
onUnmounted(() => {
  if (tickTimer) clearInterval(tickTimer)
})

const warmupCountdown = computed(() => {
  if (!isWarmup.value || !match.value?.warmupStartedAt) return '5:00'
  const elapsed = nowTick.value - new Date(match.value.warmupStartedAt).getTime()
  const remainingMs = Math.max(0, WARMUP_DURATION_MS - elapsed)
  if (remainingMs <= 0) return 'PRÊT'
  const totalSeconds = Math.ceil(remainingMs / 1000)
  const m = Math.floor(totalSeconds / 60)
  const s = totalSeconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
})

async function handleStart() {
  try {
    const programme = await get<ArbitreProgramme>('/api/arbitre/matches/')
    const allMatches = programme.playDays.flatMap((d) => d.matches)
    const anotherLive = allMatches.some((m) => m.id !== props.matchId && m.status === 'LIVE')
    if (anotherLive) {
      askConfirm('start', 'Un autre match est en cours — le démarrer le mettra en pause ?')
    } else {
      await sendAction('start')
    }
  } catch {
    // Si la vérification échoue (réseau), on démarre quand même directement.
    await sendAction('start')
  }
}

function handleLaunch() {
  chosenServer.value = null
  launchModal.value = true
}

function cancelLaunch() {
  launchModal.value = false
}

async function confirmLaunch() {
  if (!chosenServer.value) return
  const ok = await sendAction('launch', { server: chosenServer.value })
  if (ok) launchModal.value = false
}
</script>

<template>
  <div ref="containerRef" class="arb-container">
    <div
      class="arb-stage"
      :class="{ 'arb-stage--mobile': isMobile }"
      :style="{
        width: `${stageW}px`,
        height: `${stageH}px`,
        transform: `translate(${offsetX}px, ${offsetY}px) scale(${scale})`,
        transformOrigin: 'top left',
      }"
    >
      <!-- ═══════════════ Scène mobile portrait (390×844) ═══════════════ -->
      <template v-if="isMobile">
        <!-- En-tête compact -->
        <header class="arb-mobile-header">
          <button class="btn-back arb-mobile-back" @click="router.push('/arbitre')">←</button>
          <div class="arb-mobile-header-center">
            <span class="arb-mobile-stage">{{ match?.stageLabel ?? '—' }}</span>
            <span
              class="arb-status-badge"
              :class="{ tb: match?.tbActive, finished: isFinished, scheduled: isScheduled, canceled: isCanceled, warmup: isWarmup }"
            >
              {{ statusLabel }}
            </span>
          </div>
          <button class="arb-mobile-menu-btn" title="Menu" @click="mobileMenuOpen = true">☰</button>
        </header>

        <!-- Zone de tap du haut (joueur B) -->
        <button
          class="arb-mobile-tap arb-mobile-tap--top"
          :disabled="!isPlaying || locked"
          :class="{ locked: !isPlaying || locked }"
          @click="handleTap('right')"
        >
          <span
            class="arb-mobile-tap-name"
            :class="{ 'arb-mobile-tap-name--serving': match?.server === rightModelSide }"
          >{{ playerName(rightModelSide) }}</span>
          <span v-if="match?.server === rightModelSide" class="serve-ball">
            <svg viewBox="0 0 24 24" width="30" height="30" style="filter: drop-shadow(0 0 6px #E8F35A)">
              <circle cx="12" cy="12" r="10" fill="#E8F35A"/>
              <path d="M2.5 12c4-1 8.5-1 12.5 3 1.5 1.5 4.5 2.5 6.5 2.5M2.5 12c4 1 8.5 1 12.5-3 1.5-1.5 4.5-2.5 6.5-2.5" fill="none" stroke="rgba(0,0,0,0.5)" stroke-width="0.8"/>
            </svg>
          </span>
          <span class="tap-cta">+ POINT</span>
        </button>

        <!-- Score central -->
        <div class="arb-mobile-score">
          <div class="arb-mobile-score-row">
            <span class="arb-mobile-score-meta">SETS {{ sideSets(leftModelSide) }} · JEUX {{ sideGames(leftModelSide) }}</span>
            <span class="arb-mobile-score-meta">SETS {{ sideSets(rightModelSide) }} · JEUX {{ sideGames(rightModelSide) }}</span>
          </div>
          <div class="score-nums tab arb-mobile-score-nums">
            <span class="score-a">
              {{ match ? (match.tbActive ? sideTbPoints(leftModelSide) : sideDisplayPoint(leftModelSide)) : '0' }}
            </span>
            <span class="score-sep">·</span>
            <span class="score-b">
              {{ match ? (match.tbActive ? sideTbPoints(rightModelSide) : sideDisplayPoint(rightModelSide)) : '0' }}
            </span>
          </div>
          <span class="score-label">{{ match?.tbActive ? 'JEU DÉCISIF' : (isWarmup ? warmupCountdown : 'POINT') }}</span>

          <!-- Cadenas anti-tap -->
          <button
            class="arb-mobile-lock"
            :class="{ 'arb-mobile-lock--locked': locked }"
            :title="locked ? 'Appui long pour déverrouiller' : 'Verrouiller les zones de tap'"
            @click="toggleLock"
            @touchstart.prevent="startUnlockHold"
            @touchend="cancelUnlockHold"
            @mousedown="startUnlockHold"
            @mouseup="cancelUnlockHold"
            @mouseleave="cancelUnlockHold"
          >
            {{ locked ? '🔒' : '🔓' }}
          </button>
        </div>

        <!-- Zone de tap du bas (joueur A) -->
        <button
          class="arb-mobile-tap arb-mobile-tap--bottom"
          :disabled="!isPlaying || locked"
          :class="{ locked: !isPlaying || locked }"
          @click="handleTap('left')"
        >
          <span class="tap-cta">+ POINT</span>
          <span v-if="match?.server === leftModelSide" class="serve-ball">
            <svg viewBox="0 0 24 24" width="30" height="30" style="filter: drop-shadow(0 0 6px #E8F35A)">
              <circle cx="12" cy="12" r="10" fill="#E8F35A"/>
              <path d="M2.5 12c4-1 8.5-1 12.5 3 1.5 1.5 4.5 2.5 6.5 2.5M2.5 12c4 1 8.5 1 12.5-3 1.5-1.5 4.5-2.5 6.5-2.5" fill="none" stroke="rgba(0,0,0,0.5)" stroke-width="0.8"/>
            </svg>
          </span>
          <span
            class="arb-mobile-tap-name"
            :class="{ 'arb-mobile-tap-name--serving': match?.server === leftModelSide }"
          >{{ playerName(leftModelSide) }}</span>
        </button>

        <!-- Action principale en pied (Démarrer / Lancer) -->
        <footer v-if="isScheduled || isWarmup" class="arb-mobile-footer">
          <button
            v-if="isScheduled"
            class="action-btn action-btn--primary arb-mobile-primary"
            :disabled="!match?.sideA || !match?.sideB"
            @click="handleStart"
          >
            <span class="action-icon">▶</span>
            <span class="action-label">Démarrer le match</span>
          </button>
          <button
            v-else-if="isWarmup"
            class="action-btn action-btn--primary arb-mobile-primary"
            @click="handleLaunch"
          >
            <span class="action-icon">▶</span>
            <span class="action-label">Lancer le match</span>
          </button>
        </footer>
      </template>

      <!-- ═══════════════ Scène iPad (834×1112, inchangée) ═══════════════ -->
      <template v-else>
      <!-- Header -->
      <header class="arb-header">
        <button class="btn-back" @click="router.push('/arbitre')">←</button>
        <div class="arb-header-center">
          <span class="arb-category">{{ match?.stageLabel ?? '—' }}</span>
          <span v-if="match?.formatLabel" class="arb-format">{{ match.formatLabel }}</span>
          <span class="arb-status-badge" :class="{ tb: match?.tbActive, finished: isFinished, scheduled: isScheduled, canceled: isCanceled, warmup: isWarmup }">
            {{ statusLabel }}
          </span>
        </div>
        <div style="width: 44px" />
      </header>

      <!-- Bloc score -->
      <div class="arb-score-block">
        <!-- Joueur (côté gauche affiché) -->
        <div class="arb-score-player">
          <span
            class="arb-player-label"
            :class="{ 'arb-player-label--serving': match?.server === leftModelSide }"
          >{{ playerName(leftModelSide) }}</span>
          <div class="arb-player-meta">
            <span>SETS {{ sideSets(leftModelSide) }}</span>
            <span>JEUX {{ sideGames(leftModelSide) }}</span>
            <span v-if="match?.server === leftModelSide" class="serve-ball">
              <svg viewBox="0 0 24 24" width="34" height="34" style="filter: drop-shadow(0 0 6px #E8F35A)">
                <circle cx="12" cy="12" r="10" fill="#E8F35A"/>
                <path d="M2.5 12c4-1 8.5-1 12.5 3 1.5 1.5 4.5 2.5 6.5 2.5M2.5 12c4 1 8.5 1 12.5-3 1.5-1.5 4.5-2.5 6.5-2.5" fill="none" stroke="rgba(0,0,0,0.5)" stroke-width="0.8"/>
              </svg>
            </span>
          </div>
        </div>

        <!-- Score central -->
        <div class="arb-score-center">
          <span class="score-label">{{ match?.tbActive ? 'JEU DÉCISIF' : 'POINT' }}</span>
          <div class="score-nums tab">
            <span class="score-a">
              {{ match ? (match.tbActive ? sideTbPoints(leftModelSide) : sideDisplayPoint(leftModelSide)) : '0' }}
            </span>
            <span class="score-sep">·</span>
            <span class="score-b">
              {{ match ? (match.tbActive ? sideTbPoints(rightModelSide) : sideDisplayPoint(rightModelSide)) : '0' }}
            </span>
          </div>
        </div>

        <!-- Joueur (côté droit affiché) -->
        <div class="arb-score-player arb-score-player--right">
          <span
            class="arb-player-label"
            :class="{ 'arb-player-label--serving': match?.server === rightModelSide }"
          >{{ playerName(rightModelSide) }}</span>
          <div class="arb-player-meta">
            <span v-if="match?.server === rightModelSide" class="serve-ball">
              <svg viewBox="0 0 24 24" width="34" height="34" style="filter: drop-shadow(0 0 6px #E8F35A)">
                <circle cx="12" cy="12" r="10" fill="#E8F35A"/>
                <path d="M2.5 12c4-1 8.5-1 12.5 3 1.5 1.5 4.5 2.5 6.5 2.5M2.5 12c4 1 8.5 1 12.5-3 1.5-1.5 4.5-2.5 6.5-2.5" fill="none" stroke="rgba(0,0,0,0.5)" stroke-width="0.8"/>
              </svg>
            </span>
            <span>SETS {{ sideSets(rightModelSide) }}</span>
            <span>JEUX {{ sideGames(rightModelSide) }}</span>
          </div>
        </div>
      </div>

      <!-- Zones de tap -->
      <div class="arb-tap-area" :class="{ disabled: !isPlaying }">
        <button class="tap-zone tap-zone--a" :disabled="!isPlaying" @click="handleTap('left')">
          <span class="tap-player-name">{{ playerName(leftModelSide) }}</span>
          <span class="tap-cta">+ POINT</span>
          <span class="tap-hint">TAP ICI</span>
        </button>
        <button class="tap-zone tap-zone--b" :disabled="!isPlaying" @click="handleTap('right')">
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
        <template v-else-if="isWarmup">
          <button
            class="action-btn action-btn--primary"
            title="Lancer le match"
            @click="handleLaunch"
          >
            <span class="action-icon">▶</span>
            <span class="action-label">Lancer le match</span>
          </button>
          <button
            class="action-btn action-btn--danger-ghost"
            title="Annuler le match"
            @click="askConfirm('annuler', 'Annuler le match ?')"
          >
            <span class="action-icon">✕</span>
            <span class="action-label">Annuler</span>
          </button>
          <button
            class="action-btn action-btn--danger-ghost"
            title="Réinitialiser"
            @click="askConfirm('reset_all', 'Réinitialiser le match ?')"
          >
            <span class="action-icon">↺</span>
            <span class="action-label">Reset</span>
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
      </template>
    </div>

    <!-- Toast d'erreur -->
    <Teleport to="body">
      <div v-if="error" class="arb-toast" role="alert">{{ error }}</div>
    </Teleport>

    <!-- Modal de confirmation générique (reset_all, annuler) -->
    <Teleport to="body">
      <div v-if="confirmModal" class="modal-backdrop" @click.self="cancel">
        <div class="modal-card">
          <div class="modal-icon">⚠</div>
          <h3 class="modal-title">{{ confirmModal.label }}</h3>
          <p class="modal-body">Cette action est irréversible.</p>
          <div class="modal-actions">
            <button class="btn-secondary" @click="cancel">Annuler</button>
            <button class="btn-danger" @click="confirm">Confirmer</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Modal « Lancer le jeu » — choix obligatoire du premier serveur -->
    <Teleport to="body">
      <div v-if="launchModal" class="modal-backdrop" @click.self="cancelLaunch">
        <div class="modal-card">
          <div class="modal-icon">▶</div>
          <h3 class="modal-title">Lancer le match</h3>
          <p class="modal-body">Qui sert en premier ?</p>

          <div class="modal-actions modal-actions--vertical">
            <button
              class="btn-finish"
              :class="{ 'btn-finish--leading': chosenServer === 'A' }"
              @click="chosenServer = 'A'"
            >
              <span>{{ playerName('A') }}</span>
              <span v-if="chosenServer === 'A'" class="leading-badge">Choisi</span>
            </button>

            <button
              class="btn-finish"
              :class="{ 'btn-finish--leading': chosenServer === 'B' }"
              @click="chosenServer = 'B'"
            >
              <span>{{ playerName('B') }}</span>
              <span v-if="chosenServer === 'B'" class="leading-badge">Choisi</span>
            </button>

            <div class="modal-actions">
              <button class="btn-secondary" @click="cancelLaunch">Annuler</button>
              <button class="btn-danger" :disabled="!chosenServer" @click="confirmLaunch">Confirmer</button>
            </div>
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

    <!-- Feuille d'actions mobile — actions secondaires repliées (scène mobile uniquement) -->
    <Teleport to="body">
      <div v-if="isMobile && mobileMenuOpen" class="modal-backdrop arb-mobile-sheet-backdrop" @click.self="mobileMenuOpen = false">
        <div class="arb-mobile-sheet">
          <div class="arb-mobile-sheet-handle" />
          <h3 class="modal-title">Actions</h3>

          <template v-if="isScheduled">
            <button
              class="action-btn action-btn--primary arb-mobile-sheet-btn"
              :disabled="!match?.sideA || !match?.sideB"
              @click="mobileMenuOpen = false; handleStart()"
            >
              <span class="action-icon">▶</span>
              <span class="action-label">Démarrer le match</span>
            </button>
            <button class="action-btn arb-mobile-sheet-btn" @click="mobileMenuOpen = false; forfaitModal = true">
              <span class="action-icon">⚑</span>
              <span class="action-label">Forfait</span>
            </button>
            <button
              class="action-btn action-btn--danger-ghost arb-mobile-sheet-btn"
              @click="mobileMenuOpen = false; askConfirm('annuler', 'Annuler le match ?')"
            >
              <span class="action-icon">✕</span>
              <span class="action-label">Annuler</span>
            </button>
          </template>

          <template v-else-if="isWarmup">
            <button class="action-btn action-btn--primary arb-mobile-sheet-btn" @click="mobileMenuOpen = false; handleLaunch()">
              <span class="action-icon">▶</span>
              <span class="action-label">Lancer le match</span>
            </button>
            <button
              class="action-btn action-btn--danger-ghost arb-mobile-sheet-btn"
              @click="mobileMenuOpen = false; askConfirm('annuler', 'Annuler le match ?')"
            >
              <span class="action-icon">✕</span>
              <span class="action-label">Annuler</span>
            </button>
            <button
              class="action-btn action-btn--danger-ghost arb-mobile-sheet-btn"
              @click="mobileMenuOpen = false; askConfirm('reset_all', 'Réinitialiser le match ?')"
            >
              <span class="action-icon">↺</span>
              <span class="action-label">Reset</span>
            </button>
          </template>

          <template v-else>
            <button class="action-btn arb-mobile-sheet-btn" :disabled="isReadOnly" @click="mobileMenuOpen = false; handleUndo()">
              <span class="action-icon">↩</span>
              <span class="action-label">0 pts</span>
            </button>
            <button class="action-btn arb-mobile-sheet-btn" :disabled="isReadOnly" @click="mobileMenuOpen = false; correctionsOpen = true">
              <span class="action-icon">✎</span>
              <span class="action-label">Corrections</span>
            </button>
            <button
              v-if="!isReadOnly"
              class="action-btn action-btn--danger arb-mobile-sheet-btn"
              @click="mobileMenuOpen = false; openFinishModal()"
            >
              <span class="action-icon">■</span>
              <span class="action-label">Terminer</span>
            </button>
            <button
              class="action-btn action-btn--danger-ghost arb-mobile-sheet-btn"
              :disabled="isReadOnly"
              @click="mobileMenuOpen = false; askConfirm('reset_all', 'Réinitialiser le match ?')"
            >
              <span class="action-icon">↺</span>
              <span class="action-label">Reset</span>
            </button>
          </template>

          <button class="btn-secondary arb-mobile-sheet-close" @click="mobileMenuOpen = false">Fermer</button>
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

.arb-status-badge.warmup {
  background: var(--bg-4);
  color: var(--ink-1);
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

.serve-ball {
  display: flex;
  align-items: center;
  animation: serveFloat 1.8s ease-in-out infinite;
}

.arb-player-label--serving {
  color: var(--accent);
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

.btn-danger:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.modal-body--warning {
  color: var(--gold);
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

/* ── Scène mobile (390×844) ──────────────────────────────────────────── */
.arb-stage--mobile {
  flex-direction: column;
}

/* En-tête compact */
.arb-mobile-header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid var(--line-1);
  flex-shrink: 0;
}

.arb-mobile-back {
  width: 36px;
  height: 36px;
  font-size: 16px;
}

.arb-mobile-header-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.arb-mobile-stage {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-1);
  letter-spacing: 0.04em;
}

.arb-mobile-menu-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--r-md);
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  color: var(--ink-1);
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Zones de tap empilées haut/bas */
.arb-mobile-tap {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: none;
  cursor: pointer;
  transition: filter 150ms;
  padding: 16px;
}

.arb-mobile-tap:active {
  filter: brightness(1.3);
}

.arb-mobile-tap.locked {
  opacity: 0.4;
  pointer-events: none;
}

.arb-mobile-tap--top {
  background: var(--bg-3);
  border-bottom: 1px solid var(--line-2);
}

.arb-mobile-tap--bottom {
  background: var(--accent);
}

.arb-mobile-tap--top .arb-mobile-tap-name {
  color: var(--ink-0);
}

.arb-mobile-tap--bottom .arb-mobile-tap-name,
.arb-mobile-tap--bottom .tap-cta {
  color: #000;
}

.arb-mobile-tap--top .tap-cta {
  color: var(--ink-2);
}

.arb-mobile-tap-name {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.01em;
}

/* Nom du serveur mis en avant — traitement différent selon le fond de la
   zone (top = fond neutre, bottom = fond --accent où color:accent serait
   invisible sur du texte déjà noir). */
.arb-mobile-tap--top .arb-mobile-tap-name--serving {
  color: var(--accent);
}

.arb-mobile-tap--bottom .arb-mobile-tap-name--serving {
  font-weight: 900;
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.85), 0 0 3px rgba(255, 255, 255, 0.9);
}

/* Score central */
.arb-mobile-score {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 16px;
  border-top: 1px solid var(--line-1);
  border-bottom: 1px solid var(--line-1);
  flex-shrink: 0;
}

.arb-mobile-score-row {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--ink-3);
  text-transform: uppercase;
}

.arb-mobile-score-nums {
  gap: 6px;
}

.arb-mobile-score-nums .score-a,
.arb-mobile-score-nums .score-b {
  font-size: 56px;
}

.arb-mobile-score-nums .score-sep {
  font-size: 24px;
}

/* Cadenas anti-tap */
.arb-mobile-lock {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.arb-mobile-lock--locked {
  background: var(--danger-soft);
  border-color: rgba(255, 48, 82, 0.3);
}

/* Pied — action principale (Démarrer / Lancer) */
.arb-mobile-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--line-1);
  flex-shrink: 0;
}

.arb-mobile-primary {
  width: 100%;
  flex-direction: row;
  justify-content: center;
}

/* Feuille d'actions (menu mobile) */
.arb-mobile-sheet-backdrop {
  align-items: flex-end;
}

.arb-mobile-sheet {
  width: 100%;
  max-width: 480px;
  background: var(--bg-2);
  border: 1px solid var(--line-2);
  border-radius: var(--r-xl) var(--r-xl) 0 0;
  padding: 12px 20px 28px;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 10px;
}

.arb-mobile-sheet-handle {
  width: 40px;
  height: 4px;
  border-radius: 99px;
  background: var(--line-2);
  align-self: center;
  margin-bottom: 4px;
}

.arb-mobile-sheet-btn {
  width: 100%;
  flex-direction: row;
  justify-content: center;
}

.arb-mobile-sheet-close {
  margin-top: 4px;
}
</style>
