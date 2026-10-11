from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("simulation_demo", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="faultworkflowtask",
            name="simulation_backend",
            field=models.CharField(default="demo", max_length=30),
        ),
        migrations.AddField(
            model_name="faultworkflowtask",
            name="end_time",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="faultworkflowtask",
            name="flight_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="faultworkflowtask",
            name="simulation_output",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
