<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useEventStore } from '@/stores/event'
import { useAuthStore } from '@/stores/auth'

const eventStore = useEventStore()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}

onMounted(() => {
  eventStore.fetchEditions()
  eventStore.fetchAllPlayers()
})

const navItems = computed(() => {
  const kanban = eventStore.kanban
  const bracket = eventStore.bracket
  const matchCount = kanban === null
    ? null
    : kanban.backlog.length + kanban.queue.length + kanban.finished.length
  const bracketCount = bracket === null
    ? null
    : bracket.qf.length + bracket.sf.length + bracket.f.length

  return [
    { path: '/admin/tournoi',      label: 'Tournoi',       icon: '🏛', count: eventStore.events.length },
    { path: '/admin/players',      label: 'Joueurs',       icon: '👤', count: eventStore.allPlayers.length },
    { path: '/admin/inscriptions', label: 'Inscriptions',  icon: '📝', count: eventStore.players.length },
    { path: '/admin/groups',       label: 'Poules',        icon: '⊞',  count: eventStore.groups.length },
    { path: '/admin/matches',      label: 'Matchs',        icon: '⚡', count: matchCount },
    { path: '/admin/bracket',      label: 'Tableau final', icon: '🏆', count: bracketCount },
  ]
})
</script>

<template>
  <div class="admin-shell light-scope">
    <!-- Sidebar -->
    <aside class="admin-sidebar">
      <!-- Logo -->
      <div class="sb-logo">
        <div class="sb-logo-badge">M</div>
        <div class="sb-logo-text">
          <span class="sb-logo-name">MOUTILLOUX</span>
          <span class="sb-logo-sub">Open · Édition {{ eventStore.activeEdition?.year }}</span>
        </div>
      </div>

      <!-- Événement actif -->
      <div class="sb-event-selector">
        <span class="sb-event-label">ÉPREUVE</span>
        <select
          v-model="eventStore.activeEventId"
          class="sb-event-select"
          :disabled="eventStore.events.length === 0"
        >
          <option v-if="eventStore.events.length === 0" :value="null" disabled>
            Aucune épreuve
          </option>
          <option v-for="e in eventStore.events" :key="e.id" :value="e.id">
            {{ e.name }}
          </option>
        </select>
      </div>

      <!-- Navigation -->
      <nav class="sb-nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="sb-nav-item"
          :class="{ active: route.path.startsWith(item.path) }"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
          <span v-if="item.count !== null" class="nav-badge">{{ item.count }}</span>
        </RouterLink>
      </nav>

      <!-- Bas de sidebar -->
      <div class="sb-bottom">
        <a href="/tv/live" target="_blank" class="sb-link">Voir les résultats ↗</a>
        <button class="sb-link sb-link--danger" type="button" @click="handleLogout">Déconnexion</button>
      </div>
    </aside>

    <!-- Contenu principal -->
    <main class="admin-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.admin-shell {
  display: flex;
  min-height: 100vh;
  background: var(--bg-1);
}

/* ── Sidebar ─────────────────────────────────────────────────────────── */
.admin-sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-2);
  border-right: 1px solid var(--line-1);
  padding: 24px 0;
}

.sb-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 20px 24px;
  border-bottom: 1px solid var(--line-1);
}

.sb-logo-badge {
  width: 36px;
  height: 36px;
  border-radius: var(--r-sm);
  background: var(--accent);
  color: #000;
  font-size: 18px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sb-logo-name {
  display: block;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--ink-0);
}

.sb-logo-sub {
  display: block;
  font-size: 11px;
  color: var(--ink-3);
}

/* Sélecteur d'épreuve */
.sb-event-selector {
  padding: 16px 20px;
  border-bottom: 1px solid var(--line-1);
}

.sb-event-label {
  display: block;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: var(--ink-3);
  text-transform: uppercase;
  margin-bottom: 6px;
}

.sb-event-select {
  width: 100%;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: var(--r-sm);
  padding: 8px 10px;
  font-size: 13px;
  font-weight: 500;
  color: var(--ink-0);
  cursor: pointer;
}

.sb-event-select:disabled {
  opacity: 0.5;
  cursor: default;
}

/* Nav */
.sb-nav {
  flex: 1;
  padding: 12px 12px 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sb-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--r-md);
  font-size: 14px;
  font-weight: 500;
  color: var(--ink-1);
  text-decoration: none;
  transition: background 150ms;
}

.sb-nav-item:hover {
  background: var(--bg-3);
}

.sb-nav-item.active {
  background: var(--accent);
  color: #000;
  font-weight: 600;
}

.nav-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.nav-badge {
  margin-left: auto;
  font-size: 11px;
  font-weight: 600;
  background: var(--bg-3);
  border-radius: 10px;
  padding: 1px 6px;
  color: var(--ink-2);
  min-width: 20px;
  text-align: center;
}

.sb-nav-item.active .nav-badge {
  background: rgba(0, 0, 0, 0.12);
  color: #000;
}

/* Bas */
.sb-bottom {
  padding: 16px 20px 0;
  border-top: 1px solid var(--line-1);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sb-link {
  font-size: 13px;
  color: var(--ink-2);
  text-decoration: none;
  padding: 8px 0;
  display: block;
  transition: color 150ms;
}

.sb-link:hover { color: var(--ink-0); }
.sb-link--danger { color: var(--danger); }
.sb-link--danger:hover { color: var(--danger); opacity: 0.8; }

/* ── Main ────────────────────────────────────────────────────────────── */
.admin-main {
  flex: 1;
  overflow-y: auto;
  min-width: 0;
}
</style>
