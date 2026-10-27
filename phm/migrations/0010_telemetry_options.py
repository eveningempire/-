from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('phm', '0009_realtime_algorithm_detection')]
    operations = [
        migrations.AddField('telemetrysession', 'algorithm_parameters', models.JSONField(blank=True, default=dict)),
        migrations.AddField('telemetrysession', 'filter_method', models.CharField(default='none', max_length=30)),
        migrations.AddField('telemetrysession', 'filter_window', models.PositiveIntegerField(default=5)),
    ]
