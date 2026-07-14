<script setup lang="ts">
// Régie mobile (admin) — #340 : fil de la journée courante, feuille d'actions
// contextuelle par match (7 actions réutilisant des services existants),
// section Annonces TV. Voir specs/screens/admin-regie-mobile.md et
// backlog/plan/340-adminregie-ecran-complet.md.
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useEventStore } from '@/stores/event'
import { useApi } from '@/composables/useApi'
import { usePolling } from '@/composables/usePolling'
import { useScale } from '@/composables/useScale'
import { sideName } from '@/utils/participants'
import { extractApiError } from '@/lib/apiError'
import type { Announcement, Break, CalendarDay, Match } from '@/types'

const router = useRouter()
const eventStore = useEventStore()
const { get, post } = useApi()

// ── Scène mobile portrait (mêmes dimensions cible qu'ArbitreMatch.vue) ─────
const TARGET_W = 390
const TARGET_H = 844
const containerRef = ref<HTMLElement | null>(null)
const { scale, offsetX, offsetY } = useScale(containerRef, TARGET_W, TARGET_H)

// ── Chargement des données ──────────────────────────────────────────────────
const ready = ref(false)

onMounted(async () => {
  if (!eventStore.activeEdition) await eventStore.fetchEditions()
  if (eventStore.activeEdition) await eventStore.fetchCalendar(eventStore.activeEdition.id)
  ready.value = true
})

usePolling(async () => {
  if (eventStore.activeEdition) await eventStore.fetchCalendar(eventStore.activeEdition.id)
}, 5000)

async function refreshCalendar() {
  if (eventStore.activeEdition) await eventStore.fetchCalendar(eventStore.activeEdition.id)
}

// ── Score du match en cours — rafraîchi à 2 s (même taux qu'Arbitre/TV) ────
// Le calendrier (5 s) suffit pour détecter qu'un match devient/cesse d'être
// LIVE ; le score du match déjà épinglé a besoin d'un taux plus rapide.
const liveScoreData = ref<Match | null>(null)

usePolling(async () => {
  const id = liveMatch.value?.id
  if (!id) {
    liveScoreData.value = null
    return
  }
  if (id !== liveScoreData.value?.id) {
    liveScoreData.value = null
  }
  const data = await get<{ match: Match }>(`/api/matches/${id}/`)
  liveScoreData.value = data.match
}, 2000)

// ── Journée courante + match en cours (même esprit qu'ArbitreHome.vue) ─────
function isToday(dateStr: string): boolean {
  const now = new Date()
  const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  return dateStr === todayStr
}

const currentDay = computed<CalendarDay | null>(() => {
  const days = eventStore.calendar?.playDays ?? []
  const today = days.find(d => isToday(d.date))
  if (today) return today
  return days.find(d => d.matches.some(m => m.status !== 'FINISHED' && m.status !== 'CANCELED')) ?? days[0] ?? null
})

const liveMatch = computed<Match | null>(() =>
  (eventStore.calendar?.playDays ?? [])
    .flatMap(d => d.matches)
    .find(m => m.status === 'LIVE') ?? null,
)

const nextMatchId = computed<number | null>(() => {
  const day = currentDay.value
  if (!day) return null
  const upcoming = day.matches
    .filter(m => m.status === 'SCHEDULED')
    .sort((a, b) => (a.orderIndex ?? 99999) - (b.orderIndex ?? 99999))
  return upcoming[0]?.id ?? null
})

type DayItem =
  | { kind: 'match'; data: Match }
  | { kind: 'break'; data: Break }

function mergeItems(day: CalendarDay): DayItem[] {
  const matchItems: DayItem[] = day.matches.map(m => ({ kind: 'match', data: m }))
  const breakItems: DayItem[] = day.breaks.map(b => ({ kind: 'break', data: b }))
  return [...matchItems, ...breakItems].sort((a, b) => {
    const ao = a.kind === 'match' ? (a.data.orderIndex ?? 99999) : a.data.orderIndex
    const bo = b.kind === 'match' ? (b.data.orderIndex ?? 99999) : b.data.orderIndex
    return ao - bo
  })
}

// Le match en cours est épinglé en tête ; on l'exclut du fil pour ne pas le
// dupliquer visuellement.
const feedItems = computed<DayItem[]>(() => {
  const day = currentDay.value
  if (!day) return []
  const items = mergeItems(day)
  if (!liveMatch.value) return items
  return items.filter(it => !(it.kind === 'match' && it.data.id === liveMatch.value!.id))
})

