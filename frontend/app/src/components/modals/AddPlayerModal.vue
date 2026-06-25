<script setup lang="ts">
import { ref, computed } from 'vue'
import ModalShell from '@/components/ui/ModalShell.vue'
import Segmented from '@/components/ui/Segmented.vue'
import { useApi } from '@/composables/useApi'
import { useEventStore } from '@/stores/event'
import type { Player } from '@/types'

const props = defineProps<{
  editing?: Player | null
}>()

const emit = defineEmits<{ close: []; saved: [] }>()

const { post } = useApi()
const eventStore = useEventStore()

const firstName = ref(props.editing?.firstName ?? '')
const lastName = ref(props.editing?.lastName ?? '')
const birthYear = ref<string>(props.editing?.birthYear?.toString() ?? '')
const currentYear = new Date().getFullYear()
const gender = ref<'M' | 'F' | 'O' | ''>(props.editing?.gender ?? '')
const email = ref(props.editing?.email ?? '')
const phone = ref(props.editing?.phone ?? '')
const saving = ref(false)
const error = ref('')
const fieldErrors = ref<Record<string, string[]>>({})

const subtitle = computed(() =>
  props.editing
    ? `${props.editing.firstName} ${props.editing.lastName}`
    : 'Le joueur sera ajouté au registre.'
)

const genderOptions = [
  { value: '', label: 'Non précisé' },
  { value: 'M', label: 'Homme' },
  { value: 'F', label: 'Femme' },
  { value: 'O', label: 'Autre' },
]

async function save() {
  if (!firstName.value || !lastName.value) return
  saving.value = true
  error.value = ''
  fieldErrors.value = {}
  try {
    if (props.editing) {
      await eventStore.editPlayer(props.editing.id, {
        first_name: firstName.value,
        last_name: lastName.value,
        gender: gender.value || undefined,
        birth_year: birthYear.value ? parseInt(birthYear.value, 10) : undefined,
        email: email.value || undefined,
        phone: phone.value || undefined,
      })
    } else {
      await post('/api/players/create/', {
        first_name: firstName.value,
        last_name: lastName.value,
        birth_year: birthYear.value ? parseInt(birthYear.value, 10) : undefined,
        gender: gender.value || undefined,
        email: email.value || undefined,
        phone: phone.value || undefined,
      })
      await eventStore.fetchAllPlayers()
    }
    emit('saved')
    emit('close')
  } catch (e) {
    const raw = e instanceof Error ? e.message : 'Erreur inconnue.'
    const jsonStart = raw.indexOf(' — ')
    if (jsonStart !== -1) {
      try {
        const parsed = JSON.parse(raw.slice(jsonStart + 3))
        if (parsed.fields) fieldErrors.value = parsed.fields
        error.value = parsed.error ?? raw
      } catch {
        error.value = raw
      }
    } else {
      error.value = raw
    }
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <ModalShell
    :title="editing ? 'Modifier le joueur' : 'Ajouter un joueur'"
    :subtitle="subtitle"
    size="lg"
    @close="emit('close')"
  >
    <template #icon>
      <svg viewBox="0 0 24 24" width="20" height="20">
        <circle cx="10" cy="8" r="4" fill="none" stroke="currentColor" stroke-width="1.6"/>
        <path d="M2 21c0-4 4-7 8-7s8 3 8 7M18 8v6M15 11h6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
      </svg>
    </template>

    <!-- Section Identité -->
    <div class="mdl-section">
      <h4>Identité</h4>
      <div class="fld-grid">
        <label class="fld">
          <span class="fld-lbl">Prénom <em>*</em></span>
          <input v-model="firstName" class="inp" placeholder="Prénom" />
          <span v-if="fieldErrors.first_name?.length" class="fld-error">{{ fieldErrors.first_name[0] }}</span>
        </label>
        <label class="fld">
          <span class="fld-lbl">Nom <em>*</em></span>
          <input v-model="lastName" class="inp" placeholder="Nom de famille" />
          <span v-if="fieldErrors.last_name?.length" class="fld-error">{{ fieldErrors.last_name[0] }}</span>
        </label>
        <label class="fld">
          <span class="fld-lbl">Année de naissance</span>
          <input v-model="birthYear" class="inp" type="number" min="1900" :max="currentYear" placeholder="ex. 1990" />
          <span v-if="fieldErrors.birth_year?.length" class="fld-error">{{ fieldErrors.birth_year[0] }}</span>
        </label>
        <label class="fld">
          <span class="fld-lbl">Genre</span>
          <Segmented v-model="gender" :options="genderOptions" />
          <span v-if="fieldErrors.gender?.length" class="fld-error">{{ fieldErrors.gender[0] }}</span>
        </label>
      </div>
    </div>

    <!-- Section Contact -->
    <div class="mdl-section">
      <h4>Contact</h4>
      <div class="fld-grid">
        <label class="fld">
          <span class="fld-lbl">Email</span>
          <input v-model="email" class="inp" type="email" placeholder="adresse@example.com" />
          <span v-if="fieldErrors.email?.length" class="fld-error">{{ fieldErrors.email[0] }}</span>
        </label>
        <label class="fld">
          <span class="fld-lbl">Téléphone</span>
          <input v-model="phone" class="inp" type="tel" placeholder="+33 6 …" />
          <span v-if="fieldErrors.phone?.length" class="fld-error">{{ fieldErrors.phone[0] }}</span>
        </label>
      </div>
    </div>

    <p v-if="error" class="mdl-error">{{ error }}</p>

    <template #footer>
      <button class="adm-btn" type="button" @click="emit('close')">Annuler</button>
      <button
        class="adm-btn primary"
        type="button"
        :disabled="saving || !firstName || !lastName"
        @click="save"
      >
        {{ saving ? 'Enregistrement…' : editing ? 'Sauvegarder' : 'Ajouter le joueur' }}
      </button>
    </template>
  </ModalShell>
</template>

<style scoped>
.fld-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px 20px;
}

.fld {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.fld-lbl {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-2);
  letter-spacing: 0.04em;
}

.fld-lbl em {
  font-style: normal;
  color: var(--danger);
  margin-left: 2px;
}

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

.mdl-error {
  margin: 8px 0 0;
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
  transition: background 150ms, border-color 150ms;
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

.fld-error {
  font-size: 12px;
  color: var(--danger);
  margin-top: 2px;
}
</style>
