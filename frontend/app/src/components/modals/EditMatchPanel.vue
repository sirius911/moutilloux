<script setup lang="ts">
import { ref, computed } from 'vue'
import { useEventStore } from '@/stores/event'
import type { CalendarReorderPayload } from '@/stores/event'
import Segmented from '@/components/ui/Segmented.vue'
import ConfirmModal from '@/components/ui/ConfirmModal.vue'
import { extractApiError } from '@/lib/apiError'
import { useApi } from '@/composables/useApi'
import { usePolling } from '@/composables/usePolling'
import type { Match, PosterState } from '@/types'

const props = defineProps<{ match: Match; initialTab?: 'score' | 'format' | 'planning' | 'poster' }>()
const emit = defineEmits<{ close: []; saved: []; 'poster-updated': [] }>()

const eventStore = useEventStore()
const { get, post } = useApi()

// Mapping formatSets (index UI 1/2/3) ↔ best_of (nombre de sets back 1/3/5)
const FORMAT_SETS_TO_BEST_OF: Record<number, number> = { 1: 1, 2: 3, 3: 5 }
const BEST_OF_TO_FORMAT_SETS: Record<number, number> = { 1: 1, 3: 2, 5: 3 }

const tab = ref<'score' | 'format' | 'planning' | 'poster'>(props.initialTab ?? 'score')
const saving = ref(false)
const error = ref('')

// Score tab
const setsA = ref(props.match.setsA)
const setsB = ref(props.match.setsB)
const gamesA = ref(props.match.gamesA)
const gamesB = ref(props.match.gamesB)
const pointsA = ref(props.match.pointsA)
const pointsB = ref(props.match.pointsB)
const tbActive = ref(props.match.tbActive)
const winnerSide = ref<'none' | 'A' | 'B'>(props.match.winnerSide ?? 'none')

// Format tab
const formatSets = ref(BEST_OF_TO_FORMAT_SETS[props.match.bestOf] ?? 1)
const formatGames = ref(String(props.match.gamesToWin ?? 5))
const formatTb = ref(String(props.match.tbAt ?? 4))
const formatTbPoints = ref(String(props.match.tbPointsToWin ?? 7))
const formatServer = ref<'A' | 'B'>(props.match.server === 'B' ? 'B' : 'A')
const formatTbWinByTwo = ref(props.match.tbWinByTwo ?? true)
const formatDecidingSetMode = ref<'FULL_SET' | 'SUPER_TB'>(
  props.match.decidingSetMode === 'SUPER_TB' ? 'SUPER_TB' : 'FULL_SET'
)
const formatDecidingTbPoints = ref(String(props.match.decidingTbPointsToWin ?? 10))

const initialFormatSnapshot = {
  formatSets: formatSets.value,
  formatGames: formatGames.value,
  formatTb: formatTb.value,
  formatTbPoints: formatTbPoints.value,
  formatServer: formatServer.value,
  formatTbWinByTwo: formatTbWinByTwo.value,
  formatDecidingSetMode: formatDecidingSetMode.value,
  formatDecidingTbPoints: formatDecidingTbPoints.value,
}

// Sélecteur de préréglage nommé (Poule / Quart / Demi / Finale / Manuel)
const formatPreset = ref(props.match.matchFormat || 'MANUAL')

const formatPresetOptions = [
  { value: 'G_SET5_TB44', label: 'Poule : 1 set à 5, TB à 4-4' },
  { value: 'QF_SET5_TB55', label: 'Quart : 1 set à 6, TB à 5-5' },
  { value: 'NORMAL_1SET', label: 'Demi : 1 set normal' },
  { value: 'BO3', label: 'Finale : 2 sets gagnants' },
  { value: 'MANUAL', label: 'Manuel' },
]

const decidingSetModeOptions = [
  { value: 'FULL_SET', label: 'Set complet' },
  { value: 'SUPER_TB', label: 'Super tie-break' },
]

const PRESET_VALUES: Record<string, {
  formatSets: number; formatGames: string; formatTb: string; formatTbPoints: string
  formatTbWinByTwo: boolean
  formatDecidingSetMode?: 'FULL_SET' | 'SUPER_TB'
  formatDecidingTbPoints?: string
}> = {
  G_SET5_TB44: { formatSets: 1, formatGames: '5', formatTb: '4', formatTbPoints: '7', formatTbWinByTwo: true },
  QF_SET5_TB55: { formatSets: 1, formatGames: '6', formatTb: '5', formatTbPoints: '7', formatTbWinByTwo: true },
  NORMAL_1SET: { formatSets: 1, formatGames: '6', formatTb: '6', formatTbPoints: '7', formatTbWinByTwo: true },
  BO3: {
    formatSets: 2, formatGames: '6', formatTb: '6', formatTbPoints: '7', formatTbWinByTwo: true,
    formatDecidingSetMode: 'FULL_SET', formatDecidingTbPoints: '10',
  },
}

