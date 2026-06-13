<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useEventStore } from '@/stores/event'
import { extractApiError } from '@/lib/apiError'
import EditionModal from '@/components/modals/EditionModal.vue'
import EventModal from '@/components/modals/EventModal.vue'
import type { Edition, Event } from '@/types'

const router = useRouter()
const eventStore = useEventStore()

onMounted(async () => {
  await eventStore.fetchEditions()
})

const activeEdition = computed(() => eventStore.activeEdition)
const editions = computed(() => eventStore.editions)
const events = computed(() => eventStore.events)

// ── Configuration (Phase 9) ──────────────────────────────────────────────
const error = ref('')
const editionModal = ref<{ editing: Edition | null } | null>(null)
const eventModal = ref<{ editionId: number; editing: Event | null } | null>(null)

function fmtDate(iso: string | null): string {
  return iso ? iso.slice(0, 10) : '—'
}

function openEventCreate() {
  if (!activeEdition.value) return
  eventModal.value = { editionId: activeEdition.value.id, editing: null }
}

async function activate(e: Edition) {
  if (e.isActive) return
  error.value = ''
  try {
    await eventStore.activateEdition(e.id)
  } catch (err) {
    error.value = extractApiError(err)
  }
}

async function removeEdition(e: Edition) {
  if (!confirm(`Supprimer l'édition « ${e.name} » (${e.year}) ?`)) return
  error.value = ''
  try {
    await eventStore.deleteEdition(e.id)
  } catch (err) {
    error.value = extractApiError(err)
  }
}

async function removeEvent(ev: Event) {
  if (!confirm(`Supprimer l'épreuve « ${ev.name} » ? Cela efface inscriptions, poules et matchs liés.`)) return
  error.value = ''
  try {
    await eventStore.deleteEvent(ev.id)
  } catch (err) {
    error.value = extractApiError(err)
  }
}
</script>