const isEmpty = computed(() => {
  if (!ready.value) return false
  if (!eventStore.activeEdition) return true
  return (eventStore.calendar?.playDays.length ?? 0) === 0
})

// ── Affichage joueurs / score ────────────────────────────────────────────
function playerName(m: Match, side: 'A' | 'B'): string {
  if (side === 'A') return sideName(m.sideA, m.sideALabel)
  return sideName(m.sideB, m.sideBLabel)
}

function scoreDisplay(m: Match): string {
  const sets = m.setScores?.map(s => `${s.a}-${s.b}`).join(' ') ?? ''
  const current = m.status === 'LIVE' ? ` (${m.gamesA}-${m.gamesB}, ${m.displayPointA}-${m.displayPointB})` : ''
  return (sets + current).trim()
}

function formatIsoTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }).replace(':', 'h')
}

function matchTimeLabel(m: Match): string {
  if (m.status === 'FINISHED') {
    const iso = m.startedAt ?? m.finishedAt
    return iso ? formatIsoTime(iso) : (m.scheduledTime ?? '—')
  }
  return m.scheduledTime ?? '—'
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })
}

// ── Puce d'état par ligne (mêmes libellés qu'ArbitreHome.vue) ──────────────
function rowStatusLabel(m: Match, isNext: boolean): string {
  if (m.status === 'LIVE') return 'EN COURS'
  if (isNext) return 'NEXT'
  if (m.status === 'FINISHED') return 'TERMINÉ'
  if (m.status === 'CANCELED') return 'ANNULÉ'
  return 'PLANIFIÉ'
}

function rowStatusClass(m: Match, isNext: boolean): string {
  if (m.status === 'LIVE') return 'live'
  if (isNext) return 'next'
  if (m.status === 'FINISHED') return 'finished'
  if (m.status === 'CANCELED') return 'canceled'
  return 'scheduled'
}

// ── Teinte de ponctualité — version simplifiée assumée (plan #340 § 3) ─────
// Comparaison heure actuelle / heure planifiée du jour courant, uniquement
// pour les matchs pas encore LIVE/FINISHED. Pas de moteur ETA monotone.
function punctualityClass(m: Match): string | null {
  if (m.status === 'LIVE' || m.status === 'FINISHED' || m.status === 'CANCELED') return null
  if (!m.scheduledTime || !currentDay.value) return null
  const [hh, mm] = m.scheduledTime.replace(/^~/, '').split('h').map(Number)
  if (Number.isNaN(hh) || Number.isNaN(mm)) return null
  const scheduled = new Date(currentDay.value.date + 'T00:00:00')
  scheduled.setHours(hh, mm, 0, 0)
  const diffMin = (Date.now() - scheduled.getTime()) / 60000
  if (diffMin > 15) return 'punct-late'
  if (diffMin > 0) return 'punct-warn'
  return 'punct-ok'
}

// ── Toast d'erreur (dupliqué localement, pattern ArbitreMatch.vue) ─────────
const error = ref('')
let errorTimer: ReturnType<typeof setTimeout> | null = null
function showError(msg: string) {
  error.value = msg
  if (errorTimer) clearTimeout(errorTimer)
  errorTimer = setTimeout(() => { error.value = '' }, 4000)
}

async function refereeAction(matchId: number, action: string, extra: Record<string, unknown> = {}): Promise<boolean> {
  try {
    await post(`/api/matches/${matchId}/action/`, { action, ...extra })
    await refreshCalendar()
    return true
  } catch (e) {
    showError(extractApiError(e))
    return false
  }
}

// ── Feuille d'actions contextuelle ──────────────────────────────────────────
const sheetMatch = ref<Match | null>(null)

function openSheet(m: Match) {
  if (m.status === 'CANCELED') return
  sheetMatch.value = m
}

function closeSheet() {
  sheetMatch.value = null
}

function canStart(m: Match): boolean {
  return m.status === 'SCHEDULED' && !!m.sideA && !!m.sideB
}

// Démarrer
const startConfirmOpen = ref(false)

async function handleStart() {
  const m = sheetMatch.value
  if (!m) return
  const anotherLive = (eventStore.calendar?.playDays ?? [])
    .flatMap(d => d.matches)
    .some(x => x.id !== m.id && x.status === 'LIVE')
  if (anotherLive) {
    startConfirmOpen.value = true
    return
  }
  await doStart()
}

async function doStart() {
  const m = sheetMatch.value
  if (!m) return
  try {
    await eventStore.startMatch(m.id)
    await refreshCalendar()
    startConfirmOpen.value = false
    closeSheet()
  } catch (e) {
    showError(extractApiError(e))
  }
}

