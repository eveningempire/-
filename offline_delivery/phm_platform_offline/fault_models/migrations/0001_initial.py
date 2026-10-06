from django.db import migrations,models
class Migration(migrations.Migration):
 initial=True; dependencies=[]
 operations=[migrations.CreateModel(name='FaultTree',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('name',models.CharField(default='默认故障树',max_length=200)),('graph',models.JSONField(default=dict)),('version',models.PositiveIntegerField(default=1)),('updated_at',models.DateTimeField(auto_now=True))]),migrations.CreateModel(name='FmecaRecord',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('data',models.JSONField(default=dict)),('version',models.PositiveIntegerField(default=1)),('updated_at',models.DateTimeField(auto_now=True))])]
