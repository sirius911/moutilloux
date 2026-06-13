<script setup lang="ts">
import { ref, computed } from 'vue'
import { useEventStore } from '@/stores/event'
import Segmented from '@/components/ui/Segmented.vue'
import type { Match } from '@/types'

const props = defineProps<{ match: Match }>()
const emit = defineEmits<{ close: []; saved: [] }>()

const eventStore = useEventStore()

const tab = ref<'score' | 'format' | 'planning' | 'history'>('score')
const saving = ref(false)
const error = ref('')

// Score tab
const setsA = ref(props.match.setsA)
const setsB = ref(props.match.setsB)
const gamesA = ref(props.match.gamesA)
const gamesB = ref(props.match.gamesB)
const pointsA = ref(props.match.displayPointA)
const pointsB = ref(props.match.displayPointB)
const tbActive = ref(props.match.tbActive)
const winnerSide = ref<'none' | 'A' | 'B' | 'abandon'>(props.match.winnerSide ?? 'none')

// Format tab
const formatSets = ref(1)
const formatGames = ref('5')
const formatTb = ref('4')
const formatTbPoints = ref('7')
const formatServer = ref<'A' | 'B' | 'rand'>(props.match.server ?? 'A')

// Planning tab
const court = ref(props.match.court ?? '')
const scheduledTime = ref(props.match.scheduledTime ?? '')
const status = ref<'scheduled' | 'live' | 'finished' | 'canceled'>(
  props.match.status === 'LIVE' ? 'live'
    : props.match.status === 'FINISHED' ? 'finished'
    : props.match.status === 'CANCELED' ? 'canceled'
    : 'scheduled'
)
const featured = ref(props.match.isFeatured)

const nameA = computed(() =>
  props.match.sideA?.player?.fullName ?? props.match.sideALabel ?? 'Joueur A'
)
const nameB = computed(() =>
  props.match.sideB?.player?.fullName ?? props.match.sideBLabel ?? 'Joueur B'
)

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
  { id: 'history' as const, label: 'Historique' },
]

const winnerOptions = computed(() => [
  { value: 'none', label: 'À déterminer' },
  { value: 'A', label: nameA.value },
  { value: 'B', label: nameB.value },
  { value: 'abandon', label: 'Abandon' },
])

const formatSetsOptions = [
  { value: 1, label: '1 set' },
  { value: 2, label: 'Best of 3' },
  { value: 3, label: 'Best of 5' },
]

const serverOptions = computed(() => [
  { value: 'A', label: nameA.value },
  { value: 'B', label: nameB.value },
  { value: 'rand', label: 'Tirage au sort' },
])

const planningStatusOptions = [
  { value: 'scheduled', label: 'Prévu' },
  { value: 'live', label: 'En direct' },
  { value: 'finished', label: 'Terminé' },
  { value: 'canceled', label: 'Annulé' },
]

async function save() {
  const eventId = eventStore.activeEventId
  if (!eventId) return
  saving.value = true
  error.value = ''
  try {
    // Édition via MatchEditForm. On omet les points bruts (les displayPoint
    // sont des chaînes d'affichage non mappables sur 0-4) et les champs de
    // format (onglet décoratif) pour ne pas écraser les règles côté serveur.
    await eventStore.editMatch(eventId, props.match.id, {
      status: status.value.toUpperCase(),
      scheduled_time: scheduledTime.value || null,
      court: court.value || null,
      sets_a: setsA.value,
      sets_b: setsB.value,
      games_a: gamesA.value,
      games_b: gamesB.value,
      tb_active: tbActive.value,
      winner_side:
        winnerSide.value === 'A' || winnerSide.value === 'B' ? winnerSide.value : null,
    })
    // Mise en avant : seul l'enclenchement est exposé (feature_match → LIVE) ;
    // il n'existe pas de service de retrait, donc on ne déclenche qu'à l'activation.
    if (featured.value && !props.match.isFeatured) {
      await eventStore.featureMatch(eventId, props.match.id)
    }
    emit('saved')
    emit('close')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Erreur inconnue.'
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
                  <input v-model="pointsA" class="inp inp-num tab" />
                </div>
                <div class="score-grid-row">
                  <span class="score-grid-name">
                    <i class="srv srv-off" />
                    {{ nameB }}
                    <em v-if="match.sideB?.seedHint" class="seed-tag">{{ match.sideB.seedHint }}</em>
                  </span>
                  <input v-model.number="setsB" class="inp inp-num tab" type="number" min="0" />
                  <input v-model.number="gamesB" class="inp inp-num tab" type="number" min="0" />
                  <input v-model="pointsB" class="inp inp-num tab" />
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
            <div class="slide-section">
              <h4>Format du match</h4>
              <div class="fld-col">
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
              </div>
            </div>
          </template>

          <!-- Planning -->
          <template v-if="tab === 'planning'">
            <div class="slide-section">
              <h4>Planning</h4>
              <div class="fld-col">
                <div class="fld-row">
                  <label class="fld">
                    <span class="fld-lbl">Court</span>
                    <input v-model="court" class="inp" placeholder="ex. Court Central" />
                  </label>
                  <label class="fld">
                    <span class="fld-lbl">Heure prévue</span>
                    <input v-model="scheduledTime" class="inp tab" type="time" />
                  </label>
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

          <!-- Historique -->
          <template v-if="tab === 'history'">
            <div class="slide-section">
              <h4>Activité</h4>
              <div class="log">
                <div class="log-row log-empty">
                  <span>Historique non disponible pour ce match.</span>
                </div>
              </div>
            </div>
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

/* History log */
.log {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  overflow: hidden;
}

.log-row {
  display: grid;
  grid-template-columns: 90px 160px 1fr;
  gap: 8px;
  padding: 10px 14px;
  font-size: 13px;
  border-bottom: 1px solid var(--line-1);
  align-items: center;
}

.log-row:last-child { border-bottom: none; }

.log-empty {
  grid-template-columns: 1fr;
  color: var(--ink-3);
  text-align: center;
  padding: 20px;
}

.log-time { font-family: var(--font-mono); font-size: 12px; color: var(--ink-3); }
.log-who { font-size: 12px; color: var(--ink-2); font-weight: 500; }
.log-what { color: var(--ink-0); }

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
</style>
