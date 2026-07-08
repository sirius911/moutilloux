<script setup lang="ts">
import { ref, computed } from 'vue'
import ModalShell from '@/components/ui/ModalShell.vue'
import { useEventStore } from '@/stores/event'
import type { CalendarDay } from '@/types'

const emit = defineEmits<{ close: [] }>()

const eventStore = useEventStore()

// ── État du formulaire ─────────────────────────────────────────────────────
const formVisible = ref(false)
const editingId = ref<number | null>(null)
const formDate = ref('')
const formStart = ref('')
const formEnd = ref('')
const saving = ref(false)
const formError = ref('')

// ── Suppression ────────────────────────────────────────────────────────────
const confirmDeleteId = ref<number | null>(null)
const deleteError = ref<Record<number, string>>({})
const deleting = ref<Record<number, boolean>>({})

// ── Génération depuis l'édition ─────────────────────────────────────────────
const generateFormVisible = ref(false)
const generateStart = ref('09:00')
const generateEnd = ref('20:00')
const generating = ref(false)
const generateError = ref('')

const calendarDays = computed<CalendarDay[]>(() => eventStore.calendar?.playDays ?? [])

function isArchived(day: CalendarDay): boolean {
  return day.matches.some((m) => m.status === 'FINISHED')
}

function itemCount(day: CalendarDay): string {
  const m = day.matches.length
  const b = day.breaks.length
  if (m === 0 && b === 0) return 'vide'
  const parts = []
  if (m > 0) parts.push(`${m} match${m > 1 ? 's' : ''}`)
  if (b > 0) parts.push(`${b} pause${b > 1 ? 's' : ''}`)
  return parts.join(', ')
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
}

