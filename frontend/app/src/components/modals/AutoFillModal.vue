<script setup lang="ts">
import { ref, computed } from 'vue'
import ModalShell from '@/components/ui/ModalShell.vue'
import Segmented from '@/components/ui/Segmented.vue'
import { useEventStore } from '@/stores/event'

const emit = defineEmits<{ close: []; saved: [] }>()

const eventStore = useEventStore()

const activeEvent = computed(() =>
  eventStore.events.find((e) => e.id === eventStore.activeEventId) ?? null
)

const groupSize = ref<3 | 4>(activeEvent.value?.groupSizeDefault === 3 ? 3 : 4)
const method = ref<'order' | 'random'>('order')
const saving = ref(false)
const error = ref('')

const total = computed(() => eventStore.players.length)
const groupCount = computed(() =>
  total.value > 0 ? Math.max(1, Math.ceil(total.value / groupSize.value)) : 0,
)

const preview = computed(() => {
  const n = groupCount.value
  if (n === 0) return []
  const base = Math.floor(total.value / n)
  const rem = total.value % n
  return Array.from({ length: n }, (_, i) => base + (i < rem ? 1 : 0))
})

const sizeOptions = [
  { value: 3, label: '3 joueurs' },
  { value: 4, label: '4 joueurs' },
]

const methodOptions = [
  { value: 'order', label: "Ordre d'inscription" },
  { value: 'random', label: 'Aléatoire' },
]

const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

async function fill() {
  if (!eventStore.activeEventId) return
  saving.value = true
  error.value = ''
  try {
    await eventStore.autofillGroups(
      eventStore.activeEventId,
      method.value === 'random',
      groupSize.value,
    )
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
    title="Remplir les poules automatiquement"
    subtitle="Répartit les inscrits en round-robin sur des poules de taille égale."
    size="md"
    @close="emit('close')"
  >
    <template #icon>
      <svg viewBox="0 0 24 24" width="20" height="20">
        <rect x="3" y="3" width="8" height="8" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.6"/>
        <rect x="13" y="3" width="8" height="8" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.6"/>
        <rect x="3" y="13" width="8" height="8" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.6"/>
        <rect x="13" y="13" width="8" height="8" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.6"/>
      </svg>
    </template>

    <!-- Format des poules -->
    <div class="mdl-section">
      <h4>Format des poules</h4>
      <div class="fld-col">
        <label class="fld">
          <span class="fld-lbl">Joueurs par poule</span>
          <Segmented v-model="groupSize" :options="sizeOptions" />
        </label>
        <label class="fld">
          <span class="fld-lbl">Méthode de répartition</span>
          <Segmented v-model="method" :options="methodOptions" />
        </label>
      </div>
    </div>

    <!-- Prévisualisation -->
    <div class="mdl-section">
      <h4>Prévisualisation</h4>
      <div v-if="total > 0" class="preview-pills">
        <div v-for="(count, i) in preview" :key="i" class="preview-pill">
          <span class="poule-letter">{{ LETTERS[i] }}</span>
          <span>Poule {{ LETTERS[i] }}</span>
          <em class="count-badge">{{ count }} joueurs</em>
        </div>
      </div>
      <p v-else class="empty-note">Aucun joueur inscrit à cette épreuve.</p>
      <div class="mdl-warn">
        <svg viewBox="0 0 24 24" width="16" height="16">
          <path d="M12 2L1 21h22L12 2zm0 6v6m0 3v.5" fill="none" stroke="currentColor" stroke-width="1.8"/>
        </svg>
        <span>Les <b>affectations et classements actuels seront réinitialisés</b> avant la nouvelle répartition.</span>
      </div>
      <p v-if="error" class="mdl-error">{{ error }}</p>
    </div>

    <template #footer>
      <button class="adm-btn" type="button" @click="emit('close')">Annuler</button>
      <button
        class="adm-btn primary"
        type="button"
        :disabled="total === 0 || saving"
        @click="fill"
      >
        {{ saving ? 'Génération…' : `Générer ${groupCount} poules de ${groupSize}` }}
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

.fld-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.fld {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.fld-lbl {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-2);
  letter-spacing: 0.04em;
}

/* Preview */
.preview-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
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
  text-align: center;
  color: var(--ink-3);
  font-size: 13px;
  margin-bottom: 14px;
}

/* Warning */
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
}

.mdl-warn svg { flex-shrink: 0; color: var(--danger); margin-top: 1px; }

.mdl-error {
  margin: 12px 0 0;
  font-size: 13px;
  color: var(--danger);
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
