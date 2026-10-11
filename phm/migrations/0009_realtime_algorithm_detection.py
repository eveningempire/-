from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("phm", "0008_userpermissionprofile")]
    operations = [
        migrations.AddField(
            model_name="telemetrysession", name="detection_algorithm",
            field=models.CharField(default="rules", max_length=40),
        ),
        migrations.AddField(
            model_name="telemetrysession", name="algorithm_window_size",
            field=models.PositiveIntegerField(default=30),
        ),
        migrations.AddField(
            model_name="telemetrysession", name="algorithm_stride",
            field=models.PositiveIntegerField(default=10),
        ),
        migrations.CreateModel(
            name="RealtimeDetectionResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("algorithm", models.CharField(max_length=40)),
                ("decision", models.CharField(choices=[("normal", "normal"), ("abnormal", "abnormal"), ("uncertain", "uncertain"), ("error", "error")], max_length=20)),
                ("confidence", models.FloatField(blank=True, null=True)),
                ("fault_name", models.CharField(blank=True, max_length=200)),
                ("window_start", models.FloatField(blank=True, null=True)),
                ("window_end", models.FloatField(blank=True, null=True)),
                ("result", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("sample", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="detection_results", to="phm.telemetrysample")),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="detection_results", to="phm.telemetrysession")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
