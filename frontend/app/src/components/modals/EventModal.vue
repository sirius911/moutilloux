<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import ModalShell from '@/components/ui/ModalShell.vue'
import Segmented from '@/components/ui/Segmented.vue'
import { useEventStore } from '@/stores/event'
import { extractApiError } from '@/lib/apiError'
import type { Event } from '@/types'

const props = defineProps<{ editionId: number; editing?: Event | null }>()
const emit = defineEmits<{ close: []; saved: [] }>()

const eventStore = useEventStore()

const categoryId = ref<number | null>(props.editing?.categoryId ?? null)
const groupSize = ref<number>(props.editing?.groupSizeDefault ?? 4)
const qualified = ref<number>(props.editing?.qualifiedPerGroup ?? 2)
const notes = ref(props.editing?.notes ?? '')
const saving = ref(false)
const error = ref('')

const sizeOptions = [
  { value: 3, label: '3 par poule' },
  { value: 4, label: '4 par poule' },
]
const qualifiedOptions = [
  { value: 1, label: '1 qualifié' },
  { value: 2, label: '2 qualifiés' },
]

const categories = computed(() => eventStore.categories)
const noCategories = computed(() => !props.editing && categories.value.length === 0)
const canSave = computed(() => !!props.editing || categoryId.value !== null)

// C3 : baisser qualifiés sous 2 casse l'auto-remplissage du bracket.
const generated = computed(() => !!props.editing && (props.editing.hasGroups || props.editing.hasBracket))

onMounted(() => {
  if (!props.editing && categories.value.length === 0) {
    eventStore.fetchCategories()
  }
})

async function save() {
  if (!canSave.value) return
  saving.value = true
  error.value = ''
  try {
    if (props.editing) {
      await eventStore.editEvent(props.editing.id, {
        group_size_default: groupSize.value,
        qualified_per_group: qualified.value,
        notes: notes.value,
      })
    } else {
      await eventStore.createEvent(props.editionId, {
        category_id: categoryId.value!,
        group_size_default: groupSize.value,
        qualified_per_group: qualified.value,
        notes: notes.value,
      })
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
    :title="editing ? 'Modifier l\'épreuve' : 'Nouvelle épreuve'"
    :subtitle="editing ? editing.name : 'Rendre une catégorie jouable cette année.'"
    size="md"
    @close="emit('close')"
  >
    <template #icon>
      <svg viewBox="0 0 24 24" width="20" height="20">
        <path d="M12 3l2.5 5 5.5.8-4 3.9.9 5.5L12 16.6 7.1 18.2l.9-5.5-4-3.9L9.5 8z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
      </svg>
    </template>

    <div class="mdl-section">
      <div class="fld-grid">
        <label class="fld fld-span-2">
          <span class="fld-lbl">Catégorie <em>*</em></span>
          <input v-if="editing" class="inp" :value="editing.name" disabled />
          <select v-else v-model.number="categoryId" class="inp">
            <option :value="null" disabled>Choisir une catégorie…</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">
              {{ c.name }} ({{ c.mode === 'S' ? 'Simple' : 'Double' }})
            </option>
          </select>
          <span v-if="noCategories" class="fld-hint warn">
            Aucune catégorie. Créez-en une d'abord (espace Configuration).
          </span>
        </label>

        <label class="fld">
          <span class="fld-lbl">Taille de poule</span>
          <Segmented v-model="groupSize" :options="sizeOptions" />
        </label>
        <label class="fld">
          <span class="fld-lbl">Qualifiés / poule</span>
          <Segmented v-model="qualified" :options="qualifiedOptions" />
        </label>

        <label class="fld fld-span-2">
          <span class="fld-lbl">Notes</span>
          <textarea v-model="notes" class="inp" rows="3" placeholder="Optionnel"></textarea>
        </label>
      </div>

      <p v-if="generated && qualified < 2" class="fld-hint warn">
        Des poules/un tableau existent : moins de 2 qualifiés casse l'auto-remplissage du bracket.
      </p>
    </div>

    <p v-if="error" class="mdl-error">{{ error }}</p>

    <template #footer>
      <button class="adm-btn" type="button" @click="emit('close')">Annuler</button>
      <button class="adm-btn primary" type="button" :disabled="saving || !canSave || noCategories" @click="save">
        {{ saving ? 'Enregistrement…' : editing ? 'Sauvegarder' : 'Créer l\'épreuve' }}
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
.inp:disabled { opacity: 0.6; cursor: not-allowed; }
textarea.inp { resize: vertical; }

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
