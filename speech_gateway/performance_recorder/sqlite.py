from dataclasses import fields
from datetime import datetime, timezone
import queue
import sqlite3
import threading
from . import PerformanceRecorder, PerformanceRecord


class SQLitePerformanceRecorder(PerformanceRecorder):
    def __init__(self, db_path="performance.db"):
        self.db_path = db_path
        self.record_queue = queue.Queue()
        self.stop_event = threading.Event()

        self.init_db()

        self.worker_thread = threading.Thread(target=self.start_worker, daemon=True)
        self.worker_thread.start()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS performance_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        process_id TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        source TEXT,
                        text TEXT,
                        audio_format TEXT,
                        cached INTEGER,
                        elapsed REAL
                    )
                    """
                )
        finally:
            conn.close()

    def start_worker(self):
        conn = sqlite3.connect(self.db_path)
        try:
            while not self.stop_event.is_set() or not self.record_queue.empty():
                try:
                    record = self.record_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                self.insert_record(conn, record)
                self.record_queue.task_done()
        finally:
            conn.close()

    def insert_record(self, conn: sqlite3.Connection, record: PerformanceRecord):
        columns = [field.name for field in fields(PerformanceRecord)] + ["created_at"]
        placeholders = ["?"] * len(columns)
        values = [getattr(record, field.name) for field in fields(PerformanceRecord)] + [datetime.now(timezone.utc)]
        sql = f"INSERT INTO performance_records ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        conn.execute(sql, values)
        conn.commit()

    def record(
        self,
        *,
        process_id: str,
        source: str = None,
        text: str = None,
        audio_format: str = None,
        cached: int = 0,
        elapsed: float = None,
    ):
        performance_record = PerformanceRecord(
            process_id=process_id,
            source=source,
            text=text,
            audio_format=audio_format,
            cached = cached,
            elapsed = elapsed
        )

        self.record_queue.put(performance_record)

    def close(self):
        self.stop_event.set()
        self.record_queue.join()
        self.worker_thread.join()
