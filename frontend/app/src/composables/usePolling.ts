import { ref, onMounted, onUnmounted } from 'vue'
import { extractApiError } from '@/lib/apiError'

/**
 * Lance `fn` immédiatement, puis toutes les `interval` ms.
 * Cleanup automatique sur onUnmounted.
 */
export function usePolling(fn: () => Promise<void>, interval: number) {
  const loading = ref(true)
  const error = ref<string | null>(null)
  let timer: ReturnType<typeof setInterval> | null = null
  let inFlight = false

  async function run() {
    if (inFlight) return
    inFlight = true
    try {
      await fn()
      error.value = null
    } catch (e) {
      error.value = extractApiError(e, 'Erreur de synchronisation.')
    } finally {
      loading.value = false
      inFlight = false
    }
  }

  function start() {
    if (timer !== null) return
    run()
    timer = setInterval(run, interval)
  }

  function stop() {
    if (timer !== null) {
      clearInterval(timer)
      timer = null
    }
  }

  function onVisibilityChange() {
    if (document.hidden) {
      stop()
    } else {
      start()
    }
  }

  onMounted(() => {
    if (!document.hidden) start()
    document.addEventListener('visibilitychange', onVisibilityChange)
  })
  onUnmounted(() => {
    stop()
    document.removeEventListener('visibilitychange', onVisibilityChange)
  })

  return { loading, error, refresh: run }
}