// ── Génération depuis l'édition ─────────────────────────────────────────────
function addDays(dateStr: string, n: number): string {
  const d = new Date(dateStr + 'T00:00:00')
  d.setDate(d.getDate() + n)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const missingDates = computed<string[]>(() => {
  const start = eventStore.activeEdition?.startDt
  const end = eventStore.activeEdition?.endDt
  if (!start || !end) return []
  const startDate = start.slice(0, 10)
  const endDate = end.slice(0, 10)
  const existing = new Set(calendarDays.value.map((d) => d.date))
  const dates: string[] = []
  let cursor = startDate
  let guard = 0
  while (cursor <= endDate && guard < 1000) {
    if (!existing.has(cursor)) dates.push(cursor)
    if (cursor === endDate) break
    cursor = addDays(cursor, 1)
    guard += 1
  }
  return dates
})

const generateDisabledReason = computed<string>(() => {
  const start = eventStore.activeEdition?.startDt
  const end = eventStore.activeEdition?.endDt
  if (!start || !end) return "L'édition n'a pas de dates de début/fin."
  if (missingDates.value.length === 0) return 'Toutes les journées entre les dates de l\'édition sont déjà créées.'
  return ''
})

const generateDisabled = computed(() => generateDisabledReason.value !== '')

const generateFormValid = computed(() => generateStart.value && generateEnd.value && missingDates.value.length > 0)

function openGenerate() {
  generateStart.value = '09:00'
  generateEnd.value = '20:00'
  generateError.value = ''
  generateFormVisible.value = true
}

function closeGenerate() {
  generateFormVisible.value = false
}

async function confirmGenerate() {
  if (!generateFormValid.value) return
  const editionId = eventStore.activeEdition?.id
  if (!editionId) return
  generating.value = true
  generateError.value = ''
  try {
    await eventStore.generatePlayDays(editionId, {
      startTime: generateStart.value,
      targetEndTime: generateEnd.value,
    })
    closeGenerate()
  } catch (e) {
    generateError.value = e instanceof Error ? e.message : 'Erreur lors de la génération.'
  } finally {
    generating.value = false
  }
}

// ── Formulaire ─────────────────────────────────────────────────────────────
function openCreate() {
  editingId.value = null
  formDate.value = ''
  formStart.value = ''
  formEnd.value = ''
  formError.value = ''
  formVisible.value = true
}

function openEdit(day: CalendarDay) {
  editingId.value = day.id
  formDate.value = day.date
  formStart.value = day.startTime
  formEnd.value = day.targetEndTime
  formError.value = ''
  formVisible.value = true
}

function closeForm() {
  formVisible.value = false
  editingId.value = null
}

const formValid = computed(() => formDate.value && formStart.value && formEnd.value)

async function saveForm() {
  if (!formValid.value) return
  const editionId = eventStore.activeEdition?.id
  if (!editionId) return
  saving.value = true
  formError.value = ''
  try {
    const payload = { date: formDate.value, startTime: formStart.value, targetEndTime: formEnd.value }
    if (editingId.value !== null) {
      await eventStore.updatePlayDay(editingId.value, payload)
    } else {
      await eventStore.createPlayDay(editionId, payload)
    }
    closeForm()
  } catch (e) {
    formError.value = e instanceof Error ? e.message : 'Erreur lors de l\'enregistrement.'
  } finally {
    saving.value = false
  }
}

// ── Suppression ────────────────────────────────────────────────────────────
function askDelete(id: number) {
  confirmDeleteId.value = id
  delete deleteError.value[id]
}

async function confirmDelete(id: number) {
  deleting.value[id] = true
  delete deleteError.value[id]
  try {
    await eventStore.deletePlayDay(id)
    confirmDeleteId.value = null
  } catch (e) {
    deleteError.value[id] = e instanceof Error ? e.message : 'Erreur lors de la suppression.'
  } finally {
    deleting.value[id] = false
  }
}
</script>

<template>
  <ModalShell
    title="Gérer les journées"
    subtitle="Créez ou modifiez les journées de jeu de l'édition."
    size="lg"
    @close="emit('close')"
  >
    <template #icon>
      <svg viewBox="0 0 24 24" width="20" height="20">
        <rect x="3" y="4" width="18" height="18" rx="2" fill="none" stroke="currentColor" stroke-width="1.6"/>
        <path d="M3 9h18M8 2v4M16 2v4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" fill="none"/>
      </svg>
    </template>

    <!-- ── Liste des journées ───────────────────────────────────────────── -->
    <div v-if="calendarDays.length === 0 && !formVisible" class="pd-empty">
      <p>Aucune journée configurée.</p>
      <p class="pd-empty-sub">Créez la première journée pour commencer à planifier.</p>
    </div>

    <div v-else-if="calendarDays.length > 0" class="pd-list">
      <div v-for="day in calendarDays" :key="day.id" class="pd-row">
        <div class="pd-row-info">
          <span class="pd-row-date">{{ formatDate(day.date) }}</span>
          <span class="pd-row-times">{{ day.startTime }} → {{ day.targetEndTime }}</span>
          <span class="pd-row-count">{{ itemCount(day) }}</span>
        </div>
        <div class="pd-row-actions">
          <template v-if="confirmDeleteId === day.id">
            <span class="pd-confirm-text">Supprimer ?</span>
            <button class="row-btn danger" type="button" :disabled="deleting[day.id]" @click="confirmDelete(day.id)">
              {{ deleting[day.id] ? 'Suppression…' : 'Confirmer' }}
            </button>
            <button class="row-btn" type="button" @click="confirmDeleteId = null">Annuler</button>
          </template>
          <template v-else>
            <button class="row-btn" type="button" @click="openEdit(day)">Modifier</button>
            <button
              class="row-btn"
              type="button"
              :disabled="isArchived(day)"
              :title="isArchived(day) ? 'Journée archivée — matchs terminés' : undefined"
              @click="askDelete(day.id)"
            >
              Supprimer
            </button>
          </template>
        </div>
        <p v-if="deleteError[day.id]" class="pd-row-error">{{ deleteError[day.id] }}</p>
      </div>
    </div>

    <!-- ── Générer depuis l'édition ────────────────────────────────────── -->
    <div v-if="generateFormVisible" class="pd-form">
      <h4 class="pd-form-title">Générer depuis l'édition</h4>
      <div class="pd-form-fields">
        <label class="pd-fld">
          <span class="pd-fld-lbl">Heure de début <span class="req">*</span></span>
          <input v-model="generateStart" type="time" class="pd-input" :disabled="generating" />
        </label>
        <label class="pd-fld">
          <span class="pd-fld-lbl">Heure de fin cible <span class="req">*</span></span>
          <input v-model="generateEnd" type="time" class="pd-input" :disabled="generating" />
        </label>
      </div>
      <p v-if="generateDisabledReason" class="pd-form-error">{{ generateDisabledReason }}</p>
      <template v-else>
        <div class="pd-generate-preview">
          <p class="pd-generate-preview-title">Journées qui seront créées ({{ missingDates.length }}) :</p>
          <ul class="pd-generate-preview-list">
            <li v-for="date in missingDates" :key="date">{{ formatDate(date) }}</li>
          </ul>
        </div>
      </template>
      <p v-if="generateError" class="pd-form-error">{{ generateError }}</p>
      <div class="pd-form-actions">
        <button class="adm-btn" type="button" :disabled="generating" @click="closeGenerate">Annuler</button>
        <button
          class="adm-btn primary"
          type="button"
          :disabled="!generateFormValid || generating"
          @click="confirmGenerate"
        >
          {{ generating ? 'Génération…' : `Créer ${missingDates.length} journée${missingDates.length > 1 ? 's' : ''}` }}
        </button>
      </div>
    </div>

    <!-- ── Formulaire création / édition ───────────────────────────────── -->
    <div v-if="formVisible" class="pd-form">
      <h4 class="pd-form-title">{{ editingId !== null ? 'Modifier la journée' : 'Nouvelle journée' }}</h4>
      <div class="pd-form-fields">
        <label class="pd-fld">
          <span class="pd-fld-lbl">Date <span class="req">*</span></span>
          <input v-model="formDate" type="date" class="pd-input" :disabled="saving" />
        </label>
        <label class="pd-fld">
          <span class="pd-fld-lbl">Heure de début <span class="req">*</span></span>
          <input v-model="formStart" type="time" class="pd-input" :disabled="saving" />
        </label>
        <label class="pd-fld">
          <span class="pd-fld-lbl">Heure de fin cible <span class="req">*</span></span>
          <input v-model="formEnd" type="time" class="pd-input" :disabled="saving" />
        </label>
      </div>
      <p v-if="formError" class="pd-form-error">{{ formError }}</p>
      <div class="pd-form-actions">
        <button class="adm-btn" type="button" :disabled="saving" @click="closeForm">Annuler</button>
        <button class="adm-btn primary" type="button" :disabled="!formValid || saving" @click="saveForm">
          {{ saving ? 'Enregistrement…' : (editingId !== null ? 'Enregistrer' : 'Créer la journée') }}
        </button>
      </div>
    </div>

    <template #footer>
      <button
        v-if="!formVisible && !generateFormVisible"
        class="adm-btn"
        type="button"
        :disabled="generateDisabled"
        :title="generateDisabled ? generateDisabledReason : undefined"
        @click="openGenerate"
      >
        Générer depuis l'édition
      </button>
      <button v-if="!formVisible && !generateFormVisible" class="adm-btn primary" type="button" @click="openCreate">
        + Nouvelle journée
      </button>
      <button class="adm-btn" type="button" @click="emit('close')">Fermer</button>
    </template>
  </ModalShell>
</template>

<style scoped>
/* ── Liste ──────────────────────────────────────────────────────────────── */
.pd-empty {
  text-align: center;
  padding: 24px;
  color: var(--ink-3);
  font-size: 14px;
}

.pd-empty-sub { font-size: 13px; margin-top: 4px; }

.pd-list {
  display: flex;
  flex-direction: column;
  gap: 0;
  border: 1px solid var(--line-1);
  border-radius: var(--r-md);
  overflow: hidden;
}

.pd-row {
  padding: 14px 16px;
  border-bottom: 1px solid var(--line-1);
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.pd-row:last-child { border-bottom: none; }

.pd-row-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.pd-row-date {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-0);
  text-transform: capitalize;
}

.pd-row-times {
  font-size: 13px;
  color: var(--ink-2);
  font-family: var(--font-mono);
  white-space: nowrap;
}

.pd-row-count {
  font-size: 12px;
  color: var(--ink-3);
  background: var(--bg-4);
  padding: 2px 8px;
  border-radius: 99px;
  white-space: nowrap;
}

.pd-row-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.pd-confirm-text {
  font-size: 13px;
  color: var(--danger);
  font-weight: 600;
}

.pd-row-error {
  width: 100%;
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--danger);
}