function applyPresetToFields() {
  const preset = PRESET_VALUES[formatPreset.value]
  if (!preset) return // MANUAL : ne touche à rien, l'admin garde ses valeurs actuelles
  formatSets.value = preset.formatSets
  formatGames.value = preset.formatGames
  formatTb.value = preset.formatTb
  formatTbPoints.value = preset.formatTbPoints
  formatTbWinByTwo.value = preset.formatTbWinByTwo
  if (preset.formatDecidingSetMode) formatDecidingSetMode.value = preset.formatDecidingSetMode
  if (preset.formatDecidingTbPoints) formatDecidingTbPoints.value = preset.formatDecidingTbPoints
}

// Planning tab
const status = ref<'scheduled' | 'live' | 'finished' | 'canceled'>(
  props.match.status === 'LIVE' ? 'live'
    : props.match.status === 'FINISHED' ? 'finished'
    : props.match.status === 'CANCELED' ? 'canceled'
    : 'scheduled'
)
const featured = ref(props.match.isFeatured)

// Journée courante : cherche dans le calendrier quelle PlayDay contient ce match
const currentPlayDayId = computed<number | null>(() => {
  const cal = eventStore.calendar
  if (!cal) return null
  for (const day of cal.playDays) {
    if (day.matches.some(m => m.id === props.match.id)) return day.id
  }
  return null
})

const selectedPlayDayId = ref<number | null>(currentPlayDayId.value)

async function changePlayDay(newPlayDayId: number | null) {
  const editionId = eventStore.activeEdition?.id
  const cal = eventStore.calendar
  if (!editionId || !cal) return
  saving.value = true
  error.value = ''
  try {
    const matchId = props.match.id
    const payload: CalendarReorderPayload = {
      playDays: cal.playDays.map(day => {
        const matchItems = day.matches
          .filter(m => m.id !== matchId)
          .map(m => ({ type: 'match' as const, id: m.id }))
        const breakItems = day.breaks.map(b => ({ type: 'break' as const, id: b.id }))
        const added = day.id === newPlayDayId
          ? [{ type: 'match' as const, id: matchId }]
          : []
        return { playDayId: day.id, items: [...matchItems, ...breakItems, ...added] }
      }),
    }
    await eventStore.reorderCalendar(editionId, payload)
    selectedPlayDayId.value = newPlayDayId
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Erreur lors du déplacement.'
  } finally {
    saving.value = false
  }
}

const nameA = computed(() =>
  props.match.sideA?.player?.fullName ?? props.match.sideALabel ?? 'Joueur A'
)
const nameB = computed(() =>
  props.match.sideB?.player?.fullName ?? props.match.sideBLabel ?? 'Joueur B'
)

// Onglet Affiche — état + actions
const posterState = ref<PosterState | null>(null)
const posterActionError = ref('')   // erreur d'action (generate/select/clear), distincte de error (footer Score/Format/Planning)
const posterActionBusy = ref(false) // désactive les boutons pendant generate/select/clear/retirer
const showRemovePosterConfirm = ref(false)

// Attitude par side, pré-remplie depuis Player.attitude (exposé par _pack_entry)
const attitudeA = ref(props.match.sideA?.player?.attitude ?? '')
const attitudeB = ref(props.match.sideB?.player?.attitude ?? '')

async function fetchPosterState() {
  posterState.value = await get<PosterState>(`/api/matches/${props.match.id}/poster/`)
}

// Polling ~2s conforme à specs/technical/affiche-match.md, tant que le
// panneau est ouvert (le composant est monté/démonté par v-if dans
// AdminMatches.vue, usePolling gère lui-même le cleanup à onUnmounted).
usePolling(fetchPosterState, 2000)

const sidesResolved = computed(() => !!props.match.sideA && !!props.match.sideB)

const generateDisabledReason = computed<string | null>(() => {
  if (posterActionBusy.value) return null // pas de message, juste désactivé pendant l'appel
  if (!sidesResolved.value) return 'Les deux camps du match doivent être déterminés avant de générer une affiche.'
  if (posterState.value?.job?.status === 'RUNNING' || posterState.value?.job?.status === 'PENDING') {
    return 'Une génération est déjà en cours pour ce match.'
  }
  return null
})

