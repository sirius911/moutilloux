import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // Racine → redirect TV live
    { path: '/', redirect: '/tv/live' },

    // ── Login ──────────────────────────────────────────────────────────────
    {
      path: '/login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },

    // ── TV (public) ────────────────────────────────────────────────────────
    {
      path: '/tv',
      component: () => import('@/views/tv/TvLayout.vue'),
      meta: { public: true },
      children: [
        { path: 'live',    component: () => import('@/views/tv/TvScoreboard.vue') },
        { path: 'groups',  component: () => import('@/views/tv/TvPoules.vue') },
        { path: 'bracket', component: () => import('@/views/tv/TvBracket.vue') },
        { path: '', redirect: 'live' },
      ],
    },

    // ── Arbitre ────────────────────────────────────────────────────────────
    {
      path: '/arbitre',
      component: () => import('@/views/arbitre/ArbitreHome.vue'),
      meta: { requiresAuth: true, requiresReferee: true },
    },
    {
      path: '/arbitre/:matchId',
      component: () => import('@/views/arbitre/ArbitreMatch.vue'),
      props: route => ({ matchId: Number(route.params.matchId) }),
      meta: { requiresAuth: true, requiresReferee: true },
    },

    // ── Admin ──────────────────────────────────────────────────────────────
    {
      path: '/admin',
      component: () => import('@/views/admin/AdminLayout.vue'),
      redirect: '/admin/tournoi',
      meta: { requiresAuth: true, requiresAdmin: true },
      children: [
        { path: 'players', component: () => import('@/views/admin/AdminPlayers.vue') },
        { path: 'inscriptions', component: () => import('@/views/admin/AdminInscriptions.vue') },
        { path: 'groups',  component: () => import('@/views/admin/AdminGroups.vue') },
        { path: 'matches', component: () => import('@/views/admin/AdminMatches.vue') },
        { path: 'bracket', component: () => import('@/views/admin/AdminBracket.vue') },
        { path: 'tournoi', component: () => import('@/views/admin/AdminTournoi.vue') },
      ],
    },

    // ── Catch-all ──────────────────────────────────────────────────────────
    { path: '/:pathMatch(.*)*', redirect: '/tv/live' },
  ],
})

// Guard d'authentification
router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (to.meta.public) {
    // Utilisateur déjà connecté qui tente d'accéder à /login → rediriger vers l'écran par défaut
    if (to.path === '/login') {
      if (!auth.checked) await auth.fetchMe()
      // Ne rediriger que les comptes à rôle : un compte authentifié sans rôle
      // doit voir le formulaire (sinon boucle /login ↔ /arbitre avec la garde isReferee).
      if (auth.isAdmin) return { path: '/admin/tournoi' }
      if (auth.isReferee) return { path: '/arbitre' }
    }
    return true
  }

  // Charger l'utilisateur si pas encore fait
  if (!auth.checked) {
    await auth.fetchMe()
  }

  // to.matched.some() couvre la route parente et toutes ses enfants
  const requiresAuth    = to.matched.some(r => r.meta.requiresAuth)
  const requiresAdmin   = to.matched.some(r => r.meta.requiresAdmin)
  const requiresReferee = to.matched.some(r => r.meta.requiresReferee)

  if (requiresAuth && !auth.isAuthenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  // Garde de rôle : espace admin réservé aux superusers
  if (requiresAdmin && !auth.isAdmin) {
    return auth.isAuthenticated ? { path: '/arbitre' } : { path: '/login' }
  }

  // Garde de rôle : espace arbitre réservé au groupe Arbitre
  if (requiresReferee && !auth.isReferee) {
    return auth.isAdmin ? { path: '/admin/tournoi' } : { path: '/login' }
  }

  return true
})

export default router
