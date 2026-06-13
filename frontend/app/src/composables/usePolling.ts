import { ref, onMounted, onUnmounted } from 'vue'

/**
 * Lance `fn` immédiatement, puis toutes les `interval` ms.
 * Cleanup automatique sur onUnmounted.
 */
export function usePolling(fn: () => Promise<void>, interval: number) {
  const loading = ref(true)
  const error = ref<string | null>(null)
  let timer: ReturnType<typeof setInterval> | null = null

  async function run() {
    try {
      await fn()
      error.value = null
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  function start() {
    run()
    timer = setInterval(run, interval)
  }

  function stop() {
    if (timer !== null) {
      clearInterval(timer)
      timer = null
    }
  }

  onMounted(start)
  onUnmounted(stop)

  return { loading, error, refresh: run }
}
