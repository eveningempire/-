from rest_framework import viewsets
from rest_framework.response import Response
from .models import FaultTree,FmecaRecord
class Tree(viewsets.ModelViewSet):
 queryset=FaultTree.objects.all(); http_method_names=['get','post','put','patch','delete']
 def create(self,r,*a,**k): return Response(self._save(r),status=201)
 def update(self,r,*a,**k): return Response(self._save(r,self.get_object()))
 def _save(self,r,obj=None):
  obj=obj or FaultTree(); obj.name=r.data.get('name',obj.name); obj.graph=r.data.get('graph',{}); obj.version=(obj.version+1 if obj.pk else 1); obj.save(); return {'id':obj.id,'name':obj.name,'graph':obj.graph,'version':obj.version}
class Fmeca(viewsets.ModelViewSet):
 queryset=FmecaRecord.objects.all(); http_method_names=['get','post','put','patch','delete']
 def create(self,r,*a,**k): return Response(self._save(r),status=201)
 def update(self,r,*a,**k): return Response(self._save(r,self.get_object()))
 def _save(self,r,obj=None):
  obj=obj or FmecaRecord(); obj.data=r.data.get('data',r.data); obj.version=(obj.version+1 if obj.pk else 1); obj.save(); return {'id':obj.id,'data':obj.data,'version':obj.version}
