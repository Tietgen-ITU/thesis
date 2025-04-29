import os
import time
from database.duckdb import Database

TPCH_BENCHMARK_NAME = "tpch"

def setup_tpch_benchmark(db: Database, input_dir_path: str, buffer_manager_size: int, scale_factor: int):
    input_file_path = os.path.join(input_dir_path, f"tpch-{scale_factor}.db")

    db.add_extension("tpch")

    db.query(f"ATTACH DATABASE '{input_file_path}' AS tpch (READ_WRITE);")
    db.query("COPY FROM DATABASE tpch TO bench;")
    db.query("DETACH DATABASE tpch;")
    db.query(f"SET memory_limit='{buffer_manager_size}MB';")
    db.query("SET threads=1;")
    db.query("PRAGMA disable_object_cache;")
    # db.query("CALL dbgen(sf=1);")

def run_tpch_epoch_benchmark(db: Database):

    results: list[str] = []

    for query_nr in range(1, 22):
        start = time.perf_counter()
        print(f"Running TPCH query {query_nr}...")
        results = db.query(f"PRAGMA tpch({query_nr});").fetchall()
        end = time.perf_counter()

        print(f"TPCH query {query_nr} results: {results[0]}")

        # Get query elapsed time in milliseconds
        query_elapsed = (end - start) * 1000

        results.append(f"{query_nr};{query_elapsed}\n")

    return results