async function generatePosters() {
  posterActionError.value = ''
  posterActionBusy.value = true
  try {
    posterState.value = await post<PosterState>(`/api/matches/${props.match.id}/poster/generate/`, {
      attitudes: { A: attitudeA.value, B: attitudeB.value },
    })
  } catch (e) {
    posterActionError.value = extractApiError(e, 'Erreur lors du lancement de la génération.')
  } finally {
    posterActionBusy.value = false
  }
}

async function selectCandidate(index: number) {
  posterActionError.value = ''
  posterActionBusy.value = true
  try {
    posterState.value = await post<PosterState>(`/api/matches/${props.match.id}/poster/select/`, {
      candidate: index,
    })
    emit('poster-updated') // pour rafraîchir le calendrier (posterUrl du match a changé)
  } catch (e) {
    posterActionError.value = extractApiError(e, 'Erreur lors du choix de l\'affiche.')
  } finally {
    posterActionBusy.value = false
  }
}

async function relaunchPosters() {
  // "Relancer" = même appel que Générer (le serveur purge le job précédent
  // et recrée un nouveau lot de 2 candidats).
  await generatePosters()
}

function confirmRemovePoster() {
  showRemovePosterConfirm.value = true
}

async function removePoster() {
  posterActionError.value = ''
  posterActionBusy.value = true
  try {
    posterState.value = await post<PosterState>(`/api/matches/${props.match.id}/poster/clear/`)
    emit('poster-updated')
  } catch (e) {
    posterActionError.value = extractApiError(e, 'Erreur lors du retrait de l\'affiche.')
  } finally {
    posterActionBusy.value = false
    showRemovePosterConfirm.value = false
  }
}

const isLive = computed(() => props.match.status === 'LIVE')

const statusLabel = computed(() => {
  if (props.match.status === 'LIVE') return 'EN DIRECT'
  if (props.match.status === 'FINISHED') return 'TERMINÉ'
  if (props.match.status === 'CANCELED') return 'ANNULÉ'
  return 'PRÉVU'
})

const tabItems = [
  { id: 'score' as const, label: 'Score' },
  { id: 'format' as const, label: 'Format' },
  { id: 'planning' as const, label: 'Planning' },
  { id: 'poster' as const, label: 'Affiche' },
]

const winnerOptions = computed(() => [
  { value: 'none', label: 'À déterminer' },
  { value: 'A', label: nameA.value },
  { value: 'B', label: nameB.value },
])

const formatSetsOptions = [
  { value: 1, label: '1 set' },
  { value: 2, label: 'Best of 3' },
  { value: 3, label: 'Best of 5' },
]

const serverOptions = computed(() => [
  { value: 'A', label: nameA.value },
  { value: 'B', label: nameB.value },
])

const planningStatusOptions = [
  { value: 'scheduled', label: 'Prévu' },
  { value: 'live', label: 'En direct' },
  { value: 'finished', label: 'Terminé' },
  { value: 'canceled', label: 'Annulé' },
]

const showStartConfirm = ref(false)
const showFinishConfirm = ref(false)
const showFeatureConfirm = ref(false)
const showReopenConfirm = ref(false)

function hasOtherLiveMatch(): boolean {
  const allMatches = eventStore.calendar?.playDays.flatMap((d) => d.matches) ?? []
  return allMatches.some((m) => m.status === 'LIVE' && m.id !== props.match.id)
}

