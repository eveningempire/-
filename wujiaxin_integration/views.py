from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .services import asset_catalog, fmeca_records, integration_summary, node_catalog, node_detail

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
