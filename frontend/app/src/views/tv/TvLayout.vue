<script setup lang="ts">
import { ref } from 'vue'
import { RouterView } from 'vue-router'
import { useScale } from '@/composables/useScale'

const TARGET_W = 1920
const TARGET_H = 1080

const containerRef = ref<HTMLElement | null>(null)
const { scale, offsetX, offsetY } = useScale(containerRef, TARGET_W, TARGET_H)
</script>

<template>
  <div ref="containerRef" class="tv-container">
    <div
      class="tv-stage"
      :style="{
        width: `${TARGET_W}px`,
        height: `${TARGET_H}px`,
        transform: `translate(${offsetX}px, ${offsetY}px) scale(${scale})`,
        transformOrigin: 'top left',
      }"
    >
      <RouterView />
    </div>
  </div>
</template>

<style scoped>
.tv-container {
  position: fixed;
  inset: 0;
  background: var(--bg-0);
  overflow: hidden;
}

.tv-stage {
  position: absolute;
  top: 0;
  left: 0;
}
</style>
