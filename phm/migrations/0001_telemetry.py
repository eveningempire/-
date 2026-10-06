from django.db import migrations, models
import django.db.models.deletion
import uuid

class Migration(migrations.Migration):
    initial = True
    dependencies = [('auth','0012_alter_user_first_name_max_length')]
    operations = [
        migrations.CreateModel(name='TelemetrySession', fields=[('id',models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),('name',models.CharField(max_length=200)),('token_hash',models.CharField(max_length=64)),('columns',models.JSONField(default=list)),('created_at',models.DateTimeField(auto_now_add=True)),('closed_at',models.DateTimeField(blank=True,null=True)),('created_by',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='auth.user'))]),
        migrations.CreateModel(name='TelemetrySample', fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('values',models.JSONField()),('received_at',models.DateTimeField(auto_now_add=True)),('session',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='samples',to='phm.telemetrysession'))]),
        migrations.AddIndex(model_name='telemetrysample',index=models.Index(fields=['session','id'],name='telemetry_session_cursor')),
    ]
