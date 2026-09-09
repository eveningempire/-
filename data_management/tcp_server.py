from __future__ import annotations

import asyncio
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from collections import deque, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from django.db import transaction
from django.utils import timezone

from .models import PHM, PHMData
from .realtime_cache import realtime_cache
from .redis_service import redis_service
from health_management.ims_worker import enqueue_cmgdata_ids, ims_worker


class _TCPIngestServer:
    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._server: Optional[asyncio.base_events.Server] = None
        self._executor: Optional[ThreadPoolExecutor] = None
        self._host: str = ""
        self._port: int = 0
        self._allowed_cmg_ids: Optional[set[str]] = None
        self._metrics_total_batches: int = 0
        self._metrics_total_frames: int = 0
        self._metrics_by_cmg: dict[str, dict[str, int]] = defaultdict(lambda: {"batches": 0, "frames": 0})
        self._id_map: Optional[dict[str, str]] = None  # sender_id -> platform cmg_id

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and self._server is not None

    def status(self) -> Dict[str, Any]:
        return {
            "running": self.is_running(),
            "host": self._host,
            "port": self._port,
            "allowed_cmg_ids": sorted(self._allowed_cmg_ids) if self._allowed_cmg_ids else None,
        }

    def start(self, host: str, port: int, allowed_cmg_ids: Optional[List[str]] = None, id_map: Optional[Dict[str, str]] = None) -> None:
        if self.is_running():
            # If already running on same addr, ignore; otherwise restart
            if self._host == host and self._port == port:
                return
            self.stop()

        self._host, self._port = host, port
        self._allowed_cmg_ids = set(allowed_cmg_ids) if allowed_cmg_ids else None
        self._id_map = dict(id_map) if id_map else None
        self._loop = asyncio.new_event_loop()
        # 绠楁硶妫€娴嬬敱鐙珛杩涚▼鎵ц锛岄伩鍏嶉樆濉炰笌骞叉壈
        self._executor = None

        def _run_loop() -> None:
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._start_server(self._host, self._port))
            try:
                self._loop.run_forever()
            finally:
                self._loop.close()

        self._thread = threading.Thread(target=_run_loop, name="tcp-ingest-server", daemon=True)
        self._thread.start()
        _log_event(f"TCP ingest started on {self._host}:{self._port} allowed={sorted(self._allowed_cmg_ids) if self._allowed_cmg_ids else 'ANY'} map={self._id_map if self._id_map else {}}")

    def stop(self) -> None:
        if not self.is_running():
            return
        assert self._loop is not None
        assert self._server is not None

        async def _stop() -> None:
            # 鍏抽棴鏈嶅姟鍣紝涓嶅啀鎺ュ彈鏂拌繛鎺?
            self._server.close()
            await self._server.wait_closed()
            
            # 鍙栨秷鎵€鏈夊墿浣欑殑浠诲姟
            tasks = [task for task in asyncio.all_tasks(self._loop) 
                    if not task.done() and task != asyncio.current_task()]
            if tasks:
                _log_event(f"Cancelling {len(tasks)} pending tasks")
                for task in tasks:
                    task.cancel()
                # 绛夊緟浠诲姟鍙栨秷瀹屾垚
                await asyncio.gather(*tasks, return_exceptions=True)
            
            self._server = None
            self._loop.stop()

        try:
            future = asyncio.run_coroutine_threadsafe(_stop(), self._loop)
            future.result(timeout=5)  # 绛夊緟鏈€澶?绉?
        except Exception as e:
            _log_event(f"Error during stop: {e}")
        
        if self._thread:
            self._thread.join(timeout=3)
            if self._thread.is_alive():
                _log_event("Warning: TCP thread did not stop cleanly")
        
        # 娓呯悊绾跨▼姹犳墽琛屽櫒
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
        
        # 鍋滄IMS瀛愯繘绋嬶紙鑻ョ┖闂插彲瀹夊叏閫€鍑猴級
        try:
            ims_worker.stop()
        except Exception:
            pass
            
        self._thread = None
        self._loop = None
        _log_event("TCP ingest stopped")

    async def _start_server(self, host: str, port: int) -> None:
        self._server = await asyncio.start_server(self._handle_client, host, port)

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        _log_event(f"client connected: {peer}")
        
        try:
            while True:
                try:
                    # 娣诲姞瓒呮椂浠ラ伩鍏嶆棤闄愮瓑寰?
                    line = await asyncio.wait_for(reader.readline(), timeout=30.0)
                    if not line:
                        _log_event(f"client {peer} disconnected (no data)")
                        break
                    
                    try:
                        batch = json.loads(line.decode("utf-8").strip())
                    except Exception as e:
                        _log_event(f"json decode error from {peer}: {e}")
                        continue
                        
                    try:
                        await self._process_batch(batch)
                    except Exception as e:
                        # 鎵撳嵃鏀跺埌鐨勬暟鎹憳瑕侊紝渚夸簬瀹氫綅寮傚父
                        cmg_id = batch.get("cmg_id")
                        frames = batch.get("frames")
                        fps = batch.get("frame_rate")
                        _log_event(f"process batch error: {e} cmg={cmg_id} fps={fps} frames_type={type(frames).__name__} len={len(frames) if isinstance(frames, list) else 'n/a'}")
                        continue
                        
                except asyncio.TimeoutError:
                    _log_event(f"client {peer} timeout (30s), closing connection")
                    break
                except asyncio.CancelledError:
                    _log_event(f"client {peer} task cancelled")
                    break
                except ConnectionResetError:
                    _log_event(f"client {peer} connection reset")
                    break
                except Exception as e:
                    _log_event(f"read error {peer}: {e}")
                    break
        finally:
            # 纭繚杩炴帴琚纭叧闂?
            try:
                if not writer.is_closing():
                    writer.close()
                    await writer.wait_closed()
            except Exception as e:
                _log_event(f"error closing connection {peer}: {e}")
            _log_event(f"client closed: {peer}")

    async def _process_batch(self, batch: Dict[str, Any]) -> None:
        # Run blocking DB operations off the event loop
        await asyncio.to_thread(self._process_batch_sync, batch)

    def _process_batch_sync(self, batch: Dict[str, Any]) -> None:
        cmg_id: Optional[str] = batch.get("cmg_id")
        # 鍙€夋槧灏勶細灏嗗彂閫佺ID鏄犲皠涓哄钩鍙板唴閮?cmg_id
        if self._id_map and cmg_id in self._id_map:
            cmg_id = self._id_map[cmg_id]
        frames: List[Dict[str, Any]] = batch.get("frames", [])
        if not cmg_id or not frames:
            return
        try:
            cmg = PHM.objects.get(cmg_id=cmg_id)
        except PHM.DoesNotExist:
            _log_event(f"unknown cmg_id, dropped: {cmg_id}")
            return

        if self._allowed_cmg_ids is not None and cmg_id not in self._allowed_cmg_ids:
            _log_event(f"cmg not allowed, dropped: {cmg_id}")
            return

        # Parse frames -> (timestamp, data)
        rows: List[Tuple[datetime, Dict[str, Any]]] = []
        # 寮€鍙戦樁娈碉細蹇界暐甯у唴鏃堕棿鎴筹紝浣跨敤褰撳墠鏈満鏃堕棿浣滀负瀛樺偍鏃堕棿锛?
        # 涓洪伩鍏嶅悓涓€鎵规鍞竴绾︽潫鍐茬獊锛屽姣忓抚鍔犲井绉掔骇閫掑銆?
        base_now = timezone.now()
        for idx, f in enumerate(frames):
            ts = base_now + timedelta(microseconds=idx)
            data = {k: v for k, v in f.items() if k not in {"ts", "timestamp"}}
            rows.append((ts, data))

        if not rows:
            return

        # Deduplicate within batch and filter existing timestamps
        latest_by_ts: Dict[datetime, Dict[str, Any]] = {}
        for ts, data in rows:
            latest_by_ts[ts] = data
        candidate_ts = list(latest_by_ts.keys())
        existing_ts = set(
            PHMData.objects.filter(cmg=cmg, timestamp__in=candidate_ts).values_list("timestamp", flat=True)
        )
        _log_event(f"dedupe summary cmg={cmg_id}: unique={len(candidate_ts)} existing={len(existing_ts)}")
        to_create = [
            PHMData(cmg=cmg, timestamp=ts, data=latest_by_ts[ts])
            for ts in candidate_ts
            if ts not in existing_ts
        ]
        if not to_create:
            _log_event(f"batch for {cmg_id}: created=0 skipped={len(rows)}")
            return
        new_timestamps = [ts for ts in candidate_ts if ts not in existing_ts]
        # 鍚屾椂鍐欏叆鏁版嵁搴撳拰瀹炴椂缂撳瓨
        with transaction.atomic():
            PHMData.objects.bulk_create(to_create, ignore_conflicts=True)
        
        # 鍐欏叆瀹炴椂缂撳瓨锛堟棤璁烘暟鎹簱鍐欏叆鏄惁鎴愬姛锛?
        cache_data = [(ts, latest_by_ts[ts]) for ts in new_timestamps]
        if cache_data:
            realtime_cache.add_batch_data(cmg_id, cache_data)
            
            # Store to Redis cache for better performance
            redis_data = []
            for ts, data in cache_data:
                redis_data.append({
                    'timestamp': ts.isoformat(),
                    'data': data
                })
            
            if redis_data:
                redis_service.cache_realtime_data(cmg_id, redis_data)
                # Notify WebSocket clients
                redis_service.notify_realtime_update(cmg_id, redis_data[:10])  # 鍙帹閫佹渶鏂?0鏉?
        
        # Refetch saved records to ensure PKs are populated before creating related rows
        if new_timestamps:
            saved_records = list(PHMData.objects.filter(cmg=cmg, timestamp__in=new_timestamps))
            
            # 灏嗘娴嬩换鍔℃彁浜ゅ埌鐙珛IMS杩涚▼锛堜粎浼犻€扞D锛屽瓙杩涚▼鍐呮煡璇㈠苟妫€娴嬶級
            try:
                enqueue_cmgdata_ids([r.id for r in saved_records])
            except Exception as e:
                _log_event(f"Enqueue IMS detection failed for {cmg_id}: {e}")
        fps = int(batch.get("frame_rate") or len(frames) or 0)
        created = len(to_create)
        skipped = max(0, len(rows) - created)
        self._metrics_total_batches += 1
        self._metrics_total_frames += len(frames)
        m = self._metrics_by_cmg[cmg_id]
        m["batches"] += 1
        m["frames"] += len(frames)
        _log_event(f"batch for {cmg_id}: fps={fps} frames={len(frames)} created={created} skipped={skipped}")


_server_singleton = _TCPIngestServer()
_recent_events: deque[str] = deque(maxlen=200)


def _log_event(message: str) -> None:
    # 娉ㄦ剰锛氫娇鐢ㄦ湰鍦版椂鍖虹殑褰撳墠鏃堕棿锛屼究浜庝笌鐢ㄦ埛瑙傛劅涓€鑷?
    ts = datetime.now().strftime("%H:%M:%S")
    _recent_events.append(f"[{ts}] {message}")


def start_tcp_ingest(host: str, port: int, allowed_cmg_ids: Optional[List[str]] = None, id_map: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    _server_singleton.start(host, port, allowed_cmg_ids, id_map)
    return _server_singleton.status()


def stop_tcp_ingest() -> Dict[str, Any]:
    _server_singleton.stop()
    return _server_singleton.status()


def tcp_ingest_status() -> Dict[str, Any]:
    return _server_singleton.status()


def get_recent_events() -> List[str]:
    return list(_recent_events)


def get_metrics() -> Dict[str, Any]:
    return {
        "total_batches": _server_singleton._metrics_total_batches,
        "total_frames": _server_singleton._metrics_total_frames,
        "by_cmg": _server_singleton._metrics_by_cmg,
    }