function cancelStartConfirm() {
  startConfirmOpen.value = false
}

// Mettre à l'antenne
const featureConfirmOpen = ref(false)

function askFeature() {
  featureConfirmOpen.value = true
}

async function confirmFeature() {
  const m = sheetMatch.value
  if (!m) return
  try {
    await eventStore.featureMatch(m.eventId, m.id)
    await refreshCalendar()
    featureConfirmOpen.value = false
    closeSheet()
  } catch (e) {
    showError(extractApiError(e))
  }
}

function cancelFeature() {
  featureConfirmOpen.value = false
}

// Terminer — modal « Déclarer vainqueur »
const finishModalOpen = ref(false)
const finishRetirement = ref(false)

function openFinishModal() {
  finishRetirement.value = false
  finishModalOpen.value = true
}

async function confirmFinish(winner: 'A' | 'B') {
  const m = sheetMatch.value
  if (!m) return
  const ok = await refereeAction(m.id, 'finish_winner', { winner, retirement: finishRetirement.value })
  if (ok) {
    finishModalOpen.value = false
    closeSheet()
  }
}

function closeFinishModal() {
  finishModalOpen.value = false
}

// Forfait — modal « Qui est présent ? »
const forfaitModalOpen = ref(false)

async function confirmForfait(winner: 'A' | 'B') {
  const m = sheetMatch.value
  if (!m) return
  const ok = await refereeAction(m.id, 'forfait', { winner })
  if (ok) {
    forfaitModalOpen.value = false
    closeSheet()
  }
}

// Annuler — confirmation irréversible
const cancelConfirmOpen = ref(false)

async function confirmCancelMatch() {
  const m = sheetMatch.value
  if (!m) return
  const ok = await refereeAction(m.id, 'annuler')
  if (ok) {
    cancelConfirmOpen.value = false
    closeSheet()
  }
}

// Rouvrir — confirmation
const reopenConfirmOpen = ref(false)

async function confirmReopen() {
  const m = sheetMatch.value
  if (!m) return
  const ok = await refereeAction(m.id, 'reopen')
  if (ok) {
    reopenConfirmOpen.value = false
    closeSheet()
  }
}

// Correction rapide de score — formulaire compact
const scoreFormOpen = ref(false)
const scoreForm = ref({ setsA: 0, setsB: 0, gamesA: 0, gamesB: 0 })

function openScoreForm() {
  const m = sheetMatch.value
  if (!m) return
  scoreForm.value = {
    setsA: m.setsA,
    setsB: m.setsB,
    gamesA: m.gamesA,
    gamesB: m.gamesB,
  }
  scoreFormOpen.value = true
}

function closeScoreForm() {
  scoreFormOpen.value = false
}

async function saveScoreForm() {
  const m = sheetMatch.value
  if (!m) return
  try {
    await eventStore.editMatch(m.eventId, m.id, {
      sets_a: scoreForm.value.setsA,
      sets_b: scoreForm.value.setsB,
      games_a: scoreForm.value.gamesA,
      games_b: scoreForm.value.gamesB,
    })
    await refreshCalendar()
    scoreFormOpen.value = false
    closeSheet()
  } catch (e) {
    showError(extractApiError(e))
  }
}

// ── Annonces TV (pattern AdminTournoi.vue lignes 26-106, compact) ──────────
const announcements = ref<Announcement[]>([])
const newAnnouncementMessage = ref('')
const announceError = ref('')

async function fetchAnnouncements() {
  if (!eventStore.activeEdition) {
    announcements.value = []
    return
  }
  try {
    const data = await get<{ announcements: Announcement[] }>(
      `/api/editions/${eventStore.activeEdition.id}/announcements/`,
    )
    announcements.value = data.announcements
  } catch (e) {
    announceError.value = extractApiError(e)
  }
}

watch(() => eventStore.activeEdition?.id, fetchAnnouncements, { immediate: true })

async function addAnnouncement() {
  if (!eventStore.activeEdition || !newAnnouncementMessage.value.trim()) return
  announceError.value = ''
  try {
    await post(`/api/editions/${eventStore.activeEdition.id}/announcements/create/`, {
      message: newAnnouncementMessage.value.trim(),
    })
    newAnnouncementMessage.value = ''
    await fetchAnnouncements()
  } catch (e) {
    announceError.value = extractApiError(e)
  }
}

async function toggleAnnouncement(a: Announcement) {
  announceError.value = ''
  try {
    await post(`/api/announcements/${a.id}/edit/`, { isActive: !a.isActive })
    await fetchAnnouncements()
  } catch (e) {
    announceError.value = extractApiError(e)
  }
}

