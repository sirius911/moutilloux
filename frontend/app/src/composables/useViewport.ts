import { ref, onMounted, onUnmounted } from 'vue'

const MOBILE_BREAKPOINT = 600

/**
 * isMobile réactif sur la largeur du viewport (< 600px → variante mobile).
 * Sélection de scène par viewport, pas par route (specs/transverse/mobile.md).
 */
export function useViewport() {
  const isMobile = ref(window.innerWidth < MOBILE_BREAKPOINT)

  function update() {
    isMobile.value = window.innerWidth < MOBILE_BREAKPOINT
  }

  onMounted(() => window.addEventListener('resize', update))
  onUnmounted(() => window.removeEventListener('resize', update))

  return { isMobile }
}
