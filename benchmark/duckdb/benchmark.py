from dataclasses import dataclass
import argparse
import os
from threading import Thread
import time
from typing import Callable
from runner.factory import create_benchmark_runner
from device.nvme import NvmeDevice, setup_device, calculate_waf
from database import duckdb
from datetime import datetime

@dataclass
class Arguments:
    duration: int = 0
    parallel: int = 0
    threads: int = 1
    repetitions: int = 0
    scale_factor: int = 1
    buffer_manager_mem_size: int = 50
    device: str = ""
    io_backend: str = ""
    use_fdp: bool = False
    use_generic_device: bool = False
    benchmark: str = ""
    mount_path: str = None
    input_dir: str = "./"

    def valid(self) -> bool:
        print(self)
        if self.use_fdp and self.device is None:
            print("Device path is required")
            return False

        if (self.repetitions == 0 and self.duration == 0) or (self.repetitions != 0 and self.duration != 0):
            print("Either duration or repetitions must be set")
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
            default=0
        )

        parser.add_argument(
            "-r",
            "--repetitions",
            type=int,
            help="Amount of repetitions to run the benchmark",
            default=0
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

        parser.add_argument(
            "-i",
            "--input_directory",
            type=str,
            help="Input directory to use for the benchmark. That is the place where data files are stored and can data can be loaded from",
            default="./"
        )

        parser.add_argument(
            "-t",
            "--threads",
            type=int,
            help="Number of threads to use for the duckdb instance",
            default=1
        )

        parser.add_argument(
            "-par",
            "--parallel",
            type=int,
            help="Number of parallel executions of queries against duckdb",
            default=0
        )

        args = parser.parse_args()
        
        arguments: Arguments = Arguments(
            duration=args.duration,
            repetitions=args.repetitions,
            device=args.device_path,
            scale_factor=args.sf,
            buffer_manager_mem_size=args.memory_limit,
            io_backend=args.backend,
            use_fdp=args.fdp,
            use_generic_device=args.generic_device,
            benchmark=args.benchmark,
            mount_path=args.mount_path,
            input_dir=args.input_directory,
            threads=args.threads,
            parallel=args.parallel
        )

        if not arguments.valid():
            parser.print_help()
            exit(1)
        
        return arguments

type SetupFunc = Callable[[], duckdb.Database]
def prepare_setup_func(args: Arguments) -> SetupFunc:
    """
    Prepare the database configuration and database extensions that are needed depending on the storage device
    """

    device = NvmeDevice(args.device)
    def setup_nvme():
        device_namespace = setup_device(device, namespace_id=2, enable_fdp=args.use_fdp)
        device_path = device_namespace.get_generic_device_path() if args.use_generic_device else device_namespace.get_device_path()

        print(f"Using device path: {device_path}")

        # Ensure that the extension is loaded and the
        config = duckdb.ConnectionConfig(
            device_path, 
            args.io_backend, 
            args.use_fdp)
        duckdb.connect("nvmefs:///bench.db", config) # To set secrets first # TODO: Change this in the NvmeDatabase

        db = duckdb.connect("nvmefs:///bench.db", config)

        return db, device
    
    def setup_normal():

        normal_db_path = os.path.join(args.mount_path, "bench.db")

        setup_device(device, namespace_id=2, mount_path=args.mount_path)
        db: duckdb.Database = duckdb.connect(normal_db_path)
        temp_dir = os.path.join(args.mount_path, ".tmp")        
        db.execute(f"SET temp_directory = '{temp_dir}';")

        return db, device

    return setup_nvme if args.mount_path is None else setup_normal

def create_execution_threads(num_threads: int, benchmark_runner, db: duckdb.Database, run_with_duration: bool):
    """
    Create a list of threads to run the benchmark
    """

    threads = []
    for i in range(num_threads):
        thread = Thread(target=benchmark_runner, args=(db.create_concurrent_connection(), args.duration if run_with_duration else args.repetitions))
        threads.append(thread)
    
    return threads

def run_benchmark_threads(threads: list[Thread]):
    """
    Run the benchmark threads and return the results
    """

    for thread in threads:
        thread.start()
    
    return
    

def wait_for_completion(threads: list[Thread]):
    """
    Wait for all threads to complete
    """
    metric_results = []

    for thread in threads:
        results = thread.join()
        
        if results is not None or len(results) > 0:
            # If the thread has results, extend the metric results
            metric_results.extend(results)
    
    return metric_results

RUN_MEASUREMENT = True
def start_device_measurements(device: NvmeDevice, file_name: str):
    """
    Start the device measurements for the benchmark and returns that thread running the task
    """

    def run(device: NvmeDevice, file: str):
        os.system("sync")
        previous_host_written, previous_media_written = device.get_written_bytes_nsid(2)
        global RUN_MEASUREMENT

        waf_file = open(file, "w+", newline="\n")

        while RUN_MEASUREMENT:
            time.sleep(600)
            os.system("sync")
            host_written, media_written = device.get_written_bytes_nsid(2)
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
        print("Flushing WAF data to file")
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

    run_with_duration = args.duration > 0
    run_with_duration_display = f"dur{args.duration}" if run_with_duration else f"reps{args.repetitions}"
    par = f"p{args.parallel}" if args.parallel > 0 else "s"
    fdp_name = "fdp" if args.use_fdp else "nofdp"
    device_name = "nvme" if args.mount_path is None else "normal"
    name = f"{args.benchmark}-{run_with_duration_display}-{device_name}-mem{args.buffer_manager_mem_size}-{args.io_backend}-sf{args.scale_factor}-t{args.threads}-{par}-{fdp_name}" 

    device_output_file = f"{name}-device.csv"
    output_file = f"{name}.csv"

    run_benchmark, setup_benchmark = create_benchmark_runner(args.benchmark, args.scale_factor, run_with_duration)

    # Setup the database with the correct device config
    db, device = setup_device_and_db()
    setup_benchmark(db, args.input_dir, args.buffer_manager_mem_size, args.threads, args.scale_factor)
    metric_results = []

    # Run the benchmark
    stop_measurement = start_device_measurements(device, device_output_file)

    if args.parallel > 0:
        print(f"Running benchmark with {args.threads} and {args.parallel} parallel executions")
        benchmark_threads = create_execution_threads(args.parallel, run_benchmark, db, args.duration if run_with_duration else args.repetitions)
        run_benchmark_threads(benchmark_threads)
        metric_results = wait_for_completion(benchmark_threads)
    else:
        print(f"Running benchmark with {args.threads} threads with sequential execution")
        metric_results = run_benchmark(db, args.duration if run_with_duration else args.repetitions) 

    stop_measurement()
    
    # Write the metric results to a CSV file
    with open(output_file, mode="w", newline="\n") as file:
        # Write the rows
        for result in metric_results:
            file.write(result)
    
    device.reset()

    print(f"Benchmark results written to {output_file} and WAF results written to {device_output_file}")