const deleteAnnouncementTarget = ref<Announcement | null>(null)

async function confirmDeleteAnnouncement() {
  const a = deleteAnnouncementTarget.value
  if (!a) return
  announceError.value = ''
  try {
    await post(`/api/announcements/${a.id}/delete/`)
    deleteAnnouncementTarget.value = null
    await fetchAnnouncements()
  } catch (e) {
    announceError.value = extractApiError(e)
  }
}
</script>

<template>
  <div ref="containerRef" class="regie-container">
    <!-- État vide : aucune édition active / aucune journée -->
    <div v-if="isEmpty" class="regie-empty">
      <p class="regie-empty-title">Aucune édition active</p>
      <p class="regie-empty-hint">Configurez le tournoi depuis un ordinateur.</p>
    </div>

    <div
      v-else
      class="regie-stage"
      :style="{
        width: `${TARGET_W}px`,
        minHeight: `${TARGET_H}px`,
        transform: `translate(${offsetX}px, ${offsetY}px) scale(${scale})`,
        transformOrigin: 'top left',
      }"
    >
      <!-- En-tête -->
      <header class="regie-header">
        <button class="regie-back" type="button" @click="router.push('/admin/tournoi')">←</button>
        <div class="regie-header-center">
          <span class="regie-title">Régie</span>
          <span v-if="currentDay" class="regie-day">{{ formatDate(currentDay.date) }}</span>
        </div>
        <div style="width: 36px" />
      </header>

      <div class="regie-body">
        <!-- Match en cours épinglé -->
        <section v-if="liveMatch" class="regie-live-card" @click="openSheet(liveMatch)">
          <span class="regie-live-label"><i class="regie-live-dot" /> En cours</span>
          <div class="regie-live-players">
            <span>{{ playerName(liveMatch, 'A') }}</span>
            <em>vs</em>
            <span>{{ playerName(liveMatch, 'B') }}</span>
          </div>
          <div class="regie-live-meta">
            <span class="regie-live-stage">{{ liveMatch.stageLabel }}</span>
            <span class="regie-live-score tab">{{ scoreDisplay(liveScoreData ?? liveMatch) }}</span>
          </div>
        </section>

        <!-- Fil de la journée -->
        <section class="regie-feed">
          <p v-if="!currentDay || feedItems.length === 0" class="regie-feed-empty">
            Aucun match à venir dans cette journée.
          </p>

          <template v-for="item in feedItems" :key="`${item.kind}-${item.data.id}`">
            <div v-if="item.kind === 'break'" class="regie-break-row">
              <span class="regie-break-icon">⏸</span>
              <span class="regie-break-label">{{ item.data.label || 'Pause' }} · {{ item.data.durationMin }} min</span>
            </div>

            <button
              v-else
              type="button"
              class="regie-match"
              :class="[punctualityClass(item.data), { 'regie-match-canceled': item.data.status === 'CANCELED' }]"
              @click="openSheet(item.data)"
            >
              <div class="regie-match-top">
                <span :class="['regie-match-status', rowStatusClass(item.data, item.data.id === nextMatchId)]">
                  {{ rowStatusLabel(item.data, item.data.id === nextMatchId) }}
                </span>
                <span class="regie-match-time tab">{{ matchTimeLabel(item.data) }}</span>
                <span v-if="item.data.court" class="regie-match-court">{{ item.data.court }}</span>
              </div>
              <div class="regie-match-players">
                <span>{{ playerName(item.data, 'A') }}</span>
                <em>vs</em>
                <span>{{ playerName(item.data, 'B') }}</span>
              </div>
              <div class="regie-match-bottom">
                <span class="regie-match-event">{{ item.data.stageLabel }}</span>
                <span v-if="item.data.status === 'FINISHED' && scoreDisplay(item.data)" class="regie-match-score tab">
                  {{ scoreDisplay(item.data) }}
                </span>
              </div>
            </button>
          </template>
        </section>

        <!-- Annonces TV -->
        <section class="regie-announces">
          <h3 class="regie-section-title">Annonces TV</h3>
          <p v-if="announceError" class="regie-error-inline">{{ announceError }}</p>

          <div class="regie-announce-add">
            <input
              v-model="newAnnouncementMessage"
              type="text"
              class="regie-input"
              placeholder="Nouvelle annonce…"
              @keyup.enter="addAnnouncement"
            />
            <button
              class="regie-btn primary"
              type="button"
              :disabled="!newAnnouncementMessage.trim()"
              @click="addAnnouncement"
            >
              Ajouter
            </button>
          </div>

          <p v-if="announcements.length === 0" class="regie-feed-empty">Aucune annonce.</p>

          <div v-else class="regie-announce-list">
            <div v-for="a in announcements" :key="a.id" class="regie-announce">
              <label class="regie-toggle">
                <input type="checkbox" :checked="a.isActive" @change="toggleAnnouncement(a)" />
                <span class="regie-toggle-track"><span class="regie-toggle-thumb" /></span>
              </label>
              <span :class="['regie-announce-msg', { 'is-inactive': !a.isActive }]">{{ a.message }}</span>
              <button class="regie-btn danger" type="button" @click="deleteAnnouncementTarget = a">✕</button>
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- Toast d'erreur -->
    <Teleport to="body">
      <div v-if="error" class="regie-toast" role="alert">{{ error }}</div>
    </Teleport>

    <!-- Feuille d'actions contextuelle -->
    <Teleport to="body">
      <div v-if="sheetMatch" class="modal-backdrop regie-sheet-backdrop" @click.self="closeSheet">
        <div class="regie-sheet">
          <div class="regie-sheet-handle" />
          <h3 class="regie-sheet-title">
            {{ playerName(sheetMatch, 'A') }} <em>vs</em> {{ playerName(sheetMatch, 'B') }}
          </h3>
          <p class="regie-sheet-sub">{{ sheetMatch.stageLabel }}</p>

          <div class="regie-sheet-actions">
            <template v-if="sheetMatch.status === 'SCHEDULED'">
              <button
                class="regie-action-btn regie-action-btn--primary"
                :disabled="!canStart(sheetMatch)"
                type="button"
                @click="handleStart"
              >
                ▶ Démarrer
              </button>
              <button class="regie-action-btn" type="button" @click="askFeature">
                ★ Mettre à l'antenne
              </button>
              <button class="regie-action-btn" type="button" @click="forfaitModalOpen = true">
                ⚑ Forfait
              </button>
              <button class="regie-action-btn regie-action-btn--danger-ghost" type="button" @click="cancelConfirmOpen = true">
                ✕ Annuler
              </button>
            </template>

            <template v-else-if="sheetMatch.status === 'LIVE'">
              <button class="regie-action-btn regie-action-btn--danger" type="button" @click="openFinishModal">
                ■ Terminer
              </button>
              <button class="regie-action-btn" type="button" @click="openScoreForm">
                ✎ Correction rapide de score
              </button>
              <button class="regie-action-btn regie-action-btn--danger-ghost" type="button" @click="cancelConfirmOpen = true">
                ✕ Annuler
              </button>
            </template>

            <template v-else-if="sheetMatch.status === 'FINISHED'">
              <button class="regie-action-btn" type="button" @click="openScoreForm">
                ✎ Correction rapide de score
              </button>
              <button class="regie-action-btn" type="button" @click="reopenConfirmOpen = true">
                ↺ Rouvrir
              </button>
            </template>

            <template v-else>
              <p class="regie-sheet-readonly">Match annulé — lecture seule.</p>
            </template>
          </div>

          <button class="regie-btn regie-sheet-close" type="button" @click="closeSheet">Fermer</button>
        </div>
      </div>
    </Teleport>

    <!-- Confirmation Démarrer (autre match en cours) -->
    <Teleport to="body">
      <div v-if="startConfirmOpen" class="modal-backdrop" @click.self="cancelStartConfirm">
        <div class="modal-card">
          <div class="modal-icon">⚠</div>
          <h3 class="modal-title">Un autre match est en cours</h3>
          <p class="modal-body">Le démarrer le mettra en pause.</p>
          <div class="modal-actions">
            <button class="regie-btn" type="button" @click="cancelStartConfirm">Annuler</button>
            <button class="regie-btn danger" type="button" @click="doStart">Confirmer</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Confirmation Mettre à l'antenne -->
    <Teleport to="body">
      <div v-if="featureConfirmOpen" class="modal-backdrop" @click.self="cancelFeature">
        <div class="modal-card">
          <div class="modal-icon">★</div>
          <h3 class="modal-title">Mettre ce match à l'antenne ?</h3>
          <div class="modal-actions">
            <button class="regie-btn" type="button" @click="cancelFeature">Annuler</button>
            <button class="regie-btn primary" type="button" @click="confirmFeature">Confirmer</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Modal fin de match — sélection du vainqueur -->
    <Teleport to="body">
      <div v-if="finishModalOpen && sheetMatch" class="modal-backdrop" @click.self="closeFinishModal">
        <div class="modal-card">
          <div class="modal-icon">🏆</div>
          <h3 class="modal-title">Déclarer vainqueur</h3>
          <p class="modal-body">Cette action est irréversible.</p>

          <label class="regie-retirement-toggle">
            <input v-model="finishRetirement" type="checkbox" />
            <span>Abandon adverse</span>
          </label>

          <div class="modal-actions modal-actions--vertical">
            <button class="regie-btn-finish" type="button" @click="confirmFinish('A')">
              {{ playerName(sheetMatch, 'A') }}
            </button>
            <button class="regie-btn-finish" type="button" @click="confirmFinish('B')">
              {{ playerName(sheetMatch, 'B') }}
            </button>
            <button class="regie-btn" type="button" @click="closeFinishModal">Annuler</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Modal forfait — qui est présent -->
    <Teleport to="body">
      <div v-if="forfaitModalOpen && sheetMatch" class="modal-backdrop" @click.self="forfaitModalOpen = false">
        <div class="modal-card">
          <div class="modal-icon">⚑</div>
          <h3 class="modal-title">Déclarer forfait</h3>
          <p class="modal-body">Qui est présent ? Le joueur choisi est déclaré vainqueur.</p>

          <div class="modal-actions modal-actions--vertical">
            <button class="regie-btn-finish" type="button" @click="confirmForfait('A')">
              {{ playerName(sheetMatch, 'A') }}
            </button>
            <button class="regie-btn-finish" type="button" @click="confirmForfait('B')">
              {{ playerName(sheetMatch, 'B') }}
            </button>
            <button class="regie-btn" type="button" @click="forfaitModalOpen = false">Annuler</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Confirmation Annuler (irréversible) -->
    <Teleport to="body">
      <div v-if="cancelConfirmOpen" class="modal-backdrop" @click.self="cancelConfirmOpen = false">
        <div class="modal-card">
          <div class="modal-icon">⚠</div>
          <h3 class="modal-title">Annuler ce match ?</h3>
          <p class="modal-body">Cette action est irréversible.</p>
          <div class="modal-actions">
            <button class="regie-btn" type="button" @click="cancelConfirmOpen = false">Retour</button>
            <button class="regie-btn danger" type="button" @click="confirmCancelMatch">Confirmer</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Confirmation Rouvrir -->
    <Teleport to="body">
      <div v-if="reopenConfirmOpen" class="modal-backdrop" @click.self="reopenConfirmOpen = false">
        <div class="modal-card">
          <div class="modal-icon">↺</div>
          <h3 class="modal-title">Rouvrir ce match ?</h3>
          <div class="modal-actions">
            <button class="regie-btn" type="button" @click="reopenConfirmOpen = false">Annuler</button>
            <button class="regie-btn primary" type="button" @click="confirmReopen">Confirmer</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Correction rapide de score -->
    <Teleport to="body">
      <div v-if="scoreFormOpen" class="modal-backdrop" @click.self="closeScoreForm">
        <div class="modal-card regie-score-card">
          <h3 class="modal-title">Correction rapide de score</h3>

          <div class="regie-score-grid">
            <label class="regie-score-field">
              <span>Sets A</span>
              <input v-model.number="scoreForm.setsA" type="number" min="0" class="regie-input" />
            </label>
            <label class="regie-score-field">
              <span>Sets B</span>
              <input v-model.number="scoreForm.setsB" type="number" min="0" class="regie-input" />
            </label>
            <label class="regie-score-field">
              <span>Jeux A</span>
              <input v-model.number="scoreForm.gamesA" type="number" min="0" class="regie-input" />
            </label>
            <label class="regie-score-field">
              <span>Jeux B</span>
              <input v-model.number="scoreForm.gamesB" type="number" min="0" class="regie-input" />
            </label>
          </div>

          <div class="modal-actions">
            <button class="regie-btn" type="button" @click="closeScoreForm">Annuler</button>
            <button class="regie-btn primary" type="button" @click="saveScoreForm">Enregistrer</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Confirmation suppression annonce -->
    <Teleport to="body">
      <div v-if="deleteAnnouncementTarget" class="modal-backdrop" @click.self="deleteAnnouncementTarget = null">
        <div class="modal-card">
          <div class="modal-icon">⚠</div>
          <h3 class="modal-title">Supprimer cette annonce ?</h3>
          <p class="modal-body">« {{ deleteAnnouncementTarget.message }} » sera définitivement supprimée.</p>
          <div class="modal-actions">
            <button class="regie-btn" type="button" @click="deleteAnnouncementTarget = null">Annuler</button>
            <button class="regie-btn danger" type="button" @click="confirmDeleteAnnouncement">Supprimer</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.regie-container {
  position: fixed;
  inset: 0;
  background: var(--bg-1);
  overflow: auto;
}