async function save() {
  if (props.match.status === 'FINISHED' && status.value === 'live' && !showReopenConfirm.value) {
    showReopenConfirm.value = true
    return
  }

  if (status.value === 'live' && props.match.status !== 'LIVE' && hasOtherLiveMatch() && !showStartConfirm.value) {
    showReopenConfirm.value = false
    showStartConfirm.value = true
    return
  }

  if (status.value === 'finished' && props.match.status !== 'FINISHED' && !showFinishConfirm.value) {
    showFinishConfirm.value = true
    return
  }

  if (featured.value && !props.match.isFeatured && !showFeatureConfirm.value) {
    showFeatureConfirm.value = true
    return
  }

  const eventId = eventStore.activeEventId
  if (!eventId) return
  saving.value = true
  error.value = ''
  try {
    // Édition via MatchEditForm. On omet le court (mono-court, non éditable)
    // et scheduled_time (ETA dérivée, lecture seule — décisions 18-19). Les
    // champs de format sont inclus ; match_format ne bascule sur
    // MANUAL que si les champs détaillés ont réellement changé (sinon
    // MatchEditForm.clean() réappliquerait le preset silencieusement, ou on
    // basculerait à tort le format sur « Manuel » lors d'une simple édition
    // de score).
    const formatChanged =
      formatSets.value !== initialFormatSnapshot.formatSets ||
      formatGames.value !== initialFormatSnapshot.formatGames ||
      formatTb.value !== initialFormatSnapshot.formatTb ||
      formatTbPoints.value !== initialFormatSnapshot.formatTbPoints ||
      formatServer.value !== initialFormatSnapshot.formatServer ||
      formatTbWinByTwo.value !== initialFormatSnapshot.formatTbWinByTwo ||
      formatDecidingSetMode.value !== initialFormatSnapshot.formatDecidingSetMode ||
      formatDecidingTbPoints.value !== initialFormatSnapshot.formatDecidingTbPoints

    // match_format à envoyer :
    // - si le sélecteur de préréglage a changé vers un preset nommé (≠ MANUAL) :
    //   on envoie ce preset — le serveur (MatchEditForm.clean()) réapplique alors
    //   lui-même le détail exact, la source de vérité reste le back.
    // - si le sélecteur est resté sur MANUAL (ou est lui-même MANUAL) et qu'un champ
    //   détaillé a divergé de l'instantané initial : on force MANUAL (comportement #7).
    // - sinon (rien n'a changé) : on renvoie le matchFormat actuel du match, inchangé.
    const presetChanged = formatPreset.value !== props.match.matchFormat
    const matchFormatToSend =
      presetChanged && formatPreset.value !== 'MANUAL'
        ? formatPreset.value
        : formatChanged
          ? 'MANUAL'
          : props.match.matchFormat

    await eventStore.editMatch(eventId, props.match.id, {
      status: status.value.toUpperCase(),
      sets_a: setsA.value,
      sets_b: setsB.value,
      games_a: gamesA.value,
      games_b: gamesB.value,
      points_a: pointsA.value,
      points_b: pointsB.value,
      tb_active: tbActive.value,
      winner_side:
        winnerSide.value === 'A' || winnerSide.value === 'B' ? winnerSide.value : null,
      match_format: matchFormatToSend,
      best_of: FORMAT_SETS_TO_BEST_OF[formatSets.value] ?? 1,
      games_to_win: Number(formatGames.value),
      tb_at: Number(formatTb.value),
      tb_points_to_win: Number(formatTbPoints.value),
      tb_win_by_two: formatTbWinByTwo.value,
      deciding_set_mode: formatDecidingSetMode.value,
      deciding_tb_points_to_win: Number(formatDecidingTbPoints.value),
      server: formatServer.value,
      is_featured: featured.value,
    })
    if (featured.value && !props.match.isFeatured) {
      // L'activation doit toujours passer par start_match() (mark_live +
      // rétrogradation des autres matchs featured, invariant mono-LIVE —
      // cf. specs/technical/cycle-de-vie-match.md) : MatchEditForm.clean()
      // neutralise silencieusement toute activation via le payload générique
      // ci-dessus si le statut n'est pas lui-même passé à LIVE, donc c'est
      // ce second appel dédié qui active réellement la mise en avant.
      await eventStore.featureMatch(eventId, props.match.id)
    }
    emit('saved')
    emit('close')
  } catch (e) {
    error.value = extractApiError(e, 'Erreur lors de la sauvegarde.')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="slide-bg" @mousedown.self="emit('close')">
      <aside class="slide" @mousedown.stop>
        <!-- Header -->
        <header class="slide-head">
          <div class="slide-head-info">
            <div class="slide-crumb">{{ match.stageLabel }}</div>
            <h2>{{ nameA }} <em>vs</em> {{ nameB }}</h2>
            <div class="slide-tags">
              <span :class="['slide-tag', match.status === 'LIVE' ? 'live' : '']">
                <i v-if="match.status === 'LIVE'" class="live-dot" />
                {{ statusLabel }}
              </span>
              <span v-if="match.court" class="slide-tag">{{ match.court }}</span>
              <span v-if="match.scheduledTime" class="slide-tag">{{ match.scheduledTime }}</span>
              <span v-if="match.isFeatured" class="slide-tag star">★ MIS EN AVANT</span>
            </div>
          </div>
          <button class="mdl-close" aria-label="Fermer" @click="emit('close')">
            <svg viewBox="0 0 24 24" width="18" height="18">
              <path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
          </button>
        </header>

        <!-- Tabs -->
        <nav class="slide-tabs">
          <button
            v-for="t in tabItems"
            :key="t.id"
            :class="['slide-tab', { on: tab === t.id }]"
            type="button"
            @click="tab = t.id"
          >
            {{ t.label }}
          </button>
        </nav>

        <!-- Body -->
        <div class="slide-body">
          <!-- Score -->
          <template v-if="tab === 'score'">
            <div class="slide-section">
              <h4>
                Score actuel
                <span class="slide-section-sub">éditable en cas d'erreur arbitre</span>
              </h4>
              <div class="score-grid">
                <div class="score-grid-head">
                  <span></span>
                  <span>SETS</span>
                  <span>JEU EN COURS</span>
                  <span>POINT</span>
                </div>
                <div class="score-grid-row">
                  <span class="score-grid-name">
                    <i class="srv" />
                    {{ nameA }}
                    <em v-if="match.sideA?.seedHint" class="seed-tag">{{ match.sideA.seedHint }}</em>
                  </span>
                  <input v-model.number="setsA" class="inp inp-num tab" type="number" min="0" />
                  <input v-model.number="gamesA" class="inp inp-num tab" type="number" min="0" />
                  <input v-model.number="pointsA" class="inp inp-num tab" type="number" min="0" />
                </div>
                <div class="score-grid-row">
                  <span class="score-grid-name">
                    <i class="srv srv-off" />
                    {{ nameB }}
                    <em v-if="match.sideB?.seedHint" class="seed-tag">{{ match.sideB.seedHint }}</em>
                  </span>
                  <input v-model.number="setsB" class="inp inp-num tab" type="number" min="0" />
                  <input v-model.number="gamesB" class="inp inp-num tab" type="number" min="0" />
                  <input v-model.number="pointsB" class="inp inp-num tab" type="number" min="0" />
                </div>
              </div>
              <label class="sw" style="margin-top: 14px">
                <input v-model="tbActive" type="checkbox" />
                <i />
                <span>Tie-break activé</span>
              </label>
            </div>

            <div class="slide-section">
              <h4>Vainqueur</h4>
              <Segmented v-model="winnerSide" :options="winnerOptions" />
            </div>
          </template>

          <!-- Format -->
          <template v-if="tab === 'format'">
            <div v-if="isLive" class="format-lock-banner">
              <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M8 11V7a4 4 0 0 1 8 0v4" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>
              Verrouillé — match en cours. Ces champs ne seront pas pris en compte.
            </div>
            <fieldset :disabled="isLive" class="format-fieldset">
              <div class="slide-section">
                <h4>Format du match</h4>
                <div class="fld-col">
                  <label class="fld">
                    <span class="fld-lbl">Préréglage</span>
                    <select v-model="formatPreset" class="inp" @change="applyPresetToFields">
                      <option v-for="p in formatPresetOptions" :key="p.value" :value="p.value">{{ p.label }}</option>
                    </select>
                  </label>
                  <label class="fld">
                    <span class="fld-lbl">Sets à gagner</span>
                    <Segmented v-model="formatSets" :options="formatSetsOptions" />
                  </label>
                  <div class="fld-row">
                    <label class="fld">
                      <span class="fld-lbl">Jeux par set</span>
                      <select v-model="formatGames" class="inp">
                        <option value="4">4 jeux</option>
                        <option value="5">5 jeux (TB à 4)</option>
                        <option value="6">6 jeux (TB à 6)</option>
                      </select>
                    </label>
                    <label class="fld">
                      <span class="fld-lbl">Tie-break à</span>
                      <input v-model="formatTb" class="inp tab" />
                    </label>
                    <label class="fld">
                      <span class="fld-lbl">Points TB</span>
                      <select v-model="formatTbPoints" class="inp">
                        <option value="7">7 points</option>
                        <option value="10">10 points</option>
                      </select>
                    </label>
                  </div>
                  <label class="fld">
                    <span class="fld-lbl">Service initial</span>
                    <Segmented v-model="formatServer" :options="serverOptions" />
                  </label>
                  <label class="sw">
                    <input v-model="formatTbWinByTwo" type="checkbox" />
                    <i />
                    <span>Tie-break : 2 points d'écart</span>
                  </label>
                  <label class="fld">
                    <span class="fld-lbl">Set décisif (égalité en sets)</span>
                    <Segmented v-model="formatDecidingSetMode" :options="decidingSetModeOptions" />
                  </label>
                  <label v-if="formatDecidingSetMode === 'SUPER_TB'" class="fld">
                    <span class="fld-lbl">Points du super tie-break décisif</span>
                    <input v-model="formatDecidingTbPoints" class="inp tab" type="number" min="1" />
                  </label>
                </div>
              </div>
            </fieldset>
          </template>

          <!-- Planning -->
          <template v-if="tab === 'planning'">
            <div class="slide-section">
              <h4>Planning</h4>
              <div class="fld-col">
                <label class="fld">
                  <span class="fld-lbl">Journée</span>
                  <select
                    class="inp"
                    :value="selectedPlayDayId ?? ''"
                    :disabled="saving"
                    @change="changePlayDay(($event.target as HTMLSelectElement).value ? Number(($event.target as HTMLSelectElement).value) : null)"
                  >
                    <option value="">À planifier</option>
                    <option
                      v-for="day in (eventStore.calendar?.playDays ?? [])"
                      :key="day.id"
                      :value="day.id"
                    >
                      {{ new Date(day.date + 'T00:00:00').toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' }) }}
                    </option>
                  </select>
                </label>
                <div class="fld">
                  <span class="fld-lbl">Heure estimée</span>
                  <span class="inp inp-ro">{{ match.scheduledTime ? '~' + match.scheduledTime : '—' }}</span>
                </div>
                <div class="fld">
                  <span class="fld-lbl">Court</span>
                  <span class="inp inp-ro">{{ match.court || 'Central' }}</span>
                </div>
                <label class="fld">
                  <span class="fld-lbl">Statut</span>
                  <Segmented v-model="status" :options="planningStatusOptions" />
                </label>
              </div>
            </div>

            <div class="slide-section">
              <h4>Mise en avant</h4>
              <label class="sw">
                <input v-model="featured" type="checkbox" />
                <i />
                <span>Afficher ce match sur le scoreboard TV</span>
              </label>
              <p class="slide-hint">
                Un seul match peut être mis en avant à la fois. Si vous activez ce match, celui qui est actuellement à l'antenne sera retiré.
              </p>
            </div>
          </template>

          <!-- Affiche -->
          <template v-if="tab === 'poster'">
            <div class="slide-section">
              <h4>Affiche retenue</h4>
              <div v-if="posterState?.posterUrl" class="poster-current">
                <img :src="posterState.posterUrl" alt="Affiche du match" class="poster-preview" />
                <button
                  class="adm-btn"
                  type="button"
                  :disabled="posterActionBusy"
                  @click="confirmRemovePoster"
                >Retirer</button>
              </div>
              <p v-else class="slide-hint">Aucune affiche retenue pour ce match.</p>
            </div>

            <div class="slide-section">
              <h4>Générer une affiche</h4>
              <div class="fld-col">
                <label class="fld">
                  <span class="fld-lbl">Attitude — {{ nameA }}</span>
                  <input v-model="attitudeA" class="inp" type="text" placeholder="ex. charmeuse, furieux…" />
                </label>
                <label class="fld">
                  <span class="fld-lbl">Attitude — {{ nameB }}</span>
                  <input v-model="attitudeB" class="inp" type="text" placeholder="ex. charmeuse, furieux…" />
                </label>
              </div>
              <p v-if="generateDisabledReason" class="slide-hint">{{ generateDisabledReason }}</p>
              <button
                class="adm-btn primary"
                type="button"
                style="margin-top: 12px"
                :disabled="!!generateDisabledReason || posterActionBusy"
                @click="generatePosters"
              >
                {{ posterActionBusy ? 'Génération…' : 'Générer 2 propositions' }}
              </button>
            </div>

            <div v-if="posterState?.job" class="slide-section">
              <h4>Suivi de génération</h4>
              <p v-if="posterState.job.status === 'PENDING' || posterState.job.status === 'RUNNING'" class="slide-hint">
                Génération en cours… vous pouvez fermer ce panneau et revenir plus tard.
              </p>
              <p v-if="posterState.job.status === 'ERROR'" class="slide-err">{{ posterState.job.error }}</p>

              <div v-if="posterState.job.status === 'DONE' && posterState.job.candidates.length > 0" class="poster-gallery">
                <div v-for="(url, i) in posterState.job.candidates" :key="i" class="poster-candidate">
                  <img :src="url" alt="Proposition d'affiche" class="poster-preview" />
                  <button
                    class="adm-btn primary"
                    type="button"
                    :disabled="posterActionBusy"
                    @click="selectCandidate(i)"
                  >Choisir</button>
                </div>
              </div>
              <button
                v-if="posterState.job.status === 'DONE' || posterState.job.status === 'ERROR'"
                class="adm-btn"
                type="button"
                style="margin-top: 12px"
                :disabled="posterActionBusy"
                @click="relaunchPosters"
              >Relancer</button>
            </div>

            <p v-if="posterActionError" class="slide-err">{{ posterActionError }}</p>
          </template>
        </div>

        <!-- Footer -->
        <footer class="slide-foot">
          <span v-if="error" class="slide-err">{{ error }}</span>
          <span v-else class="slide-foot-spacer" />
          <button class="adm-btn" type="button" @click="emit('close')">Annuler</button>
          <button class="adm-btn primary" type="button" :disabled="saving" @click="save">
            {{ saving ? 'Enregistrement…' : 'Enregistrer' }}
          </button>
        </footer>
      </aside>
    </div>
    <ConfirmModal
      v-if="showReopenConfirm"
      title="Rouvrir ce match ?"
      body="Le match repasse EN DIRECT, le score actuel est conservé. Cette action est réservée aux administrateurs."
      confirm-label="Rouvrir"
      :danger="false"
      @confirm="save"
      @close="showReopenConfirm = false"
    />
    <ConfirmModal
      v-if="showStartConfirm"
      title="Démarrer ce match ?"
      body="Un autre match est en cours — le démarrer le mettra en pause (il repasse Prévu, score conservé)."
      confirm-label="Démarrer"
      :danger="false"
      @confirm="save"
      @close="showStartConfirm = false"
    />
    <ConfirmModal
      v-if="showFinishConfirm"
      title="Terminer ce match ?"
      body="Le vainqueur sera figé, la mise en avant retirée si active, et le classement/tableau final recalculés. Une réouverture reste possible ensuite (admin)."
      confirm-label="Terminer"
      :danger="false"
      @confirm="save"
      @close="showFinishConfirm = false"
    />
    <ConfirmModal
      v-if="showFeatureConfirm"
      title="Mettre ce match en avant ?"
      body="Ce match passe EN DIRECT et devient le match affiché sur la TV. Le match actuellement à l'antenne est retiré."
      confirm-label="Mettre en avant"
      :danger="false"
      @confirm="save"
      @close="showFeatureConfirm = false"
    />
    <ConfirmModal
      v-if="showRemovePosterConfirm"
      title="Retirer l'affiche ?"
      body="L'affiche retenue sera définitivement supprimée. Vous pourrez en générer une nouvelle ensuite."
      confirm-label="Retirer"
      :danger="true"
      @confirm="removePoster"
      @close="showRemovePosterConfirm = false"
    />
  </Teleport>
</template>

<style scoped>
/* ── Overlay ─────────────────────────────────────────────────────── */
.slide-bg {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: flex-end;
  z-index: 200;
}

.slide {
  width: 520px;
  max-width: 100%;
  height: 100%;
  background: var(--bg-2);
  border-left: 1px solid var(--line-2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── Header ───────────────────────────────────────────────────────── */
.slide-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 24px 24px 16px;
  border-bottom: 1px solid var(--line-1);
  flex-shrink: 0;
}

.slide-head-info { flex: 1; min-width: 0; }

.slide-crumb {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.1em;
  color: var(--ink-3);
  text-transform: uppercase;
  margin-bottom: 6px;
}

.slide-head h2 {
  margin: 0 0 10px;
  font-size: 18px;
  font-weight: 700;
  color: var(--ink-0);
}

.slide-head h2 em {
  font-style: normal;
  font-size: 13px;
  color: var(--ink-3);
  margin: 0 4px;
}

.slide-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.slide-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 99px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  background: var(--bg-4);
  color: var(--ink-2);
  border: 1px solid var(--line-2);
}

.slide-tag.live { background: var(--danger-soft); color: var(--danger); border-color: transparent; }
.slide-tag.star { color: var(--accent); border-color: var(--accent); background: var(--accent-soft); }

.live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--danger);
  animation: pulse 1.5s ease-in-out infinite;
  display: inline-block;
}

.mdl-close {
  width: 32px;
  height: 32px;
  border-radius: var(--r-sm);
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  color: var(--ink-2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  cursor: pointer;
  transition: background 150ms;
}

.mdl-close:hover { background: var(--bg-4); color: var(--ink-0); }

/* ── Tabs ─────────────────────────────────────────────────────────── */
.slide-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--line-1);
  flex-shrink: 0;
}

.slide-tab {
  flex: 1;
  padding: 12px 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--ink-2);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: color 150ms, border-color 150ms;
  font-family: inherit;
}

