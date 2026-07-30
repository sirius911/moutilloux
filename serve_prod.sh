#!/usr/bin/env bash
# Lance le serveur du tournoi (données réelles, base db.sqlite3) sur le
# réseau local, avec détection automatique de l'adresse IP et du nom mDNS
# du Mac. Voir « Utilisation sur le réseau local » dans le README.
#
# Usage : ./serve_prod.sh [port]     (8000 par défaut)

set -euo pipefail
cd "$(dirname "$0")"

PORT="${1:-8000}"

# Équivalent macOS de `hostname -I` : on prend l'interface de la route par
# défaut, puis son adresse IPv4.
IFACE=$(route -n get default 2>/dev/null | awk '/interface:/{print $2}')
IP=$(ipconfig getifaddr "${IFACE:-en0}" 2>/dev/null || true)
if [[ -z "$IP" ]]; then
  echo "Impossible de détecter l'adresse IP locale (machine hors réseau ?)." >&2
  exit 1
fi

# Nom mDNS (« <machine>.local »), en minuscules : les navigateurs envoient
# les en-têtes Host/Origin en minuscules.
MDNS="$(scutil --get LocalHostName | tr '[:upper:]' '[:lower:]').local"

if [[ ! -f frontend/app/dist/index.html ]]; then
  echo "Build SPA absent (frontend/app/dist/). Lancer d'abord :" >&2
  echo "  cd frontend/app && npm ci && npm run build" >&2
  exit 1
fi

echo "Serveur tournoi — base de production (db.sqlite3)"
echo
echo "  http://$IP:$PORT/tv/live        affichage TV"
echo "  http://$IP:$PORT/arbitre/       tablettes arbitre"
echo "  http://$IP:$PORT/admin/         panneau d'administration (SPA)"
echo "  http://$IP:$PORT/django-admin/  configuration (Django natif)"
echo
echo "  (aussi joignable via http://$MDNS:$PORT/)"
echo

MOUTILLOUX_ENV=prod \
DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost,$IP,$MDNS" \
DJANGO_CSRF_TRUSTED_ORIGINS="http://$IP:$PORT,http://$MDNS:$PORT" \
exec _env/bin/python manage.py runserver "0.0.0.0:$PORT"
