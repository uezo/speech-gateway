from dataclasses import fields
from datetime import datetime, timezone
import logging
import queue
import threading
import time
import psycopg2
from . import PerformanceRecorder, PerformanceRecord

logger = logging.getLogger(__name__)


class PostgreSQLPerformanceRecorder(PerformanceRecorder):
    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 5432,
        dbname: str = "speech_gateway",
        user: str = "postgres",
        password: str = None,
    ):
        self.connection_params = {
            "host": host,
            "port": port,
            "dbname": dbname,
            "user": user,
            "password": password,
        }
        self.record_queue = queue.Queue()
        self.stop_event = threading.Event()

        self.init_db()

        self.worker_thread = threading.Thread(target=self.start_worker, daemon=True)
        self.worker_thread.start()

    def connect_db(self):
        return psycopg2.connect(**self.connection_params)

    def init_db(self):
        conn = self.connect_db()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS performance_records (
                            id SERIAL PRIMARY KEY,
                            process_id TEXT NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL,
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
        conn = self.connect_db()
        try:
            while not self.stop_event.is_set() or not self.record_queue.empty():
                try:
                    record = self.record_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                try:
                    print(f"rec: {record}")
                    self.insert_record(conn, record)
                except (psycopg2.InterfaceError, psycopg2.OperationalError):
                    try:
                        conn.close()
                    except Exception:
                        pass

                    logger.warning("Connection is not available. Retrying insert_record with new connection...")
                    time.sleep(0.5)
                    conn = self.connect_db()
                    self.insert_record(conn, record)
                    print(f"rec2: {record}")

                self.record_queue.task_done()
        finally:
            try:
                conn.close()
            except Exception:
                pass


    def insert_record(self, conn, record: PerformanceRecord):
        columns = [field.name for field in fields(PerformanceRecord)] + ["created_at"]
        placeholders = ["%s"] * len(columns)
        values = [getattr(record, field.name) for field in fields(PerformanceRecord)] + [
            datetime.now(timezone.utc)
        ]

        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO performance_records ({', '.join(columns)}) VALUES ({', '.join(placeholders)})",
                values,
            )
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
            cached=cached,
            elapsed=elapsed,
        )
        self.record_queue.put(performance_record)

    def close(self):
        self.stop_event.set()
        self.record_queue.join()
        self.worker_thread.join()
