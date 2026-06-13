<script setup lang="ts">
defineProps<{
  modelValue: string | number
  options: { value: string | number; label: string }[]
}>()

const emit = defineEmits<{ 'update:modelValue': [value: string | number] }>()
</script>

<template>
  <div class="seg" role="radiogroup">
    <button
      v-for="opt in options"
      :key="opt.value"
      role="radio"
      :aria-checked="modelValue === opt.value"
      :class="['seg-opt', { on: modelValue === opt.value }]"
      type="button"
      @click="emit('update:modelValue', opt.value)"
    >
      {{ opt.label }}
    </button>
  </div>
</template>

<style scoped>
.seg {
  display: flex;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  padding: 3px;
  gap: 2px;
}

.seg-opt {
  flex: 1;
  padding: 7px 12px;
  border-radius: var(--r-sm);
  background: transparent;
  border: none;
  font-size: 13px;
  font-weight: 500;
  color: var(--ink-2);
  transition: background 150ms, color 150ms;
  white-space: nowrap;
}

.seg-opt:hover {
  color: var(--ink-1);
}

.seg-opt.on {
  background: var(--accent);
  color: #000;
  font-weight: 600;
}
</style>