<template>
  <div class="admin-page">
    <header class="page-header">
      <div>
        <p class="breadcrumb">Administration</p>
        <h1 class="page-title">Tournoi</h1>
        <p class="page-sub">Vue d'ensemble de l'édition active</p>
      </div>
      <button class="adm-btn primary" type="button" @click="editionModal = { editing: null }">
        + Nouvelle édition
      </button>
    </header>

    <div class="page-content">
      <p v-if="error" class="adm-page-error">{{ error }}</p>

      <!-- Edition active -->
      <section class="adm-card adm-edition-card">
        <div class="adm-card-head">
          <h3>
            <span v-if="activeEdition" class="edition-dot" />
            {{ activeEdition ? `Édition active · ${activeEdition.name} ${activeEdition.year}` : 'Édition active' }}
          </h3>
        </div>

        <!-- État vide -->
        <div v-if="!activeEdition" class="adm-empty adm-edition-empty">
          <p>Aucune édition active.</p>
          <p class="adm-edition-empty-hint">
            Créez une nouvelle édition ou activez-en une depuis l'historique ci-dessous.
          </p>
        </div>

        <!-- Contenu édition active -->
        <div v-else class="adm-edition-body">
          <!-- Période -->
          <div v-if="activeEdition.startDt || activeEdition.endDt" class="adm-edition-period">
            {{ fmtDate(activeEdition.startDt) }} → {{ fmtDate(activeEdition.endDt) }}
          </div>

          <!-- Stats édition (toutes épreuves confondues) -->
          <div class="adm-edition-stats">
            <div class="adm-stat">
              <span class="adm-stat-lbl">Joueurs inscrits</span>
              <span class="adm-stat-val tab">{{ activeEdition.distinctPlayersCount }}</span>
            </div>
            <div class="adm-stat">
              <span class="adm-stat-lbl">Épreuves</span>
              <span class="adm-stat-val tab">{{ activeEdition.eventsCount }}</span>
            </div>
            <div class="adm-stat">
              <span class="adm-stat-lbl">Matchs joués</span>
              <span class="adm-stat-val tab">
                {{ activeEdition.matchesFinished }}<em>/{{ activeEdition.matchesTotal }}</em>
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- Épreuves -->
      <section class="adm-card">
        <div class="adm-card-head">
          <h3>Épreuves de l'édition</h3>
          <button
            class="adm-btn primary"
            type="button"
            :disabled="!activeEdition"
            @click="openEventCreate()"
          >
            + Nouvelle épreuve
          </button>
        </div>

        <div v-if="events.length === 0" class="adm-empty">
          Aucune épreuve créée pour cette édition.
        </div>

        <div v-else class="adm-events">
          <article v-for="ev in events" :key="ev.id" class="adm-event">
            <div class="adm-event-head">
              <span class="adm-event-mode">{{ ev.categoryMode }}</span>
              <div class="adm-event-name">
                <h4>{{ ev.name }}</h4>
                <span>{{ ev.categoryMode === 'S' ? 'Simple' : 'Double' }}</span>
              </div>
              <span :class="['adm-event-state', ev.hasBracket ? 'state-final' : ev.hasGroups ? 'state-poules' : 'state-prep']">
                {{ ev.hasBracket ? 'Phase finale' : ev.hasGroups ? 'Poules' : 'À préparer' }}
              </span>
            </div>
            <div class="adm-event-meta">
              <span>Poules de {{ ev.groupSizeDefault }} · {{ ev.qualifiedPerGroup }} qualifié{{ ev.qualifiedPerGroup > 1 ? 's' : '' }}</span>
              <span>·</span>
              <span>{{ ev.entriesCount }} inscrit{{ ev.entriesCount !== 1 ? 's' : '' }}</span>
            </div>
            <div class="adm-event-acts">
              <button class="adm-btn" type="button" @click="eventStore.activeEventId = ev.id; router.push('/admin/inscriptions')">
                Inscriptions
              </button>
              <button class="adm-btn" type="button" @click="eventStore.activeEventId = ev.id; router.push('/admin/groups')">
                Poules
              </button>
              <button class="adm-btn" type="button" @click="eventStore.activeEventId = ev.id; router.push('/admin/matches')">
                Matchs
              </button>
              <span class="adm-event-spacer" />
              <button class="adm-btn" type="button" @click="eventModal = { editionId: ev.editionId, editing: ev }">
                Modifier
              </button>
              <button class="adm-btn danger" type="button" @click="removeEvent(ev)">
                Supprimer
              </button>
              <button
                class="adm-btn primary"
                type="button"
                :disabled="eventStore.activeEventId === ev.id"
                @click="eventStore.activeEventId = ev.id"
              >
                {{ eventStore.activeEventId === ev.id ? 'Sélectionnée ✓' : 'Sélectionner' }}
              </button>
            </div>
          </article>
        </div>
      </section>

      <!-- Historique éditions -->
      <section class="adm-card">
        <div class="adm-card-head">
          <h3>Historique des éditions</h3>
        </div>

        <div v-if="editions.length === 0" class="adm-empty">
          Aucune édition dans l'historique.
        </div>

        <table v-else class="adm-table">
          <thead>
            <tr>
              <th>Édition</th>
              <th>Année</th>
              <th>Dates</th>
              <th>Épreuves</th>
              <th>Statut</th>
              <th class="ta-r">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="e in editions" :key="e.id">
              <td>
                <div class="adm-player">
                  <div
                    class="adm-avatar"
                    :style="{ background: e.isActive ? 'var(--accent)' : 'var(--bg-4)', color: e.isActive ? '#000' : 'var(--ink-2)' }"
                  >
                    {{ String(e.year).slice(2) }}
                  </div>
                  <div>
                    <div class="adm-player-name">{{ e.name }}</div>
                    <div class="adm-player-meta">{{ e.isActive ? 'Édition active' : 'Archive' }}</div>
                  </div>
                </div>
              </td>
              <td class="tab">{{ e.year }}</td>
              <td class="tab adm-dates">{{ fmtDate(e.startDt) }} → {{ fmtDate(e.endDt) }}</td>
              <td class="tab">{{ e.eventsCount }}</td>
              <td>
                <span :class="['adm-pill', e.isActive ? '' : 'adm-pill-ghost']">
                  {{ e.isActive ? 'En cours' : 'Terminée' }}
                </span>
              </td>
              <td class="ta-r">
                <button
                  class="adm-btn"
                  type="button"
                  :disabled="e.isActive"
                  @click="activate(e)"
                >
                  {{ e.isActive ? 'Active ✓' : 'Activer' }}
                </button>
                <button class="adm-btn" type="button" @click="editionModal = { editing: e }">Modifier</button>
                <button class="adm-btn danger" type="button" @click="removeEdition(e)">Supprimer</button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>

    <!-- Modales (Phase 9) -->
    <EditionModal
      v-if="editionModal"
      :editing="editionModal.editing"
      @close="editionModal = null"
      @saved="error = ''"
    />
    <EventModal
      v-if="eventModal"
      :edition-id="eventModal.editionId"
      :editing="eventModal.editing"
      @close="eventModal = null"
      @saved="error = ''"
    />
  </div>
</template>

<style scoped>
.admin-page { padding: 0; }

