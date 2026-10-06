from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .services import catalog as get_catalog, files as get_files, preview as get_preview

@require_GET
def catalog(request): return JsonResponse(get_catalog())

@require_GET
def files(request, category):
    try: return JsonResponse({"category": category, "results": get_files(category)})
    except ValueError as exc: return JsonResponse({"error": str(exc)}, status=404)

@require_GET
def preview(request):
    try: return JsonResponse(get_preview(request.GET.get("member", ""), int(request.GET.get("limit", 30))))
    except (ValueError, KeyError) as exc: return JsonResponse({"error": str(exc)}, status=400)
