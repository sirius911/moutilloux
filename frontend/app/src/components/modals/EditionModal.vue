<script setup lang="ts">
import { ref, computed } from 'vue'
import ModalShell from '@/components/ui/ModalShell.vue'
import { useEventStore } from '@/stores/event'
import { extractApiError } from '@/lib/apiError'
import type { Edition } from '@/types'

const props = defineProps<{ editing?: Edition | null }>()
const emit = defineEmits<{ close: []; saved: [] }>()

const eventStore = useEventStore()

const name = ref(props.editing?.name ?? '')
const year = ref(String(props.editing?.year ?? new Date().getFullYear()))
const startDt = ref(props.editing?.startDt ? props.editing.startDt.slice(0, 10) : '')
const endDt = ref(props.editing?.endDt ? props.editing.endDt.slice(0, 10) : '')
const saving = ref(false)
const error = ref('')

const yearNum = computed(() => Number.parseInt(year.value, 10))
const canSave = computed(() => !!name.value.trim() && Number.isFinite(yearNum.value))

const subtitle = computed(() =>
  props.editing
    ? `${props.editing.name} (${props.editing.year})`
    : 'Une nouvelle année de tournoi.',
)

async function save() {
  if (!canSave.value) return
  saving.value = true
  error.value = ''
  try {
    const base = {
      name: name.value.trim(),
      year: yearNum.value,
      start_dt: startDt.value || null,
      end_dt: endDt.value || null,
    }
    if (props.editing) {
      await eventStore.editEdition(props.editing.id, base)
    } else {
      // Activation automatique si aucune édition active n'existe (spec §modale-édition)
      await eventStore.createEdition({ ...base, activate: !eventStore.activeEdition })
    }
    emit('saved')
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
    :title="editing ? 'Modifier l\'édition' : 'Nouvelle édition'"
    :subtitle="subtitle"
    size="md"
    @close="emit('close')"
  >
    <template #icon>
      <svg viewBox="0 0 24 24" width="20" height="20">
        <path d="M4 7h16M4 12h16M4 17h10" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
      </svg>
    </template>

    <div class="mdl-section">
      <div class="fld-grid">
        <label class="fld fld-span-2">
          <span class="fld-lbl">Nom <em>*</em></span>
          <input v-model="name" class="inp" placeholder="Tournoi des Moutilloux 2027" />
        </label>
        <label class="fld">
          <span class="fld-lbl">Année <em>*</em></span>
          <input v-model="year" class="inp" type="number" inputmode="numeric" placeholder="2027" />
        </label>
        <label class="fld">
          <span class="fld-lbl">Date de début</span>
          <input v-model="startDt" class="inp" type="date" />
        </label>
        <label class="fld">
          <span class="fld-lbl">Date de fin</span>
          <input v-model="endDt" class="inp" type="date" />
        </label>
      </div>

    </div>

    <p v-if="error" class="mdl-error">{{ error }}</p>

    <template #footer>
      <button class="adm-btn" type="button" @click="emit('close')">Annuler</button>
      <button class="adm-btn primary" type="button" :disabled="saving || !canSave" @click="save">
        {{ saving ? 'Enregistrement…' : editing ? 'Sauvegarder' : 'Créer l\'édition' }}
      </button>
    </template>
  </ModalShell>
</template>

<style scoped>
.fld-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px 20px; }
.fld { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.fld-span-2 { grid-column: span 2; }
.fld-lbl { font-size: 12px; font-weight: 600; color: var(--ink-2); letter-spacing: 0.04em; }
.fld-lbl em { font-style: normal; color: var(--danger); margin-left: 2px; }

.inp {
  width: 100%;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  padding: 9px 12px;
  font-size: 14px;
  color: var(--ink-0);
  outline: none;
  transition: border-color 150ms;
  box-sizing: border-box;
  font-family: inherit;
}
.inp:focus { border-color: var(--accent); }

.mdl-error { margin: 8px 0 0; font-size: 13px; color: var(--danger); }

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
  transition: background 150ms, border-color 150ms;
  font-family: inherit;
}
.adm-btn:hover { background: var(--bg-4); }
.adm-btn.primary { background: var(--accent); border-color: var(--accent); color: #000; }
.adm-btn.primary:hover { opacity: 0.9; }
.adm-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
