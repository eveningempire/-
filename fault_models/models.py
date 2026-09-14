from django.db import models
class FaultTree(models.Model):
 name=models.CharField(max_length=200,default='默认故障树'); graph=models.JSONField(default=dict); version=models.PositiveIntegerField(default=1); updated_at=models.DateTimeField(auto_now=True)
class FmecaRecord(models.Model):
 data=models.JSONField(default=dict); version=models.PositiveIntegerField(default=1); updated_at=models.DateTimeField(auto_now=True)
