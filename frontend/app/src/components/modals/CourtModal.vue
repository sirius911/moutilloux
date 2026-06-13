<script setup lang="ts">
import { ref, computed } from 'vue'
import ModalShell from '@/components/ui/ModalShell.vue'
import { useEventStore } from '@/stores/event'
import { extractApiError } from '@/lib/apiError'
import type { Court } from '@/types'

const props = defineProps<{ editing?: Court | null }>()
const emit = defineEmits<{ close: []; saved: [] }>()

const eventStore = useEventStore()

const name = ref(props.editing?.name ?? '')
const saving = ref(false)
const error = ref('')

const canSave = computed(() => !!name.value.trim())
// D3 : « Central » est ciblé littéralement par l'auto-assignation des matchs.
const isCentral = computed(() => props.editing?.name === 'Central')

async function save() {
  if (!canSave.value) return
  saving.value = true
  error.value = ''
  try {
    if (props.editing) {
      await eventStore.editCourt(props.editing.id, name.value.trim())
    } else {
      await eventStore.createCourt(name.value.trim())
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
    :title="editing ? 'Renommer le court' : 'Nouveau court'"
    :subtitle="editing ? editing.name : 'Un terrain de jeu.'"
    size="sm"
    @close="emit('close')"
  >
    <template #icon>
      <svg viewBox="0 0 24 24" width="20" height="20">
        <rect x="4" y="5" width="16" height="14" rx="1" fill="none" stroke="currentColor" stroke-width="1.6"/>
        <path d="M12 5v14M4 12h16" fill="none" stroke="currentColor" stroke-width="1.6"/>
      </svg>
    </template>

    <div class="mdl-section">
      <label class="fld">
        <span class="fld-lbl">Nom <em>*</em></span>
        <input v-model="name" class="inp" placeholder="Court 1" @keyup.enter="save" />
      </label>
      <p v-if="isCentral" class="fld-hint warn">
        « Central » est utilisé tel quel pour l'auto-assignation des matchs ordonnés.
        Le renommer désactive ce mécanisme.
      </p>
    </div>

    <p v-if="error" class="mdl-error">{{ error }}</p>

    <template #footer>
      <button class="adm-btn" type="button" @click="emit('close')">Annuler</button>
      <button class="adm-btn primary" type="button" :disabled="saving || !canSave" @click="save">
        {{ saving ? 'Enregistrement…' : editing ? 'Renommer' : 'Créer le court' }}
      </button>
    </template>
  </ModalShell>
</template>

<style scoped>
.fld { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.fld-lbl { font-size: 12px; font-weight: 600; color: var(--ink-2); letter-spacing: 0.04em; }
.fld-lbl em { font-style: normal; color: var(--danger); margin-left: 2px; }
.fld-hint { font-size: 11px; color: var(--ink-3); margin: 10px 0 0; }
.fld-hint.warn { color: var(--warn, var(--accent)); }

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
