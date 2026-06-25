from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]
    operations = [
        migrations.AddField(
            model_name="tournamentedition",
            name="default_match_duration_min",
            field=models.PositiveSmallIntegerField(default=27),
        ),
    ]
