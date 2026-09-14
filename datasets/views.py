from rest_framework import viewsets,parsers
from rest_framework.permissions import IsAuthenticated
from phm_backend.permissions import PHMRolePermission
from django.http import FileResponse
import csv
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Dataset

class DatasetAdminPermission(PHMRolePermission):
    required_permission = 'manage_structure'

class DatasetViewSet(viewsets.ModelViewSet):
    queryset=Dataset.objects.order_by('-created_at'); parser_classes=[parsers.MultiPartParser,parsers.FormParser]
    def get_permissions(self):
        if self.action in ('create','destroy','update','partial_update'):
            return [IsAuthenticated(), DatasetAdminPermission()]
        return [IsAuthenticated()]
    def list(self,request,*a,**k):
        qs=self.queryset
        if request.GET.get('q'): qs=qs.filter(name__icontains=request.GET['q'])
        for key in ('source','fault_type','system','component'):
            if request.GET.get(key): qs=qs.filter(**{key:request.GET[key]})
        return Response([self.item(x) for x in qs])
    def retrieve(self,request,*a,**k):
        d=self.get_object(); item=self.item(d); item['size']=d.file.size if d.file else 0
        item['columns']=[]; item['preview']=[]
        if d.file:
            try:
                with open(d.file.path,encoding='utf-8-sig',newline='') as f:
                    reader=csv.DictReader(f); item['columns']=reader.fieldnames or []; item['preview']=[x for _,x in zip(range(20),reader)]
            except Exception: pass
        return Response(item)
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        d=self.get_object()
        if not d.file: return Response({'detail':'数据集没有文件'}, status=404)
        filename = d.name or f'dataset-{d.pk}'
        if not filename.lower().endswith('.csv'):
            filename += '.csv'
        return FileResponse(d.file.open('rb'), as_attachment=True, filename=filename, content_type='text/csv; charset=utf-8')
    @action(detail=True, methods=['get'], url_path='samples')
    def samples(self, request, pk=None):
        d = self.get_object()
        try:
            from itertools import islice
            offset = int(request.query_params.get('offset', 0))
            limit = int(request.query_params.get('limit', 500))
            if offset < 0 or not 1 <= limit <= 1000:
                raise ValueError('offset 必须非负，limit 必须为 1 到 1000')
            with d.file.open('rb') as raw:
                import io
                with io.TextIOWrapper(raw, encoding='utf-8-sig', newline='') as text:
                    reader = csv.DictReader(text)
                    columns = reader.fieldnames or []
                    if not columns or len(columns) != len(set(columns)):
                        raise ValueError('CSV 字段为空或重名')
                    rows = list(islice(reader, offset, offset + limit + 1))
            return Response({'columns': columns, 'rows': rows[:limit],
                             'next_offset': offset + min(limit, len(rows)), 'has_more': len(rows) > limit})
        except (ValueError, OSError, UnicodeError) as exc:
            return Response({'detail': f'CSV 读取失败：{exc}'}, status=400)
    def create(self,request,*a,**k):
        d=Dataset.objects.create(**{x:request.data.get(x) for x in ['name','source','fault_type','injection_time','launch_number','degradation','system','component'] if request.data.get(x) is not None},file=request.FILES.get('file'))
        return Response(self.item(d),status=201)
    def destroy(self, request, *args, **kwargs):
        d = self.get_object()
        if d.file:
            d.file.delete(save=False)
        d.delete()
        return Response(status=204)
    @staticmethod
    def item(x): return {'id':x.id,'name':x.name,'source':x.source,'fault_type':x.fault_type,'injection_time':x.injection_time,'launch_number':x.launch_number,'degradation':x.degradation,'system':x.system,'component':x.component,'file':x.file.url if x.file else None}
