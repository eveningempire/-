"""Persistent, authenticated MATLAB telemetry. No simulated-data fallback."""
import csv
import hashlib
import math
import re
import secrets
from datetime import timedelta

from django.db import transaction
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.http import content_disposition_header
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from phm_backend.permissions import has_permission
from .models import TelemetrySample, TelemetrySession


def describe(session):
    last = session.samples.order_by('-id').first()
    state = 'closed' if session.closed_at else 'waiting'
    if last and not session.closed_at:
        state = 'live' if last.received_at > timezone.now() - timedelta(seconds=5) else 'stale'
    return {'id': str(session.id), 'name': session.name, 'columns': session.columns,
            'state': state, 'sample_count': session.samples.count(),
            'created_at': session.created_at, 'closed_at': session.closed_at,
            'last_received_at': last.received_at if last else None}


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def sessions(request):
    if request.method == 'GET':
        return Response([describe(s) for s in TelemetrySession.objects.order_by('-created_at')[:100]])
    if not has_permission(request.user, 'manage_structure'):
        return Response({'detail': '只有管理员可以创建采集会话'}, status=403)
    name = request.data.get('name')
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 200:
        return Response({'detail': '会话名称应为 1 到 200 个字符'}, status=400)
    token = secrets.token_urlsafe(32)
    session = TelemetrySession.objects.create(name=name.strip(), created_by=request.user,
                                            token_hash=hashlib.sha256(token.encode()).hexdigest())
    return Response({**describe(session), 'token': token,
                     'ingest_path': f'/api/v1/phm/telemetry/sessions/{session.id}/ingest/'}, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def samples(request, session_id):
    session = get_object_or_404(TelemetrySession, pk=session_id)
    try:
        after = int(request.query_params.get('after', 0))
        limit = int(request.query_params.get('limit', 500))
        if after < 0 or not 1 <= limit <= 1000:
            raise ValueError()
    except (TypeError, ValueError):
        return Response({'detail': 'after 必须非负，limit 必须为 1 到 1000'}, status=400)
    batch = list(session.samples.filter(id__gt=after).order_by('id')[:limit + 1])
    visible = batch[:limit]
    return Response({**describe(session), 'rows': [s.values for s in visible],
                     'next_cursor': visible[-1].id if visible else after, 'has_more': len(batch) > limit})


def validate_rows(payload, columns):
    rows = payload.get('samples') if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not 1 <= len(rows) <= 1000:
        raise ValueError('samples 必须包含 1 到 1000 个采样点')
    if not isinstance(rows[0], dict):
        raise ValueError('每个采样点必须是字段到数值的对象')
    schema = columns or list(rows[0])
    if 'time' not in schema or not 2 <= len(schema) <= 65:
        raise ValueError('每个采样点必须包含 time（仿真秒）及至少一个信号，最多 64 个信号')
    if any(not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}', k) for k in schema):
        raise ValueError('字段名必须是 ASCII 字母开头的字母、数字或下划线')
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(schema):
            raise ValueError('同一会话的信号字段必须一致；更换信号请新建会话')
        if any(isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v)
               for v in row.values()):
            raise ValueError('遥测信号必须全部为有限数值，不允许 NaN、Infinity 或字符串')
    return rows, schema


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def ingest(request, session_id):
    # MATLAB uses a session-specific bearer token, not browser cookies/CSRF.
    session = get_object_or_404(TelemetrySession, pk=session_id)
    auth = request.headers.get('Authorization', '')
    token = auth[7:] if auth.startswith('Bearer ') else ''
    if not token or not secrets.compare_digest(hashlib.sha256(token.encode()).hexdigest(), session.token_hash):
        return Response({'detail': '采集令牌无效'}, status=403)
    try:
        with transaction.atomic():
            session = TelemetrySession.objects.select_for_update().get(pk=session_id)
            if session.closed_at:
                return Response({'detail': '采集会话已结束，请新建会话'}, status=409)
            rows, columns = validate_rows(request.data, session.columns)
            last = session.samples.order_by('-id').first()
            previous = last.values['time'] if last else -math.inf
            for row in rows:
                if row['time'] <= previous:
                    raise ValueError('time 必须严格递增；重发或仿真重新开始时请检查时间或新建会话')
                previous = row['time']
            if not session.columns:
                session.columns = columns
                session.save(update_fields=['columns'])
            TelemetrySample.objects.bulk_create([TelemetrySample(session=session, values=row) for row in rows])
        return Response({'ok': True, 'accepted': len(rows), 'last_time': rows[-1]['time']}, status=201)
    except (ValueError, OverflowError) as exc:
        return Response({'detail': str(exc)}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def close(request, session_id):
    if not has_permission(request.user, 'manage_structure'):
        return Response({'detail': '只有管理员可以结束采集'}, status=403)
    with transaction.atomic():
        session = get_object_or_404(TelemetrySession.objects.select_for_update(), pk=session_id)
        if not session.closed_at:
            session.closed_at = timezone.now()
            session.save(update_fields=['closed_at'])
    return Response(describe(session))


class Echo:
    def write(self, value):
        return value


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export(request, session_id):
    session = get_object_or_404(TelemetrySession, pk=session_id)
    last = session.samples.order_by('-id').first()
    if not last:
        return Response({'detail': '尚无可导出的遥测数据'}, status=400)
    # Snapshot the upper cursor so an active stream cannot extend the download.
    query = session.samples.filter(id__lte=last.id).order_by('id')
    def lines():
        writer = csv.writer(Echo())
        yield '\ufeff'
        yield writer.writerow(session.columns)
        for sample in query.iterator(chunk_size=1000):
            yield writer.writerow([sample.values[k] for k in session.columns])
    response = StreamingHttpResponse(lines(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = content_disposition_header(True, f'matlab-{session.id}.csv')
    return response
