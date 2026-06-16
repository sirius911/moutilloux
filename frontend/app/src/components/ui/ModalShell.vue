<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

defineProps<{
  title: string
  subtitle?: string
  size?: 'sm' | 'md' | 'lg'
}>()

const emit = defineEmits<{ close: [] }>()

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}
onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <div class="mdl-bg" @mousedown.self="emit('close')">
      <div :class="['mdl', `mdl-${size ?? 'md'}`]" @mousedown.stop>
        <header class="mdl-head">
          <div v-if="$slots.icon" class="mdl-icon">
            <slot name="icon" />
          </div>
          <div class="mdl-head-text">
            <h2>{{ title }}</h2>
            <p v-if="subtitle">{{ subtitle }}</p>
          </div>
          <button class="mdl-close" aria-label="Fermer" @click="emit('close')">
            <svg viewBox="0 0 24 24" width="18" height="18">
              <path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
          </button>
        </header>

        <div class="mdl-body">
          <slot />
        </div>

        <footer v-if="$slots.footer" class="mdl-foot">
          <slot name="footer" />
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.mdl-bg {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.mdl {
  background: var(--bg-2);
  border: 1px solid var(--line-2);
  border-radius: var(--r-xl);
  box-shadow: var(--shadow-2);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
  overflow: hidden;
}

.mdl-sm  { width: 420px; }
.mdl-md  { width: 580px; }
.mdl-lg  { width: 740px; }

.mdl-head {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 24px 28px 20px;
  border-bottom: 1px solid var(--line-1);
  flex-shrink: 0;
}

.mdl-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--r-md);
  background: var(--accent-soft);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.mdl-head-text {
  flex: 1;
  min-width: 0;
}

.mdl-head-text h2 {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: var(--ink-0);
  letter-spacing: -0.01em;
}

.mdl-head-text p {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--ink-2);
}

.mdl-close {
  width: 32px;
  height: 32px;
  border-radius: var(--r-sm);
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  color: var(--ink-2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 150ms;
}

.mdl-close:hover {
  background: var(--bg-4);
  color: var(--ink-0);
}

.mdl-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.mdl-foot {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 28px;
  border-top: 1px solid var(--line-1);
  flex-shrink: 0;
}
</style>
