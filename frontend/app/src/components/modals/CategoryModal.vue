<script setup lang="ts">
import { ref, computed } from 'vue'
import ModalShell from '@/components/ui/ModalShell.vue'
import Segmented from '@/components/ui/Segmented.vue'
import { useEventStore } from '@/stores/event'
import { extractApiError } from '@/lib/apiError'
import type { Category, CategoryMode } from '@/types'

const props = defineProps<{ editing?: Category | null }>()
const emit = defineEmits<{ close: []; saved: [] }>()

const eventStore = useEventStore()

const name = ref(props.editing?.name ?? '')
const mode = ref<CategoryMode>(props.editing?.mode ?? 'S')
const saving = ref(false)
const error = ref('')

const modeOptions = [
  { value: 'S', label: 'Simple' },
  { value: 'D', label: 'Double' },
]

const canSave = computed(() => !!name.value.trim())

// B3 : le mode est verrouillé côté serveur si des inscriptions existent.
const modeLocked = computed(() => !!props.editing && props.editing.eventsCount > 0)

async function save() {
  if (!canSave.value) return
  saving.value = true
  error.value = ''
  try {
    if (props.editing) {
      await eventStore.editCategory(props.editing.id, { name: name.value.trim(), mode: mode.value })
    } else {
      await eventStore.createCategory({ name: name.value.trim(), mode: mode.value })
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
    :title="editing ? 'Modifier la catégorie' : 'Nouvelle catégorie'"
    :subtitle="editing ? editing.name : 'Référentiel partagé entre les éditions.'"
    size="md"
    @close="emit('close')"
  >
    <template #icon>
      <svg viewBox="0 0 24 24" width="20" height="20">
        <path d="M4 6h16v4H4zM4 14h10v4H4z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
      </svg>
    </template>

    <div class="mdl-section">
      <div class="fld-grid">
        <label class="fld fld-span-2">
          <span class="fld-lbl">Nom <em>*</em></span>
          <input v-model="name" class="inp" placeholder="Double mixte" />
        </label>
        <label class="fld fld-span-2">
          <span class="fld-lbl">Mode <em>*</em></span>
          <Segmented v-model="mode" :options="modeOptions" />
          <span v-if="modeLocked" class="fld-hint">
            Changer le mode peut être refusé si des inscriptions existent déjà.
          </span>
        </label>
      </div>
    </div>

    <p v-if="error" class="mdl-error">{{ error }}</p>

    <template #footer>
      <button class="adm-btn" type="button" @click="emit('close')">Annuler</button>
      <button class="adm-btn primary" type="button" :disabled="saving || !canSave" @click="save">
        {{ saving ? 'Enregistrement…' : editing ? 'Sauvegarder' : 'Créer la catégorie' }}
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
.fld-hint { font-size: 11px; color: var(--ink-3); }

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
