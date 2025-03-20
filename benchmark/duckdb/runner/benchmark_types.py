from typing import Callable

from database.duckdb import Database

type BenchmarkRunnerFunc = Callable[[Database], None]
type BenchmarkSetupFunc = Callable[[Database], None]