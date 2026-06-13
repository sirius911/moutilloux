import { ref, onMounted, onUnmounted, type Ref } from 'vue'

/**
 * Scale un contenu de taille fixe (targetW × targetH) pour qu'il
 * tienne dans le viewport tout en conservant les proportions.
 *
 * Usage :
 *   const { scale, offsetX, offsetY } = useScale(containerRef, 1920, 1080)
 *   // Appliquer sur l'élément enfant :
 *   // :style="{ transform: `translate(${offsetX}px, ${offsetY}px) scale(${scale})` }"
 */
export function useScale(
  containerRef: Ref<HTMLElement | null>,
  targetW: number,
  targetH: number,
) {
  const scale = ref(1)
  const offsetX = ref(0)
  const offsetY = ref(0)

  function update() {
    const el = containerRef.value
    if (!el) return

    const availW = el.clientWidth
    const availH = el.clientHeight

    const s = Math.min(availW / targetW, availH / targetH)
    scale.value = s

    // Centrage en espace post-scale (pixels viewport).
    // À utiliser avec : transform: `translate(${offsetX}px, ${offsetY}px) scale(${scale})`
    offsetX.value = (availW - targetW * s) / 2
    offsetY.value = (availH - targetH * s) / 2
  }

  let ro: ResizeObserver | null = null

  onMounted(() => {
    update()
    ro = new ResizeObserver(update)
    if (containerRef.value) ro.observe(containerRef.value)
  })

  onUnmounted(() => {
    ro?.disconnect()
  })

  return { scale, offsetX, offsetY }
}