.regie-empty {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px;
  text-align: center;
}

.regie-empty-title { font-size: 18px; font-weight: 700; color: var(--ink-0); }
.regie-empty-hint { font-size: 13px; color: var(--ink-3); }

.regie-stage {
  position: absolute;
  top: 0;
  left: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-1);
}

/* ── En-tête ─────────────────────────────────────────────────────────── */
.regie-header {
  height: 64px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid var(--line-1);
}

.regie-back {
  width: 36px;
  height: 36px;
  border-radius: var(--r-md);
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  color: var(--ink-1);
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.regie-header-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.regie-title { font-size: 14px; font-weight: 700; color: var(--ink-0); letter-spacing: 0.04em; }
.regie-day { font-size: 11px; color: var(--ink-3); text-transform: capitalize; }

.regie-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── Match en cours épinglé ─────────────────────────────────────────── */
.regie-live-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: var(--bg-2);
  border: 1px solid var(--accent-soft);
  border-radius: var(--r-lg);
  box-shadow: var(--glow);
  cursor: pointer;
  text-align: left;
}

.regie-live-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
}

.regie-live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--danger);
  animation: pulse 1.5s ease-in-out infinite;
  display: inline-block;
}

.regie-live-players {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 19px;
  font-weight: 700;
  color: var(--ink-0);
}

