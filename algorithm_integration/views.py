from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .services import asset_catalog, fmeca_records, integration_summary, node_catalog, node_detail
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@require_GET
def summary(request): return JsonResponse(integration_summary())

@require_GET
def fmeca(request):
    rows = fmeca_records()
    severity = request.GET.get("severity")
    if severity: rows = [r for r in rows if severity in str(r.get("degree_harm", ""))]
    return JsonResponse({"count": len(rows), "results": rows})

@require_GET
def components(request):
    rows = node_catalog()
    keyword = request.GET.get("q", "").strip().lower()
    if keyword: rows = [r for r in rows if keyword in f"{r['code']} {r['name']}".lower()]
    return JsonResponse({"count": len(rows), "results": rows})

@require_GET
def component_detail(request, code): return JsonResponse(node_detail(code))

@require_GET
def assets(request): return JsonResponse(asset_catalog())


@csrf_exempt
def parameter_batch(request):
    """Validate up to thousands of parameter files in bounded request chunks."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': '仅支持 POST'}, status=405)
    files = request.FILES.getlist('files') or request.FILES.getlist('file')
    if not files:
        return JsonResponse({'ok': False, 'error': '请上传参数文件'}, status=400)
    if len(files) > 2000:
        return JsonResponse({'ok': False, 'error': '单次最多处理 2000 个参数文件'}, status=400)
    from .parameter_processing import validate
    import tempfile, os
    results = []
    for uploaded in files:
        path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=uploaded.name[uploaded.name.rfind('.'):], delete=False) as tmp:
                for chunk in uploaded.chunks(): tmp.write(chunk)
                path = tmp.name
            results.append({'status': 'success', 'report': validate(path, filename=uploaded.name)})
        except Exception as exc:
            results.append({'status': 'failed', 'file_name': uploaded.name, 'error': str(exc)})
        finally:
            if path:
                os.unlink(path)
    return JsonResponse({'ok': True, 'total': len(results), 'success': sum(x['status'] == 'success' and x['report']['status'] == 'valid' for x in results), 'warning': sum(x['status'] == 'success' and x['report']['status'] == 'warning' for x in results), 'failed': sum(x['status'] == 'failed' for x in results), 'results': results})
