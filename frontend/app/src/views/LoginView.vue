<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useEventStore } from '@/stores/event'
import { useApi } from '@/composables/useApi'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const eventStore = useEventStore()
const { post } = useApi()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

onMounted(() => {
  eventStore.fetchEditions()
})

/**
 * Valide la destination mémorisée (spec login.md — « Retour après login ») :
 * chemin interne uniquement, et permis au rôle du compte connecté.
 * Sinon : destination par défaut du rôle, sans rebond visible.
 */
function resolveDestination(redirect?: string): string {
  const fallback = authStore.isAdmin ? '/admin/tournoi' : '/arbitre'
  if (!redirect) return fallback
  if (!redirect.startsWith('/') || redirect.startsWith('//')) return fallback
  if (redirect.startsWith('/admin') && !authStore.isAdmin) return fallback
  if (redirect.startsWith('/arbitre') && !authStore.isReferee) return fallback
  return redirect
}

async function submit() {
  // Bloque toute voie de soumission (bouton ET touche Entrée) pendant la requête.
  if (!username.value || !password.value || loading.value) return
  loading.value = true
  error.value = ''

  try {
    await post<{ ok: boolean; isAdmin: boolean; isReferee: boolean }>(
      '/api/auth/login/',
      { username: username.value, password: password.value },
    )

    await authStore.fetchMe()

    if (!authStore.isAdmin && !authStore.isReferee) {
      // Spec : ne laisser aucune session inutilisable ouverte côté serveur.
      error.value = 'Compte non autorisé.'
      password.value = ''
      try {
        await authStore.logout()
      } catch {
        // Échec du logout (réseau) : ne pas masquer le message « Compte non autorisé. »
      }
      return
    }

    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : undefined
    router.push(resolveDestination(redirect))
  } catch (err) {
    const msg = err instanceof Error ? err.message : ''
    if (msg.startsWith('[401]')) {
      error.value = 'Identifiants incorrects. Vérifiez votre nom d\'utilisateur et votre mot de passe.'
    } else {
      error.value = 'Une erreur est survenue. Veuillez réessayer.'
    }
    password.value = ''
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="lgn light-scope">
    <div class="lgn-bg" />

    <div class="lgn-wrap">
      <!-- Formulaire gauche -->
      <div class="lgn-card">
        <!-- Brand -->
        <div class="lgn-brand">
          <div class="lgn-mark">
            <svg viewBox="0 0 24 24" width="22" height="22">
              <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="1.6"/>
              <path d="M2 9c5 2.5 15 2.5 20 0M2 15c5-2.5 15-2.5 20 0" fill="none" stroke="currentColor" stroke-width="1.6"/>
            </svg>
          </div>
          <div>
            <div class="lgn-tournament">OPEN DE MOUTILLOUX</div>
            <div class="lgn-edition">
              {{ eventStore.activeEdition?.name ?? (eventStore.activeEdition?.year ? `Édition ${eventStore.activeEdition.year}` : '—') }}
            </div>
          </div>
        </div>

        <h1 class="lgn-title">Connexion</h1>
        <p class="lgn-sub">Connectez-vous avec votre compte</p>

        <!-- Formulaire identifiants -->
        <div class="lgn-form">
          <label class="fld-lbl">Identifiant</label>
          <input
            v-model="username"
            class="inp"
            type="text"
            placeholder="nom d'utilisateur"
            autocomplete="username"
            @keydown.enter="submit"
          />
          <label class="fld-lbl">Mot de passe</label>
          <input
            v-model="password"
            class="inp"
            type="password"
            placeholder="••••••••"
            @keydown.enter="submit"
          />
          <p v-if="error" class="lgn-error">{{ error }}</p>
          <button
            class="lgn-submit"
            :disabled="!username || !password || loading"
            type="button"
            @click="submit"
          >
            {{ loading ? 'Connexion…' : 'Se connecter' }}
            <svg viewBox="0 0 24 24" width="16" height="16">
              <path d="M5 12h14m0 0l-5-5m5 5l-5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>

        <div class="lgn-divider"><span>OU</span></div>

        <!-- Accès public -->
        <button class="lgn-kiosk" type="button" @click="router.push('/tv/live')">
          <span class="lgn-kiosk-dot" />
          En direct
          <span class="lgn-kiosk-sub">accès libre · TV, poules, tableau final</span>
        </button>
      </div>

      <!-- Aside droite -->
      <aside class="lgn-side">
        <div class="lgn-side-mark">
          <svg viewBox="0 0 24 24" width="56" height="56" style="color: var(--accent)">
            <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="1" opacity="0.4"/>
            <path d="M2 9c5 2.5 15 2.5 20 0M2 15c5-2.5 15-2.5 20 0" fill="none" stroke="currentColor" stroke-width="1" opacity="0.4"/>
          </svg>
        </div>
        <div class="lgn-side-quote">
          <em>«</em> Le tournoi du village, géré au cordeau. <em>»</em>
        </div>
        <div class="lgn-side-stats">
          <div>
            <b class="tab">{{ eventStore.events.length }}</b>
            <span>épreuves</span>
          </div>
        </div>
        <div class="lgn-side-foot">
          <span><i class="lgn-side-dot" /> Serveur · raspberrypi.local</span>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.lgn {
  width: 100vw;
  height: 100vh;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-1);
  overflow: hidden;
}

.lgn-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 60% 50% at 25% 30%, rgba(0, 200, 220, 0.10), transparent 60%),
    radial-gradient(ellipse 50% 50% at 80% 70%, rgba(255, 200, 61, 0.12), transparent 60%),
    repeating-linear-gradient(135deg, transparent 0 18px, rgba(0,0,0,0.015) 18px 19px);
}