.regie-live-players em { font-style: normal; font-size: 12px; color: var(--ink-3); }

.regie-live-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
}

.regie-live-stage { color: var(--ink-3); }
.regie-live-score { font-weight: 700; color: var(--accent); font-size: 15px; }

/* ── Fil de journée ─────────────────────────────────────────────────── */
.regie-feed {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.regie-feed-empty {
  text-align: center;
  color: var(--ink-4);
  font-size: 13px;
  margin: 12px 0;
}

.regie-break-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 14px;
  background: var(--bg-3);
  border: 1px solid var(--line-1);
  border-radius: var(--r-md);
  opacity: 0.8;
}

.regie-break-icon { font-size: 13px; color: var(--ink-3); }
.regie-break-label { font-size: 12px; color: var(--ink-2); }

.regie-match {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 16px;
  background: var(--bg-2);
  border: 1px solid var(--line-2);
  border-left: 3px solid var(--line-2);
  border-radius: var(--r-lg);
  text-align: left;
  font: inherit;
  color: inherit;
  width: 100%;
}

.regie-match-canceled { opacity: 0.55; }

.regie-match.punct-warn { border-left-color: var(--gold, #ffc83d); }
.regie-match.punct-late { border-left-color: var(--danger); }
.regie-match.punct-ok   { border-left-color: var(--success, #2ecc71); }

.regie-match-top {
  display: flex;
  align-items: center;
  gap: 8px;
}

.regie-match-status {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.12em;
  padding: 3px 8px;
  border-radius: 99px;
  text-transform: uppercase;
}

.regie-match-status.live      { background: var(--danger-soft); color: var(--danger); }
.regie-match-status.next      { background: var(--bg-4); color: var(--ink-2); }
.regie-match-status.scheduled { background: var(--accent-soft); color: var(--accent); }
.regie-match-status.finished  { background: var(--bg-4); color: var(--ink-3); }
.regie-match-status.canceled  { background: var(--bg-4); color: var(--ink-4); }

.regie-match-time { font-size: 12px; font-weight: 700; color: var(--accent); }
.regie-match-court { font-size: 11px; color: var(--ink-3); margin-left: auto; }

.regie-match-players {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: var(--ink-0);
}

.regie-match-players em { font-style: normal; font-size: 11px; color: var(--ink-3); }

.regie-match-bottom {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
}

.regie-match-event { color: var(--ink-3); flex: 1; }
.regie-match-score { font-weight: 700; color: var(--ink-2); }

/* ── Annonces ────────────────────────────────────────────────────────── */
.regie-announces {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  background: var(--bg-2);
  border: 1px solid var(--line-1);
  border-radius: var(--r-lg);
}

.regie-section-title {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--ink-0);
}

.regie-error-inline { margin: 0; font-size: 12px; color: var(--danger); }

.regie-announce-add {
  display: flex;
  gap: 8px;
}

.regie-input {
  flex: 1;
  padding: 8px 10px;
  border-radius: var(--r-md);
  border: 1px solid var(--line-2);
  background: var(--bg-3);
  color: var(--ink-0);
  font-size: 13px;
  font-family: inherit;
}

.regie-input:focus { outline: none; border-color: var(--accent); }

.regie-announce-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.regie-announce {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-top: 1px solid var(--line-1);
}

.regie-announce:first-child { border-top: none; }

.regie-announce-msg { flex: 1; font-size: 13px; color: var(--ink-0); }
.regie-announce-msg.is-inactive { color: var(--ink-3); text-decoration: line-through; }

.regie-toggle {
  position: relative;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  flex-shrink: 0;
}

.regie-toggle input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.regie-toggle-track {
  width: 34px;
  height: 18px;
  border-radius: 999px;
  background: var(--bg-4);
  border: 1px solid var(--line-2);
  display: inline-flex;
  align-items: center;
  padding: 2px;
  transition: background 150ms;
}

.regie-toggle-thumb {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--ink-3);
  transition: transform 150ms, background 150ms;
}

.regie-toggle input:checked + .regie-toggle-track {
  background: var(--accent-soft);
  border-color: var(--accent);
}

.regie-toggle input:checked + .regie-toggle-track .regie-toggle-thumb {
  background: var(--accent);
  transform: translateX(16px);
}

/* ── Boutons génériques ─────────────────────────────────────────────── */
.regie-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--r-md);
  border: 1px solid var(--line-2);
  background: var(--bg-3);
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-1);
  cursor: pointer;
  font-family: inherit;
}

