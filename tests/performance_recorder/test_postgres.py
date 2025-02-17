import os
import pytest
import threading
from time import sleep
from speech_gateway.performance_recorder.postgres import PostgreSQLPerformanceRecorder

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DBNAME = os.getenv("POSTGRES_DBNAME")


@pytest.fixture
def postgres_recorder(tmp_path):
    recorder = PostgreSQLPerformanceRecorder(
        dbname=POSTGRES_DBNAME,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    yield recorder
    conn = recorder.connect_db()
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE performance_records;")
    conn.commit()
    conn.close()
    recorder.close()

def test_single_thread_record_and_close(postgres_recorder):
    """
    Verify that the record -> close flow finishes without deadlocks 
    in a single-thread scenario, and confirm the correct number of rows is inserted.
    Also, check that the 'id' field is auto-incrementing correctly.
    """
    # Insert 5 records
    for i in range(5):
        postgres_recorder.record(
            process_id=f"process_{i}",
            source="test_source",
            text=f"test_text_{i}",
            audio_format="wav",
            cached=0,
            elapsed=0.01 * i,
        )

    # Although close() will be called by the fixture teardown,
    # here we explicitly call it for clarity.
    postgres_recorder.close()

    # Directly open the database to check how many records were inserted
    conn = postgres_recorder.connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM performance_records;")
        count = cursor.fetchone()[0]
        assert count == 5, f"Expected 5 records, got {count}"

        # Retrieve all IDs in ascending order
        cursor.execute("SELECT id FROM performance_records ORDER BY id;")
        ids = [row[0] for row in cursor.fetchall()]

        # Confirm we have 5 IDs
        assert len(ids) == 5, f"Expected 5 IDs, got {len(ids)}"

        # Check they are strictly increasing by 1
        for i in range(1, len(ids)):
            assert ids[i] == ids[i - 1] + 1, "IDs are not incrementing as expected"
    finally:
        conn.close()


def test_multi_thread_record_no_deadlock(postgres_recorder):
    """
    Verify that concurrent calls to record() do not cause deadlocks
    and that data is correctly committed to the database.
    """
    NUM_THREADS = 5
    RECORDS_PER_THREAD = 100

    def worker(thread_id: int):
        for i in range(RECORDS_PER_THREAD):
            postgres_recorder.record(
                process_id=f"thread_{thread_id}_process_{i}",
                source="test_source",
                text=f"test_text_{i}",
                audio_format="wav",
                cached=1,
                elapsed=0.1 * i,
            )
            # Sleep a bit to make concurrency testing more likely to expose issues
            sleep(0.001)

    threads = []
    for t_id in range(NUM_THREADS):
        t = threading.Thread(target=worker, args=(t_id,))
        t.start()
        threads.append(t)

    # Wait for all threads to complete
    for t in threads:
        t.join()

    # Close the recorder to ensure the queue is fully processed
    postgres_recorder.close()

    # Check that all records were indeed written to the database
    total_expected = NUM_THREADS * RECORDS_PER_THREAD
    conn = postgres_recorder.connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM performance_records;")
        count = cursor.fetchone()[0]
        assert count == total_expected, f"Expected {total_expected} records, got {count}"
    finally:
        conn.close()
