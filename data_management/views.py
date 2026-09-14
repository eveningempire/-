"""
View definitions for the data_management application.

These views expose RESTful endpoints for creating and retrieving PHMs,
initiating data import sessions and fetching raw measurement records. They
use the Django REST framework's viewsets for concise definitions.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import mixins, viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.request import Request

logger = logging.getLogger(__name__)

from .models import PHM, PHMType, Satellite, PHMModel, ImportSession, PHMData
from .serializers import (
    PHMTypeSerializer,
    SatelliteSerializer,
    PHMModelSerializer,
    PHMSerializer,
    ImportSessionSerializer,
    PHMDataSerializer,
)
from health_management.models import IMSDetectionResult
from .redis_service import redis_service, cache_database_query, get_cached_database_query
from health_management.services import (
    run_offline_anomaly_detection,
    handle_real_time_data,
)
from .tcp_server import start_tcp_ingest, stop_tcp_ingest, tcp_ingest_status, get_recent_events, get_metrics
from .realtime_cache import realtime_cache
from .batch_processing import batch_processor
from .config import get_config, set_config, get_all_config, update_config


class PHMTypeViewSet(viewsets.ModelViewSet):
    """CRUD operations for PHMType objects."""

    queryset = PHMType.objects.all()
    serializer_class = PHMTypeSerializer
    permission_classes = [AllowAny]


class SatelliteViewSet(viewsets.ModelViewSet):
    """CRUD operations for Satellite objects."""

    queryset = Satellite.objects.all()
    serializer_class = SatelliteSerializer
    permission_classes = [AllowAny]


class PHMModelViewSet(viewsets.ModelViewSet):
    """CRUD operations for PHMModel objects."""

    queryset = PHMModel.objects.select_related("cmg_type").all()
    serializer_class = PHMModelSerializer
    permission_classes = [AllowAny]


class PHMViewSet(viewsets.ModelViewSet):
    """CRUD operations for PHM objects."""

    queryset = PHM.objects.select_related("satellite", "cmg_model").all()
    serializer_class = PHMSerializer
    permission_classes = [AllowAny]


class ImportSessionViewSet(viewsets.ModelViewSet):
    """
    Handles creation and listing of data import sessions.

    On creation, if a file is provided the backend will read the file,
    persist its contents as DataRecord objects and trigger offline anomaly
    detection. For TCP imports the session represents a configuration
    placeholder; actual data ingestion is handled by a separate process.
    """

    queryset = ImportSession.objects.select_related("cmg").all()
    serializer_class = ImportSessionSerializer
    parser_classes = [MultiPartParser, FileUploadParser]
    permission_classes = [AllowAny]

    def perform_create(self, serializer: ImportSessionSerializer) -> None:
        # 澶勭悊max_rows鍙傛暟
        max_rows = self.request.data.get('max_rows')
        if max_rows:
            try:
                max_rows = int(max_rows)
                if max_rows <= 0:
                    raise ValueError("max_rows must be positive")
            except (ValueError, TypeError):
                # 濡傛灉max_rows鏃犳晥锛屽拷鐣ュ畠
                max_rows = None
        
        # 澶勭悊import_mode鍙傛暟
        import_mode = self.request.data.get('import_mode', 'IMPORT_AND_DETECT')
        if import_mode not in [ImportSession.ImportMode.IMPORT_AND_DETECT, ImportSession.ImportMode.IMPORT_ONLY]:
            import_mode = ImportSession.ImportMode.IMPORT_AND_DETECT
        
        # 澶勭悊add_milliseconds鍙傛暟
        add_milliseconds = self.request.data.get('add_milliseconds', 'true')
        if isinstance(add_milliseconds, str):
            add_milliseconds = add_milliseconds.lower() == 'true'
        else:
            add_milliseconds = bool(add_milliseconds)
        
        # Save the import session record
        session: ImportSession = serializer.save(max_rows=max_rows, import_mode=import_mode, add_milliseconds=add_milliseconds)
        # If a file was uploaded, start async processing
        if session.method == ImportSession.Method.FILE and session.file:
            try:
                from .batch_processing import batch_processor
                batch_processor.process_import_session_async(session.id)
            try:
                from .batch_processing import batch_processor
                batch_processor.process_import_session_async(session.id)
            except Exception:
                try:
                    self._handle_file_import(session)
                except Exception:
                    session.processing_status = ImportSession.ProcessingStatus.FAILED
                    session.error_message = str(e)
                    session.save(update_fields=["processing_status", "error_message"])

    def _handle_file_import(self, session: ImportSession) -> None:
        """Reads an uploaded file and stores its records.

        The actual file format is defined by the data ingestion team. This
        placeholder implementation reads JSON lines with timestamp and
        key-value pairs. Extend this function to handle your real file
        format.
        """
        import json
        import csv
        from pathlib import Path
        from openpyxl import load_workbook

        file_path = session.file.path
        data_to_create = []
        try:
            from django.utils import timezone

            def parse_ts(value: str | datetime) -> datetime:
                if isinstance(value, datetime):
                    ts = value
                else:
                    s = str(value).strip()
                    # Try ISO first (supports microseconds)
                    try:
                        ts = datetime.fromisoformat(s)
                    except Exception:
                        # Support custom format like 2024_03_25_21:07:07
                        try:
                            ts = datetime.strptime(s, "%Y_%m_%d_%H:%M:%S")
                        except Exception:
                            # Try with microseconds
                            try:
                                ts = datetime.strptime(s, "%Y_%m_%d_%H:%M:%S.%f")
                            except Exception:
                                # Replace underscores with spaces then try common format
                                try:
                                    ts = datetime.strptime(s.replace("_", " "), "%Y %m %d %H:%M:%S")
                                except Exception:
                                    # Try with microseconds
                                    try:
                                        ts = datetime.strptime(s.replace("_", " "), "%Y %m %d %H:%M:%S.%f")
                                    except Exception:
                                        raise
                if ts.tzinfo is None:
                    ts = timezone.make_aware(ts)
                return ts
            suffix = Path(file_path).suffix.lower()
            if suffix in {".json", ".ndjson"}:
                with open(file_path, "r", encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        data_dict = json.loads(line)
                        timestamp_str: str = data_dict.pop("timestamp")
                        ts = parse_ts(timestamp_str)
                        data_to_create.append(PHMData(cmg=session.cmg, timestamp=ts, data=data_dict, import_session=session))
            elif suffix == ".csv":
                with open(file_path, "r", encoding="utf-8") as fh:
                    reader = csv.reader(fh)
                    rows = list(reader)
                    if not rows:
                        return
                    headers = rows[0]
                    # 绗竴鍒椾负鏃堕棿鎴筹紝鍏朵綑鍒椾负鍙傛暟
                    param_names = headers[1:]
                    for r in rows[1:]:
                        if not r:
                            continue
                        ts = parse_ts(r[0])
                        data_dict = {}
                        for i, name in enumerate(param_names, start=1):
                            val = r[i] if i < len(r) else None
                            # 灏濊瘯鎶婃暟鍊艰浆鎹负 float锛屽惁鍒欎繚鎸佸師鏍?                            try:
                                data_dict[name] = float(val) if val not in (None, "") else None
                            except Exception:
                                data_dict[name] = val
                        data_to_create.append(PHMData(cmg=session.cmg, timestamp=ts, data=data_dict, import_session=session))
            elif suffix in {".xlsx", ".xlsm"}:
                wb = load_workbook(file_path, read_only=True)
                ws = wb.active
                rows = list(ws.iter_rows(values_only=True))
                if not rows:
                    return
                headers = list(rows[0])
                param_names = [h for h in headers[1:]]
                for r in rows[1:]:
                    if not r or r[0] is None:
                        continue
                    ts = parse_ts(r[0])
                    data_dict = {}
                    for i, name in enumerate(param_names, start=1):
                        val = r[i] if i < len(r) else None
                        try:
                            data_dict[name] = float(val) if (val is not None and val != "") else None
                        except Exception:
                            data_dict[name] = val
                    data_to_create.append(PHMData(cmg=session.cmg, timestamp=ts, data=data_dict, import_session=session))
            else:
                # 榛樿灏濊瘯鎸?CSV
                with open(file_path, "r", encoding="utf-8") as fh:
                    reader = csv.reader(fh)
                    headers = next(reader, None)
                    if headers is None:
                        return
                    param_names = headers[1:]
                    for r in reader:
                        if not r:
                            continue
                        ts = parse_ts(r[0])
                        data_dict = {}
                        for i, name in enumerate(param_names, start=1):
                            val = r[i] if i < len(r) else None
                            try:
                                data_dict[name] = float(val) if val not in (None, "") else None
                            except Exception:
                                data_dict[name] = val
                        data_to_create.append(PHMData(cmg=session.cmg, timestamp=ts, data=data_dict, import_session=session))
        except Exception:
            # Ideally log and propagate errors to the client
            return

        if data_to_create:
            # 娉ㄦ剰锛氳繖閲屼笉鍐嶈繘琛屾椂闂存埑鍘婚噸锛屽洜涓洪噸澶嶆椂闂存埑浼氬湪batch_processing.py涓€氳繃娣诲姞姣澶勭悊
            # 鐩存帴浣跨敤鎵€鏈夎В鏋愮殑鏁版嵁锛岃batch_processing.py澶勭悊鏃堕棿鎴冲敮涓€鎬?            candidate_objs = data_to_create
            # 杩囨护鏁版嵁搴撳凡瀛樺湪鐨勬椂闂存埑锛岄伩鍏嶅敮涓€绾︽潫鍐茬獊
            existing_timestamps = set(
                PHMData.objects.filter(cmg=session.cmg, timestamp__in=[o.timestamp for o in candidate_objs])
                .values_list("timestamp", flat=True)
            )
            to_create = [o for o in candidate_objs if o.timestamp not in existing_timestamps]
            if to_create:
                PHMData.objects.bulk_create(to_create, ignore_conflicts=True)
                
                # 鍚屾椂鍐欏叆瀹炴椂缂撳瓨锛堜粎瀵规渶杩戠殑鏁版嵁锛?                cache_data = [(d.timestamp, d.data) for d in to_create]
                if cache_data:
                    realtime_cache.add_batch_data(session.cmg.cmg_id, cache_data)
                
                # Best-effort algorithm processing should not break storage
                try:
                    run_offline_anomaly_detection(session.cmg, to_create)
                except Exception:
                    pass

    @action(detail=True, methods=["get"], url_path="status")
    def get_processing_status(self, request: Request, pk=None) -> Response:
        """鑾峰彇瀵煎叆浼氳瘽鐨勫鐞嗙姸鎬佸拰杩涘害"""
        try:
            session = self.get_object()
            status_data = batch_processor.get_session_status(session.id)
            if status_data:
                return Response(status_data)
            else:
                return Response({
                    'id': session.id,
                    'status': session.processing_status,
                    'progress': session.processing_progress,
                    'total_records': session.total_records,
                    'processed_records': session.processed_records,
                    'failed_records': session.failed_records,
                    'error_message': session.error_message,
                    'detection_summary': session.detection_summary
                })
        except ImportSession.DoesNotExist:
            return Response({"detail": "瀵煎叆浼氳瘽涓嶅瓨鍦?}, status=404)
        except Exception as e:
            return Response({"detail": f"鑾峰彇鐘舵€佸け璐? {str(e)}"}, status=500)

    @action(detail=True, methods=["get"], url_path="progress")
    def get_processing_progress(self, request: Request, pk=None) -> Response:
        """鑾峰彇瀵煎叆浼氳瘽鐨勫疄鏃跺鐞嗚繘搴︼紙浠嶳edis杞锛?""
        try:
            session = self.get_object()
            
            # 浠嶳edis鑾峰彇瀹炴椂杩涘害
            from .redis_service import redis_service
            redis_progress = redis_service.get_processing_progress(session.id)
            
            if redis_progress:
                # 杩斿洖Redis涓殑瀹炴椂杩涘害鏁版嵁
                return Response({
                    'session_id': session.id,
                    'progress': redis_progress.get('progress', 0.0),
                    'processed': redis_progress.get('processed', 0),
                    'total': redis_progress.get('total', 0),
                    'status': redis_progress.get('status'),
                    'message': redis_progress.get('message'),
                    'updated_at': redis_progress.get('updated_at'),
                    'source': 'redis'
                })
            else:
                # 濡傛灉Redis涓病鏈夎繘搴︽暟鎹紝杩斿洖鏁版嵁搴撲腑鐨勭姸鎬?                return Response({
                    'session_id': session.id,
                    'progress': session.processing_progress,
                    'processed': session.processed_records,
                    'total': session.total_records,
                    'status': session.processing_status,
                    'message': session.error_message,
                    'updated_at': session.updated_at.isoformat() if session.updated_at else None,
                    'source': 'database'
                })
                
        except ImportSession.DoesNotExist:
            return Response({"detail": "瀵煎叆浼氳瘽涓嶅瓨鍦?}, status=404)
        except Exception as e:
            logger.error(f"鑾峰彇杩涘害澶辫触: {e}")
            return Response({"detail": f"鑾峰彇杩涘害澶辫触: {str(e)}"}, status=500)

    @action(detail=True, methods=["post"], url_path="restart")
    def restart_processing(self, request: Request, pk=None) -> Response:
        """閲嶆柊寮€濮嬪鐞嗗鍏ヤ細璇?""
        try:
            session = self.get_object()
            
            # 妫€鏌ユ槸鍚﹀凡鍦ㄥ鐞嗕腑
            if batch_processor.is_session_active(session.id):
                return Response({"detail": "浼氳瘽姝ｅ湪澶勭悊涓?}, status=400)
            
            session.processing_status = ImportSession.ProcessingStatus.PENDING
            session.processing_progress = 0.0
            session.processed_records = 0
            session.failed_records = 0
            session.error_message = None
            session.started_at = None
            session.completed_at = None
            session.save()
            
            # 閲嶆柊寮€濮嬪紓姝ュ鐞?            batch_processor.process_import_session_async(session.id)
            
            return Response({"detail": "閲嶆柊寮€濮嬪鐞?})
            
        except ImportSession.DoesNotExist:
            return Response({"detail": "瀵煎叆浼氳瘽涓嶅瓨鍦?}, status=404)
        except Exception as e:
            return Response({"detail": f"閲嶅惎澶辫触: {str(e)}"}, status=500)


class TCPIngestViewSet(viewsets.ViewSet):
    """Control TCP ingest server from REST API."""

    permission_classes = [AllowAny]

    @action(detail=False, methods=["get"], url_path="status")
    def status(self, request: Request) -> Response:
        return Response(tcp_ingest_status())

    @action(detail=False, methods=["post"], url_path="start")
    def start(self, request: Request) -> Response:
        host = request.data.get("host", "0.0.0.0")
        port = int(request.data.get("port", 9000))
        allowed = request.data.get("allowed_cmg_ids")
        if isinstance(allowed, list) and allowed:
            allowed = [str(x) for x in allowed]
        else:
            allowed = None
        id_map = request.data.get("id_map")  # 鍙€夛細{ sender_id: platform_cmg_id }
        if not isinstance(id_map, dict):
            id_map = None
        return Response(start_tcp_ingest(host, port, allowed, id_map))

    @action(detail=False, methods=["post"], url_path="stop")
    def stop(self, request: Request) -> Response:
        return Response(stop_tcp_ingest())

    @action(detail=False, methods=["get"], url_path="events")
    def events(self, request: Request) -> Response:
        return Response({"events": get_recent_events()})

    @action(detail=False, methods=["get"], url_path="metrics")
    def metrics(self, request: Request) -> Response:
        return Response(get_metrics())


class PHMDataViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Provides read-only access to individual data records or lists filtered
    by PHM and time range.
    """

    serializer_class = PHMDataSerializer
    permission_classes = [AllowAny]

    def get_queryset(self) -> Any:
        # 鏋勫缓鏌ヨ鍙傛暟
        query_params = {
            'cmg_id': self.request.query_params.get("cmg_id"),
            'start': self.request.query_params.get("start"),
            'end': self.request.query_params.get("end"),
            'since': self.request.query_params.get("since"),
            'limit': self.request.query_params.get("limit"),
        }
        
        # 灏濊瘯浠庣紦瀛樿幏鍙栫粨鏋滐紙缂撳瓨涓瓨鐨勬槸绾瓧鍏稿垪琛紝闇€瑕佽浆涓鸿交閲忓寘瑁呭璞′緵搴忓垪鍖栧櫒璇诲彇锛?        cached_result = get_cached_database_query(query_params)
        if cached_result is not None:
            # 缂撳瓨鏁版嵁鍙兘鏄敱 JSON 搴忓垪鍖栫殑绠€鍖栫粨鏋勶紝涓嶄竴瀹氭槸 PHMData 瀹炰緥
            # 灏嗗叾鍖呰鎴愭嫢鏈夊睘鎬х殑瀵硅薄锛屼娇寰?ModelSerializer 涓嶄細鎶ラ敊
            class _PHMDataLike:
                __slots__ = ("cmg", "timestamp", "data", "import_session", "id", "created_at", "updated_at")
                def __init__(self, item: Dict[str, Any]):
                    from types import SimpleNamespace
                    cmg_val = item.get("cmg")
                    # cmg 鍙渶瑕佹槸涓€涓湁 id 鐨勫璞℃垨涓婚敭鍊硷紝杩欓噷淇濈暀鍘熷€间緵 PK 瀛楁浣跨敤
                    self.cmg = cmg_val
                    self.timestamp = item.get("timestamp")
                    self.data = item.get("data")
                    self.import_session = item.get("import_session")
                    self.id = item.get("id")
                    self.created_at = item.get("created_at")
                    self.updated_at = item.get("updated_at")
            try:
                return [_PHMDataLike(it) for it in cached_result]
            except Exception:
                # 鍥為€€锛氳嫢鍖呰澶辫触锛屽垯蹇界暐缂撳瓨
                pass
        
        # 鎵ц鏁版嵁搴撴煡璇?        qs = PHMData.objects.select_related("cmg").all()
        cmg_id = query_params['cmg_id']
        start = query_params['start']
        end = query_params['end']
        since = query_params['since']
        limit = query_params['limit']
        
        if cmg_id:
            # Filter by the PHM's user-defined identifier
            qs = qs.filter(cmg__cmg_id=cmg_id)
        def _parse_dt(value: Optional[str]) -> Optional[datetime]:
            if not value:
                return None
            dt = parse_datetime(value)
            if dt is None:
                try:
                    # 鍏煎浠?Z 缁撳熬鐨?UTC 瀛楃涓?                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except Exception:
                    return None
            if timezone.is_naive(dt):
                try:
                    dt = timezone.make_aware(dt)
                except Exception:
                    pass
            return dt

        if start:
            start_dt = _parse_dt(start)
            if start_dt:
                qs = qs.filter(timestamp__gte=start_dt)
        if end:
            end_dt = _parse_dt(end)
            if end_dt:
                qs = qs.filter(timestamp__lte=end_dt)
        has_time_filter = False
        if start:
            has_time_filter = True
        if end:
            has_time_filter = True
        if since:
            since_dt = _parse_dt(since)
            if since_dt:
                qs = qs.filter(timestamp__gt=since_dt)
                has_time_filter = True
        
        # 鎵ц鏌ヨ骞惰幏鍙栫粨鏋?        if not has_time_filter:
            try:
                default_limit = int(limit) if limit is not None else 2000
            except ValueError:
                default_limit = 2000
            # 鍙栨渶杩戠殑 default_limit 鏉★紝鐒跺悗鎸夋椂闂存搴忚繑鍥?            recent_data = list(qs.order_by("-timestamp")[:default_limit])
            recent_data.reverse()  # 杞负鏃堕棿姝ｅ簭
            result = recent_data
        else:
            # 鍘嗗彶妯″紡涓嬶紝濡傛灉鏈夋椂闂磋繃婊ゅ櫒锛岃幏鍙栨墍鏈夋暟鎹?            # 浣嗕负浜嗛伩鍏嶅唴瀛橀棶棰橈紝璁剧疆涓€涓悎鐞嗙殑涓婇檺
            try:
                max_limit = int(limit) if limit is not None else 5000000
            except ValueError:
                max_limit = 5000000
            
            # 瀵逛簬澶ф暟鎹泦锛屼娇鐢ㄦ洿楂樻晥鐨勫垎鎵瑰鐞?            if max_limit > 100000:
                # 鍒嗘壒鑾峰彇鏁版嵁锛岄伩鍏嶄竴娆℃€у姞杞借繃澶氭暟鎹埌鍐呭瓨
                result = []
                batch_size = 100000
                offset = 0
                
                while offset < max_limit:
                    batch = list(qs.order_by("timestamp")[offset:offset + batch_size])
                    if not batch:
                        break
                    result.extend(batch)
                    offset += batch_size
                    
                    # 濡傛灉宸茬粡鑾峰彇浜嗚冻澶熺殑鏁版嵁锛屽仠姝?                    if len(result) >= max_limit:
                        result = result[:max_limit]
                        break
            else:
                # 瀵逛簬杈冨皬鐨勬暟鎹泦锛岀洿鎺ヨ幏鍙?                result = list(qs.order_by("timestamp")[:max_limit])
        
        # 缂撳瓨缁撴灉锛堣緝灏忕殑鏁版嵁闆嗙紦瀛樻洿闀挎椂闂达級
        cache_ttl = 2 if len(result) > 1000 else 5  # 鍒嗛挓
        cache_database_query(query_params, result, cache_ttl)
        
        return result

    @action(detail=False, methods=["post"], url_path="real-time")
    def handle_real_time(self, request: Request) -> Response:
        """
        Endpoint for streaming real-time data into the system.

        The request body should contain the PHM identifier and a list of
        timestamped records. For each incoming record this method triggers
        real-time anomaly detection. The implementation calls into
        ``handle_real_time_data`` defined in ``health_management.services``.
        """
        data: Dict[str, Any] = request.data
        cmg_id: Optional[str] = data.get("cmg_id")
        records = data.get("records", [])
        if not cmg_id or not records:
            return Response({"detail": "cmg_id and records are required"}, status=400)
        try:
            cmg = PHM.objects.get(cmg_id=cmg_id)
        except PHM.DoesNotExist:
            return Response({"detail": f"PHM {cmg_id} not found"}, status=404)
        handle_real_time_data(cmg, records)
        return Response({"detail": "Data processed"})

    @action(detail=False, methods=["post"], url_path="delete-range")
    def delete_range(self, request: Request) -> Response:
        """Delete data for a PHM, optionally within a time range."""
        cmg_id = request.data.get("cmg_id")
        start = request.data.get("start")
        end = request.data.get("end")
        if not cmg_id:
            return Response({"detail": "cmg_id is required"}, status=400)
        try:
            cmg = PHM.objects.get(cmg_id=cmg_id)
        except PHM.DoesNotExist:
            return Response({"detail": "PHM not found"}, status=404)
        qs = PHMData.objects.filter(cmg=cmg)
        try:
            if start:
                qs = qs.filter(timestamp__gte=datetime.fromisoformat(start))
            if end:
                qs = qs.filter(timestamp__lte=datetime.fromisoformat(end))
        except ValueError:
            return Response({"detail": "Invalid datetime format"}, status=400)
        deleted, _ = qs.delete()
        
        # 濡傛灉鍒犻櫎浜嗘墍鏈夋暟鎹紝娓呯┖瀵瑰簲鐨勫疄鏃剁紦瀛?        if not start and not end:
            realtime_cache.clear_cmg_cache(cmg_id)
            redis_service.clear_cmg_cache(cmg_id)
        
        # 鏇存柊缁熻淇℃伅
        if deleted > 0:
            try:
                from .models import DatabaseStatistics
                # 鏇存柊PHM鏁版嵁缁熻
                DatabaseStatistics.update_statistics('cmg_data', cmg)
                DatabaseStatistics.update_statistics('total_frames', cmg)
                # 鏇存柊鍏ㄥ眬缁熻
                DatabaseStatistics.update_statistics('cmg_data')
                DatabaseStatistics.update_statistics('total_frames')
                # 鐢变簬鍒犻櫎浜嗘暟鎹紝鐩稿叧鐨勬娴嬬粨鏋滀篃浼氳绾ц仈鍒犻櫎锛岄渶瑕佹洿鏂版娴嬬粨鏋滅粺璁?                DatabaseStatistics.update_statistics('ims_results', cmg)
                DatabaseStatistics.update_statistics('rule_results', cmg)
                DatabaseStatistics.update_statistics('msfg_results', cmg)
                DatabaseStatistics.update_statistics('anomaly_frames', cmg)
                DatabaseStatistics.update_statistics('ims_results')
                DatabaseStatistics.update_statistics('rule_results')
                DatabaseStatistics.update_statistics('msfg_results')
                DatabaseStatistics.update_statistics('anomaly_frames')
            except Exception as e:
                logger.error(f"鏇存柊缁熻淇℃伅澶辫触: {e}")
        
        return Response({"deleted": deleted})

    @action(detail=False, methods=["get"], url_path="realtime")
    def get_realtime_data(self, request: Request) -> Response:
        """鑾峰彇瀹炴椂缂撳瓨鏁版嵁锛屼紭鍏堜粠Redis鑾峰彇"""
        cmg_id = request.query_params.get("cmg_id")
        since_ms = request.query_params.get("since_ms")
        limit = int(request.query_params.get("limit", 1000))
        
        if not cmg_id:
            return Response({"error": "cmg_id is required"}, status=400)
        
        try:
            since_ms = int(since_ms) if since_ms else None
        except (ValueError, TypeError):
            since_ms = None
        
        # 浼樺厛浠嶳edis鑾峰彇鏁版嵁
        data = redis_service.get_realtime_data(cmg_id, since_ms, limit)
        
        # 濡傛灉Redis涓病鏈夋暟鎹紝灏濊瘯浠庡唴瀛樼紦瀛樿幏鍙?        if not data:
            data = realtime_cache.get_recent_data(cmg_id, since_ms, limit)
        
        # 濡傛灉缂撳瓨涓病鏈夋暟鎹垨鏁版嵁涓嶈冻锛屼粠鏁版嵁搴撹ˉ鍏?        if len(data) < limit and since_ms is None:
            db_limit = limit - len(data)
            db_data = list(
                PHMData.objects.filter(cmg__cmg_id=cmg_id)
                .order_by('-timestamp')[:db_limit]
                .values('timestamp', 'data')
            )
            
            # 杞崲鏍煎紡骞跺悎骞?            db_formatted = [
                {
                    'timestamp': record['timestamp'].isoformat(),
                    'data': record['data']
                }
                for record in reversed(db_data)
            ]
            
            # 鍘婚噸鍚堝苟锛堜紭鍏堜娇鐢ㄧ紦瀛樻暟鎹級
            cache_timestamps = {item['timestamp'] for item in data}
            for item in db_formatted:
                if item['timestamp'] not in cache_timestamps:
                    data.append(item)
        
        return Response(data)

    @action(detail=False, methods=["get"], url_path="count")
    def get_count(self, request: Request) -> Response:
        """鑾峰彇鏁版嵁璁板綍鎬绘暟"""
        cmg_id = request.query_params.get("cmg_id")
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        
        # 鐩存帴鏌ヨ鏁版嵁搴擄紝涓嶅彈缂撳瓨鍜宭imit闄愬埗
        qs = PHMData.objects.all()
        
        if cmg_id:
            qs = qs.filter(cmg__cmg_id=cmg_id)
        
        if start:
            try:
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                qs = qs.filter(timestamp__gte=start_dt)
            except ValueError:
                pass
        
        if end:
            try:
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                qs = qs.filter(timestamp__lte=end_dt)
            except ValueError:
                pass
        
        count = qs.count()
        return Response({"count": count})

    @action(detail=False, methods=["get"], url_path="statistics")
    def get_statistics(self, request: Request) -> Response:
        """鑾峰彇鏁版嵁搴撶粺璁′俊鎭?- 瀹炴椂璁＄畻"""
        cmg_id = request.query_params.get('cmg_id')
        force_refresh = request.query_params.get('refresh', 'false').lower() == 'true'
        
        try:
            from .models import DatabaseStatistics
            
            if force_refresh:
                # 寮哄埗鍒锋柊缁熻淇℃伅
                if cmg_id:
                    cmg = PHM.objects.get(cmg_id=cmg_id)
                    DatabaseStatistics.update_statistics('cmg_data', cmg)
                    DatabaseStatistics.update_statistics('ims_results', cmg)
                    DatabaseStatistics.update_statistics('rule_results', cmg)
                    DatabaseStatistics.update_statistics('msfg_results', cmg)
                    DatabaseStatistics.update_statistics('anomaly_frames', cmg)
                    DatabaseStatistics.update_statistics('total_frames', cmg)
                    stats = DatabaseStatistics.get_statistics(cmg)
                else:
                    DatabaseStatistics.refresh_all_statistics()
                    stats = DatabaseStatistics.get_statistics()
            else:
                # 鑾峰彇缂撳瓨鐨勭粺璁′俊鎭?                if cmg_id:
                    cmg = PHM.objects.get(cmg_id=cmg_id)
                    stats = DatabaseStatistics.get_statistics(cmg)
                else:
                    stats = DatabaseStatistics.get_statistics()
            
            return Response({
                "statistics": stats,
                "cmg_id": cmg_id,
                "timestamp": timezone.now().isoformat(),
                "refreshed": force_refresh
            })
        except PHM.DoesNotExist:
            return Response({"error": "PHM not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
    
    @action(detail=False, methods=["post"], url_path="refresh-statistics")
    def refresh_statistics(self, request: Request) -> Response:
        """鍒锋柊鏁版嵁搴撶粺璁′俊鎭?""
        try:
            from .models import DatabaseStatistics
            DatabaseStatistics.refresh_all_statistics()
            return Response({
                "message": "缁熻淇℃伅宸插埛鏂?,
                "timestamp": timezone.now().isoformat()
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=["get"], url_path="cache-stats")
    def get_cache_stats(self, request: Request) -> Response:
        """鑾峰彇瀹炴椂缂撳瓨缁熻淇℃伅"""
        memory_stats = realtime_cache.get_cache_stats()
        redis_stats = redis_service.get_cache_info()
        
        return Response({
            'memory_cache': memory_stats,
            'redis_cache': redis_stats,
            'cache_health': {
                'redis_connected': redis_stats.get('redis_connected', False),
                'total_keys': redis_stats.get('keys_count', {}).get('total', 0),
                'memory_usage': redis_stats.get('memory_used', '0B')
            }
        })

    @action(detail=False, methods=["post"], url_path="clear-cache")
    def clear_cache(self, request: Request) -> Response:
        """娓呯┖鎸囧畾PHM鐨勭紦瀛?""
        cmg_id = request.data.get("cmg_id")
        if not cmg_id:
            return Response({"error": "cmg_id is required"}, status=400)
        
        # 娓呯┖鍐呭瓨缂撳瓨
        realtime_cache.clear_cmg_cache(cmg_id)
        
        # 娓呯┖Redis缂撳瓨
        success = redis_service.clear_cmg_cache(cmg_id)
        
        return Response({
            "message": f"Cache cleared for PHM {cmg_id}",
            "redis_success": success
        })

    
class SystemConfigViewSet(viewsets.ViewSet):
    """绯荤粺閰嶇疆绠＄悊瑙嗗浘闆?""
    
    permission_classes = [AllowAny]
    
    def list(self, request):
        """鑾峰彇鎵€鏈夐厤缃?""
        config = get_all_config()
        return Response({
            'config': config,
            'descriptions': {
                'streaming_threshold': '娴佸紡澶勭悊瑙﹀彂闃堝€硷紙甯ф暟锛?,
                'batch_size': '姣忔壒澶勭悊甯ф暟',
                'batch_size_for_save': '鎵归噺淇濆瓨鐨勬壒娆″ぇ灏?,
                'detection_frequency': '妫€娴嬮鐜囨帶鍒堕厤缃?
            },
            'limits': {
                'streaming_threshold': {
                    'min': 100,
                    'max': 1000000,
                    'step': 1000,
                    'unit': '甯?
                },
                'batch_size': {
                    'min': 50,
                    'max': 50000,
                    'step': 100,
                    'unit': '甯?
                },
                'batch_size_for_save': {
                    'min': 100,
                    'max': 50000,
                    'step': 500,
                    'unit': '鏉?
                }
            }
        })
    
    @action(detail=False, methods=['put', 'patch'], url_path='update')
    def update_config(self, request):
        """鏇存柊閰嶇疆"""
        config_data = request.data.get('config', {})
        if not config_data:
            return Response({'error': '閰嶇疆鏁版嵁涓嶈兘涓虹┖'}, status=400)
        
        try:
            # 楠岃瘉閰嶇疆鍊?            # 瀹氫箟鍚勫弬鏁扮殑鍚堢悊鑼冨洿锛堜笌鍓嶇淇濇寔涓€鑷达級
            PARAM_LIMITS = {
                'streaming_threshold': {'min': 100, 'max': 1000000},
                'batch_size': {'min': 50, 'max': 50000},
                'batch_size_for_save': {'min': 100, 'max': 50000}
            }
            
            for key, value in config_data.items():
                if key in ['streaming_threshold', 'batch_size', 'batch_size_for_save']:
                    if not isinstance(value, int):
                        return Response({'error': f'{key} 蹇呴』鏄暣鏁?}, status=400)
                    
                    limits = PARAM_LIMITS[key]
                    if value < limits['min'] or value > limits['max']:
                        return Response({
                            'error': f'{key} 蹇呴』鍦?{limits["min"]} 鍒?{limits["max"]} 涔嬮棿'
                        }, status=400)
                elif key == 'detection_frequency':
                    # 楠岃瘉妫€娴嬮鐜囬厤缃?                    if not isinstance(value, dict):
                        return Response({'error': 'detection_frequency 蹇呴』鏄璞?}, status=400)
                    
                    # 楠岃瘉鍩烘湰瀛楁
                    if 'enabled' in value and not isinstance(value['enabled'], bool):
                        return Response({'error': 'detection_frequency.enabled 蹇呴』鏄竷灏斿€?}, status=400)
                    
                    if 'mode' in value and value['mode'] not in ['high_frequency', 'medium_frequency', 'low_frequency', 'adaptive', 'disabled']:
                        return Response({'error': 'detection_frequency.mode 蹇呴』鏄湁鏁堢殑妯″紡'}, status=400)
                    
                    # 楠岃瘉鍚勬ā寮忕殑闂撮殧璁剧疆
                    for mode in ['high_frequency', 'medium_frequency', 'low_frequency']:
                        if mode in value and isinstance(value[mode], dict):
                            interval = value[mode].get('interval_seconds')
                            if interval is not None and (not isinstance(interval, int) or interval <= 0):
                                return Response({'error': f'detection_frequency.{mode}.interval_seconds 蹇呴』鏄鏁存暟'}, status=400)
                    
                    # 楠岃瘉鑷€傚簲妯″紡璁剧疆
                    if 'adaptive' in value and isinstance(value['adaptive'], dict):
                        adaptive = value['adaptive']
                        for field in ['small_dataset_threshold', 'medium_dataset_threshold', 'large_dataset_threshold']:
                            if field in adaptive and (not isinstance(adaptive[field], int) or adaptive[field] <= 0):
                                return Response({'error': f'detection_frequency.adaptive.{field} 蹇呴』鏄鏁存暟'}, status=400)
                        
                        for field in ['small_dataset_interval', 'medium_dataset_interval', 'large_dataset_interval']:
                            if field in adaptive and (not isinstance(adaptive[field], int) or adaptive[field] <= 0):
                                return Response({'error': f'detection_frequency.adaptive.{field} 蹇呴』鏄鏁存暟'}, status=400)
            
            # 鏇存柊閰嶇疆
            update_config(config_data)
            
            return Response({
                'message': '閰嶇疆鏇存柊鎴愬姛',
                'config': get_all_config()
            })
        except Exception as e:
            return Response({'error': f'閰嶇疆鏇存柊澶辫触: {str(e)}'}, status=500)
    
    @action(detail=False, methods=['post'], url_path='reset')
    def reset(self, request):
        """閲嶇疆涓洪粯璁ら厤缃?""
        try:
            from .config import system_config
            system_config.reset_to_default()
            return Response({
                'message': '閰嶇疆宸查噸缃负榛樿鍊?,
                'config': get_all_config()
            })
        except Exception as e:
            return Response({'error': f'閲嶇疆閰嶇疆澶辫触: {str(e)}'}, status=500)


class DetectionOverviewView(APIView):
    """涓烘娴嬬粨鏋滄€昏椤甸潰鎻愪緵涓撻棬鐨凙PI鎺ュ彛"""
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """鑾峰彇妫€娴嬬粨鏋滄€昏椤甸潰鐨勬暟鎹?""
        action = request.query_params.get("action")
        
        if action == "cmg_models":
            return self._get_cmg_models()
        elif action == "cmg_individuals":
            return self._get_cmg_individuals(request)
        elif action == "cmg_timeline":
            return self._get_cmg_timeline(request)
        elif action == "anomaly_results":
            return self._get_anomaly_results(request)
        elif action == "ims_details":
            return self._get_ims_details(request)
        elif action == "rule_details":
            return self._get_rule_details(request)
        elif action == "msfg_details":
            return self._get_msfg_details(request)
        elif action == "telemetry_data":
            return self._get_telemetry_data(request)
        elif action == "test":
            return self._test_api(request)
        elif action == "component_scores":
            return self._get_component_scores(request)
        elif action == "lifetime_trend":
            return self._get_lifetime_trend(request)
        elif action == "component_details":
            return self._get_component_details(request)
        elif action == "latest_msfg_health":
            return self._get_latest_msfg_health(request)
        else:
            return Response({"error": "Invalid action. Use 'cmg_models', 'cmg_individuals', 'cmg_timeline', 'anomaly_results', 'ims_details', 'rule_details', 'msfg_details', 'telemetry_data', 'test', 'component_scores', 'lifetime_trend', 'component_details', or 'latest_msfg_health'"}, status=400)

    def _get_cmg_models(self) -> Response:
        """鑾峰彇鎵€鏈塁MG鍨嬪彿渚涚敤鎴烽€夋嫨"""
        try:
            # 鑾峰彇鎵€鏈夋椿璺冪殑PHM鍨嬪彿锛屾寜鍨嬪彿鍚嶇О鎺掑簭
            cmg_models = PHMModel.objects.filter(
                is_active=True,
                is_hidden=False
            ).order_by('model_name').values(
                'id', 'model_name', 'description', 'is_default'
            )
            
            return Response({
                "cmg_models": list(cmg_models),
                "total_count": len(cmg_models)
            })
        except Exception as e:
            logger.error(f"鑾峰彇PHM鍨嬪彿澶辫触: {e}")
            return Response({"error": "鑾峰彇PHM鍨嬪彿澶辫触"}, status=500)

    def _get_cmg_individuals(self, request: Request) -> Response:
        """鏍规嵁PHM鍨嬪彿鑾峰彇鎵€鏈塁MG涓綋"""
        cmg_model_id = request.query_params.get("cmg_model_id")
        
        if not cmg_model_id:
            return Response({"error": "cmg_model_id is required"}, status=400)
        
        try:
            # 楠岃瘉PHM鍨嬪彿鏄惁瀛樺湪
            try:
                cmg_model = PHMModel.objects.get(id=cmg_model_id)
            except PHMModel.DoesNotExist:
                return Response({"error": "PHM鍨嬪彿涓嶅瓨鍦?}, status=404)
            
            # 鑾峰彇璇ュ瀷鍙蜂笅鐨勬墍鏈塁MG涓綋锛屾寜鍚嶇О鎺掑簭
            # 浣跨敤cmg_model_id杩涜绛涢€夛紝杩欐槸Django ORM鐨勬爣鍑嗗仛娉?            cmg_individuals = PHM.objects.filter(
                cmg_model_id=cmg_model_id,  # 浣跨敤澶栭敭ID杩涜绛涢€?                enabled=True
            ).select_related('cmg_model').order_by('name').values(
                'id', 'cmg_id', 'name', 'enabled', 'cmg_model_id', 'cmg_model__model_name'
            )
            
            return Response({
                "cmg_individuals": list(cmg_individuals),
                "cmg_model": {
                    "id": cmg_model.id,
                    "model_name": cmg_model.model_name,
                    "description": cmg_model.description
                },
                "total_count": len(cmg_individuals)
            })
        except Exception as e:
            logger.error(f"鑾峰彇PHM涓綋澶辫触: {e}")
            return Response({"error": "鑾峰彇PHM涓綋澶辫触"}, status=500)

    def _get_cmg_timeline(self, request: Request) -> Response:
        """鑾峰彇PHM涓綋鐨勬椂闂磋酱鏁版嵁"""
        cmg_id = request.query_params.get("cmg_id")
        
        logger.info(f"鏃堕棿杞磋姹?- cmg_id: {cmg_id}, 绫诲瀷: {type(cmg_id)}")
        
        if not cmg_id:
            logger.error("cmg_id鍙傛暟缂哄け")
            return Response({"error": "cmg_id is required"}, status=400)
        
        try:
            # 楠岃瘉PHM涓綋鏄惁瀛樺湪 - 浣跨敤鏁版嵁搴揑D鏌ユ壘
            try:
                cmg = PHM.objects.get(id=cmg_id)
                logger.info(f"鎵惧埌PHM涓綋 - 鏁版嵁搴揑D: {cmg.id}, 鍚嶇О: {cmg.cmg_id}")
            except PHM.DoesNotExist:
                logger.error(f"PHM涓綋涓嶅瓨鍦? {cmg_id}")
                return Response({"error": "PHM涓綋涓嶅瓨鍦?}, status=404)
            
            # 鑾峰彇璇MG涓綋鐨勬墍鏈夋暟鎹椂闂存埑
            # 鐩存帴浣跨敤鏁版嵁搴揑D鍖归厤PHMData琛ㄤ腑鐨刢mg_id瀛楁
            timestamps = PHMData.objects.filter(
                cmg_id=cmg_id  # 浣跨敤鏁版嵁搴揑D鐩存帴鍖归厤
            ).order_by('timestamp').values_list('timestamp', flat=True)
            
            logger.info(f"鎵惧埌 {len(timestamps)} 鏉℃椂闂存埑鏁版嵁")
            
            if not timestamps:
                return Response({
                    "cmg_id": cmg.cmg_id,
                    "cmg_name": cmg.name,
                    "timeline": [],
                    "total_count": 0,
                    "time_range": None
                })
            
            # 璁＄畻鏃堕棿鑼冨洿
            start_time = timestamps[0]
            end_time = timestamps[len(timestamps) - 1]
            
            # 鐢熸垚鏃堕棿杞存暟鎹紙姣?00涓椂闂存埑鍙栦竴涓牱鏈紝閬垮厤鏁版嵁杩囧锛?            timeline_data = []
            step = max(1, len(timestamps) // 100)  # 鏈€澶?00涓偣
            
            for i in range(0, len(timestamps), step):
                timeline_data.append({
                    "timestamp": timestamps[i].isoformat(),
                    "index": i
                })
            
            # 纭繚鍖呭惈鏈€鍚庝竴涓椂闂存埑
            if len(timestamps) - 1 not in [item["index"] for item in timeline_data]:
                timeline_data.append({
                    "timestamp": timestamps[len(timestamps) - 1].isoformat(),
                    "index": len(timestamps) - 1
                })
            
            return Response({
                "cmg_id": cmg.cmg_id,
                "cmg_name": cmg.name,
                "timeline": timeline_data,
                "total_count": len(timestamps),
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            })
        except Exception as e:
            logger.error(f"鑾峰彇PHM鏃堕棿杞村け璐? {e}")
            return Response({"error": "鑾峰彇PHM鏃堕棿杞村け璐?}, status=500)

    def _get_anomaly_results(self, request: Request) -> Response:
        """鑾峰彇PHM涓綋鐨勫紓甯告娴嬬粨鏋?""
        cmg_id = request.query_params.get("cmg_id")
        start_time = request.query_params.get("start_time")
        end_time = request.query_params.get("end_time")
        
        logger.info(f"寮傚父妫€娴嬬粨鏋滆姹?- cmg_id: {cmg_id}, start_time: {start_time}, end_time: {end_time}")
        
        if not cmg_id:
            logger.error("cmg_id鍙傛暟缂哄け")
            return Response({"error": "cmg_id is required"}, status=400)
        
        if not start_time or not end_time:
            logger.error("鏃堕棿鍙傛暟缂哄け")
            return Response({"error": "start_time and end_time are required"}, status=400)
        
        try:
            # 楠岃瘉PHM涓綋鏄惁瀛樺湪
            try:
                cmg = PHM.objects.get(id=cmg_id)
                logger.info(f"鎵惧埌PHM涓綋 - 鏁版嵁搴揑D: {cmg.id}, 鍚嶇О: {cmg.cmg_id}")
            except PHM.DoesNotExist:
                logger.error(f"PHM涓綋涓嶅瓨鍦? {cmg_id}")
                return Response({"error": "PHM涓綋涓嶅瓨鍦?}, status=404)
            
            # 瑙ｆ瀽鏃堕棿鍙傛暟
            try:
                from datetime import datetime
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError as e:
                logger.error(f"鏃堕棿鏍煎紡閿欒: {e}")
                return Response({"error": "Invalid time format"}, status=400)
            
            # 鑾峰彇鎸囧畾鏃堕棿鑼冨洿鍐呯殑鎵€鏈夋暟鎹?            total_frames = PHMData.objects.filter(
                cmg_id=cmg_id,
                timestamp__gte=start_dt,
                timestamp__lte=end_dt
            ).count()
            
            # 鑾峰彇寮傚父妫€娴嬬粨鏋?            from health_management.models import IMSDetectionResult
            anomaly_results = IMSDetectionResult.objects.filter(
                data_point__cmg_id=cmg_id,
                data_point__timestamp__gte=start_dt,
                data_point__timestamp__lte=end_dt,
                is_anomaly=True
            ).select_related('data_point').order_by('-data_point__timestamp')
            
            # 鏍煎紡鍖栧紓甯稿抚鏁版嵁
            anomaly_frames = []
            for result in anomaly_results:
                # 鎻愬彇寮傚父閬ユ祴閲忥紙鍙傛暟鍒嗘暟楂樹簬闃堝€肩殑鍙傛暟锛?                abnormal_params = []
                if result.parameter_scores:
                    # 鎸夊垎鏁颁粠楂樺埌浣庢帓搴忥紝鍙栧墠5涓紓甯稿弬鏁?                    sorted_params = sorted(
                        result.parameter_scores.items(), 
                        key=lambda x: x[1], 
                        reverse=True
                    )
                    # 鍙€夋嫨鍒嗘暟>0.3鐨勫弬鏁帮紙琛ㄧず寮傚父锛?                    abnormal_params = [
                        param for param, score in sorted_params[:5] 
                        if score > 0.3
                    ]
                
                anomaly_frames.append({
                    'id': result.id,
                    'timestamp': result.data_point.timestamp.isoformat(),
                    'score': result.anomaly_score,
                    'data_point_id': result.data_point.id,
                    'abnormal_parameters': abnormal_params  # 鏂板锛氬紓甯搁仴娴嬮噺鍒楄〃
                })
            
            # 璁＄畻寮傚父甯ф瘮渚?            anomaly_ratio = len(anomaly_frames) / total_frames if total_frames > 0 else 0
            
            logger.info(f"鎵惧埌 {total_frames} 鏉℃€绘暟鎹紝{len(anomaly_frames)} 鏉″紓甯告暟鎹紝寮傚父姣斾緥: {anomaly_ratio:.4f}")
            
            return Response({
                "cmg_id": cmg.cmg_id,
                "cmg_name": cmg.name,
                "time_range": {
                    "start": start_time,
                    "end": end_time
                },
                "total_frames": total_frames,
                "anomaly_frames": anomaly_frames,
                "anomaly_count": len(anomaly_frames),
                "anomaly_ratio": anomaly_ratio
            })
            
        except Exception as e:
            logger.error(f"鑾峰彇寮傚父妫€娴嬬粨鏋滃け璐? {e}")
            return Response({"error": "鑾峰彇寮傚父妫€娴嬬粨鏋滃け璐?}, status=500)

    def _get_ims_details(self, request: Request) -> Response:
        """鑾峰彇鍗曚釜寮傚父甯х殑IMS妫€娴嬭鎯?""
        frame_id = request.query_params.get("frame_id")
        
        logger.info(f"IMS妫€娴嬭鎯呰姹?- frame_id: {frame_id}")
        
        if not frame_id:
            logger.error("frame_id鍙傛暟缂哄け")
            return Response({"error": "frame_id is required"}, status=400)
        
        try:
            # 鑾峰彇IMS妫€娴嬬粨鏋?            from health_management.models import IMSDetectionResult
            ims_result = IMSDetectionResult.objects.select_related(
                'data_point__cmg',
                'ims_model'
            ).get(id=frame_id)
            
            logger.info(f"鎵惧埌IMS妫€娴嬬粨鏋?- ID: {ims_result.id}, PHM: {ims_result.data_point.cmg.cmg_id}")
            
            return Response({
                "frame_id": frame_id,
                "timestamp": ims_result.data_point.timestamp.isoformat(),
                "cmg_id": ims_result.data_point.cmg.cmg_id,
                "cmg_name": ims_result.data_point.cmg.name,
                "ims": {
                    "model_name": ims_result.ims_model.name,
                    "is_anomaly": ims_result.is_anomaly,
                    "anomaly_score": ims_result.anomaly_score,
                    "parameter_scores": ims_result.parameter_scores,
                    "detection_details": ims_result.detection_details
                }
            })
            
        except IMSDetectionResult.DoesNotExist:
            logger.error(f"IMS妫€娴嬬粨鏋滀笉瀛樺湪: {frame_id}")
            return Response({"error": "寮傚父甯т笉瀛樺湪"}, status=404)
        except Exception as e:
            logger.error(f"鑾峰彇IMS妫€娴嬭鎯呭け璐? {e}")
            return Response({"error": "鑾峰彇IMS妫€娴嬭鎯呭け璐?}, status=500)

    def _get_rule_details(self, request: Request) -> Response:
        """鑾峰彇鍗曚釜寮傚父甯х殑瑙勫垯妫€娴嬬粨鏋?""
        frame_id = request.query_params.get("frame_id")
        
        logger.info(f"瑙勫垯妫€娴嬭鎯呰姹?- frame_id: {frame_id}")
        
        if not frame_id:
            logger.error("frame_id鍙傛暟缂哄け")
            return Response({"error": "frame_id is required"}, status=400)
        
        try:
            # 鑾峰彇IMS妫€娴嬬粨鏋滀互鑾峰彇瀵瑰簲鐨勬暟鎹偣
            from health_management.models import IMSDetectionResult
            ims_result = IMSDetectionResult.objects.select_related('data_point').get(id=frame_id)
            data_point_id = ims_result.data_point.id
            
            logger.info(f"鎵惧埌IMS妫€娴嬬粨鏋?- ID: {ims_result.id}, 鏁版嵁鐐笽D: {data_point_id}")
            
            # 鑾峰彇瑙勫垯妫€娴嬬粨鏋?            from rule_detection.models import RuleDetectionResult
            rule_results = RuleDetectionResult.objects.filter(
                data_point_id=data_point_id
            ).select_related('rule_definition__fault_definition').order_by('-confidence_score')
            
            logger.info(f"涓烘暟鎹偣 {data_point_id} 鎵惧埌 {len(rule_results)} 鏉¤鍒欐娴嬬粨鏋?)
            
            # 鏍煎紡鍖栬鍒欐娴嬬粨鏋?            rule_details = []
            for rule_result in rule_results:
                try:
                    fault_def = rule_result.rule_definition.fault_definition
                    rule_details.append({
                        'id': rule_result.id,
                        'name': rule_result.rule_definition.rule_id,
                        'confidence': rule_result.confidence_score,
                        'status': '宸茶Е鍙? if rule_result.is_triggered else '鏈Е鍙?,
                        'is_triggered': rule_result.is_triggered,
                        'rule_id': rule_result.rule_definition.rule_id,
                        'rule_expression': rule_result.rule_definition.rule_expression,
                        'fault_name': fault_def.fault_name if fault_def else '鏈煡鏁呴殰',
                        'fault_level': fault_def.fault_level if fault_def else 'N/A',
                        'related_parameters': rule_result.rule_definition.related_parameters
                    })
                except Exception as e:
                    logger.error(f"澶勭悊瑙勫垯缁撴灉 {rule_result.id} 鏃跺嚭閿? {e}")
                    continue
            
            return Response({
                "frame_id": frame_id,
                "timestamp": ims_result.data_point.timestamp.isoformat(),
                "cmg_id": ims_result.data_point.cmg.cmg_id,
                "rules": rule_details
            })
            
        except IMSDetectionResult.DoesNotExist:
            logger.error(f"IMS妫€娴嬬粨鏋滀笉瀛樺湪: {frame_id}")
            return Response({"error": "寮傚父甯т笉瀛樺湪"}, status=404)
        except Exception as e:
            logger.error(f"鑾峰彇瑙勫垯妫€娴嬭鎯呭け璐? {e}")
            return Response({"error": "鑾峰彇瑙勫垯妫€娴嬭鎯呭け璐?}, status=500)

    def _get_msfg_details(self, request: Request) -> Response:
        """鑾峰彇鍗曚釜寮傚父甯х殑MSFG妫€娴嬬粨鏋?""
        frame_id = request.query_params.get("frame_id")
        
        logger.info(f"MSFG妫€娴嬭鎯呰姹?- frame_id: {frame_id}")
        
        if not frame_id:
            logger.error("frame_id鍙傛暟缂哄け")
            return Response({"error": "frame_id is required"}, status=400)
        
        try:
            # 鑾峰彇IMS妫€娴嬬粨鏋滀互鑾峰彇瀵瑰簲鐨勬暟鎹偣
            from health_management.models import IMSDetectionResult
            ims_result = IMSDetectionResult.objects.select_related('data_point').get(id=frame_id)
            data_point_id = ims_result.data_point.id
            
            logger.info(f"鎵惧埌IMS妫€娴嬬粨鏋?- ID: {ims_result.id}, 鏁版嵁鐐笽D: {data_point_id}")
            
            # 鑾峰彇MSFG鍒嗘瀽缁撴灉
            from msfg_analysis.models import MSFGAnalysisResult
            msfg_result = MSFGAnalysisResult.objects.filter(
                data_point_id=data_point_id
            ).select_related('msfg_definition').first()
            
            if not msfg_result:
                logger.warning(f"鏈壘鍒版暟鎹偣 {data_point_id} 鐨凪SFG鍒嗘瀽缁撴灉")
                return Response({
                    "frame_id": frame_id,
                    "timestamp": ims_result.data_point.timestamp.isoformat(),
                    "cmg_id": ims_result.data_point.cmg.cmg_id,
                    "msfg": None
                })
            
            logger.info(f"鎵惧埌MSFG鍒嗘瀽缁撴灉 - ID: {msfg_result.id}")
            
            # 浠巆omponent_results瀛楁涓彁鍙栭儴浠跺垎鏁?            component_results = msfg_result.component_results or {}
            logger.info(f"MSFG鍒嗘瀽缁撴灉ID: {msfg_result.id}")
            logger.info(f"MSFG瀹氫箟: {msfg_result.msfg_definition.name}")
            logger.info(f"鏁翠綋鍋ュ悍鍒嗘暟: {msfg_result.overall_health_score}")
            logger.info(f"component_results瀛楁绫诲瀷: {type(component_results)}")
            logger.info(f"component_results瀛楁鍐呭: {component_results}")
            logger.info(f"component_results瀛楁闀垮害: {len(component_results) if isinstance(component_results, dict) else 'N/A'}")
            
            # 鎻愬彇鎵€鏈夐儴浠跺強鍏跺垎鏁帮紝骞舵帓搴忔壘鍑哄垎鏁版渶浣庣殑涓変釜
            component_scores = []
            if isinstance(component_results, dict):
                for component_name, score_data in component_results.items():
                    logger.info(f"澶勭悊閮ㄤ欢: {component_name}, 鏁版嵁绫诲瀷: {type(score_data)}, 鏁版嵁鍐呭: {score_data}")
                    try:
                        # 澶勭悊涓嶅悓鐨勬暟鎹牸寮?                        if isinstance(score_data, dict):
                            # 濡傛灉score_data鏄瓧鍏革紝灏濊瘯鑾峰彇鍒嗘暟
                            score = score_data.get('score', score_data.get('health_score', 0.0))
                            logger.info(f"浠庡瓧鍏镐腑鎻愬彇鍒嗘暟: {score}")
                        elif isinstance(score_data, (int, float)):
                            # 濡傛灉score_data鐩存帴鏄暟瀛?                            score = float(score_data)
                            logger.info(f"鐩存帴浣跨敤鏁板瓧鍒嗘暟: {score}")
                        else:
                            # 鍏朵粬鎯呭喌锛屽皾璇曡浆鎹负娴偣鏁?                            score = float(score_data) if score_data else 0.0
                            logger.info(f"杞崲鍚庣殑鍒嗘暟: {score}")
                        
                        component_scores.append({
                            'component': component_name,
                            'score': score
                        })
                        logger.info(f"鎴愬姛娣诲姞閮ㄤ欢: {component_name}, 鍒嗘暟: {score}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"澶勭悊閮ㄤ欢 {component_name} 鐨勫垎鏁版椂鍑洪敊: {e}")
                        continue
            else:
                logger.warning(f"component_results涓嶆槸瀛楀吀绫诲瀷: {type(component_results)}")
            
            # 鎸夊垎鏁板崌搴忔帓搴忥紝鍙栧墠涓変釜锛堝垎鏁版渶浣庣殑锛?            component_scores.sort(key=lambda x: x['score'])
            top3_components = component_scores[:3]
            
            logger.info(f"鎵惧埌 {len(component_scores)} 涓儴浠讹紝鍒嗘暟鏈€浣庣殑3涓? {top3_components}")
            
            # 鏍煎紡鍖朚SFG璇︽儏鏁版嵁
            msfg_details = {
                'overall_health_score': msfg_result.overall_health_score,
                'top3': [
                    {
                        'component': comp['component'],
                        'score': comp['score'],
                        'scores': {
                            'measurement': [{'name': comp['component'], 'value': f"{comp['score']:.4f}"}]
                        }
                    }
                    for comp in top3_components
                ]
            }
            
            return Response({
                "frame_id": frame_id,
                "timestamp": ims_result.data_point.timestamp.isoformat(),
                "cmg_id": ims_result.data_point.cmg.cmg_id,
                "msfg": msfg_details
            })
            
        except IMSDetectionResult.DoesNotExist:
            logger.error(f"IMS妫€娴嬬粨鏋滀笉瀛樺湪: {frame_id}")
            return Response({"error": "寮傚父甯т笉瀛樺湪"}, status=404)
        except Exception as e:
            logger.error(f"鑾峰彇MSFG妫€娴嬭鎯呭け璐? {e}")
            return Response({"error": "鑾峰彇MSFG妫€娴嬭鎯呭け璐?}, status=500)

    def _get_telemetry_data(self, request: Request) -> Response:
        """鑾峰彇鎸囧畾鏃堕棿鎴冲墠鍚庡悇n甯х殑閬ユ祴鏁版嵁"""
        try:
            # 鑾峰彇璇锋眰鍙傛暟
            frame_id = request.query_params.get("frame_id")
            frames_before = int(request.query_params.get("frames_before", 100))  # 榛樿鍓嶅悗鍚?00甯?            frames_after = int(request.query_params.get("frames_after", 100))
            selected_parameters = request.query_params.getlist("parameters")  # 鍙€夌殑閬ユ祴閲忛€夋嫨
            
            logger.info(f"閬ユ祴鏁版嵁API璋冪敤 - frame_id: {frame_id}, frames_before: {frames_before}, frames_after: {frames_after}, selected_parameters: {selected_parameters}")
            
            if not frame_id:
                logger.error("閬ユ祴鏁版嵁API璋冪敤澶辫触: frame_id鍙傛暟缂哄け")
                return Response({"error": "frame_id is required"}, status=400)
            
            # 鑾峰彇寮傚父甯у搴旂殑鏁版嵁鐐?            try:
                logger.info(f"姝ｅ湪鏌ユ壘IMS妫€娴嬬粨鏋?- frame_id: {frame_id}")
                ims_result = IMSDetectionResult.objects.select_related('data_point').get(id=frame_id)
                data_point = ims_result.data_point
                target_timestamp = data_point.timestamp
                cmg = data_point.cmg
                logger.info(f"鎵惧埌IMS妫€娴嬬粨鏋?- data_point_id: {data_point.id}, timestamp: {target_timestamp}, cmg_id: {cmg.cmg_id}")
            except IMSDetectionResult.DoesNotExist:
                logger.error(f"鏈壘鍒癐MS妫€娴嬬粨鏋?- frame_id: {frame_id}")
                return Response({"error": "Frame not found"}, status=404)
            except Exception as e:
                logger.error(f"鏌ユ壘IMS妫€娴嬬粨鏋滄椂鍙戠敓閿欒 - frame_id: {frame_id}, error: {e}")
                return Response({"error": f"Error finding frame: {str(e)}"}, status=500)
            
            # 浼樺寲锛氱洿鎺ヤ娇鐢ㄦ椂闂存埑鑼冨洿鏌ヨ锛岄伩鍏嶄竴娆℃€у姞杞芥墍鏈夋暟鎹?            logger.info(f"姝ｅ湪鏌ヨPHM鏁版嵁 - cmg_id: {cmg.cmg_id}")
            
            try:
                # 鍏堣幏鍙栧墠鍚庡悇n甯х殑鏁版嵁锛堝熀浜庢椂闂存埑鑼冨洿锛?                data_before = PHMData.objects.filter(
                    cmg=cmg,
                    timestamp__lt=target_timestamp
                ).order_by('-timestamp')[:frames_before]
                
                data_after = PHMData.objects.filter(
                    cmg=cmg,
                    timestamp__gte=target_timestamp
                ).order_by('timestamp')[:frames_after + 1]  # +1 鍖呭惈鐩爣鏃堕棿鎴?                
                # 鍚堝苟骞舵寜鏃堕棿鎴虫帓搴?                telemetry_data = list(reversed(list(data_before))) + list(data_after)
                logger.info(f"鑾峰彇閬ユ祴鏁版嵁: 鍓?{len(data_before)} 甯? 鍚?{len(data_after)} 甯? 鍏?{len(telemetry_data)} 鏉¤褰?)
                
            except Exception as e:
                logger.error(f"鏌ヨPHM鏁版嵁鏃跺彂鐢熼敊璇? {e}")
                return Response({"error": f"Error querying PHM data: {str(e)}"}, status=500)
            
            # 鎻愬彇鎵€鏈夐仴娴嬮噺鍙傛暟
            try:
                all_parameters = set()
                for data in telemetry_data:
                    if hasattr(data, 'data') and data.data and isinstance(data.data, dict):
                        all_parameters.update(data.data.keys())
                
                logger.info(f"鎻愬彇鍒伴仴娴嬮噺鍙傛暟: {sorted(list(all_parameters))}")
                
                # 濡傛灉鐢ㄦ埛鎸囧畾浜嗗弬鏁帮紝鍒欏彧杩斿洖鎸囧畾鐨勫弬鏁?                if selected_parameters:
                    parameters_to_return = [p for p in selected_parameters if p in all_parameters]
                else:
                    parameters_to_return = sorted(list(all_parameters))
                
                logger.info(f"杩斿洖鐨勯仴娴嬮噺鍙傛暟: {parameters_to_return}")
                
                # 鏋勫缓杩斿洖鏁版嵁
                result_data = []
                for data in telemetry_data:
                    data_point = {
                        "timestamp": data.timestamp.isoformat(),
                        "is_target": data.timestamp == target_timestamp,
                        "parameters": {}
                    }
                    
                    # 鎻愬彇鎸囧畾鐨勯仴娴嬮噺鏁版嵁
                    for param in parameters_to_return:
                        if hasattr(data, 'data') and data.data and isinstance(data.data, dict) and param in data.data:
                            data_point["parameters"][param] = data.data[param]
                        else:
                            data_point["parameters"][param] = None
                    
                    result_data.append(data_point)
                
                logger.info(f"鏋勫缓浜?{len(result_data)} 涓暟鎹偣")
                
            except Exception as e:
                logger.error(f"澶勭悊閬ユ祴鏁版嵁鏃跺彂鐢熼敊璇? {e}")
                return Response({"error": f"Error processing telemetry data: {str(e)}"}, status=500)
            
            logger.info(f"鑾峰彇閬ユ祴鏁版嵁鎴愬姛: 甯D={frame_id}, 鏁版嵁鐐规暟閲?{len(result_data)}, 閬ユ祴閲忔暟閲?{len(parameters_to_return)}")
            
            return Response({
                "frame_id": frame_id,
                "target_timestamp": target_timestamp.isoformat(),
                "cmg_id": cmg.cmg_id,
                "cmg_name": cmg.name,
                "frames_before": frames_before,
                "frames_after": frames_after,
                "total_frames": len(result_data),
                "available_parameters": sorted(list(all_parameters)),
                "selected_parameters": parameters_to_return,
                "telemetry_data": result_data
            })
            
        except Exception as e:
            logger.error(f"鑾峰彇閬ユ祴鏁版嵁澶辫触: {e}")
            return Response({"error": f"鑾峰彇閬ユ祴鏁版嵁澶辫触: {str(e)}"}, status=500)

    def _test_api(self, request: Request) -> Response:
        """娴嬭瘯API鏄惁姝ｅ父宸ヤ綔"""
        try:
            logger.info("娴嬭瘯API璋冪敤鎴愬姛")
            return Response({
                "status": "success",
                "message": "API is working",
                "timestamp": timezone.now().isoformat()
            })
        except Exception as e:
            logger.error(f"娴嬭瘯API澶辫触: {e}")
            return Response({"error": f"娴嬭瘯API澶辫触: {str(e)}"}, status=500)

    def _get_component_scores(self, request: Request) -> Response:
        """鑾峰彇鎸囧畾鏃堕棿娈靛唴PHM涓綋鐨勯儴浠跺钩鍧囧垎鏁?""
        try:
            # 鑾峰彇璇锋眰鍙傛暟
            cmg_id = request.query_params.get("cmg_id")
            start_time = request.query_params.get("start_time")
            end_time = request.query_params.get("end_time")
            
            logger.info(f"閮ㄤ欢鍒嗘暟API璋冪敤 - cmg_id: {cmg_id}, start_time: {start_time}, end_time: {end_time}")
            
            if not cmg_id or not start_time or not end_time:
                logger.error("閮ㄤ欢鍒嗘暟API璋冪敤澶辫触: 缂哄皯蹇呰鍙傛暟")
                return Response({"error": "cmg_id, start_time, and end_time are required"}, status=400)
            
            # 瑙ｆ瀽鏃堕棿鍙傛暟
            try:
                start_datetime = parse_datetime(start_time)
                end_datetime = parse_datetime(end_time)
                if not start_datetime or not end_datetime:
                    raise ValueError("Invalid datetime format")
            except Exception as e:
                logger.error(f"鏃堕棿鍙傛暟瑙ｆ瀽澶辫触: {e}")
                return Response({"error": "Invalid datetime format"}, status=400)
            
            # 鑾峰彇PHM涓綋
            try:
                cmg = PHM.objects.get(id=cmg_id)
                logger.info(f"鎵惧埌PHM涓綋: {cmg.cmg_id}")
            except PHM.DoesNotExist:
                logger.error(f"鏈壘鍒癈MG涓綋: {cmg_id}")
                return Response({"error": "PHM not found"}, status=404)
            
            # 鑾峰彇鎸囧畾鏃堕棿娈靛唴鐨凪SFG鍒嗘瀽缁撴灉
            try:
                from msfg_analysis.models import MSFGAnalysisResult
                from health_management.models import IMSDetectionResult
                from django.db.models import Q
                
                # 馃敡 鏅鸿兘鍋ュ悍鍒嗘暟绛栫暐锛氬熀浜庡紓甯稿抚姣斾緥鍐冲畾鏄惁鎺掗櫎姝ｅ父甯?                logger.info(f"========== 寮€濮嬮儴浠跺垎鏁拌绠楋細PHM {cmg.cmg_id}, 鏃堕棿娈?{start_datetime} ~ {end_datetime} ==========")
                
                # 1. 缁熻鎬绘暟鎹抚鏁帮紙PHMData锛夊拰IMS寮傚父甯ф暟
                logger.info(f"姝ラ1锛氱粺璁℃€绘暟鎹抚鏁板拰IMS寮傚父甯ф暟")
                total_frames = PHMData.objects.filter(
                    cmg=cmg,
                    timestamp__gte=start_datetime,
                    timestamp__lte=end_datetime
                ).count()
                logger.info(f"  鈫?鏌ヨ鏉′欢锛歝mg={cmg.cmg_id}, 鏃堕棿娈?[{start_datetime}, {end_datetime}]")
                logger.info(f"  鈫?鎬绘暟鎹抚鏁帮紙PHMData锛? {total_frames}")
                
                anomaly_frames = IMSDetectionResult.objects.filter(
                    data_point__cmg=cmg,
                    data_point__timestamp__gte=start_datetime,
                    data_point__timestamp__lte=end_datetime,
                    is_anomaly=True
                ).count()
                logger.info(f"  鈫?鏌ヨ鏉′欢锛歝mg={cmg.cmg_id}, 鏃堕棿娈?[{start_datetime}, {end_datetime}], is_anomaly=True")
                logger.info(f"  鈫?IMS寮傚父甯ф暟: {anomaly_frames}")
                
                normal_frames = total_frames - anomaly_frames
                logger.info(f"  鈫?姝ｅ父甯ф暟: {normal_frames}")
                
                # 2. 璁＄畻寮傚父甯ф瘮渚?                logger.info(f"姝ラ2锛氳绠楀紓甯稿抚姣斾緥")
                if total_frames > 0:
                    anomaly_ratio = anomaly_frames / total_frames
                    logger.info(f"  鈫?璁＄畻鍏紡锛歿anomaly_frames} / {total_frames} = {anomaly_ratio:.6f}")
                    logger.info(f"  鈫?寮傚父甯ф瘮渚嬶細{anomaly_ratio*100:.4f}%")
                else:
                    anomaly_ratio = 0
                    logger.info(f"  鈫?鎬诲抚鏁颁负0锛屽紓甯告瘮渚嬭涓?")
                
                # 3. 鏍规嵁寮傚父甯ф瘮渚嬪喅瀹氭煡璇㈢瓥鐣?                logger.info(f"姝ラ3锛氭牴鎹紓甯稿抚姣斾緥閫夋嫨鏌ヨ绛栫暐")
                threshold = 0.01
                logger.info(f"  鈫?鍒ゆ柇闃堝€硷細{threshold*100:.2f}%")
                logger.info(f"  鈫?褰撳墠姣斾緥锛歿anomaly_ratio*100:.4f}%")
                logger.info(f"  鈫?姣旇緝缁撴灉锛歿anomaly_ratio} {'>' if anomaly_ratio > threshold else '鈮?} {threshold}")
                
                if anomaly_ratio > 0.01:  # 寮傚父甯ф瘮渚?> 1%
                    # 绛栫暐A锛氭帓闄ゆ甯稿抚锛堝彧鐪嬪紓甯稿抚锛?                    logger.info(f"  鈫?閫夋嫨绛栫暐锛氱瓥鐣锛堟帓闄ゆ甯稿抚锛屽彧缁熻寮傚父甯э級")
                    logger.info(f"  鈫?鍘熷洜锛氬紓甯稿抚姣斾緥 {anomaly_ratio*100:.4f}% > 1%锛岃鏄庣‘瀹炴湁绯荤粺鎬ч棶棰?)
                    msfg_results = MSFGAnalysisResult.objects.filter(
                        data_point__cmg=cmg,
                        data_point__timestamp__gte=start_datetime,
                        data_point__timestamp__lte=end_datetime,
                        overall_health_score__lt=0.9999  # 鎺掗櫎榛樿鍊?.0
                    ).select_related('data_point')
                    logger.info(f"  鈫?鏌ヨ绛栫暐锛氬彧鏌ヨ overall_health_score < 0.9999 鐨勮褰?)
                else:
                    # 绛栫暐B锛氬叏灞€鍔犳潈锛堝寘鍚甯稿抚鍜屽紓甯稿抚锛?                    logger.info(f"  鈫?閫夋嫨绛栫暐锛氱瓥鐣锛堝叏灞€鍔犳潈锛屽寘鍚墍鏈夊抚锛?)
                    logger.info(f"  鈫?鍘熷洜锛氬紓甯稿抚姣斾緥 {anomaly_ratio*100:.4f}% 鈮?1%锛屽彲鑳芥槸鍋跺彂寮傚父")
                    msfg_results = MSFGAnalysisResult.objects.filter(
                        data_point__cmg=cmg,
                        data_point__timestamp__gte=start_datetime,
                        data_point__timestamp__lte=end_datetime
                    ).select_related('data_point')
                    logger.info(f"  鈫?鏌ヨ绛栫暐锛氭煡璇㈡墍鏈夎褰曪紙鍖呭惈姝ｅ父甯у拰寮傚父甯э級")
                
                logger.info(f"鎵惧埌 {len(msfg_results)} 涓狹SFG鍒嗘瀽缁撴灉锛岀瓥鐣?{'A(鎺掗櫎姝ｅ父甯?' if anomaly_ratio > 0.01 else 'B(鍏ㄥ眬鍔犳潈)'}")
                
                if len(msfg_results) == 0:
                    logger.warning(f"鎸囧畾鏃堕棿娈靛唴娌℃湁MSFG鍒嗘瀽缁撴灉")
                    return Response({
                        "cmg_id": cmg.cmg_id,
                        "cmg_name": cmg.name,
                        "start_time": start_time,
                        "end_time": end_time,
                        "component_scores": [],
                        "total_records": 0,
                        "message": "No MSFG analysis results found in the specified time range"
                    })
                
                # 鎻愬彇鎵€鏈夐儴浠剁殑鍒嗘暟
                component_scores_dict = {}
                
                for result in msfg_results:
                    if result.component_results and isinstance(result.component_results, dict):
                        for component_name, score in result.component_results.items():
                            # 澶勭悊涓嶅悓鐨勫垎鏁版牸寮?                            if isinstance(score, (int, float)):
                                actual_score = float(score)
                            elif isinstance(score, dict):
                                # 浼樺厛浣跨敤health_score锛屽鏋滄病鏈夊垯浣跨敤score
                                if 'health_score' in score:
                                    actual_score = float(score['health_score'])
                                elif 'score' in score:
                                    actual_score = float(score['score'])
                                else:
                                    logger.warning(f"璺宠繃鏃犳硶澶勭悊鐨勫垎鏁版牸寮? {component_name} = {score}")
                                    continue  # 璺宠繃鏃犳硶澶勭悊鐨勬牸寮?                            else:
                                logger.warning(f"璺宠繃鏃犳硶澶勭悊鐨勫垎鏁版牸寮? {component_name} = {score}")
                                continue  # 璺宠繃鏃犳硶澶勭悊鐨勬牸寮?                            
                            if component_name not in component_scores_dict:
                                component_scores_dict[component_name] = []
                            component_scores_dict[component_name].append(actual_score)
                    else:
                        logger.warning(f"MSFG缁撴灉 {result.id} 鐨刢omponent_results鏃犳晥: {result.component_results}")
                
                logger.info(f"鎻愬彇鍒?{len(component_scores_dict)} 涓儴浠剁殑鍒嗘暟鏁版嵁")
                
                # 璁＄畻姣忎釜閮ㄤ欢鐨勫钩鍧囧垎鏁?                component_averages = []
                for component_name, scores in component_scores_dict.items():
                    if scores:  # 纭繚鏈夊垎鏁版暟鎹?                        average_score = sum(scores) / len(scores)
                        component_averages.append({
                            "component_name": component_name,
                            "average_score": round(average_score, 4),
                            "score_count": len(scores),
                            "min_score": round(min(scores), 4),
                            "max_score": round(max(scores), 4)
                        })
                
                # 鎸夊钩鍧囧垎鏁伴檷搴忔帓搴?                component_averages.sort(key=lambda x: x['average_score'], reverse=True)
                
                logger.info(f"璁＄畻浜?{len(component_averages)} 涓儴浠剁殑骞冲潎鍒嗘暟")
                
                return Response({
                    "cmg_id": cmg.cmg_id,
                    "cmg_name": cmg.name,
                    "start_time": start_time,
                    "end_time": end_time,
                    "component_scores": component_averages,
                    "total_records": len(msfg_results),
                    "total_components": len(component_averages)
                })
                
            except Exception as e:
                logger.error(f"澶勭悊MSFG鍒嗘瀽缁撴灉鏃跺彂鐢熼敊璇? {e}")
                return Response({"error": f"Error processing MSFG results: {str(e)}"}, status=500)
                
        except Exception as e:
            logger.error(f"鑾峰彇閮ㄤ欢鍒嗘暟澶辫触: {e}")
            return Response({"error": f"鑾峰彇閮ㄤ欢鍒嗘暟澶辫触: {str(e)}"}, status=500)

    def _get_lifetime_trend(self, request: Request) -> Response:
        """
        鑾峰彇鍓╀綑瀵垮懡鍜屽仴搴疯秼鍔挎暟鎹?        
        鍙傛暟:
        - cmg_id: PHM鏁版嵁搴揑D
        - start_time: 寮€濮嬫椂闂?(ISO鏍煎紡)
        - end_time: 缁撴潫鏃堕棿 (ISO鏍煎紡)
        - design_life: 璁捐瀵垮懡 (骞达紝鍙€夛紝榛樿5骞?
        - start_use_time: PHM寮€濮嬩娇鐢ㄦ椂闂?(鍙€夛紝榛樿浣跨敤鏁版嵁寮€濮嬫椂闂?
        - algorithm: 棰勬祴绠楁硶 (鍙€夛紝榛樿strategy0)
        """
        try:
            # 鑾峰彇鍙傛暟
            cmg_id = request.GET.get('cmg_id')
            start_time = request.GET.get('start_time')
            end_time = request.GET.get('end_time')
            design_life = request.GET.get('design_life', '5')  # 榛樿5骞?            start_use_time = request.GET.get('start_use_time')
            algorithm = request.GET.get('algorithm', 'strategy0')  # 榛樿绠楁硶
            
            if not cmg_id:
                return Response({'error': '缂哄皯cmg_id鍙傛暟'}, status=400)
            
            if not start_time or not end_time:
                return Response({'error': '缂哄皯start_time鎴杄nd_time鍙傛暟'}, status=400)
            
            # 鑾峰彇PHM瀵硅薄
            try:
                cmg = PHM.objects.get(id=cmg_id)
            except PHM.DoesNotExist:
                return Response({'error': f'PHM ID {cmg_id} 涓嶅瓨鍦?}, status=404)
            
            # 瀵煎叆瀵垮懡棰勬祴鏈嶅姟
            from lifetime_prediction.services import LifetimePredictionService
            
            # 鍒涘缓棰勬祴鏈嶅姟瀹炰緥
            prediction_service = LifetimePredictionService()
            
            # 濡傛灉娌℃湁鎻愪緵寮€濮嬩娇鐢ㄦ椂闂达紝浣跨敤鏁版嵁寮€濮嬫椂闂?            if not start_use_time:
                # 鑾峰彇璇MG鐨勬渶鏃╂暟鎹椂闂翠綔涓哄紑濮嬩娇鐢ㄦ椂闂?                earliest_data = PHMData.objects.filter(cmg=cmg).order_by('timestamp').first()
                if earliest_data:
                    start_use_time = earliest_data.timestamp.strftime('%Y/%m/%d %H:%M:%S')
                else:
                    start_use_time = start_time.replace('T', ' ').split('.')[0]  # 杞崲鏃堕棿鏍煎紡
            
            logger.info(f"寮€濮嬪鍛介娴? PHM={cmg.cmg_id}, 鏃堕棿娈?{start_time}鍒皗end_time}, 璁捐瀵垮懡={design_life}骞? 寮€濮嬩娇鐢ㄦ椂闂?{start_use_time}, 绠楁硶={algorithm}")
            
            # 鎵ц瀵垮懡棰勬祴
            prediction_result = prediction_service.predict_lifetime(
                cmg_id=cmg.cmg_id,
                design_life=float(design_life),
                start_time=start_use_time,
                data_start_time=start_time,
                end_time=end_time,
                use_time_range=True,  # 浣跨敤鏃堕棿娈佃繃婊ゆ暟鎹?                algorithm=algorithm   # 浼犻€掔畻娉曞弬鏁?            )
            
            if prediction_result.get('status') == 'error':
                logger.error(f"瀵垮懡棰勬祴澶辫触: {prediction_result.get('message')}")
                return Response({
                    'error': prediction_result.get('message'),
                    'details': prediction_result
                }, status=400)
            
            # 鎻愬彇缁撴灉
            rul_value = prediction_result.get('rul_value', 0.0)
            hi_sequence = prediction_result.get('hi_sequence', [])
            
            # 鏋勫缓鍋ュ悍瓒嬪娍鏁版嵁
            trend_data = []
            if hi_sequence:
                # 鑾峰彇瀵瑰簲鐨勬椂闂存埑
                cmg_data = PHMData.objects.filter(
                    cmg=cmg,
                    timestamp__gte=start_time,
                    timestamp__lte=end_time
                ).order_by('timestamp')
                
                timestamps = [data.timestamp for data in cmg_data]
                
                # 纭繚鏃堕棿鎴冲拰鍋ュ悍鎸囨暟搴忓垪闀垮害鍖归厤
                min_length = min(len(timestamps), len(hi_sequence))
                for i in range(min_length):
                    trend_data.append({
                        'timestamp': timestamps[i].isoformat(),
                        'health_index': round(hi_sequence[i], 4)
                    })
            
            # 鏋勫缓鍝嶅簲鏁版嵁
            response_data = {
                'cmg_id': cmg.cmg_id,
                'cmg_name': cmg.name,
                'remaining_life_years': round(rul_value, 2),  # 淇瀛楁鍚嶏細RUL鍊肩殑鍗曚綅鏄勾
                'remaining_life_hours': round(rul_value * 365 * 24, 2),  # 濡傛灉闇€瑕佸皬鏃舵暟锛屽疄闄呰绠?                'remaining_life_days': round(rul_value * 365, 2),  # 濡傛灉闇€瑕佸ぉ鏁帮紝瀹為檯璁＄畻
                'design_life_years': float(design_life),
                'start_use_time': start_use_time,
                'prediction_time': prediction_result.get('prediction_time'),
                'trend_data': trend_data,
                'trend_count': len(trend_data),
                'status': 'success'
            }
            
            logger.info(f"瀵垮懡棰勬祴瀹屾垚: PHM={cmg.cmg_id}, RUL={rul_value:.2f}骞? 瓒嬪娍鐐规暟={len(trend_data)}")
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"鑾峰彇瀵垮懡瓒嬪娍鏁版嵁澶辫触: {str(e)}")
            return Response({
                'error': f'鑾峰彇瀵垮懡瓒嬪娍鏁版嵁澶辫触: {str(e)}'
            }, status=500)

    def _get_component_details(self, request: Request) -> Response:
        """
        鑾峰彇鎸囧畾閮ㄤ欢鐨勮缁嗕俊鎭紝鍖呮嫭鐩稿叧娴嬬偣銆佹晠闅滃拰鍒嗘暟
        
        鍙傛暟:
        - cmg_id: PHM鏁版嵁搴揑D
        - component_name: 閮ㄤ欢鍚嶇О
        - start_time: 寮€濮嬫椂闂?(ISO鏍煎紡)
        - end_time: 缁撴潫鏃堕棿 (ISO鏍煎紡)
        """
        try:
            # 鑾峰彇璇锋眰鍙傛暟
            cmg_id = request.query_params.get("cmg_id")
            component_name = request.query_params.get("component_name")
            start_time = request.query_params.get("start_time")
            end_time = request.query_params.get("end_time")
            
            logger.info(f"閮ㄤ欢璇︽儏API璋冪敤 - cmg_id: {cmg_id}, component_name: {component_name}, start_time: {start_time}, end_time: {end_time}")
            
            if not cmg_id or not component_name or not start_time or not end_time:
                logger.error("閮ㄤ欢璇︽儏API璋冪敤澶辫触: 缂哄皯蹇呰鍙傛暟")
                return Response({"error": "cmg_id, component_name, start_time, and end_time are required"}, status=400)
            
            # 瑙ｆ瀽鏃堕棿鍙傛暟
            try:
                start_datetime = parse_datetime(start_time)
                end_datetime = parse_datetime(end_time)
                if not start_datetime or not end_datetime:
                    raise ValueError("Invalid datetime format")
            except Exception as e:
                logger.error(f"鏃堕棿鍙傛暟瑙ｆ瀽澶辫触: {e}")
                return Response({"error": "Invalid datetime format"}, status=400)
            
            # 鑾峰彇PHM涓綋
            try:
                cmg = PHM.objects.get(id=cmg_id)
                logger.info(f"鎵惧埌PHM涓綋: {cmg.cmg_id}")
            except PHM.DoesNotExist:
                logger.error(f"鏈壘鍒癈MG涓綋: {cmg_id}")
                return Response({"error": "PHM not found"}, status=404)
            
            # 鑾峰彇MSFG瀹氫箟
            try:
                from msfg_analysis.models import MSFGDefinition
                msfg_definition = MSFGDefinition.objects.filter(
                    cmg_model=cmg.cmg_model,
                    is_active=True
                ).order_by('-updated_at').first()
                
                if not msfg_definition:
                    logger.warning(f"鏈壘鍒版椿璺冪殑MSFG瀹氫箟: {cmg.cmg_model.model_name}")
                    return Response({
                        "error": "No active MSFG definition found for this PHM model",
                        "component_name": component_name
                    }, status=404)
                
                logger.info(f"鎵惧埌MSFG瀹氫箟: {msfg_definition.name}")
            except Exception as e:
                logger.error(f"鑾峰彇MSFG瀹氫箟澶辫触: {e}")
                return Response({"error": f"Failed to get MSFG definition: {str(e)}"}, status=500)
            
            # 鑾峰彇閮ㄤ欢鐩稿叧鐨勬槧灏勫叧绯?            try:
                from msfg_analysis.models import TestPointComponentMapping, FaultComponentMapping
                
                # 鑾峰彇娴嬬偣-閮ㄤ欢鏄犲皠
                testpoint_mappings = TestPointComponentMapping.objects.filter(
                    msfg_definition=msfg_definition,
                    component_name=component_name
                )
                
                # 鑾峰彇鏁呴殰-閮ㄤ欢鏄犲皠
                fault_mappings = FaultComponentMapping.objects.filter(
                    msfg_definition=msfg_definition,
                    component_name=component_name
                )
                
                logger.info(f"鎵惧埌 {len(testpoint_mappings)} 涓祴鐐规槧灏? {len(fault_mappings)} 涓晠闅滄槧灏?)
                
                # 璋冭瘯锛氳緭鍑烘槧灏勮鎯?                if testpoint_mappings:
                    logger.info("娴嬬偣鏄犲皠璇︽儏:")
                    for mapping in testpoint_mappings:
                        logger.info(f"  - {mapping.test_point_name} -> {mapping.component_name} (鏉冮噸: {mapping.weight})")
                
                if fault_mappings:
                    logger.info("鏁呴殰鏄犲皠璇︽儏:")
                    for mapping in fault_mappings:
                        logger.info(f"  - {mapping.fault_name} -> {mapping.component_name} (鏉冮噸: {mapping.weight})")
                
                # 妫€鏌ユ槸鍚︽湁鍏朵粬閮ㄤ欢鐨勬槧灏?                all_testpoint_mappings = TestPointComponentMapping.objects.filter(
                    msfg_definition=msfg_definition
                )
                all_fault_mappings = FaultComponentMapping.objects.filter(
                    msfg_definition=msfg_definition
                )
                logger.info(f"MSFG瀹氫箟 '{msfg_definition.name}' 鎬诲叡鏈?{len(all_testpoint_mappings)} 涓祴鐐规槧灏? {len(all_fault_mappings)} 涓晠闅滄槧灏?)
                
                # 杈撳嚭鎵€鏈夐儴浠跺悕绉?                all_components = set()
                for mapping in all_testpoint_mappings:
                    all_components.add(mapping.component_name)
                for mapping in all_fault_mappings:
                    all_components.add(mapping.component_name)
                logger.info(f"鎵€鏈夐儴浠? {sorted(all_components)}")
                
            except Exception as e:
                logger.error(f"鑾峰彇鏄犲皠鍏崇郴澶辫触: {e}")
                return Response({"error": f"Failed to get component mappings: {str(e)}"}, status=500)
            
            # 鑾峰彇鎸囧畾鏃堕棿娈靛唴鐨凪SFG鍒嗘瀽缁撴灉
            try:
                from msfg_analysis.models import MSFGAnalysisResult
                from health_management.models import IMSDetectionResult
                from django.db.models import Q
                
                # 馃敡 鏅鸿兘鍋ュ悍鍒嗘暟绛栫暐锛氬熀浜庡紓甯稿抚姣斾緥鍐冲畾鏄惁鎺掗櫎姝ｅ父甯?                logger.info(f"========== 寮€濮嬮儴浠惰鎯呰绠楋細閮ㄤ欢 {component_name}, PHM {cmg.cmg_id}, 鏃堕棿娈?{start_datetime} ~ {end_datetime} ==========")
                
                # 1. 缁熻鎬绘暟鎹抚鏁帮紙PHMData锛夊拰IMS寮傚父甯ф暟
                logger.info(f"姝ラ1锛氱粺璁℃€绘暟鎹抚鏁板拰IMS寮傚父甯ф暟")
                total_frames = PHMData.objects.filter(
                    cmg=cmg,
                    timestamp__gte=start_datetime,
                    timestamp__lte=end_datetime
                ).count()
                logger.info(f"  鈫?鏌ヨ鏉′欢锛歝mg={cmg.cmg_id}, 鏃堕棿娈?[{start_datetime}, {end_datetime}]")
                logger.info(f"  鈫?鎬绘暟鎹抚鏁帮紙PHMData锛? {total_frames}")
                
                anomaly_frames = IMSDetectionResult.objects.filter(
                    data_point__cmg=cmg,
                    data_point__timestamp__gte=start_datetime,
                    data_point__timestamp__lte=end_datetime,
                    is_anomaly=True
                ).count()
                logger.info(f"  鈫?鏌ヨ鏉′欢锛歝mg={cmg.cmg_id}, 鏃堕棿娈?[{start_datetime}, {end_datetime}], is_anomaly=True")
                logger.info(f"  鈫?IMS寮傚父甯ф暟: {anomaly_frames}")
                
                normal_frames = total_frames - anomaly_frames
                logger.info(f"  鈫?姝ｅ父甯ф暟: {normal_frames}")
                
                # 2. 璁＄畻寮傚父甯ф瘮渚?                logger.info(f"姝ラ2锛氳绠楀紓甯稿抚姣斾緥")
                if total_frames > 0:
                    anomaly_ratio = anomaly_frames / total_frames
                    logger.info(f"  鈫?璁＄畻鍏紡锛歿anomaly_frames} / {total_frames} = {anomaly_ratio:.6f}")
                    logger.info(f"  鈫?寮傚父甯ф瘮渚嬶細{anomaly_ratio*100:.4f}%")
                else:
                    anomaly_ratio = 0
                    logger.info(f"  鈫?鎬诲抚鏁颁负0锛屽紓甯告瘮渚嬭涓?")
                
                # 3. 鏍规嵁寮傚父甯ф瘮渚嬪喅瀹氭煡璇㈢瓥鐣?                logger.info(f"姝ラ3锛氭牴鎹紓甯稿抚姣斾緥閫夋嫨鏌ヨ绛栫暐")
                threshold = 0.01
                logger.info(f"  鈫?鍒ゆ柇闃堝€硷細{threshold*100:.2f}%")
                logger.info(f"  鈫?褰撳墠姣斾緥锛歿anomaly_ratio*100:.4f}%")
                logger.info(f"  鈫?姣旇緝缁撴灉锛歿anomaly_ratio} {'>' if anomaly_ratio > threshold else '鈮?} {threshold}")
                
                if anomaly_ratio > 0.01:  # 寮傚父甯ф瘮渚?> 1%
                    # 绛栫暐A锛氭帓闄ゆ甯稿抚锛堝彧鐪嬪紓甯稿抚锛?                    logger.info(f"  鈫?閫夋嫨绛栫暐锛氱瓥鐣锛堟帓闄ゆ甯稿抚锛屽彧缁熻寮傚父甯э級")
                    logger.info(f"  鈫?鍘熷洜锛氬紓甯稿抚姣斾緥 {anomaly_ratio*100:.4f}% > 1%锛岃鏄庣‘瀹炴湁绯荤粺鎬ч棶棰?)
                    msfg_results = MSFGAnalysisResult.objects.filter(
                        data_point__cmg=cmg,
                        data_point__timestamp__gte=start_datetime,
                        data_point__timestamp__lte=end_datetime,
                        msfg_definition=msfg_definition,
                        overall_health_score__lt=0.9999  # 鎺掗櫎榛樿鍊?.0
                    ).select_related('data_point').order_by('data_point__timestamp')
                    logger.info(f"  鈫?鏌ヨ绛栫暐锛氬彧鏌ヨ overall_health_score < 0.9999 鐨勮褰?)
                else:
                    # 绛栫暐B锛氬叏灞€鍔犳潈锛堝寘鍚甯稿抚鍜屽紓甯稿抚锛?                    logger.info(f"  鈫?閫夋嫨绛栫暐锛氱瓥鐣锛堝叏灞€鍔犳潈锛屽寘鍚墍鏈夊抚锛?)
                    logger.info(f"  鈫?鍘熷洜锛氬紓甯稿抚姣斾緥 {anomaly_ratio*100:.4f}% 鈮?1%锛屽彲鑳芥槸鍋跺彂寮傚父")
                    msfg_results = MSFGAnalysisResult.objects.filter(
                        data_point__cmg=cmg,
                        data_point__timestamp__gte=start_datetime,
                        data_point__timestamp__lte=end_datetime,
                        msfg_definition=msfg_definition
                    ).select_related('data_point').order_by('data_point__timestamp')
                    logger.info(f"  鈫?鏌ヨ绛栫暐锛氭煡璇㈡墍鏈夎褰曪紙鍖呭惈姝ｅ父甯у拰寮傚父甯э級")
                
                logger.info(f"鎵惧埌 {len(msfg_results)} 涓狹SFG鍒嗘瀽缁撴灉锛岀瓥鐣?{'A(鎺掗櫎姝ｅ父甯?' if anomaly_ratio > 0.01 else 'B(鍏ㄥ眬鍔犳潈)'}")
                
                if len(msfg_results) == 0:
                    return Response({
                        "component_name": component_name,
                        "cmg_id": cmg.cmg_id,
                        "start_time": start_time,
                        "end_time": end_time,
                        "testpoint_mappings": [],
                        "fault_mappings": [],
                        "testpoint_scores": [],
                        "fault_scores": [],
                        "component_scores": [],
                        "total_records": 0,
                        "message": "No MSFG analysis results found in the specified time range"
                    })
                
            except Exception as e:
                logger.error(f"鑾峰彇MSFG鍒嗘瀽缁撴灉澶辫触: {e}")
                return Response({"error": f"Failed to get MSFG results: {str(e)}"}, status=500)
            
            # 鏋勫缓娴嬬偣鏄犲皠淇℃伅
            testpoint_mapping_info = []
            for mapping in testpoint_mappings:
                testpoint_mapping_info.append({
                    "test_point_name": mapping.test_point_name,
                    "component_name": mapping.component_name,
                    "mapping_type": mapping.mapping_type,
                    "weight": mapping.weight,
                    "component_type": mapping.component_type,
                    "importance_weight": mapping.importance_weight,
                    "is_critical": mapping.is_critical,
                    "description": mapping.description
                })
            
            # 鏋勫缓鏁呴殰鏄犲皠淇℃伅
            fault_mapping_info = []
            for mapping in fault_mappings:
                fault_mapping_info.append({
                    "fault_name": mapping.fault_name,
                    "component_name": mapping.component_name,
                    "mapping_type": mapping.mapping_type,
                    "weight": mapping.weight,
                    "is_critical": mapping.is_critical,
                    "description": mapping.description
                })
            
            # 鎻愬彇娴嬬偣鍒嗘暟鍜屾晠闅滃垎鏁?            testpoint_scores = {}
            fault_scores = {}
            component_scores = []
            
            # 鑾峰彇鎵€鏈夌浉鍏崇殑娴嬬偣鍚嶇О鍜屾晠闅滃悕绉?            related_testpoints = set(mapping.test_point_name for mapping in testpoint_mappings)
            related_faults = set(mapping.fault_name for mapping in fault_mappings)
            
            logger.info(f"鐩稿叧娴嬬偣: {related_testpoints}")
            logger.info(f"鐩稿叧鏁呴殰: {related_faults}")
            
            # 鍙娇鐢ㄦ暟鎹簱涓殑鏄庣‘鏄犲皠鍏崇郴锛屼笉杩涜鍥為€€
            if not related_testpoints and not related_faults:
                logger.warning(f"閮ㄤ欢 '{component_name}' 娌℃湁浠讳綍鏄犲皠鍏崇郴锛屽皢杩斿洖绌虹粨鏋?)
                return Response({
                    "component_name": component_name,
                    "cmg_id": cmg.cmg_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "center_component": {
                        "name": component_name,
                        "type": "component",
                        "average_score": 0.0,
                        "min_score": 0.0,
                        "max_score": 0.0,
                        "score_count": 0,
                        "average_fault_count": 0.0,
                        "max_fault_count": 0
                    },
                    "surrounding_testpoints": [],
                    "surrounding_faults": [],
                    "total_records": len(msfg_results),
                    "total_testpoints": 0,
                    "total_faults": 0,
                    "message": f"閮ㄤ欢 '{component_name}' 娌℃湁鎵惧埌浠讳綍鏄犲皠鍏崇郴"
                })
            else:
                logger.info(f"浣跨敤鏁版嵁搴撲腑鐨勬槧灏勫叧绯? 娴嬬偣 {len(related_testpoints)} 涓? 鏁呴殰 {len(related_faults)} 涓?)
            
            for result in msfg_results:
                timestamp = result.data_point.timestamp.isoformat()
                
                # 澶勭悊娴嬬偣鍒嗘暟 - 浠巘est_results涓彁鍙?                if result.test_results and isinstance(result.test_results, dict):
                    for test_name, test_data in result.test_results.items():
                        if test_name in related_testpoints:
                            if test_name not in testpoint_scores:
                                testpoint_scores[test_name] = []
                            # 鎻愬彇score瀛楁
                            score = 0.0
                            if isinstance(test_data, dict):
                                score = float(test_data.get('score', 0.0))
                            elif isinstance(test_data, (int, float)):
                                score = float(test_data)
                            testpoint_scores[test_name].append({
                                "timestamp": timestamp,
                                "score": score
                            })
                
                # 澶勭悊鏁呴殰鍒嗘暟 - 浠巉ault_results涓彁鍙?                if result.fault_results and isinstance(result.fault_results, dict):
                    for fault_name, fault_data in result.fault_results.items():
                        if fault_name in related_faults:
                            if fault_name not in fault_scores:
                                fault_scores[fault_name] = []
                            # 鎻愬彇fault_probability瀛楁
                            score = 0.0
                            if isinstance(fault_data, dict):
                                score = float(fault_data.get('fault_probability', 0.0))
                            elif isinstance(fault_data, (int, float)):
                                score = float(fault_data)
                            fault_scores[fault_name].append({
                                "timestamp": timestamp,
                                "score": score
                            })
                
                # 澶勭悊閮ㄤ欢鍒嗘暟
                if result.component_results and isinstance(result.component_results, dict):
                    if component_name in result.component_results:
                        component_data = result.component_results[component_name]
                        if isinstance(component_data, dict):
                            # 鎻愬彇鍋ュ悍鍒嗘暟浣滀负涓昏鍒嗘暟
                            health_score = float(component_data.get('health_score', 1.0))
                            # 鎻愬彇鍏朵粬鐩稿叧鍒嗘暟
                            max_fault_score = float(component_data.get('max_fault_score', 0.0))
                            avg_fault_score = float(component_data.get('avg_fault_score', 0.0))
                            max_test_score = float(component_data.get('max_test_score', 0.0))
                            active_fault_count = int(component_data.get('active_fault_count', 0))
                            
                            component_scores.append({
                                "timestamp": timestamp,
                                "health_score": health_score,
                                "active_fault_count": active_fault_count,
                                "max_fault_score": max_fault_score,
                                "avg_fault_score": avg_fault_score,
                                "max_test_score": max_test_score
                            })
                        elif isinstance(component_data, (int, float)):
                            # 濡傛灉鐩存帴鏄暟鍊硷紝浣滀负鍋ュ悍鍒嗘暟
                            component_scores.append({
                                "timestamp": timestamp,
                                "health_score": float(component_data),
                                "active_fault_count": 0,
                                "max_fault_score": 0.0,
                                "avg_fault_score": 0.0,
                                "max_test_score": 0.0
                            })
            
            logger.info(f"鎻愬彇鍒?{len(testpoint_scores)} 涓祴鐐圭殑鍒嗘暟鏁版嵁")
            logger.info(f"鎻愬彇鍒?{len(fault_scores)} 涓晠闅滅殑鍒嗘暟鏁版嵁")
            logger.info(f"鎻愬彇鍒?{len(component_scores)} 涓儴浠跺垎鏁拌褰?)
            
            # 璋冭瘯锛氳緭鍑轰竴浜涙牱鏈暟鎹?            if testpoint_scores:
                sample_testpoint = list(testpoint_scores.keys())[0]
                logger.info(f"娴嬬偣鏍锋湰 '{sample_testpoint}': {testpoint_scores[sample_testpoint][:2] if testpoint_scores[sample_testpoint] else '鏃犳暟鎹?}")
            
            if fault_scores:
                sample_fault = list(fault_scores.keys())[0]
                logger.info(f"鏁呴殰鏍锋湰 '{sample_fault}': {fault_scores[sample_fault][:2] if fault_scores[sample_fault] else '鏃犳暟鎹?}")
            
            if component_scores:
                logger.info(f"閮ㄤ欢鏍锋湰: {component_scores[:2]}")
            
            # 璁＄畻娴嬬偣缁熻淇℃伅
            testpoint_statistics = []
            for test_name, scores in testpoint_scores.items():
                if scores:
                    score_values = [s['score'] for s in scores]
                    testpoint_statistics.append({
                        "test_point_name": test_name,
                        "average_score": round(sum(score_values) / len(score_values), 4),
                        "min_score": round(min(score_values), 4),
                        "max_score": round(max(score_values), 4),
                        "score_count": len(score_values),
                        "scores": scores
                    })
            
            # 璁＄畻鏁呴殰缁熻淇℃伅
            fault_statistics = []
            for fault_name, scores in fault_scores.items():
                if scores:
                    score_values = [s['score'] for s in scores]
                    fault_statistics.append({
                        "fault_name": fault_name,
                        "average_score": round(sum(score_values) / len(score_values), 4),
                        "min_score": round(min(score_values), 4),
                        "max_score": round(max(score_values), 4),
                        "score_count": len(score_values),
                        "scores": scores
                    })
            
            # 璁＄畻閮ㄤ欢缁熻淇℃伅
            component_statistics = {}
            if component_scores:
                health_scores = [s['health_score'] for s in component_scores]
                fault_counts = [s['active_fault_count'] for s in component_scores]
                max_fault_scores = [s['max_fault_score'] for s in component_scores]
                avg_fault_scores = [s['avg_fault_score'] for s in component_scores]
                max_test_scores = [s['max_test_score'] for s in component_scores]
                
                component_statistics = {
                    "average_health_score": round(sum(health_scores) / len(health_scores), 4),
                    "min_health_score": round(min(health_scores), 4),
                    "max_health_score": round(max(health_scores), 4),
                    "average_fault_count": round(sum(fault_counts) / len(fault_counts), 2),
                    "max_fault_count": max(fault_counts),
                    "average_max_fault_score": round(sum(max_fault_scores) / len(max_fault_scores), 4),
                    "average_avg_fault_score": round(sum(avg_fault_scores) / len(avg_fault_scores), 4),
                    "average_max_test_score": round(sum(max_test_scores) / len(max_test_scores), 4),
                    "score_count": len(component_scores)
                }
            
            # 鏋勫缓鍦嗗舰甯冨眬鏁版嵁
            # 涓績閮ㄤ欢鏁版嵁
            center_component = {
                "name": component_name,
                "type": "component",
                "average_score": component_statistics.get("average_health_score", 0.0),
                "min_score": component_statistics.get("min_health_score", 0.0),
                "max_score": component_statistics.get("max_health_score", 0.0),
                "score_count": component_statistics.get("score_count", 0),
                "average_fault_count": component_statistics.get("average_fault_count", 0.0),
                "max_fault_count": component_statistics.get("max_fault_count", 0)
            }
            
            # 鍛ㄥ洿娴嬬偣鏁版嵁
            surrounding_testpoints = []
            for stat in testpoint_statistics:
                surrounding_testpoints.append({
                    "name": stat["test_point_name"],
                    "type": "testpoint",
                    "average_score": stat["average_score"],
                    "min_score": stat["min_score"],
                    "max_score": stat["max_score"],
                    "score_count": stat["score_count"],
                    "mapping_info": next((m for m in testpoint_mapping_info if m["test_point_name"] == stat["test_point_name"]), {})
                })
            
            # 鍛ㄥ洿鏁呴殰鏁版嵁
            surrounding_faults = []
            for stat in fault_statistics:
                surrounding_faults.append({
                    "name": stat["fault_name"],
                    "type": "fault",
                    "average_score": stat["average_score"],
                    "min_score": stat["min_score"],
                    "max_score": stat["max_score"],
                    "score_count": stat["score_count"],
                    "mapping_info": next((m for m in fault_mapping_info if m["fault_name"] == stat["fault_name"]), {})
                })
            
            # 鏋勫缓鍝嶅簲鏁版嵁
            response_data = {
                "component_name": component_name,
                "cmg_id": cmg.cmg_id,
                "cmg_name": cmg.name,
                "msfg_definition": msfg_definition.name,
                "start_time": start_time,
                "end_time": end_time,
                "center_component": center_component,
                "surrounding_testpoints": surrounding_testpoints,
                "surrounding_faults": surrounding_faults,
                "total_records": len(msfg_results),
                "total_testpoints": len(testpoint_statistics),
                "total_faults": len(fault_statistics),
                # 淇濈暀鍘熷鏁版嵁鐢ㄤ簬璋冭瘯
                "raw_data": {
                    "testpoint_mappings": testpoint_mapping_info,
                    "fault_mappings": fault_mapping_info,
                    "testpoint_statistics": testpoint_statistics,
                    "fault_statistics": fault_statistics,
                    "component_statistics": component_statistics,
                    "component_scores": component_scores
                }
            }
            
            logger.info(f"閮ㄤ欢璇︽儏鑾峰彇瀹屾垚: {component_name}, 娴嬬偣鏁? {len(testpoint_statistics)}, 鏁呴殰鏁? {len(fault_statistics)}")
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"鑾峰彇閮ㄤ欢璇︽儏澶辫触: {e}")
            return Response({"error": f"鑾峰彇閮ㄤ欢璇︽儏澶辫触: {str(e)}"}, status=500)

    def _get_latest_msfg_health(self, request: Request) -> Response:
        """
        鑾峰彇鎸囧畾PHM涓綋鐨勬渶鏂癕SFG鏁存満鍋ュ悍鍒嗘暟
        
        鍙傛暟:
        - cmg_id: PHM鏁版嵁搴揑D
        """
        try:
            # 鑾峰彇璇锋眰鍙傛暟
            cmg_id = request.query_params.get("cmg_id")
            
            logger.info(f"鏈€鏂癕SFG鍋ュ悍鍒嗘暟API璋冪敤 - cmg_id: {cmg_id}")
            
            if not cmg_id:
                logger.error("鏈€鏂癕SFG鍋ュ悍鍒嗘暟API璋冪敤澶辫触: 缂哄皯cmg_id鍙傛暟")
                return Response({"error": "cmg_id is required"}, status=400)
            
            # 楠岃瘉PHM涓綋鏄惁瀛樺湪
            try:
                cmg = PHM.objects.get(id=cmg_id)
                logger.info(f"鎵惧埌PHM涓綋 - 鏁版嵁搴揑D: {cmg.id}, 鍚嶇О: {cmg.cmg_id}")
            except PHM.DoesNotExist:
                logger.error(f"PHM涓綋涓嶅瓨鍦? {cmg_id}")
                return Response({"error": "PHM涓綋涓嶅瓨鍦?}, status=404)
            
            # 瀵煎叆鐩稿叧妯″瀷
            from msfg_analysis.models import MSFGAnalysisResult
            from health_management.models import IMSDetectionResult
            from django.db.models import Q, Count
            
            # 馃敡 鏅鸿兘鍋ュ悍鍒嗘暟绛栫暐锛氬熀浜庡紓甯稿抚姣斾緥鍐冲畾鏄惁鎺掗櫎姝ｅ父甯?            logger.info(f"========== 寮€濮嬫櫤鑳藉仴搴峰垎鏁拌绠楋細PHM {cmg.cmg_id} ==========")
            
            # 1. 缁熻鎬诲抚鏁帮紙PHMData鍘熷鏁版嵁鐐癸級鍜孖MS寮傚父甯ф暟
            logger.info(f"姝ラ1锛氱粺璁℃€绘暟鎹抚鏁板拰IMS寮傚父甯ф暟")
            total_frames = PHMData.objects.filter(
                cmg_id=cmg_id
            ).count()
            logger.info(f"  鈫?鏌ヨ鏉′欢锛歝mg_id={cmg_id}")
            logger.info(f"  鈫?鎬绘暟鎹抚鏁帮紙PHMData锛? {total_frames}")
            
            anomaly_frames = IMSDetectionResult.objects.filter(
                data_point__cmg_id=cmg_id,
                is_anomaly=True
            ).count()
            logger.info(f"  鈫?鏌ヨ鏉′欢锛歞ata_point__cmg_id={cmg_id}, is_anomaly=True")
            logger.info(f"  鈫?IMS寮傚父甯ф暟: {anomaly_frames}")
            
            normal_frames = total_frames - anomaly_frames
            logger.info(f"  鈫?姝ｅ父甯ф暟: {normal_frames}")
            
            # 2. 璁＄畻寮傚父甯ф瘮渚?            logger.info(f"姝ラ2锛氳绠楀紓甯稿抚姣斾緥")
            if total_frames > 0:
                anomaly_ratio = anomaly_frames / total_frames
                logger.info(f"  鈫?璁＄畻鍏紡锛歿anomaly_frames} / {total_frames} = {anomaly_ratio:.6f}")
                logger.info(f"  鈫?寮傚父甯ф瘮渚嬶細{anomaly_ratio*100:.4f}%")
            else:
                anomaly_ratio = 0
                logger.info(f"  鈫?鎬诲抚鏁颁负0锛屽紓甯告瘮渚嬭涓?")
            
            # 3. 鏍规嵁寮傚父甯ф瘮渚嬪喅瀹氭煡璇㈢瓥鐣?            logger.info(f"姝ラ3锛氭牴鎹紓甯稿抚姣斾緥閫夋嫨鏌ヨ绛栫暐")
            threshold = 0.01
            logger.info(f"  鈫?鍒ゆ柇闃堝€硷細{threshold*100:.2f}%")
            logger.info(f"  鈫?褰撳墠姣斾緥锛歿anomaly_ratio*100:.4f}%")
            logger.info(f"  鈫?姣旇緝缁撴灉锛歿anomaly_ratio} {'>' if anomaly_ratio > threshold else '鈮?} {threshold}")
            
            if anomaly_ratio > 0.01:  # 寮傚父甯ф瘮渚?> 1%
                # 绛栫暐A锛氭帓闄ゆ甯稿抚锛堝彧鐪嬪紓甯稿抚锛?                logger.info(f"  鈫?閫夋嫨绛栫暐锛氱瓥鐣锛堟帓闄ゆ甯稿抚锛屽彧缁熻寮傚父甯э級")
                logger.info(f"  鈫?鍘熷洜锛氬紓甯稿抚姣斾緥 {anomaly_ratio*100:.4f}% > 1%锛岃鏄庣‘瀹炴湁绯荤粺鎬ч棶棰?)
                latest_msfg_result = MSFGAnalysisResult.objects.filter(
                    data_point__cmg_id=cmg_id,
                    overall_health_score__lt=0.9999  # 鎺掗櫎榛樿鍊?.0
                ).order_by('-created_at').first()
                logger.info(f"  鈫?鏌ヨ绛栫暐锛氬彧鏌ヨ overall_health_score < 0.9999 鐨勮褰?)
            else:
                # 绛栫暐B锛氬叏灞€鍔犳潈锛堝寘鍚甯稿抚鍜屽紓甯稿抚锛?                logger.info(f"  鈫?閫夋嫨绛栫暐锛氱瓥鐣锛堝叏灞€鍔犳潈锛屽寘鍚墍鏈夊抚锛?)
                logger.info(f"  鈫?鍘熷洜锛氬紓甯稿抚姣斾緥 {anomaly_ratio*100:.4f}% 鈮?1%锛屽彲鑳芥槸鍋跺彂寮傚父")
                latest_msfg_result = MSFGAnalysisResult.objects.filter(
                    data_point__cmg_id=cmg_id
                ).order_by('-created_at').first()
                logger.info(f"  鈫?鏌ヨ绛栫暐锛氭煡璇㈡墍鏈夎褰曪紙鍖呭惈姝ｅ父甯у拰寮傚父甯э級")
            
            if latest_msfg_result:
                health_score = latest_msfg_result.overall_health_score
                is_default_value = abs(health_score - 1.0) < 0.0001
                logger.info(f"鎵惧埌PHM {cmg.cmg_id} 鐨勬渶鏂癕SFG鍋ュ悍鍒嗘暟: {health_score} "
                          f"{'(姝ｅ父甯?' if is_default_value else '(寮傚父甯?'}, "
                          f"绛栫暐={'A(鎺掗櫎姝ｅ父甯?' if anomaly_ratio > 0.01 else 'B(鍏ㄥ眬鍔犳潈)'}")
                
                return Response({
                    "cmg_id": cmg.cmg_id,
                    "cmg_name": cmg.name,
                    "health_score": health_score,
                    "timestamp": latest_msfg_result.data_point.timestamp.isoformat(),
                    "msfg_definition": latest_msfg_result.msfg_definition.name if latest_msfg_result.msfg_definition else None,
                    "has_data": True
                })
            else:
                logger.info(f"PHM {cmg.cmg_id} 娌℃湁MSFG鍒嗘瀽缁撴灉")
                return Response({
                    "cmg_id": cmg.cmg_id,
                    "cmg_name": cmg.name,
                    "health_score": None,
                    "timestamp": None,
                    "msfg_definition": None,
                    "has_data": False
                })
                
        except Exception as e:
            logger.error(f"鑾峰彇鏈€鏂癕SFG鍋ュ悍鍒嗘暟澶辫触: {e}")
            return Response({"error": f"鑾峰彇鏈€鏂癕SFG鍋ュ悍鍒嗘暟澶辫触: {str(e)}"}, status=500)

    def delete(self, request: Request) -> Response:
        """鍒犻櫎寮傚父甯э紙浜哄伐鍒ゅ畾涓鸿櫄璀︼級"""
        action = request.query_params.get("action")
        
        if action == "delete_anomaly_frame":
            return self._delete_anomaly_frame(request)
        else:
            return Response({"error": "Invalid action. Use 'delete_anomaly_frame'"}, status=400)
    
    def _delete_anomaly_frame(self, request: Request) -> Response:
        """
        鍒犻櫎鎸囧畾鐨勫紓甯稿抚璁板綍锛堜汉宸ュ垽瀹氫负铏氳锛?        
        鍙傛暟:
        - frame_id: IMS妫€娴嬬粨鏋滅殑ID
        """
        frame_id = request.query_params.get("frame_id")
        
        logger.info(f"鍒犻櫎寮傚父甯ц姹?- frame_id: {frame_id}")
        
        if not frame_id:
            logger.error("frame_id鍙傛暟缂哄け")
            return Response({"error": "frame_id is required"}, status=400)
        
        try:
            # 鑾峰彇IMS妫€娴嬬粨鏋?            from health_management.models import IMSDetectionResult
            
            try:
                ims_result = IMSDetectionResult.objects.get(id=frame_id)
                logger.info(f"鎵惧埌寮傚父甯?- ID: {ims_result.id}, PHM: {ims_result.data_point.cmg.cmg_id}, 鏃堕棿鎴? {ims_result.data_point.timestamp}")
            except IMSDetectionResult.DoesNotExist:
                logger.error(f"寮傚父甯т笉瀛樺湪: {frame_id}")
                return Response({"error": "寮傚父甯т笉瀛樺湪"}, status=404)
            
            # 璁板綍琚垹闄ょ殑淇℃伅锛堢敤浜庢棩蹇楋級
            cmg_info = ims_result.data_point.cmg.cmg_id
            timestamp_info = ims_result.data_point.timestamp.isoformat()
            score_info = ims_result.anomaly_score
            
            # 鍒犻櫎IMS妫€娴嬬粨鏋滆褰?            ims_result.delete()
            
            logger.info(f"鎴愬姛鍒犻櫎寮傚父甯?- frame_id: {frame_id}, PHM: {cmg_info}, 鏃堕棿鎴? {timestamp_info}, 鍒嗘暟: {score_info}")
            
            return Response({
                "success": True,
                "message": "寮傚父甯у凡鎴愬姛鍒犻櫎",
                "deleted_frame": {
                    "id": frame_id,
                    "cmg_id": cmg_info,
                    "timestamp": timestamp_info,
                    "score": score_info
                }
            })
            
        except Exception as e:
            logger.error(f"鍒犻櫎寮傚父甯уけ璐? {e}", exc_info=True)
            return Response({"error": f"鍒犻櫎寮傚父甯уけ璐? {str(e)}"}, status=500)


class TimelineDataView(APIView):
    """涓烘暟鎹椂闂磋酱鎻愪緵鐙珛鐨勬暟鎹帴鍙?""
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        cmg_pk = request.query_params.get("cmg_id")
        if not cmg_pk:
            return Response({"detail": "cmg_id (pk) is required"}, status=400)

        try:
            cmg = PHM.objects.get(pk=cmg_pk)
        except (PHM.DoesNotExist, ValueError):
            return Response({"detail": "PHM not found"}, status=404)

        timestamps = PHMData.objects.filter(cmg=cmg).order_by("timestamp").values_list("timestamp", flat=True)
        if not timestamps:
            return Response([])

        anomaly_timestamps = set(IMSDetectionResult.objects.filter(
            data_point__cmg=cmg,
            is_anomaly=True
        ).values_list("data_point__timestamp", flat=True))

        segments = []
        if timestamps:
            from datetime import timedelta
            time_threshold = timedelta(minutes=1)
            current_segment_start = timestamps[0]
            current_segment_has_anomaly = False

            for i in range(1, len(timestamps)):
                prev_ts = timestamps[i-1]
                current_ts = timestamps[i]

                if prev_ts in anomaly_timestamps:
                    current_segment_has_anomaly = True

                if current_ts - prev_ts > time_threshold:
                    segments.append({
                        "start": current_segment_start.isoformat(),
                        "end": prev_ts.isoformat(),
                        "has_anomaly": current_segment_has_anomaly
                    })
                    current_segment_start = current_ts
                    current_segment_has_anomaly = False
            
            if timestamps[len(timestamps)-1] in anomaly_timestamps:
                current_segment_has_anomaly = True
            segments.append({
                "start": current_segment_start.isoformat(),
                "end": timestamps[len(timestamps)-1].isoformat(),
                "has_anomaly": current_segment_has_anomaly
            })

        return Response(segments)


class RealtimeDetectionView(APIView):
    """
    瀹炴椂妫€娴婣PI - 绠€鍖栫増
    鎺ユ敹鏂囦欢涓婁紶锛屾墽琛屾娴嬶紝鐩存帴杩斿洖鍐呭瓨涓殑妫€娴嬬粨鏋?    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser]
    
    def post(self, request: Request) -> Response:
        """
        澶勭悊鏂囦欢涓婁紶鍜屾娴嬭姹?        """
        import tempfile
        import os
        from .batch_processing import BatchFileProcessor
        
        try:
            # 楠岃瘉鍙傛暟
            if 'file' not in request.FILES:
                return Response({'error': '娌℃湁涓婁紶鏂囦欢'}, status=400)
            
            cmg_id = request.data.get('cmg_id')
            if not cmg_id:
                return Response({'error': '缂哄皯PHM ID'}, status=400)
            
            detection_mode = request.data.get('detection_mode', 'full')
            save_results = True  # 寮哄埗淇濆瓨缁撴灉鍒版暟鎹簱锛堜緵鍏朵粬妯″潡浣跨敤锛?            return_memory_results = request.data.get('return_memory_results', 'false').lower() == 'true'
            
            logger.info(f"瀹炴椂妫€娴嬶細寮哄埗淇濆瓨缁撴灉鍒版暟鎹簱锛堜緵鍚庣画妯″潡浣跨敤锛?)
            
            # 鑾峰彇鏁版嵁澶勭悊鍙傛暟
            max_rows = request.data.get('max_rows')
            if max_rows:
                try:
                    max_rows = int(max_rows)
                    logger.debug(f"璁剧疆鏈€澶у鐞嗚鏁? {max_rows}")
                except (ValueError, TypeError):
                    max_rows = None
            
            add_milliseconds = request.data.get('add_milliseconds', 'false').lower() == 'true'
            
            # 鑾峰彇PHM瀵硅薄
            try:
                cmg = PHM.objects.get(id=cmg_id)
            except PHM.DoesNotExist:
                return Response({'error': 'PHM涓嶅瓨鍦?}, status=404)
            
            # 淇濆瓨涓婁紶鐨勬枃浠跺埌涓存椂鐩綍
            uploaded_file = request.FILES['file']
            logger.debug(f"鏀跺埌鏂囦欢涓婁紶: {uploaded_file.name}, 澶у皬: {uploaded_file.size} bytes")
            
            with tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=os.path.splitext(uploaded_file.name)[1]
            ) as tmp_file:
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            try:
                # 鎵ц妫€娴?                logger.debug(f"寮€濮嬪疄鏃舵娴? PHM={cmg.cmg_id}, 鏂囦欢={uploaded_file.name}, 妯″紡={detection_mode}")
                
                # 璋冪敤batch_processing鐨勬娴嬮€昏緫
                processor = BatchFileProcessor()
                results = processor.process_file_for_detection(
                    file_path=tmp_file_path,
                    cmg=cmg,
                    detection_mode=detection_mode,
                    save_to_db=save_results,
                    return_details=return_memory_results,
                    max_rows=max_rows,  # 浼犻€掓渶澶ц鏁板弬鏁?                    add_milliseconds=add_milliseconds  # 浼犻€掓椂闂存埑澶勭悊鍙傛暟
                )
                
                logger.debug(f"妫€娴嬪畬鎴? 鎬诲抚鏁?{results['total_frames']}, 寮傚父鏁?{results['anomaly_count']}")
                
                return Response({
                    'success': True,
                    'message': '妫€娴嬪畬鎴?,
                    'results': results
                }, status=200)
                
            finally:
                # 娓呯悊涓存椂鏂囦欢
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                    logger.debug(f"涓存椂鏂囦欢宸叉竻鐞? {tmp_file_path}")
            
        except Exception as e:
            logger.error(f"瀹炴椂妫€娴嬪け璐? {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=500)




