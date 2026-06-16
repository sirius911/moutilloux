<script setup lang="ts">
import ModalShell from '@/components/ui/ModalShell.vue'

withDefaults(defineProps<{
  title: string
  body: string
  confirmLabel?: string
  danger?: boolean
}>(), {
  confirmLabel: 'Supprimer',
  danger: true,
})

const emit = defineEmits<{ confirm: []; close: [] }>()
</script>

<template>
  <ModalShell :title="title" size="sm" @close="emit('close')">
    <template #icon>
      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
    </template>
    <p class="confirm-body">{{ body }}</p>
    <template #footer>
      <button class="mdl-btn" type="button" @click="emit('close')">Annuler</button>
      <button
        :class="['mdl-btn', danger ? 'danger' : 'primary']"
        type="button"
        @click="emit('confirm')"
      >
        {{ confirmLabel }}
      </button>
    </template>
  </ModalShell>
</template>

<style scoped>
.confirm-body {
  margin: 0;
  font-size: 14px;
  color: var(--ink-1);
  line-height: 1.6;
}

.mdl-btn {
  display: inline-flex;
  align-items: center;
  padding: 8px 18px;
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

.mdl-btn:hover { background: var(--bg-4); }

.mdl-btn.danger {
  background: var(--danger);
  border-color: var(--danger);
  color: #fff;
}

.mdl-btn.danger:hover { opacity: 0.85; }

.mdl-btn.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #000;
}

.mdl-btn.primary:hover { opacity: 0.9; }
</style>
