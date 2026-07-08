/**
 * Extrait un message d'erreur lisible d'une exception levée par `useApi`.
 *
 * `useApi` lève `new Error('[<status>] <path> — <body>')` où `<body>` est le
 * corps brut de la réponse. Côté Django, les erreurs métier renvoient
 * `{ "error": "..." }`, et certaines erreurs de formulaire non liées à un champ
 * précis (`NON_FIELD_ERRORS`) sont renvoyées dans `{ "fields": { "__all__": [...] } }`.
 * On priorise `fields.__all__` (message métier le plus précis), sinon `error`,
 * sinon un message générique.
 *
 * Même logique que l'`extractError` historiquement dupliqué dans
 * `AdminBracket.vue` / `ArbitreMatch.vue`, factorisée ici.
 */
export function extractApiError(e: unknown, fallback = 'Action impossible.'): string {
  const raw = e instanceof Error ? e.message : String(e)
  const sep = raw.indexOf('— ')
  const tail = sep >= 0 ? raw.slice(sep + 2) : raw
  try {
    const parsed = JSON.parse(tail)
    const allErrors = parsed?.fields?.__all__
    if (Array.isArray(allErrors) && allErrors.length > 0 && allErrors.every((m: unknown) => typeof m === 'string')) {
      return allErrors.join(' ')
    }
    if (parsed && typeof parsed.error === 'string') return parsed.error
  } catch {
    /* corps non-JSON : on retombe sur le message générique */
  }
  return fallback
}
