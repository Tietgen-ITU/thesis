import benchmark_types 
import tpch


def create_benchmark_runner(name: str) -> tuple[benchmark_types.BenchmarkRunnerFunc, benchmark_types.BenchmarkSetupFunc]:
    if name == tpch.TPCH_BENCHMARK_NAME:
        return tpch.run_tpch_benchmark, tpch.setup_tpch_benchmark 
    
    raise ValueError(f"Unknown benchmark '{name}'")