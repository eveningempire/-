import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("phm", "0005_faultevent_faultreplay")]
    operations = [
        migrations.CreateModel(
            name="ReleaseAssessment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("vehicle_id", models.CharField(db_index=True, max_length=100)),
                ("mission_name", models.CharField(blank=True, max_length=200)),
                ("subsystem_health", models.JSONField(default=dict)),
                ("subsystem_weights", models.JSONField(default=dict)),
                ("system_health_index", models.FloatField()),
                ("mission_success_probability", models.FloatField()),
                ("release_threshold", models.FloatField(default=0.85)),
                ("decision", models.CharField(db_index=True, max_length=30)),
                ("blockers", models.JSONField(blank=True, default=list)),
                ("algorithm_trace", models.JSONField(blank=True, default=dict)),
                ("created_by", models.CharField(blank=True, max_length=150)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={"ordering": ["-created_at"]},
        )
    ]
