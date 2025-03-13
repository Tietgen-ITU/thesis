from dataclasses import dataclass
import argparse
from database import duckdb

@dataclass
class Arguments:
    iterations: int
    device: str
    io_backend: str
    use_fdp: bool

    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "-i",
            "--iterations",
            type=int,
            help="Number of iterations to run the benchmark",
            default=10
        )

        parser.add_argument(
            "-d",
            "--device",
            type=str,
            help="File path to the device to run the benchmark on",
            default=None
        )

        parser.add_argument(
            "-b",
            "--backend",
            type=str,
            help="Backend to use for the benchmark ('io_uring_cmd', 'io_uring')",
            default="io_uring_cmd"
        )

        parser.add_argument(
            "-f",
            "--fdp",
            action="store_true",
            help="Use file descriptor passing for the benchmark",
            default=False
        )

        args = parser.parse_args()

        return Arguments(
            iterations=args.iterations,
            device=args.device,
            io_backend=args.backend,
            use_fdp=args.fdp
        )

if __name__ == "__main__":

    args: Arguments = Arguments.parse_args()

    db: duckdb.Database = duckdb.connect("nvmefs://bench.db", args.device, args.io_backend, args.use_fdp)
    # NOTE: The connection is not thread-safe, search for duckdb cursor in the client library to see how to use in a multi-threaded environment
    db.query("CREATE TABLE test (a INTEGER, b INTEGER, c INTEGER)")
    db.query("INSERT INTO test VALUES (1, 2, 3)")
    db.query("SELECT * FROM test")