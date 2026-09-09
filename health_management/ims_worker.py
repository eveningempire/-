from __future__ import annotations

import os
import time
import traceback
from multiprocessing import Process, Queue, Event
from typing import List, Optional


class _IMSTask:
    def __init__(self, record_ids: List[int]) -> None:
        self.record_ids = record_ids


def _worker_loop(task_queue: Queue, stop_event: Event) -> None:
    """Worker process entrypoint. Initializes Django and processes tasks."""
    try:
        # Ensure Django settings for spawned process (Windows uses spawn)
        if "DJANGO_SETTINGS_MODULE" not in os.environ:
            os.environ["DJANGO_SETTINGS_MODULE"] = "phm_backend.settings"
        import django  # type: ignore
        # Ensure Django is initialized in the child process
        django.setup()

        from data_management.models import PHMData  # type: ignore
        from .ims_service import run_ims_detection  # type: ignore

        while not stop_event.is_set():
            try:
                try:
                    task: _IMSTask = task_queue.get(timeout=0.5)  # type: ignore
                except Exception:
                    continue

                # Fetch records in one query if possible
                ids = list(task.record_ids)
                if not ids:
                    continue
                records = list(PHMData.objects.filter(id__in=ids).select_related("cmg"))
                for rec in records:
                    try:
                        run_ims_detection(rec)
                    except Exception:
                        traceback.print_exc()
                        continue
            except KeyboardInterrupt:
                break
            except Exception:
                traceback.print_exc()
                time.sleep(0.1)
    except Exception:
        traceback.print_exc()


class IMSWorkerManager:
    """Manages a background process dedicated to running IMS detection."""

    def __init__(self) -> None:
        self._proc: Optional[Process] = None
        self._queue: Optional[Queue] = None
        self._stop: Optional[Event] = None

    def start(self) -> None:
        if self._proc is not None and self._proc.is_alive():
            return
        # Multiprocessing requires spawn-safe setup (Windows)
        self._queue = Queue()
        self._stop = Event()
        self._proc = Process(target=_worker_loop, args=(self._queue, self._stop), name="IMS-Worker", daemon=True)
        self._proc.start()

    def stop(self, timeout: float = 3.0) -> None:
        if self._proc is None:
            return
        try:
            if self._stop is not None:
                self._stop.set()
            if self._proc.is_alive():
                self._proc.join(timeout=timeout)
        finally:
            if self._proc.is_alive():
                try:
                    self._proc.terminate()
                except Exception:
                    pass
            self._proc = None
            self._queue = None
            self._stop = None

    def enqueue_record_ids(self, record_ids: List[int]) -> None:
        if not record_ids:
            return
        if self._queue is None or self._proc is None or not self._proc.is_alive():
            self.start()
        # Chunk large batches to avoid huge messages
        CHUNK = 200
        for i in range(0, len(record_ids), CHUNK):
            chunk = record_ids[i : i + CHUNK]
            try:
                assert self._queue is not None
                self._queue.put(_IMSTask(chunk))
            except Exception:
                traceback.print_exc()


# Global singleton instance
ims_worker = IMSWorkerManager()


def enqueue_cmgdata_ids(record_ids: List[int]) -> None:
    ims_worker.enqueue_record_ids(record_ids)



