from typing import Callable

from database.duckdb import Database

type BenchmarkRunnerFunc = Callable[[Database, int], list[str]]
type BenchmarkEpochFunc = Callable[[Database], list[str]]
type BenchmarkSetupFunc = Callable[[Database, str, int, int], None]