<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useEventStore } from '@/stores/event'
import { usePolling } from '@/composables/usePolling'

const eventStore = useEventStore()
usePolling(async () => {
  await eventStore.fetchEditions()
  if (eventStore.activeEventId) {
    await eventStore.fetchGroups(eventStore.activeEventId)
  }
}, 5000)

// Rotation entre les groupes (mise en avant visuelle)
const activeGroupIdx = ref(0)
let rotationTimer: ReturnType<typeof setInterval> | null = null

const groups = computed(() => eventStore.groups)

onMounted(() => {
  rotationTimer = setInterval(() => {
    if (groups.value.length > 0) {
      activeGroupIdx.value = (activeGroupIdx.value + 1) % groups.value.length
    }
  }, 4000)
})

onUnmounted(() => {
  if (rotationTimer) clearInterval(rotationTimer)
})

function now(): string {
  return new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
</script>

<template>
  <div class="poules-screen">
    <!-- Header -->
    <header class="poules-header">
      <div class="ph-logo">
        <span class="logo-badge">M</span>
        <div>
          <span class="logo-title">PHASE DE POULES</span>
          <span class="logo-sub">{{ eventStore.events[0]?.name }} · {{ groups.length }} groupes</span>
        </div>
      </div>
      <!-- Indicateur de rotation -->
      <div class="rotation-indicator">
        <div
          v-for="(g, i) in groups"
          :key="g.id"
          class="rot-bar"
          :class="{ active: i === activeGroupIdx }"
        />
      </div>
    </header>

    <!-- Grille 2×2 des groupes -->
    <div class="poules-grid">
      <div
        v-for="(group, idx) in groups"
        :key="group.id"
        class="group-card"
        :class="{ 'group-card--active': idx === activeGroupIdx }"
      >
        <!-- En-tête de groupe -->
        <div class="gc-header">
          <span class="gc-letter">{{ group.name }}</span>
          <span class="gc-title">Poule {{ group.name }}</span>
        </div>

        <div class="gc-body">
          <!-- Standings -->
          <table class="standings-table">
            <thead>
              <tr>
                <th class="col-rank">#</th>
                <th class="col-player">Joueur</th>
                <th>V</th>
                <th>D</th>
                <th>Jeux</th>
                <th>Pts</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in group.standings"
                :key="row.entryId"
                :class="{ qualified: row.qualified }"
              >
                <td class="col-rank tab">{{ row.rank }}</td>
                <td class="col-player">
                  <span class="player-name">{{ row.name }}</span>
                  <span v-if="row.qualified" class="q-badge">Q</span>
                </td>
                <td class="tab">{{ row.wins }}</td>
                <td class="tab">{{ row.losses }}</td>
                <td class="tab mono">{{ row.gamesRatio }}</td>
                <td class="tab">{{ row.points }}</td>
              </tr>
            </tbody>
          </table>

          <!-- Grille croisée -->
          <div class="cross-grid">
            <div
              v-for="(rowCells, ri) in group.grid"
              :key="ri"
              class="cg-row"
            >
              <div
                v-for="(cell, ci) in rowCells"
                :key="ci"
                class="cg-cell"
                :class="{ diagonal: ri === ci }"
              >
                {{ cell.score ?? '—' }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="poules-footer">
      <span class="legend">Q · Qualifié pour le tableau final</span>
      <span class="updated">Mis à jour {{ now() }}</span>
    </footer>
  </div>
</template>

<style scoped>
.poules-screen {
  width: 1920px;
  height: 1080px;
  background: var(--bg-1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── Header ─────────────────────────────────────────────────────────── */
.poules-header {
  height: 96px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 56px;
  border-bottom: 1px solid var(--line-1);
  flex-shrink: 0;
}

.ph-logo {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-badge {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--accent);
  color: #000;
  font-size: 20px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-title {
  display: block;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.20em;
  color: var(--ink-0);
  text-transform: uppercase;
}

.logo-sub {
  display: block;
  font-size: 12px;
  color: var(--ink-2);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.rotation-indicator {
  display: flex;
  gap: 8px;
  align-items: center;
}

.rot-bar {
  width: 48px;
  height: 4px;
  border-radius: 2px;
  background: var(--line-3);
  transition: background 400ms ease;
}

.rot-bar.active {
  background: var(--accent);
}

/* ── Grid ────────────────────────────────────────────────────────────── */
.poules-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 24px;
  padding: 24px 56px;
}

/* ── Group card ──────────────────────────────────────────────────────── */
.group-card {
  background: var(--bg-2);
  border: 1px solid var(--line-1);
  border-radius: var(--r-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: box-shadow 400ms ease, border-color 400ms ease;
}

.group-card--active {
  border-color: var(--accent-soft);
  box-shadow: 0 0 0 1px var(--accent-soft), 0 0 40px rgba(255, 200, 61, 0.08);
}

.gc-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 24px;
  border-bottom: 1px solid var(--line-1);
}

.gc-letter {
  font-size: 64px;
  font-weight: 800;
  color: var(--accent);
  line-height: 1;
}

.gc-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--ink-1);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.gc-body {
  flex: 1;
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 0;
  overflow: hidden;
}

/* ── Standings ───────────────────────────────────────────────────────── */
.standings-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 15px;
  padding: 12px 16px;
  align-self: start;
}

.standings-table th {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.16em;
  color: var(--ink-3);
  text-transform: uppercase;
  padding: 8px 6px;
  text-align: center;
}

.standings-table th.col-player { text-align: left; }

.standings-table td {
  padding: 10px 6px;
  color: var(--ink-1);
  text-align: center;
  border-bottom: 1px solid var(--line-1);
}

.col-rank {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--ink-3);
  width: 32px;
}

.col-player { text-align: left !important; }

.standings-table tr.qualified td {
  background: linear-gradient(90deg, var(--accent-soft), transparent);
}

.standings-table tr.qualified .player-name {
  font-weight: 700;
  color: var(--ink-0);
}

.mono { font-family: var(--font-mono); }

.player-name { margin-right: 8px; }

.q-badge {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  background: var(--accent);
  color: #000;
  padding: 2px 6px;
  border-radius: var(--r-xs);
}

/* ── Grille croisée ──────────────────────────────────────────────────── */
.cross-grid {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px;
  gap: 4px;
}

.cg-row {
  display: flex;
  gap: 4px;
}

.cg-cell {
  width: 56px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: var(--ink-1);
  border-radius: var(--r-xs);
  background: var(--bg-3);
  font-family: var(--font-mono);
}

.cg-cell.diagonal {
  background: transparent;
  color: var(--ink-4);
}

/* ── Footer ──────────────────────────────────────────────────────────── */
.poules-footer {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 56px;
  border-top: 1px solid var(--line-1);
  flex-shrink: 0;
  font-size: 11px;
  color: var(--ink-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
</style>
