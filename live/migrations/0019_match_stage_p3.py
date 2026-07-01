from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('live', '0018_match_is_walkover'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='stage',
            field=models.CharField(
                choices=[
                    ('GROUP', 'Poule'),
                    ('QF', 'Quart'),
                    ('SF', 'Demi'),
                    ('F', 'Finale'),
                    ('P3', '3e place'),
                ],
                db_index=True,
                max_length=10,
            ),
        ),
    ]
