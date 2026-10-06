import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("phm", "0004_remove_realtimealarm_unique_realtime_sample_signal_alarm_and_more")]
    operations = [
        migrations.CreateModel(
            name="FaultEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200)),
                ("severity", models.CharField(default="warning", max_length=20)),
                ("isolation_target", models.CharField(blank=True, max_length=200)),
                ("start_time", models.FloatField(db_index=True)),
                ("end_time", models.FloatField(blank=True, null=True)),
                ("diagnosis", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("alarm", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="fault_event", to="phm.realtimealarm")),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="fault_events", to="phm.telemetrysession")),
            ], options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="FaultReplay",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("window_start", models.FloatField()), ("window_end", models.FloatField()),
                ("current_time", models.FloatField()), ("speed", models.FloatField(default=1.0)),
                ("state", models.CharField(choices=[("paused", "paused"), ("playing", "playing"), ("finished", "finished")], default="paused", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="replays", to="phm.faultevent")),
            ],
        ),
    ]
