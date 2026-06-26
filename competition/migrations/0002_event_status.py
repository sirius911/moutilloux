from django.db import migrations, models


def set_event_status_from_matches(apps, schema_editor):
    Event = apps.get_model("competition", "Event")
    Match = apps.get_model("live", "Match")

    for event in Event.objects.all():
        final_finished = Match.objects.filter(
            event=event, stage="F", status="FINISHED"
        ).exists()
        has_group_match = Match.objects.filter(event=event, stage="GROUP").exists()

        if final_finished:
            event.status = "TERMINEE"
        elif has_group_match:
            event.status = "EN_COURS"
        else:
            event.status = "INSCRIPTION"
        event.save(update_fields=["status"])


def reverse_event_status(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("competition", "0001_initial"),
        ("live", "0017_playday_break"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="status",
            field=models.CharField(
                choices=[
                    ("INSCRIPTION", "Inscription"),
                    ("EN_COURS", "En cours"),
                    ("TERMINEE", "Terminée"),
                ],
                db_index=True,
                default="INSCRIPTION",
                max_length=15,
            ),
        ),
        migrations.RunPython(set_event_status_from_matches, reverse_event_status),
    ]