.regie-btn.primary { background: var(--accent); border-color: var(--accent); color: #000; }
.regie-btn.danger { color: var(--danger); }
.regie-btn.danger:hover { background: var(--danger); border-color: var(--danger); color: #fff; }

/* ── Toast d'erreur ──────────────────────────────────────────────────── */
.regie-toast {
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
  font-size: 14px;
  font-weight: 600;
  text-align: center;
  box-shadow: var(--shadow-2);
}

/* ── Feuille d'actions (bottom-sheet, pattern ArbitreMatch.vue) ──────── */
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

.regie-sheet-backdrop { align-items: flex-end; }

.regie-sheet {
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

.regie-sheet-handle {
  width: 40px;
  height: 4px;
  border-radius: 99px;
  background: var(--line-2);
  align-self: center;
  margin-bottom: 4px;
}

.regie-sheet-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: var(--ink-0);
  text-align: center;
}

.regie-sheet-title em { font-style: normal; font-size: 12px; color: var(--ink-3); margin: 0 4px; }

.regie-sheet-sub {
  margin: 0 0 4px;
  font-size: 12px;
  color: var(--ink-3);
  text-align: center;
}

.regie-sheet-readonly {
  text-align: center;
  color: var(--ink-3);
  font-size: 13px;
  padding: 12px 0;
}

.regie-sheet-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.regie-action-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: var(--r-md);
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  color: var(--ink-1);
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
}

.regie-action-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.regie-action-btn--primary { background: var(--accent); border-color: var(--accent); color: #000; }
.regie-action-btn--danger { background: var(--danger-soft); border-color: rgba(255,48,82,0.3); color: var(--danger); }
.regie-action-btn--danger-ghost { background: transparent; border-color: var(--line-2); color: var(--danger); }

.regie-sheet-close { margin-top: 4px; justify-content: center; }

/* ── Modales de confirmation (pattern ArbitreMatch.vue) ───────────────── */
.modal-card {
  background: var(--bg-2);
  border: 1px solid var(--line-2);
  border-radius: var(--r-xl);
  padding: 32px 28px;
  max-width: 420px;
  width: 90%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  box-shadow: var(--shadow-2);
}

.modal-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--danger-soft);
  color: var(--danger);
  font-size: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-title { margin: 0; font-size: 18px; font-weight: 700; color: var(--ink-0); text-align: center; }
.modal-body { margin: 0; font-size: 13px; color: var(--ink-2); text-align: center; }

.modal-actions { display: flex; gap: 10px; margin-top: 4px; }
.modal-actions--vertical { flex-direction: column; width: 100%; }

.regie-retirement-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  align-self: flex-start;
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-1);
  cursor: pointer;
}

.regie-retirement-toggle input { width: 16px; height: 16px; accent-color: var(--accent); }

.regie-btn-finish {
  width: 100%;
  padding: 12px 24px;
  border-radius: var(--r-md);
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  color: var(--ink-1);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
}

.regie-btn-finish:hover { background: var(--bg-4); }

/* ── Correction rapide de score ────────────────────────────────────── */
.regie-score-card { align-items: stretch; }

.regie-score-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.regie-score-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ink-3);
}
</style>
