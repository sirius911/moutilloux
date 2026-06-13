import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useApi } from '@/composables/useApi'

interface Me {
  id: number
  username: string
  isSuperuser: boolean
  isReferee: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const { get, post } = useApi()

  const user = ref<Me | null>(null)
  const checked = ref(false)

  const isAuthenticated = computed(() => user.value !== null)
  const isAdmin = computed(() => user.value?.isSuperuser ?? false)
  const isReferee = computed(() => user.value?.isReferee ?? false)

  async function fetchMe() {
    try {
      user.value = await get<Me>('/api/me/')
    } catch {
      user.value = null
    } finally {
      checked.value = true
    }
  }

  async function logout() {
    try {
      await post('/api/auth/logout/')
    } catch {
      // Nettoyer le store même si la requête réseau échoue
    }
    user.value = null
    checked.value = false
  }

  return { user, checked, isAuthenticated, isAdmin, isReferee, fetchMe, logout }
})