.page-header {
  padding: 32px 40px 24px;
  border-bottom: 1px solid var(--line-1);
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.breadcrumb { margin: 0 0 4px; font-size: 12px; color: var(--ink-3); letter-spacing: 0.06em; }
.page-title { margin: 0 0 4px; font-size: 26px; font-weight: 700; color: var(--ink-0); }
.page-sub { margin: 0; font-size: 13px; color: var(--ink-2); }

.page-content {
  padding: 24px 40px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ── Cards ─────────────────────────────────────────────────────────── */
.adm-card {
  background: var(--bg-2);
  border: 1px solid var(--line-1);
  border-radius: var(--r-lg);
  overflow: hidden;
}

.adm-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--line-1);
}

.adm-card-head h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--ink-0);
  display: flex;
  align-items: center;
  gap: 10px;
}

.edition-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  display: inline-block;
  flex-shrink: 0;
  animation: pulse 2s ease-in-out infinite;
}

/* ── Edition stats ─────────────────────────────────────────────────── */
.adm-edition-body {
  display: flex;
  flex-direction: column;
}

.adm-edition-period {
  padding: 10px 20px;
  font-size: 13px;
  color: var(--ink-2);
  border-bottom: 1px solid var(--line-1);
}

.adm-edition-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
}

.adm-stat {
  padding: 24px 20px;
  border-bottom: 1px solid var(--line-1);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.adm-stat:not(:last-child) { border-right: 1px solid var(--line-1); }

.adm-stat-lbl {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--ink-3);
  text-transform: uppercase;
}

.adm-stat-val {
  font-size: 32px;
  font-weight: 800;
  color: var(--ink-0);
  line-height: 1;
}

.adm-stat-val em {
  font-style: normal;
  font-size: 18px;
  color: var(--ink-3);
}

/* ── Events list ───────────────────────────────────────────────────── */
.adm-events {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.adm-event {
  padding: 16px 20px;
  border-bottom: 1px solid var(--line-1);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.adm-event:last-child { border-bottom: none; }

.adm-event-head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.adm-event-mode {
  width: 32px;
  height: 32px;
  border-radius: var(--r-sm);
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.adm-event-name h4 {
  margin: 0 0 2px;
  font-size: 15px;
  font-weight: 700;
  color: var(--ink-0);
}

.adm-event-name span { font-size: 12px; color: var(--ink-3); }

.adm-event-state {
  margin-left: auto;
  padding: 3px 10px;
  border-radius: var(--r-xs);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

.state-prep  { background: var(--bg-4); color: var(--ink-2); }
.state-poules { background: var(--accent-soft); color: var(--accent); }
.state-final { background: var(--accent); color: #000; }

.adm-event-meta {
  display: flex;
  gap: 6px;
  font-size: 12px;
  color: var(--ink-3);
}

.adm-event-acts {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* ── Table ─────────────────────────────────────────────────────────── */
.adm-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.adm-table th {
  padding: 10px 20px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.1em;
  color: var(--ink-3);
  text-transform: uppercase;
  border-bottom: 1px solid var(--line-1);
  background: var(--bg-3);
}

.adm-table td {
  padding: 14px 20px;
  border-bottom: 1px solid var(--line-1);
  color: var(--ink-1);
  vertical-align: middle;
}

.adm-table tr:last-child td { border-bottom: none; }

/* Player row */
.adm-player {
  display: flex;
  align-items: center;
  gap: 12px;
}

.adm-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.adm-player-name { font-size: 14px; font-weight: 600; color: var(--ink-0); }
.adm-player-meta { font-size: 12px; color: var(--ink-3); }

/* Pills */
.adm-pill {
  display: inline-block;
  padding: 3px 10px;
  border-radius: var(--r-xs);
  font-size: 12px;
  font-weight: 600;
  background: var(--accent);
  color: #000;
}

.adm-pill-ghost {
  background: var(--bg-4);
  color: var(--ink-2);
  border: 1px solid var(--line-2);
}

/* Empty state */
.adm-empty {
  padding: 40px;
  text-align: center;
  color: var(--ink-3);
  font-size: 14px;
}

.adm-edition-empty p { margin: 0 0 6px; }
.adm-edition-empty-hint { font-size: 12px; color: var(--ink-3); }

/* ── Buttons ───────────────────────────────────────────────────────── */
.adm-btn {
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
.adm-btn.danger { color: var(--danger); }
.adm-btn.danger:hover { background: var(--danger); border-color: var(--danger); color: #fff; }
.adm-table td .adm-btn + .adm-btn { margin-left: 8px; }

.adm-event-spacer { flex: 1; }

/* Page-level error */
.adm-page-error { margin: 0; font-size: 13px; color: var(--danger); }

/* Table helpers */
.ta-r { text-align: right; }
.adm-dates { color: var(--ink-2); }

/* Tab monospace */
.tab { font-family: var(--font-mono); }
</style>
