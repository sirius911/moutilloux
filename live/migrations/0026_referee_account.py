# Crée le compte arbitre (arbitre/arbitre) et son groupe « Arbitre » pour
# qu'une base reconstruite depuis les migrations soit utilisable sans étape
# manuelle. Les permissions du groupe restent posées par live/setup_roles.py
# (les Permission n'existent qu'après le post_migrate).

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_referee_account(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Group = apps.get_model("auth", "Group")

    group, _ = Group.objects.get_or_create(name="Arbitre")
    # get_or_create : sur une base où le compte existe déjà, on ne touche
    # pas à son mot de passe.
    user, _ = User.objects.get_or_create(
        username="arbitre",
        defaults={"password": make_password("arbitre")},
    )
    user.groups.add(group)


class Migration(migrations.Migration):

    dependencies = [
        ("live", "0025_alter_announcement_options"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(create_referee_account, migrations.RunPython.noop),
    ]
