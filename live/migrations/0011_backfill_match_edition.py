from django.db import migrations


def forwards(apps, schema_editor):
    Match = apps.get_model("live", "Match")

    for m in Match.objects.select_related("event"):
        m.edition_id = m.event.edition_id
        m.save(update_fields=["edition"])


def backwards(apps, schema_editor):
    Match = apps.get_model("live", "Match")
    Match.objects.update(edition=None)


class Migration(migrations.Migration):

    dependencies = [
        ("live", "0010_remove_match_uniq_order_per_edition_court_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
