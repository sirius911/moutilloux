/**
 * Fetch wrapper avec :
 * - CSRF token lu depuis le cookie `csrftoken` (Django)
 * - base URL configurable via VITE_API_BASE (défaut : '')
 * - JSON par défaut
 */

const BASE = import.meta.env.VITE_API_BASE ?? ''

function getCsrfToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match ? match[1] : ''
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${BASE}${path}`
  const isWrite = options.method && options.method !== 'GET'

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  if (isWrite) {
    const csrf = getCsrfToken()
    console.log(`[useApi] ${options.method} ${path} — csrf="${csrf || '(vide !)'}"`)
    headers['X-CSRFToken'] = csrf
  }

  const res = await fetch(url, {
    credentials: 'include',   // envoie le cookie de session Django
    ...options,
    headers,
  })

  console.log(`[useApi] ${options.method ?? 'GET'} ${path} → ${res.status} ${res.url !== url ? `(redirect → ${res.url})` : ''}`)

  // Session expirée : Django redirige vers /accounts/login/ → HTML, pas JSON
  if (res.redirected && res.url.includes('/accounts/login')) {
    window.location.href = '/login'
    throw new Error('Session expirée — redirection vers /login')
  }

  if (!res.ok) {
    const text = await res.text()
    console.error(`[useApi] erreur ${res.status} sur ${path}:`, text.slice(0, 300))
    throw new Error(`[${res.status}] ${path} — ${text}`)
  }

  const contentType = res.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) {
    const text = await res.text()
    console.error(`[useApi] réponse non-JSON pour ${path} (content-type: ${contentType}):`, text.slice(0, 300))
    throw new Error(`Réponse non-JSON pour ${path}`)
  }

  return res.json() as Promise<T>
}

export function useApi() {
  function get<T>(path: string): Promise<T> {
    return apiFetch<T>(path)
  }

  function post<T>(path: string, body?: unknown): Promise<T> {
    return apiFetch<T>(path, {
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  }

  function patch<T>(path: string, body?: unknown): Promise<T> {
    return apiFetch<T>(path, {
      method: 'PATCH',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  }

  return { get, post, patch }
}
