<script setup lang="ts">
import { ref, computed } from 'vue'
import ModalShell from '@/components/ui/ModalShell.vue'
import { useEventStore } from '@/stores/event'

const emit = defineEmits<{ close: []; saved: [] }>()

const eventStore = useEventStore()

const saving = ref(false)
const error = ref('')

const rows = computed(() =>
  eventStore.groups.map((g) => {
    const n = g.standings.length
    const matchCount = (n * (n - 1)) / 2
    return { id: g.name, n, matchCount }
  })
)

const totalPlayers = computed(() => rows.value.reduce((s, r) => s + r.n, 0))
const totalMatches = computed(() => rows.value.reduce((s, r) => s + r.matchCount, 0))

async function generate() {
  if (!eventStore.activeEventId) return
  saving.value = true
  error.value = ''
  try {
    await eventStore.generateMatches(eventStore.activeEventId)
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
  <ModalShell
    title="Générer les matchs de poule"
    subtitle="Round-robin complet pour chaque poule · format par défaut (5 jeux, TB à 4)."
    size="md"
    @close="emit('close')"
  >
    <template #icon>
      <svg viewBox="0 0 24 24" width="20" height="20">
        <rect x="3" y="4" width="5" height="16" rx="1" fill="none" stroke="currentColor" stroke-width="1.6"/>
        <rect x="10" y="4" width="5" height="16" rx="1" fill="none" stroke="currentColor" stroke-width="1.6"/>
        <rect x="17" y="4" width="4" height="16" rx="1" fill="none" stroke="currentColor" stroke-width="1.6"/>
      </svg>
    </template>

    <!-- Répartition -->
    <div class="mdl-section">
      <h4>Répartition à générer</h4>
      <div v-if="rows.length > 0" class="gen-table">
        <div class="gen-row gen-row-head">
          <span>Poule</span>
          <span>Joueurs</span>
          <span>Matchs</span>
          <span>Estimation</span>
        </div>
        <div v-for="r in rows" :key="r.id" class="gen-row">
          <span>
            <span class="poule-letter">{{ r.id }}</span>
            Poule {{ r.id }}
          </span>
          <span class="tab">{{ r.n }}</span>
          <span class="tab">{{ r.matchCount }}</span>
          <span class="adm-mono">~{{ r.matchCount * 45 }} min</span>
        </div>
        <div class="gen-row gen-row-total">
          <span><b>Total</b></span>
          <span class="tab"><b>{{ totalPlayers }}</b></span>
          <span class="tab"><b>{{ totalMatches }}</b></span>
          <span class="adm-mono"><b>~{{ Math.round((totalMatches * 45) / 60) }} h</b></span>
        </div>
      </div>
      <p v-else class="empty-note">Aucune poule configurée. Créez d'abord les poules.</p>
      <p v-if="error" class="mdl-error">{{ error }}</p>
    </div>

    <template #footer>
      <button class="adm-btn" type="button" @click="emit('close')">Annuler</button>
      <button
        class="adm-btn primary"
        type="button"
        :disabled="rows.length === 0 || saving"
        @click="generate"
      >
        {{ saving ? 'Génération…' : `Générer ${totalMatches} matchs` }}
      </button>
    </template>
  </ModalShell>
</template>

<style scoped>
.mdl-section h4 {
  margin: 0 0 14px;
  font-size: 13px;
  font-weight: 700;
  color: var(--ink-2);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.mdl-error {
  margin: 12px 0 0;
  font-size: 13px;
  color: var(--danger);
}

/* Table de répartition */
.gen-table {
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  overflow: hidden;
}

.gen-row {
  display: grid;
  grid-template-columns: 1fr 80px 80px 100px;
  align-items: center;
  padding: 10px 16px;
  font-size: 13px;
  gap: 8px;
  border-bottom: 1px solid var(--line-1);
}

.gen-row:last-child { border-bottom: none; }

.gen-row-head {
  background: var(--bg-3);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--ink-3);
  text-transform: uppercase;
}

.gen-row-total {
  background: var(--bg-3);
  font-weight: 700;
}

.gen-row .tab {
  font-family: var(--font-mono);
  font-size: 14px;
}

.poule-letter {
  display: inline-flex;
  width: 22px;
  height: 22px;
  border-radius: var(--r-xs);
  background: var(--accent);
  color: #000;
  font-size: 11px;
  font-weight: 800;
  align-items: center;
  justify-content: center;
  margin-right: 6px;
}

.adm-mono { font-family: var(--font-mono); font-size: 13px; color: var(--ink-2); }

.empty-note {
  text-align: center;
  color: var(--ink-3);
  font-size: 13px;
  padding: 20px 0;
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