/* ── Formulaire ─────────────────────────────────────────────────────────── */
.pd-form {
  border: 1px solid var(--accent);
  border-radius: var(--r-md);
  padding: 20px;
  background: var(--bg-3);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.pd-form-title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--ink-1);
}

.pd-form-fields {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 14px;
}

.pd-fld {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.pd-fld-lbl {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-2);
  letter-spacing: 0.04em;
}

.req { color: var(--danger); margin-left: 2px; }

.pd-input {
  padding: 8px 10px;
  border: 1px solid var(--line-2);
  border-radius: var(--r-sm);
  background: var(--bg-2);
  font-size: 14px;
  color: var(--ink-0);
  font-family: inherit;
  outline: none;
  transition: border-color 150ms;
}

.pd-input:focus { border-color: var(--accent); }
.pd-input:disabled { opacity: 0.5; }

.pd-form-error {
  margin: 0;
  font-size: 13px;
  color: var(--danger);
}

.pd-generate-preview {
  border: 1px solid var(--line-1);
  border-radius: var(--r-sm);
  background: var(--bg-2);
  padding: 10px 14px;
  max-height: 180px;
  overflow-y: auto;
}

.pd-generate-preview-title {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-2);
}

.pd-generate-preview-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.pd-generate-preview-list li {
  font-size: 13px;
  color: var(--ink-0);
  text-transform: capitalize;
}

.pd-form-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* ── Boutons ────────────────────────────────────────────────────────────── */
.row-btn {
  padding: 6px 12px;
  border-radius: var(--r-sm);
  border: 1px solid var(--line-2);
  background: var(--bg-3);
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-1);
  cursor: pointer;
  transition: background 150ms, border-color 150ms;
  font-family: inherit;
  white-space: nowrap;
}

.row-btn:hover { background: var(--bg-4); border-color: var(--accent); }
.row-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.row-btn.danger {
  color: var(--danger);
  border-color: var(--danger);
}

.row-btn.danger:hover { background: var(--danger-soft); }

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
.adm-btn.primary { background: var(--accent); border-color: var(--accent); color: #000; }
.adm-btn.primary:hover { opacity: 0.9; }
.adm-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
