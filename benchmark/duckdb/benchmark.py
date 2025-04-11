from dataclasses import dataclass
import argparse
from typing import Callable
from runner.factory import create_benchmark_runner
from device.nvme import NvmeDevice, setup_device
from database import duckdb
import csv

@dataclass
class Arguments:
    duration: int = 1
    scale_factor: int = 1
    buffer_manager_mem_size: int = 50
    device: str = ""
    io_backend: str = ""
    use_fdp: bool = False
    use_generic_device: bool = False
    benchmark: str = ""

    def valid(self) -> bool:
        print(self)
        if self.use_fdp and self.device is None:
            print("Device path is required")
            return False
        
        return True

    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "benchmark",
            type=str,
            help="Name of the benchmark to run(tpch)",
            default="tpch")

        parser.add_argument(
            "-s",
            "--sf",
            type=int,
            help="Scale factor to use for the benchmark",
            default=1)

        parser.add_argument(
            "-d",
            "--duration",
            type=int,
            help="Duration in minutes to run the benchmark",
            default=10
        )

        parser.add_argument(
            "-m",
            "--memory_limit",
            type=int,
            help="Memory limit to use for the benchmark for the buffer manager in MB",
            default=50
        )

        parser.add_argument(
            "-p",
            "--device_path",
            type=str,
            help="File path to the device to run the benchmark on(/dev/nvme1)",
            default=None
        )

        parser.add_argument(
            "-g",
            "--generic_device",
            type=bool,
            help="Use the generic device path for the benchmark",
            default=False
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
        
        arguments: Arguments = Arguments(
            duration=args.duration,
            device=args.device_path,
            scale_factor=args.sf,
            buffer_manager_mem_size=args.memory_limit,
            io_backend=args.backend,
            use_fdp=args.fdp,
            use_generic_device=args.generic_device,
            benchmark=args.benchmark
        )

        if not arguments.valid():
            parser.print_help()
            exit(1)
        
        return arguments

type SetupFunc = Callable[[int], duckdb.Database]
def prepare_setup_func(args: Arguments) -> SetupFunc:
    """
    Prepare the database configuration and database extensions that are needed depending on the storage device
    """

    # TODO: Add buffer manager size as a config parameter
    def setup_nvme(buffer_manager_size: int):
        device = NvmeDevice(args.device)
        nvme_device_path, generic_device_path = setup_device(device, enable_fdp=args.use_fdp)
        device_path = generic_device_path if args.use_generic_device else nvme_device_path

        # Ensure that the extension is loaded and the
        con = duckdb.connect(config={"allow_unsigned_extensions": "true"})
        con.load_extension("nvmefs")
        con.execute(f"""CREATE OR REPLACE PERSISTENT SECRET nvmefs (
                        TYPE NVMEFS,
                        nvme_device_path '{device.device_path}',
                        fdp_plhdls       '{7}'
                    );""")
    
        con.execute("ATTACH DATABASE 'nvmefs:///bench.db' AS bench (READ_WRITE);")
        con.close()

        config = duckdb.ConnectionConfig(
            device_path, 
            args.io_backend, 
            args.use_fdp)
        db = duckdb.connect("nvmefs:///bench.db", config)
        db.query(f"SET memory_limit='{buffer_manager_size}MB';")
        db.query("PRAGMA disable_object_cache;")

        return db
    
    def setup_normal(buffer_manager_size: int):

        db: duckdb.Database = duckdb.connect("bench.db")
        db.query(f"SET memory_limit='{buffer_manager_size}MB';")
        db.query("PRAGMA disable_object_cache;")

        return db

    return setup_nvme if args.device is not None else setup_normal


if __name__ == "__main__":

    args: Arguments = Arguments.parse_args()
    setup_database = prepare_setup_func(args)

    run_benchmark, setup_benchmark = create_benchmark_runner(args.benchmark)

    # Setup the database with the correct device config
    db: duckdb.Database = setup_database(args.buffer_manager_mem_size)

    setup_benchmark(db)

    # NOTE: The connection is not thread-safe, search for duckdb cursor in the client library to see how to use in a multi-threaded environment
    metric_results = run_benchmark(db, args.iterations) 
    
    # Write the metric results to a CSV file
    fdp_name = "fdp" if args.use_fdp else "nofdp"
    output_file = f"duckdb-bench-{args.io_backend}-{args.scale_factor}-{fdp_name}.csv"

    with open(output_file, mode="w", newline="\n") as file:
        # Write the rows
        for result in metric_results:
            file.write(result)

    print(f"Benchmark results written to {output_file}")
