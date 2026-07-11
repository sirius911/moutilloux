import { onUnmounted, watch, type Ref } from 'vue'

/**
 * Empêche l'écran de se verrouiller tant que `active` est vrai (Screen Wake
 * Lock API). Ré-acquis au retour de visibilité de l'onglet — le navigateur
 * relâche le verrou silencieusement quand l'onglet est caché. Échec
 * silencieux si l'API n'est pas disponible (specs/transverse/mobile.md).
 */
export function useWakeLock(active: Ref<boolean>) {
  let sentinel: WakeLockSentinel | null = null

  async function acquire() {
    if (!active.value || sentinel) return
    try {
      sentinel = await navigator.wakeLock?.request('screen')
      sentinel?.addEventListener('release', () => { sentinel = null })
    } catch {
      sentinel = null
    }
  }

  async function release() {
    try {
      await sentinel?.release()
    } catch {
      // ignore
    }
    sentinel = null
  }

  function handleVisibilityChange() {
    if (document.visibilityState === 'visible' && active.value) acquire()
  }

  watch(active, (value) => {
    if (value) acquire()
    else release()
  }, { immediate: true })

  document.addEventListener('visibilitychange', handleVisibilityChange)
  onUnmounted(() => {
    document.removeEventListener('visibilitychange', handleVisibilityChange)
    release()
  })
}
