from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0003_entry_withdrawn'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='has_third_place',
            field=models.BooleanField(default=False),
        ),
    ]
