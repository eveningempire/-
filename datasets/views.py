from rest_framework import viewsets,parsers
from rest_framework.permissions import IsAuthenticated
from phm_backend.permissions import PHMRolePermission
from django.http import FileResponse
import csv
from pathlib import Path
import mimetypes
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
import json
from .batch_processing import inspect_file, SUPPORTED_SUFFIXES
from .models import Dataset
from phm.models import StructureNode


def _structure_node_id(value):
    if value in (None, ''):
        return None
    try:
        node = StructureNode.objects.get(pk=int(value), node_type='product')
    except (TypeError, ValueError, StructureNode.DoesNotExist) as exc:
        raise ValueError('结构节点必须是已登记的 PBS 单机产品') from exc
    return node.pk

class DatasetAdminPermission(PHMRolePermission):
    required_permission = 'manage_structure'

class DatasetViewSet(viewsets.ModelViewSet):
    queryset=Dataset.objects.order_by('-created_at'); parser_classes=[parsers.MultiPartParser,parsers.FormParser,parsers.JSONParser]
    def get_permissions(self):
        if self.action in ('create','destroy','update','partial_update','batch_import','inspect'):
            return [IsAuthenticated(), DatasetAdminPermission()]
        return [IsAuthenticated()]
    def list(self,request,*a,**k):
        # Build a fresh queryset per request. Reusing the class-level queryset
        # can retain Django's result cache and make deleted datasets reappear.
        qs=Dataset.objects.select_related('structure_node').order_by('-created_at')
        if request.GET.get('q'): qs=qs.filter(name__icontains=request.GET['q'])
        for key in ('source','fault_type','system','component'):
            if request.GET.get(key): qs=qs.filter(**{key:request.GET[key]})
        return Response([self.item(x) for x in qs])
    def retrieve(self,request,*a,**k):
        d=self.get_object(); item=self.item(d); item['size']=d.file.size if d.file else 0
        item['columns']=[]; item['preview']=[]
        if d.file:
            try:
                report = inspect_file(d.file.path, display_name=d.name)
                item['columns'] = report['columns']; item['preview'] = report['sample']; item['quality'] = {k: report[k] for k in ('row_count', 'numeric_columns', 'numeric_parameter_columns', 'time_column', 'fault_flag_column', 'parameter_columns', 'column_roles', 'time_summary', 'fault_label_summary', 'quality_status', 'quality_message')}
            except Exception: pass
        return Response(item)
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        d=self.get_object()
        if not d.file: return Response({'detail':'数据集没有文件'}, status=404)
        filename = d.name or Path(d.file.name).name or f'dataset-{d.pk}'
        suffix = Path(d.file.name).suffix or '.csv'
        if not Path(filename).suffix:
            filename += suffix
        content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        return FileResponse(d.file.open('rb'), as_attachment=True, filename=filename, content_type=content_type)
    @action(detail=True, methods=['get'], url_path='samples')
    def samples(self, request, pk=None):
        d = self.get_object()
        try:
            from itertools import islice
            from .batch_processing import iter_rows
            from .schema import column_roles
            offset = int(request.query_params.get('offset', 0))
            limit = int(request.query_params.get('limit', 500))
            if offset < 0 or not 1 <= limit <= 1000:
                raise ValueError('offset 必须非负,limit 必须为 1 到 1000')
            columns, reader = iter_rows(d.file.path)
            if not columns or len(columns) != len(set(columns)):
                raise ValueError('数据字段为空或重名')
            rows = list(islice(reader, offset, offset + limit + 1))
            return Response({'columns': columns, **column_roles(columns), 'rows': rows[:limit],
                             'next_offset': offset + min(limit, len(rows)), 'has_more': len(rows) > limit})
        except (ValueError, OSError, UnicodeError) as exc:
            return Response({'detail': f'CSV 读取失败:{exc}'}, status=400)
    def create(self,request,*a,**k):
        uploaded = request.FILES.get('file')
        if not uploaded: return Response({'detail':'必须选择数据文件'}, status=400)
        if not uploaded.name.lower().endswith(tuple(SUPPORTED_SUFFIXES)):
            return Response({'detail':'支持 CSV、JSON、JSONL、XLSX 文件'}, status=400)
        try:
            structure_node_id = _structure_node_id(request.data.get('structure_node_id'))
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)
        d=Dataset.objects.create(**{x:request.data.get(x) for x in ['name','source','fault_type','injection_time','launch_number','degradation','system','component'] if request.data.get(x) is not None},structure_node_id=structure_node_id,file=request.FILES.get('file'))
        return Response(self.item(d),status=201)

    @action(detail=False, methods=['post'], url_path='batch-import')
    def batch_import(self, request, *args, **kwargs):
        """Import dozens of data files in one request and return per-file QA."""
        files = request.FILES.getlist('files') or request.FILES.getlist('file')
        if not files:
            return Response({'detail': '请至少选择一个数据文件'}, status=400)
        if len(files) > 2000:
            return Response({'detail': '单次最多处理 2000 个文件'}, status=400)
        try:
            metadata = json.loads(request.data.get('metadata', '{}') or '{}')
        except (TypeError, json.JSONDecodeError):
            return Response({'detail': 'metadata 必须是 JSON 对象'}, status=400)
        results = []
        for index, uploaded in enumerate(files):
            if not uploaded.name.lower().endswith(tuple(SUPPORTED_SUFFIXES)):
                results.append({'file_name': uploaded.name, 'status': 'failed', 'error': '不支持的文件格式'})
                continue
            try:
                with transaction.atomic():
                    name = (metadata.get(str(index), {}) if isinstance(metadata, dict) else {}).get('name') or uploaded.name
                    entry = metadata.get(str(index), {}) if isinstance(metadata, dict) else {}
                    dataset = Dataset.objects.create(
                        name=name,
                        source=(metadata.get(str(index), {}) if isinstance(metadata, dict) else {}).get('source', 'offline'),
                        fault_type=(metadata.get(str(index), {}) if isinstance(metadata, dict) else {}).get('fault_type', ''),
                        system=(metadata.get(str(index), {}) if isinstance(metadata, dict) else {}).get('system', ''),
                        component=(metadata.get(str(index), {}) if isinstance(metadata, dict) else {}).get('component', ''),
                        structure_node_id=_structure_node_id(entry.get('structure_node_id')),
                        file=uploaded,
                    )
                    report = inspect_file(dataset.file.path, display_name=uploaded.name)
                    inferred = report.get('inferred_metadata', {})
                    changed = False
                    for field in ('system', 'component', 'fault_type'):
                        if not getattr(dataset, field) and inferred.get(field):
                            setattr(dataset, field, inferred[field]); changed = True
                    if changed: dataset.save(update_fields=['system', 'component', 'fault_type'])
                results.append({'file_name': uploaded.name, 'status': 'imported', 'dataset_id': dataset.id, 'report': report})
            except Exception as exc:
                results.append({'file_name': uploaded.name, 'status': 'failed', 'error': str(exc)})
        return Response({'ok': True, 'total': len(files), 'imported': sum(x['status'] == 'imported' for x in results), 'failed': sum(x['status'] == 'failed' for x in results), 'results': results}, status=201)

    @action(detail=False, methods=['post'], url_path='inspect')
    def inspect(self, request, *args, **kwargs):
        """Validate files without saving them; useful before a large import."""
        files = request.FILES.getlist('files') or request.FILES.getlist('file')
        if not files: return Response({'detail': '请至少选择一个文件'}, status=400)
        import tempfile, os
        reports = []
        for uploaded in files[:2000]:
            suffix = Path(uploaded.name).suffix
            try:
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    for chunk in uploaded.chunks(): tmp.write(chunk)
                    path = tmp.name
                reports.append({'status': 'ok', 'report': inspect_file(path, display_name=uploaded.name)})
            except Exception as exc:
                reports.append({'status': 'failed', 'file_name': uploaded.name, 'error': str(exc)})
            finally:
                if 'path' in locals(): os.unlink(path); del path
        return Response({'ok': True, 'reports': reports})
    def destroy(self, request, *args, **kwargs):
        d = self.get_object()
        if d.file:
            d.file.delete(save=False)
        d.delete()
        return Response(status=204)
    def partial_update(self,request,*a,**k):
        dataset=self.get_object()
        try:
            if 'structure_node_id' in request.data:
                dataset.structure_node_id=_structure_node_id(request.data.get('structure_node_id'))
                dataset.save(update_fields=['structure_node'])
            else:
                return Response({'detail':'只支持更新 structure_node_id'}, status=400)
        except ValueError as exc:
            return Response({'detail':str(exc)},status=400)
        return Response(self.item(dataset))
    @staticmethod
    def item(x): return {'id':x.id,'name':x.name,'source':x.source,'fault_type':x.fault_type,'injection_time':x.injection_time,'launch_number':x.launch_number,'degradation':x.degradation,'system':x.system,'component':x.component,'structure_node_id':x.structure_node_id,'structure_node_key':x.structure_node.node_key if x.structure_node_id else None,'structure_node_name':x.structure_node.name if x.structure_node_id else None,'file':x.file.url if x.file else None}