.slide-tab:hover { color: var(--ink-0); }

.slide-tab.on {
  color: var(--accent);
  border-bottom-color: var(--accent);
  font-weight: 600;
}

/* ── Body ─────────────────────────────────────────────────────────── */
.slide-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.slide-section {
  padding-bottom: 24px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--line-1);
}

.slide-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.slide-section h4 {
  margin: 0 0 14px;
  font-size: 13px;
  font-weight: 700;
  color: var(--ink-2);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.slide-section-sub {
  font-size: 11px;
  font-weight: 400;
  text-transform: none;
  letter-spacing: 0;
  color: var(--ink-3);
}

.slide-hint {
  font-size: 12px;
  color: var(--ink-3);
  margin-top: 10px;
  line-height: 1.5;
}

/* ── Score grid ───────────────────────────────────────────────────── */
.score-grid {
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  overflow: hidden;
  margin-bottom: 4px;
}

.score-grid-head {
  display: grid;
  grid-template-columns: 1fr 70px 100px 80px;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-3);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--ink-3);
  text-transform: uppercase;
}

.score-grid-row {
  display: grid;
  grid-template-columns: 1fr 70px 100px 80px;
  gap: 8px;
  padding: 10px 12px;
  align-items: center;
  border-top: 1px solid var(--line-1);
}