.lgn-wrap {
  position: relative;
  width: 1080px;
  height: 660px;
  display: grid;
  grid-template-columns: 1fr 320px;
  background: var(--bg-2);
  border: 1px solid var(--line-2);
  border-radius: 24px;
  box-shadow: 0 40px 100px rgba(11, 15, 23, 0.18);
  overflow: hidden;
}

/* ── Card gauche ─────────────────────────────────────────────────── */
.lgn-card {
  padding: 48px 56px 40px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
  overflow-y: auto;
}

.lgn-brand {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 6px;
}

.lgn-mark {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--accent);
  color: #001215;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.lgn-tournament {
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.16em;
  color: var(--ink-0);
}

.lgn-edition {
  font-size: 11px;
  color: var(--ink-3);
  letter-spacing: 0.06em;
  margin-top: 3px;
}

.lgn-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0;
  letter-spacing: -0.015em;
  color: var(--ink-0);
}

.lgn-sub {
  font-size: 13px;
  color: var(--ink-2);
  margin: 0;
}

/* Formulaire */
.lgn-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.fld-lbl {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-2);
  letter-spacing: 0.04em;
}

.inp {
  width: 100%;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  padding: 10px 14px;
  font-size: 14px;
  color: var(--ink-0);
  outline: none;
  transition: border-color 150ms;
}

.inp:focus { border-color: var(--accent); }

.lgn-error {
  font-size: 13px;
  color: var(--danger);
  margin: 0;
}

.lgn-submit {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: var(--accent);
  border: none;
  border-radius: var(--r-md);
  padding: 12px 20px;
  font-size: 14px;
  font-weight: 700;
  color: #001215;
  transition: opacity 150ms;
}

.lgn-submit:disabled { opacity: 0.5; cursor: not-allowed; }

/* Divider */
.lgn-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--ink-4);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.1em;
}

.lgn-divider::before,
.lgn-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--line-2);
}

/* Kiosk */
.lgn-kiosk {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-1);
  transition: background 150ms;
}

.lgn-kiosk:hover { background: var(--bg-4); }

.lgn-kiosk-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--success);
  flex-shrink: 0;
  animation: pulse 1.5s ease-in-out infinite;
}

.lgn-kiosk-sub {
  font-size: 12px;
  font-weight: 400;
  color: var(--ink-3);
  margin-left: auto;
}

/* ── Aside droite ────────────────────────────────────────────────── */
.lgn-side {
  background: var(--bg-3);
  border-left: 1px solid var(--line-2);
  padding: 48px 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
  text-align: center;
}

.lgn-side-mark {
  opacity: 0.6;
}

.lgn-side-quote {
  font-size: 16px;
  font-style: italic;
  color: var(--ink-2);
  line-height: 1.6;
}

.lgn-side-quote em {
  color: var(--accent);
  font-style: normal;
  font-size: 20px;
}

.lgn-side-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.lgn-side-stats > div {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.lgn-side-stats b {
  font-size: 22px;
  font-weight: 800;
  color: var(--ink-0);
}

.lgn-side-stats span {
  color: var(--ink-3);
}

.lgn-side-foot {
  font-size: 11px;
  color: var(--ink-4);
  letter-spacing: 0.04em;
}

.lgn-side-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--success);
  margin-right: 6px;
  vertical-align: middle;
}
</style>
