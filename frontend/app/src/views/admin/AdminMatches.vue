<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useEventStore } from '@/stores/event'
import EditMatchPanel from '@/components/modals/EditMatchPanel.vue'
import type { Match } from '@/types'

const eventStore = useEventStore()
const editingMatch = ref<Match | null>(null)

watch(() => eventStore.activeEventId, (id) => {
  if (id) eventStore.fetchMatches(id)
}, { immediate: true })

const backlog = computed<Match[]>(() => eventStore.kanban?.backlog ?? [])
const queue = computed<Match[]>(() => eventStore.kanban?.queue ?? [])
const finished = computed<Match[]>(() => eventStore.kanban?.finished ?? [])

async function feature(match: Match) {
  if (!eventStore.activeEventId) return
  await eventStore.featureMatch(eventStore.activeEventId, match.id)
}

function playerLabel(match: Match, side: 'A' | 'B'): string {
  if (side === 'A') return match.sideA?.player?.fullName ?? match.sideALabel ?? 'TBD'
  return match.sideB?.player?.fullName ?? match.sideBLabel ?? 'TBD'
}

function stageTag(match: Match): string {
  const labels: Record<string, string> = {
    GROUP: `POULE ${match.sideALabel?.[0] ?? ''}`,
    QF: 'QUART',
    SF: 'DEMI',
    F: 'FINALE',
  }
  return labels[match.stage] ?? match.stage
}
</script>

<template>
  <div class="admin-page">
    <header class="page-header">
      <div>
        <p class="breadcrumb">Tournoi · {{ eventStore.events.find((ev) => ev.id === eventStore.activeEventId)?.name }}</p>
        <h1 class="page-title">Matchs</h1>
      </div>
    </header>

    <EditMatchPanel
      v-if="editingMatch"
      :match="editingMatch"
      @close="editingMatch = null"
      @saved="editingMatch = null"
    />

    <div class="page-content">
      <div class="kanban">
        <!-- Backlog -->
        <div class="kanban-col">
          <div class="col-header">
            <span class="col-dot" style="background: var(--ink-3)" />
            <span class="col-name">Backlog</span>
            <span class="col-count">{{ backlog.length }}</span>
          </div>
          <div class="col-body">
            <div
              v-for="match in backlog"
              :key="match.id"
              class="match-card"
              style="cursor: pointer"
              @click="editingMatch = match"
            >
              <div class="mc-tag">{{ stageTag(match) }}</div>
              <div class="mc-players">
                {{ playerLabel(match, 'A') }} <span class="vs">vs</span> {{ playerLabel(match, 'B') }}
              </div>
            </div>
            <div v-if="backlog.length === 0" class="col-empty">—</div>
          </div>
        </div>

        <!-- File d'attente -->
        <div class="kanban-col">
          <div class="col-header">
            <span class="col-dot" style="background: var(--accent)" />
            <span class="col-name">File d'attente</span>
            <span class="col-count">{{ queue.length }}</span>
          </div>
          <div class="col-body">
            <div
              v-for="match in queue"
              :key="match.id"
              class="match-card"
              :class="{ featured: match.isFeatured }"
              style="cursor: pointer"
              @click="editingMatch = match"
            >
              <span v-if="match.isFeatured" class="featured-badge">EN AVANT</span>
              <div class="mc-tag">{{ stageTag(match) }}</div>
              <div class="mc-players">
                {{ playerLabel(match, 'A') }} <span class="vs">vs</span> {{ playerLabel(match, 'B') }}
              </div>
              <div class="mc-meta">
                <span v-if="match.court">{{ match.court }}</span>
                <span v-if="match.scheduledTime">{{ match.scheduledTime }}</span>
              </div>
              <div class="mc-footer">
                <button
                  v-if="!match.isFeatured"
                  class="mc-btn mc-btn--star"
                  @click.stop="feature(match)"
                >
                  ★ Mettre en avant
                </button>
              </div>
            </div>
            <div v-if="queue.length === 0" class="col-empty">—</div>
          </div>
        </div>

        <!-- Terminés -->
        <div class="kanban-col">
          <div class="col-header">
            <span class="col-dot" style="background: var(--success)" />
            <span class="col-name">Terminés</span>
            <span class="col-count">{{ finished.length }}</span>
          </div>
          <div class="col-body">
            <div
              v-for="match in finished"
              :key="match.id"
              class="match-card match-card--finished"
              style="cursor: pointer"
              @click="editingMatch = match"
            >
              <div class="mc-tag">{{ stageTag(match) }}</div>
              <div class="mc-players">
                {{ playerLabel(match, 'A') }} <span class="vs">vs</span> {{ playerLabel(match, 'B') }}
              </div>
              <div class="mc-meta">
                <span v-if="match.setScores.length > 0">
                  Score : {{ match.setScores.map((s) => `${s.a}-${s.b}`).join(' ') }}
                </span>
              </div>
            </div>
            <div v-if="finished.length === 0" class="col-empty">—</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-page { padding: 0; }

.page-header {
  padding: 32px 40px 24px;
  border-bottom: 1px solid var(--line-1);
}

.breadcrumb { margin: 0 0 4px; font-size: 12px; color: var(--ink-3); letter-spacing: 0.06em; }
.page-title { margin: 0 0 4px; font-size: 26px; font-weight: 700; color: var(--ink-0); }

.page-content {
  padding: 24px 40px;
  height: calc(100vh - 120px);
  overflow: hidden;
}

/* ── Kanban ──────────────────────────────────────────────────────────── */
.kanban {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 20px;
  height: 100%;
}

.kanban-col {
  display: flex;
  flex-direction: column;
  gap: 0;
  background: var(--bg-3);
  border-radius: var(--r-lg);
  overflow: hidden;
}

.col-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--line-1);
  flex-shrink: 0;
}

.col-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.col-name {
  flex: 1;
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-0);
}

.col-count {
  font-size: 12px;
  font-weight: 700;
  color: var(--ink-3);
  background: var(--bg-4);
  padding: 2px 8px;
  border-radius: 99px;
}

.col-body {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.col-empty {
  text-align: center;
  color: var(--ink-4);
  font-size: 13px;
  padding: 24px;
}

/* ── Match card ──────────────────────────────────────────────────────── */
.match-card {
  position: relative;
  background: var(--bg-2);
  border: 1px solid var(--line-1);
  border-radius: var(--r-md);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.match-card.featured {
  border-color: var(--accent-soft);
  box-shadow: 0 0 0 1px var(--accent-soft);
}

.match-card--finished {
  opacity: 0.7;
}

.featured-badge {
  position: absolute;
  top: -10px;
  left: 12px;
  background: var(--accent);
  color: #000;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.1em;
  padding: 2px 8px;
  border-radius: 99px;
}

.mc-tag {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.14em;
  color: var(--ink-3);
  text-transform: uppercase;
}

.mc-players {
  font-size: 15px;
  font-weight: 600;
  color: var(--ink-0);
}

.vs {
  font-size: 11px;
  font-weight: 400;
  color: var(--ink-3);
  margin: 0 4px;
}

.mc-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--ink-2);
  border-top: 1px dashed var(--line-1);
  padding-top: 6px;
}

.mc-footer {
  display: flex;
  gap: 8px;
}

.mc-btn {
  background: none;
  border: 1px solid var(--line-2);
  border-radius: var(--r-sm);
  padding: 5px 10px;
  font-size: 12px;
  color: var(--ink-2);
  cursor: pointer;
  transition: background 150ms;
}

.mc-btn:hover { background: var(--bg-4); }

.mc-btn--star { color: var(--accent); border-color: var(--accent-soft); }
</style>
