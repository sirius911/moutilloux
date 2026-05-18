from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("live", "0015_remove_match_match_sides_must_be_different_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="match",
            name="deciding_set_mode",
            field=models.CharField(
                choices=[("FULL_SET", "Set décisif normal"), ("SUPER_TB", "Super tie-break décisif")],
                default="FULL_SET",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="match",
            name="deciding_tb_points_to_win",
            field=models.PositiveSmallIntegerField(default=10),
        ),
        migrations.AddField(
            model_name="match",
            name="set_scores",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