.score-grid-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-0);
}

.srv {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  flex-shrink: 0;
}

.srv-off { background: var(--line-3); }

.seed-tag {
  font-style: normal;
  font-size: 10px;
  font-family: var(--font-mono);
  background: var(--accent-soft);
  color: var(--accent);
  padding: 1px 5px;
  border-radius: var(--r-xs);
}

/* ── Inputs ───────────────────────────────────────────────────────── */
.inp {
  width: 100%;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  padding: 8px 10px;
  font-size: 14px;
  color: var(--ink-0);
  outline: none;
  transition: border-color 150ms;
  box-sizing: border-box;
  font-family: inherit;
}

.inp:focus { border-color: var(--accent); }

.inp-num {
  text-align: center;
  padding: 8px 6px;
  font-size: 16px;
  font-weight: 700;
}

.inp-ro {
  display: flex;
  align-items: center;
  padding: 8px 10px;
  background: var(--bg-4);
  border: 1px solid var(--line-1);
  border-radius: var(--r-md);
  font-size: 14px;
  color: var(--ink-2);
  min-height: 38px;
  box-sizing: border-box;
}

.tab { font-family: var(--font-mono); }

/* Field helpers */
.fld-col { display: flex; flex-direction: column; gap: 16px; }
.fld-row { display: flex; gap: 12px; }
.fld { display: flex; flex-direction: column; gap: 6px; flex: 1; }

