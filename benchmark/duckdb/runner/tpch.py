from database.duckdb import Database

TPCH_BENCHMARK_NAME = "name"

def setup_tpch_benchmark(db: Database):
    # TODO: Load the tpch extension to be used when running the benchmarks
    db.load_extension("tpch")

    db.query("ATTACH DATABASE 'tpch-1.db' AS tpch (READ_WRITE);") # TODO: Add parameter with file to copy data from
    db.query("COPY FROM DATABASE tpch TO bench;")
    db.query("DETACH DATABASE tpch;")

    db.query("USE bench;")

    pass

def run_tpch_benchmark(db: Database):

    for query_nr in range(1, 22):
        result = db.query(f"PRAGMA tpch({query_nr});")

        # TODO: Can we add query result verification???


    pass