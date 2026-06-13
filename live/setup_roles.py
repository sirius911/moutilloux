from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Match


def _ensure_group():
    try:
        g, _ = Group.objects.get_or_create(name="Arbitre")

        ct = ContentType.objects.get_for_model(Match)
        perms = Permission.objects.filter(content_type=ct, codename__in=["view_match", "change_match"])
        g.permissions.set(perms)
        g.save()
    except Exception:
        # Les tables n'existent pas encore (première migration) — on ignore.
        pass


_ensure_group()
