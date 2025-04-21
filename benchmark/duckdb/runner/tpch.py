import time
from database.duckdb import Database

TPCH_BENCHMARK_NAME = "tpch"

def setup_tpch_benchmark(db: Database):
    # TODO: Load the tpch extension to be used when running the benchmarks
    db.add_extension("tpch")

    # db.query("ATTACH DATABASE 'tpch-1.db' AS tpch (READ_WRITE);") # TODO: Add parameter with file to copy data from
    # db.query("COPY FROM DATABASE tpch TO bench;")
    # db.query("DETACH DATABASE tpch;")
    db.query("CALL dbgen(sf=1);")

def run_tpch_epoch_benchmark(db: Database):

    results: list[str] = []

    for query_nr in range(1, 22):
        start = time.perf_counter()
        result = db.query(f"PRAGMA tpch({query_nr});")
        end = time.perf_counter()

        print(f"Query {query_nr} result: {result}")

        # Get query elapsed time in milliseconds
        query_elapsed = (end - start) * 1000

        # TODO: Add other metrics to the results?
        results.append(f"{query_nr};{query_elapsed}")

        # TODO: Can we add query result verification???

    return results