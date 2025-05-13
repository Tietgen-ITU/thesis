import time
from . import benchmark_types, tpch, oocha


def create_benchmark_runner(name: str) -> tuple[benchmark_types.BenchmarkRunnerFunc, benchmark_types.BenchmarkSetupFunc]:

    def create_runner_function(benchmark: benchmark_types.BenchmarkEpochFunc) -> benchmark_types.BenchmarkRunnerFunc:
        """
        Create a benchmark runner function that runs the benchmark for a specified duration.
        :param benchmark: The benchmark function to run.
        :return: A function that runs the benchmark for a specified duration.
        """
        def wrapper(db: benchmark_types.Database, duration_minutes: int) -> list[str]:

            def get_time():
                # Return the current time in minutes
                return time.monotonic() / 60

            start_time = get_time()
            delta = 0
            consolidated_results: list[str] = []

            print(f"Running benchmark '{name}' for {duration_minutes} minutes...")

            while delta < duration_minutes:
                # Run the benchmark
                results = benchmark(db)

                consolidated_results.extend(results)

                delta = get_time() - start_time

            return consolidated_results
    
        return wrapper

    if name == tpch.TPCH_BENCHMARK_NAME:
        return create_runner_function(tpch.run_tpch_epoch_benchmark), tpch.setup_tpch_benchmark 
    
    raise ValueError(f"Unknown benchmark '{name}'")