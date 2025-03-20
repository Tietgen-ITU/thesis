from database.duckdb import Database

TPCH_BENCHMARK_NAME = "name"

def setup_tpch_benchmark(db: Database):
    # TODO: Load the tpch extension to be used when running the benchmarks

    # TODO: Query if the table already exists then there is no reason to copy it over to the new db
    pass

def run_tpch_benchmark(db: Database):
    # TODO: Implement TPCH benchmark
    print("Running TPCH benchmark(not implemented yet)")
    pass