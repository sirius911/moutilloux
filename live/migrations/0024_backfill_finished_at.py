from django.db import migrations, models


def backfill_finished_at(apps, schema_editor):
    Match = apps.get_model('live', 'Match')
    Match.objects.filter(status='FINISHED', finished_at__isnull=True).update(finished_at=models.F('updated_at'))


class Migration(migrations.Migration):

    dependencies = [
        ('live', '0023_match_play_started_at_match_warmup_started_at'),
    ]

    operations = [
        migrations.RunPython(backfill_finished_at, migrations.RunPython.noop),
    ]
