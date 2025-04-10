from typing import Callable

from database.duckdb import Database

type BenchmarkRunnerFunc = Callable[[Database, int], list[str]]
type BenchmarkEpocFunc = Callable[[Database], list[str]]
type BenchmarkSetupFunc = Callable[[Database], None]