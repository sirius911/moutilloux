<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import ModalShell from '@/components/ui/ModalShell.vue'
import { useEventStore } from '@/stores/event'
import { useApi } from '@/composables/useApi'
import { extractApiError } from '@/lib/apiError'
import type { Event } from '@/types'

const props = defineProps<{ event: Event }>()
const emit = defineEmits<{ close: []; started: [] }>()

const eventStore = useEventStore()
const { get } = useApi()

interface GroupRow { name: string; playerCount: number; matchCount: number }

const groups = ref<GroupRow[]>([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    const data = await get<{ locked: boolean; groups: { name: string; standings: unknown[] }[] }>(
      `/api/events/${props.event.id}/groups/`
    )
    groups.value = data.groups.map(g => {
      const n = g.standings.length
      return { name: g.name, playerCount: n, matchCount: Math.floor(n * (n - 1) / 2) }
    })
  } catch (e) {
    error.value = extractApiError(e)
  } finally {
    loading.value = false
  }
})

const totalPlaced = computed(() => groups.value.reduce((s, g) => s + g.playerCount, 0))
const unplacedCount = computed(() => props.event.entriesCount - totalPlaced.value)
const totalMatches = computed(() => groups.value.reduce((s, g) => s + g.matchCount, 0))
const playableGroups = computed(() => groups.value.filter(g => g.playerCount >= 2))
const canStart = computed(() => playableGroups.value.length > 0)

async function confirm() {
  saving.value = true
  error.value = ''
  try {
    await eventStore.startEvent(props.event.id)
    emit('started')
    emit('close')
  } catch (e) {
    error.value = extractApiError(e)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <ModalShell
    title="Débuter l'épreuve"
    :subtitle="event.name"
    size="md"
    @close="emit('close')"
  >
    <template #icon>
      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8">
        <polygon points="5 3 19 12 5 21 5 3"/>
      </svg>
    </template>

    <div v-if="loading" class="loading-note">Chargement des poules…</div>

    <template v-else>
      <!-- Aperçu des poules -->
      <div class="mdl-section">
        <h4>Poules jouables ({{ playableGroups.length }})</h4>
        <div v-if="playableGroups.length > 0" class="preview-pills">
          <div v-for="g in playableGroups" :key="g.name" class="preview-pill">
            <span class="poule-letter">{{ g.name }}</span>
            <span>Poule {{ g.name }}</span>
            <em class="count-badge">{{ g.playerCount }} joueurs · {{ g.matchCount }} match{{ g.matchCount > 1 ? 's' : '' }}</em>
          </div>
        </div>
        <p v-else class="empty-note">Aucune poule jouable (au moins 2 joueurs par poule requis).</p>
        <p class="total-note">Total : <strong>{{ totalMatches }}</strong> match{{ totalMatches > 1 ? 's' : '' }} à générer</p>
      </div>

      <!-- Avertissement inscrits non placés -->
      <div v-if="unplacedCount > 0" class="mdl-warn">
        <svg viewBox="0 0 24 24" width="16" height="16">
          <path d="M12 2L1 21h22L12 2zm0 6v6m0 3v.5" fill="none" stroke="currentColor" stroke-width="1.8"/>
        </svg>
        <span>
          <b>{{ unplacedCount }} inscrit{{ unplacedCount > 1 ? 's' : '' }} non placé{{ unplacedCount > 1 ? 's' : '' }}</b>
          ne participeront pas à l'épreuve. Retournez dans Poules pour les affecter avant de débuter.
        </span>
      </div>

      <p v-if="error" class="mdl-error">{{ error }}</p>
    </template>

    <template #footer>
      <button class="adm-btn" type="button" @click="emit('close')">Annuler</button>
      <button
        class="adm-btn primary"
        type="button"
        :disabled="loading || saving || !canStart"
        @click="confirm"
      >
        {{ saving ? 'Démarrage…' : 'Débuter l\'épreuve' }}
      </button>
    </template>
  </ModalShell>
</template>

<style scoped>
.loading-note {
  font-size: 13px;
  color: var(--ink-3);
  padding: 8px 0;
}

.mdl-section h4 {
  margin: 0 0 14px;
  font-size: 13px;
  font-weight: 700;
  color: var(--ink-2);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.preview-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.preview-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  padding: 8px 14px;
  font-size: 13px;
  color: var(--ink-1);
}

.poule-letter {
  width: 24px;
  height: 24px;
  border-radius: var(--r-xs);
  background: var(--accent);
  color: #000;
  font-size: 12px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.count-badge {
  font-style: normal;
  font-size: 12px;
  font-family: var(--font-mono);
  color: var(--ink-3);
}

.empty-note {
  font-size: 13px;
  color: var(--ink-3);
  margin-bottom: 12px;
}

.total-note {
  font-size: 13px;
  color: var(--ink-2);
  margin: 0;
}

.mdl-warn {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: var(--r-md);
  padding: 12px 14px;
  font-size: 13px;
  color: var(--ink-1);
  line-height: 1.5;
  margin-top: 16px;
}

.mdl-warn svg { flex-shrink: 0; color: var(--danger); margin-top: 1px; }

.mdl-error {
  margin: 12px 0 0;
  font-size: 13px;
  color: var(--danger);
}

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
