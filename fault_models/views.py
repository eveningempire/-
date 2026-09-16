from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import FaultTree,FmecaRecord


def validate_graph(graph):
 nodes=graph.get('nodes',[]); edges=graph.get('edges',[])
 if not isinstance(nodes,list) or not isinstance(edges,list): raise ValueError('graph.nodes 和 graph.edges 必须是数组')
 ids=[str(n.get('id')) for n in nodes]
 if not ids or any(x in ('None','') for x in ids): raise ValueError('故障树至少需要一个带ID的节点')
 if len(ids)!=len(set(ids)): raise ValueError('节点ID不能重复')
 allowed={'event','basic','top','AND','OR'}
 if any(n.get('type','event') not in allowed for n in nodes): raise ValueError('节点类型仅支持 top/event/basic/AND/OR')
 pairs=[]
 for edge in edges:
  source,target=str(edge.get('source','')),str(edge.get('target',''))
  if source not in ids or target not in ids: raise ValueError('边的起点和终点必须引用现有节点')
  if source==target: raise ValueError('节点不能连接自身')
  pairs.append((source,target))
 if len(pairs)!=len(set(pairs)): raise ValueError('边不能重复')
 graph_map={node:[] for node in ids}
 for source,target in pairs: graph_map[source].append(target)
 visiting=set(); visited=set()
 def walk(node):
  if node in visiting: raise ValueError('故障树不能包含循环引用')
  if node in visited:return
  visiting.add(node)
  for nxt in graph_map[node]:walk(nxt)
  visiting.remove(node);visited.add(node)
 for node in ids:walk(node)
 return {'nodes':nodes,'edges':edges,'layout':graph.get('layout',{})}

def tree_data(obj):
 return {'id':obj.id,'name':obj.name,'graph':obj.graph,'version':obj.version,'updated_at':obj.updated_at}

def fmeca_data(obj):
 return {'id':obj.id,'data':obj.data,'version':obj.version,'updated_at':obj.updated_at}

class Tree(viewsets.ModelViewSet):
 queryset=FaultTree.objects.all(); http_method_names=['get','post','put','patch','delete']
 def list(self,r,*a,**k): return Response([tree_data(obj) for obj in self.get_queryset()])
 def retrieve(self,r,*a,**k): return Response(tree_data(self.get_object()))
 def create(self,r,*a,**k): return Response(self._save(r),status=201)
 def update(self,r,*a,**k): return Response(self._save(r,self.get_object()))
 def _save(self,r,obj=None):
  obj=obj or FaultTree(); obj.name=r.data.get('name',obj.name)
  try: obj.graph=validate_graph(r.data.get('graph',{}))
  except ValueError as exc: raise ValidationError({'graph':str(exc)})
  obj.version=(obj.version+1 if obj.pk else 1); obj.save(); return {'id':obj.id,'name':obj.name,'graph':obj.graph,'version':obj.version}
class Fmeca(viewsets.ModelViewSet):
 queryset=FmecaRecord.objects.order_by('-updated_at'); http_method_names=['get','post','put','patch','delete']
 def list(self,r,*a,**k): return Response([fmeca_data(obj) for obj in self.get_queryset()])
 def retrieve(self,r,*a,**k): return Response(fmeca_data(self.get_object()))
 def create(self,r,*a,**k): return Response(self._save(r),status=201)
 def update(self,r,*a,**k): return Response(self._save(r,self.get_object()))
 def _save(self,r,obj=None):
  obj=obj or FmecaRecord(); obj.data=r.data.get('data',r.data); obj.version=(obj.version+1 if obj.pk else 1); obj.save(); return {'id':obj.id,'data':obj.data,'version':obj.version}
