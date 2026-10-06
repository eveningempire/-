from django.db import models
class Dataset(models.Model):
    name=models.CharField(max_length=200); file=models.FileField(upload_to='datasets/%Y/%m/%d')
    source=models.CharField(max_length=20,default='offline'); fault_type=models.CharField(max_length=100,blank=True)
    injection_time=models.FloatField(null=True,blank=True); launch_number=models.IntegerField(null=True,blank=True)
    degradation=models.FloatField(null=True,blank=True); system=models.CharField(max_length=100,blank=True); component=models.CharField(max_length=100,blank=True)
    structure_node=models.ForeignKey('phm.StructureNode',null=True,blank=True,on_delete=models.SET_NULL,related_name='datasets')
    created_at=models.DateTimeField(auto_now_add=True)
