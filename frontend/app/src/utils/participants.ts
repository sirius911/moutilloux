import type { Entry } from '@/types'

/**
 * Nom affiché d'un côté de match, par priorité décroissante :
 * displayName de l'entrée assignée → étiquette de provenance du slot → « À désigner ».
 * Seul point d'entrée pour nommer un participant de match (spec transverse
 * affichage-participant) — ne jamais lire `side.player.fullName` directement,
 * ce champ ignore les équipes de Double.
 */
export function sideName(side: Entry | null | undefined, label?: string | null): string {
  return side?.displayName ?? label ?? 'À désigner'
}
