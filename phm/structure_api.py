import json

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import StructureNode


def _node(node, children=None):
    data = {"id": node.id, "node_key": node.node_key, "name": node.name,
            "node_type": node.node_type, "pbs_code": node.pbs_code, "parent_id": node.parent_id,
            "properties": node.properties, "created_at": node.created_at,
            "updated_at": node.updated_at}
    if children is not None:
        data["children"] = children
    return data


def _tree():
    nodes = list(StructureNode.objects.order_by("id"))
    children = {node.id: [] for node in nodes}
    roots = []
    for node in nodes:
        (children[node.parent_id] if node.parent_id in children else roots).append(node)

    def build(node):
        return _node(node, [build(child) for child in children[node.id]])
    return [build(root) for root in roots]


def _parent(value):
    if value in (None, ""):
        return None
    try:
        return StructureNode.objects.get(pk=value)
    except (StructureNode.DoesNotExist, ValueError, TypeError):
        try:
            return StructureNode.objects.get(node_key=value)
        except StructureNode.DoesNotExist as exc:
            raise ValueError("父节点不存在") from exc


def _ensure_not_cycle(node, parent):
    cursor = parent
    while cursor is not None:
        if cursor.pk == node.pk:
            raise ValueError("不能将节点移动到自身或其子节点下")
        cursor = cursor.parent


TYPE_ORDER = {"vehicle": 1, "system": 2, "subsystem": 3, "product": 4}


def _validate_level(node_type, parent, node=None):
    if node_type not in TYPE_ORDER:
        raise ValueError("节点类型应为 vehicle、system、subsystem 或 product")
    if node_type == "vehicle":
        if parent is not None:
            raise ValueError("运载器根节点不能设置父节点")
        roots = StructureNode.objects.filter(node_type="vehicle")
        if node is not None:
            roots = roots.exclude(pk=node.pk)
        if roots.exists():
            raise ValueError("结构树只能包含一个运载器根节点")
        return
    if parent is None:
        raise ValueError("分系统、子系统和单机产品必须设置父节点")
    if TYPE_ORDER[node_type] != TYPE_ORDER.get(parent.node_type, 0) + 1:
        raise ValueError("层级关系必须为：运载器 → 分系统 → 子系统 → 单机产品")


@csrf_exempt
def structure_collection(request):
    if request.method == "GET":
        return JsonResponse({"ok": True, "results": [_node(x) for x in StructureNode.objects.order_by("id")], "tree": _tree()})
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "仅支持 GET/POST"}, status=405)
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
        with transaction.atomic():
            parent = _parent(body.get("parent_id", body.get("parent_key")))
            node_type = body.get("node_type", "product")
            _validate_level(node_type, parent)
            obj = StructureNode.objects.create(
                node_key=body["node_key"], name=body["name"],
                node_type=node_type, pbs_code=body["pbs_code"], properties=body.get("properties", {}),
                parent=parent)
        return JsonResponse({"ok": True, "node": _node(obj), "tree": _tree()}, status=201)
    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)


@csrf_exempt
def structure_detail(request, node_id):
    try:
        node = StructureNode.objects.select_related("parent").get(pk=node_id)
    except StructureNode.DoesNotExist:
        return JsonResponse({"ok": False, "error": "节点不存在"}, status=404)
    if request.method == "GET":
        return JsonResponse({"ok": True, "node": _node(node), "tree": _tree()})
    if request.method in ("PUT", "PATCH"):
        try:
            body = json.loads(request.body.decode("utf-8") or "{}")
            with transaction.atomic():
                parent = node.parent
                if "parent_id" in body or "parent_key" in body:
                    parent = _parent(body.get("parent_id", body.get("parent_key")))
                    _ensure_not_cycle(node, parent)
                node_type = body.get("node_type", node.node_type)
                _validate_level(node_type, parent, node)
                node.parent = parent
                for field in ("node_key", "name", "node_type", "pbs_code", "properties"):
                    if field in body:
                        setattr(node, field, body[field])
                node.save()
            return JsonResponse({"ok": True, "node": _node(node), "tree": _tree()})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return JsonResponse({"ok": False, "error": str(exc)}, status=400)
    if request.method == "DELETE":
        cascade = request.GET.get("cascade") == "true"
        if node.children.exists() and not cascade:
            return JsonResponse({"ok": False, "error": "节点存在子节点；请先移动子节点，或使用 cascade=true 级联删除"}, status=409)
        if cascade:
            ids, pending = [], [node]
            while pending:
                current = pending.pop()
                ids.append(current.pk)
                pending.extend(current.children.all())
            StructureNode.objects.filter(pk__in=ids).delete()
        else:
            node.delete()
        return JsonResponse({"ok": True, "tree": _tree()})
    return JsonResponse({"ok": False, "error": "仅支持 GET/PUT/PATCH/DELETE"}, status=405)
