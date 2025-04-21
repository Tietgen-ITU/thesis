from dataclasses import dataclass
import argparse
import datetime
import os
from threading import Thread
import time
from typing import Callable
from runner.factory import create_benchmark_runner
from device.nvme import NvmeDevice, setup_device, calculate_waf
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
    mount_path: str = None

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
            help="Use the generic device path for the benchmark",
            action="store_true",
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

        parser.add_argument(
            "-mp",
            "--mount_path",
            type=str,
            help="Mount path to use for the benchmark",
            default=None
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
            benchmark=args.benchmark,
            mount_path=args.mount_path
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

    device = NvmeDevice(args.device)
    def setup_nvme(buffer_manager_size: int):
        device_namespace = setup_device(device, enable_fdp=args.use_fdp)
        device_path = device_namespace.get_generic_device_path() if args.use_generic_device else device_namespace.get_device_path()

        print(f"Using device path: {device_path}")

        # Ensure that the extension is loaded and the
        config = duckdb.ConnectionConfig(
            device_path, 
            args.io_backend, 
            args.use_fdp)
        db = duckdb.connect("nvmefs:///bench.db", config)
        db.query(f"SET memory_limit='{buffer_manager_size}MB';")
        db.query("PRAGMA disable_object_cache;")

        return db, device
    
    def setup_normal(buffer_manager_size: int):

        db: duckdb.Database = duckdb.connect("bench.db")
        db.query(f"SET memory_limit='{buffer_manager_size}MB';")
        db.query("PRAGMA disable_object_cache;")

        return db, device

    return setup_nvme if args.mount_path is None else setup_normal

RUN_MEASUREMENT = True
def start_device_measurements(device: NvmeDevice, file_name: str):
    """
    Start the device measurements for the benchmark and returns that thread running the task
    """

    def run(device: NvmeDevice, file: str):
        previous_host_written = 0
        previous_media_written = 0
        global RUN_MEASUREMENT

        waf_file = open(file, "w+", newline="\n")

        while RUN_MEASUREMENT:
            time.sleep(600)
            host_written, media_written = device.get_written_bytes()
            if host_written == 0:
                continue

            # Calculate the Write Amplification Factor (WAF)
            diff_host_written = host_written - previous_host_written
            diff_media_written = media_written - previous_media_written
            waf = calculate_waf(diff_host_written, diff_media_written)

            # Write the results to the CSV file
            waf_file.write(f"{datetime.now()};{diff_host_written},{diff_media_written};{waf}\n")

            previous_host_written = host_written
            previous_media_written = media_written

        # Ensure that the data is written to file
        waf_file.flush()
        os.fsync(waf_file.fileno())
        waf_file.close()
    
    waf_measurement_runner = Thread(target=run, args=(device, file_name))
    waf_measurement_runner.start()
    def stop_measurement():
        global RUN_MEASUREMENT
        RUN_MEASUREMENT = False
        waf_measurement_runner.join()

        return

    return stop_measurement


if __name__ == "__main__":

    args: Arguments = Arguments.parse_args()
    setup_device_and_db = prepare_setup_func(args)

    fdp_name = "fdp" if args.use_fdp else "nofdp"
    name = f"duckdb-bench-{args.io_backend}-{args.scale_factor}-{fdp_name}" 
    device_output_file = f"{name}-device.csv"
    output_file = f"{name}.csv"

    run_benchmark, setup_benchmark = create_benchmark_runner(args.benchmark)

    # Setup the database with the correct device config
    db, device = setup_device_and_db(args.buffer_manager_mem_size)

    setup_benchmark(db)

    # NOTE: The connection is not thread-safe, search for duckdb cursor in the client library to see how to use in a multi-threaded environment
    stop_measurement = start_device_measurements(device, device_output_file)
    metric_results = run_benchmark(db, args.duration) 
    stop_measurement()
    
    # Write the metric results to a CSV file

    with open(output_file, mode="w", newline="\n") as file:
        # Write the rows
        for result in metric_results:
            file.write(result)
    
    device.clean_device()

    print(f"Benchmark results written to {output_file} and WAF results written to {device_output_file}")
