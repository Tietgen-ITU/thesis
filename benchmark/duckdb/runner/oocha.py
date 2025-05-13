import os
import time
from database.duckdb import Database

OOCHA_BENCHMARK_NAME = "oocha"

def setup_oocha_benchmark(db: Database, input_dir_path: str, buffer_manager_size: int, scale_factor: int):
    input_file_path = os.path.join(input_dir_path, f"oocha-{scale_factor}.db")

    db.query(f"ATTACH DATABASE '{input_file_path}' AS oocha (READ_WRITE);")
    db.query("COPY FROM DATABASE oocha TO bench;")
    db.query("DETACH DATABASE oocha;")
    db.query(f"SET memory_limit='{buffer_manager_size}MB';")
    db.query("SET threads=4;")
    db.query("PRAGMA disable_object_cache;")


def run_oocha_epoch_benchmark(db: Database):

    start = time.perf_counter()
    db.query(f"""SELECT count(*) FROM (SELECT distinct(l_orderkey) FROM lineitem)""")
    end = time.perf_counter()

    # Get query elapsed time in milliseconds
    query_elapsed = (end - start) * 1000

    return [f"{query_elapsed}\n"]