.fld-lbl {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-2);
  letter-spacing: 0.04em;
}

/* Toggle switch */
.sw {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-size: 14px;
  color: var(--ink-1);
}

.sw input { display: none; }

.sw i {
  width: 36px;
  height: 20px;
  border-radius: 99px;
  background: var(--line-3);
  position: relative;
  flex-shrink: 0;
  transition: background 200ms;
}

.sw i::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  transition: transform 200ms;
}

.sw input:checked ~ i { background: var(--accent); }
.sw input:checked ~ i::after { transform: translateX(16px); }

/* ── Format lock ──────────────────────────────────────────────────── */
.format-lock-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  margin-bottom: 12px;
  background: var(--danger-soft);
  color: var(--danger);
  font-size: 12px;
  font-weight: 600;
  border-radius: var(--r-md);
  border: 1px solid var(--danger);
}

.format-fieldset {
  border: none;
  padding: 0;
  margin: 0;
  min-width: 0;
}

.format-fieldset:disabled {
  opacity: 0.45;
  pointer-events: none;
}

/* ── Footer ───────────────────────────────────────────────────────── */
.slide-foot {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 24px;
  border-top: 1px solid var(--line-1);
  flex-shrink: 0;
}

.slide-foot-spacer { flex: 1; }

.slide-err {
  flex: 1;
  min-width: 0;
  font-size: 12px;
  color: var(--danger);
  line-height: 1.4;
}

/* Buttons */
.adm-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  border-radius: var(--r-md);
  border: 1px solid var(--line-2);
  background: var(--bg-3);
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-1);
  cursor: pointer;
  transition: background 150ms;
  font-family: inherit;
}

.adm-btn:hover { background: var(--bg-4); }

.adm-btn.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #000;
}

.adm-btn.primary:hover { opacity: 0.9; }
.adm-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Affiche ──────────────────────────────────────────────────────── */
.poster-current { display: flex; flex-direction: column; gap: 10px; align-items: flex-start; }
.poster-preview {
  width: 100%;
  max-width: 320px;
  border-radius: var(--r-md);
  border: 1px solid var(--line-2);
  display: block;
}
.poster-gallery {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 8px;
}
.poster-candidate { display: flex; flex-direction: column; gap: 8px; align-items: stretch; }
</style>
