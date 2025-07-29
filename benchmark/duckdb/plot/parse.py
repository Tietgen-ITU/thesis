import csv
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class BenchmarkRun:
    benchmark: str
    run_type: str
    device: str
    backend: str
    span: int
    span_type: str
    memory: int
    scale_factor: int
    threads: int
    parallel: bool
    parallel_threads: int
    fdp: bool
    results: dict = None


def parse_filename(filepath: str):
    """
    Parse the filename to extract the benchmark name and parameters.
    oocha-reps4-normal-mem20000-io_uring_cmd-sf2-t16-s-nofdp
    """
    # Split the filename into parts
    filename = filepath.split("/")[-1]
    parts = filename.split("-")
    
    # Extract the benchmark name
    benchmark_name = parts[0]
    if (not parts[1].startswith("reps")) and (not parts[1].startswith("dur")):
        benchmark_name = f"{parts[0]}-{parts[1]}"
        index = 2
    else:
        index = 1

    span_type = "duration" if "dur" in parts[index] else "repetition"
    is_span_type_duration = span_type == "duration"

    span = int(parts[index][3:]) if is_span_type_duration else int(parts[index][4:])
    index += 1

    device = parts[index]
    index += 1

    memory = int(parts[index][3:])
    index += 1

    backend = parts[index]
    index += 1

    scale_factor = int(parts[index][2:])
    index += 1

    threads = int(parts[index][1:])
    index += 1

    parallel = False if "s" in parts[index] else True
    parallel_threads = int(parts[index][1:]) if parallel else 1
    index += 1

    fdp = True if "fdp" == parts[index].split(".")[0] else False
    
    # Extract the parameters
    benchmark = BenchmarkRun(
        benchmark=benchmark_name,
        run_type=span_type,
        device=device,
        backend=backend,
        span_type=span_type,
        span=span,
        memory=memory,
        scale_factor=scale_factor,
        threads=threads,
        parallel=parallel,
        parallel_threads=parallel_threads,
        fdp=fdp
    )

    return benchmark


def parse_oocha_results(filepath: str) -> BenchmarkRun:
    """
    Parse the oocha results file to extract the benchmark name and parameters.
    """
    # Read the file
    oocha_groupings = {
        "l_returnflag-l_linestatus": 1, 
        "l_partkey": 2,
        "l_partkey-l_returnflag-l_linestatus": 3,
        "l_suppkey-l_partkey": 4,
        "l_orderkey": 5,
        "l_orderkey-l_returnflag-l_linestatus": 6,
        "l_suppkey-l_partkey-l_returnflag-l_linestatus": 7,
        "l_suppkey-l_partkey-l_shipinstruct": 8,
        "l_suppkey-l_partkey-l_shipmode": 9,
        "l_suppkey-l_partkey-l_shipinstruct-l_shipmode": 10,
        "l_orderkey-l_partkey": 11,
        "l_orderkey-l_suppkey": 12,
        "l_suppkey-l_partkey-l_orderkey": 13
    }

    benchmark = parse_filename(filepath)

    grouped_results = defaultdict(lambda: list())
    with open(filepath, newline='\n') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')

        for group, wide, elapsed_ms in reader:
            if group not in oocha_groupings:
                # Skip uknown groupings. I was stupid and generated to many grouping queries
                continue

            is_wide = True if wide == "True" else False

            grouped_results[(oocha_groupings[group], is_wide)].append(float(elapsed_ms))

    benchmark.results = grouped_results
    return benchmark

def parse_tpch_results(filepath: str) -> BenchmarkRun:
    """
    Parse the TPCH results file to extract the benchmark name and parameters.
    """
    benchmark = parse_filename(filepath)

    grouped_results = defaultdict(lambda: list())
    with open(filepath, newline='\n') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')

        for query_nr, elapsed_ms in reader:
            grouped_results[int(query_nr)].append(float(elapsed_ms))

    benchmark.results = grouped_results
    return benchmark

def parse_oocha_spill_waf_results(filepath: str) -> BenchmarkRun:
    """
    Parse the TPCH results file to extract the benchmark name and parameters.
    """
    benchmark = parse_filename(filepath)

    grouped_results = defaultdict(lambda: list())
    with open(filepath, newline='\n') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')

        minute = 0
        for _, bytes_written, waf in reader:

            host_written_bytes, media_written_bytes = map(int, bytes_written.split(","))
            grouped_results[minute].append((host_written_bytes, media_written_bytes, float(waf)))
            minute += 10

    benchmark.results = grouped_results
    return benchmark

def parse_oocha_spill_elapsed_results(filepath: str) -> BenchmarkRun:
    """
    Parse the TPCH results file to extract the benchmark name and parameters.
    """
    benchmark = parse_filename(filepath)

    grouped_results = defaultdict(lambda: list())
    with open(filepath, newline='\n') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')

        for row in reader:
            elapsed_ms = row[0]
            grouped_results[1].append(float(elapsed_ms))

    benchmark.results = grouped_results
    return benchmark
import csv
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class BenchmarkRun:
    benchmark: str
    run_type: str
    device: str
    backend: str
    span: int
    span_type: str
    memory: int
    scale_factor: int
    threads: int
    parallel: bool
    parallel_threads: int
    fdp: bool
    results: dict = None


def parse_filename(filepath: str):
    """
    Parse the filename to extract the benchmark name and parameters.
    oocha-reps4-normal-mem20000-io_uring_cmd-sf2-t16-s-nofdp
    """
    # Split the filename into parts
    filename = filepath.split("/")[-1]
    parts = filename.split("-")
    
    # Extract the benchmark name
    has_dash_in_benchmark_name = not (parts[1].startswith("reps") or parts[1].startswith("dur"))
    benchmark_name = f"{parts[0]}-{parts[1]}" if has_dash_in_benchmark_name else parts[0]
    index = 2 if has_dash_in_benchmark_name else 1
    span_type = "duration" if "dur" in parts[index] else "repetition"
    span = int(parts[index][3:]) if span_type == "duration" else int(parts[index][4:])
    index += 1
    device = parts[index]
    index += 1
    memory = int(parts[index][3:])
    index += 1
    backend = parts[index]
    index += 1
    scale_factor = int(parts[index][2:])
    index += 1
    threads = int(parts[index][1:])
    index += 1
    parallel = False if "s" in parts[index] else True
    parallel_threads = int(parts[index][1:]) if parallel else 1
    index += 1
    fdp = True if "fdp" == parts[index].split(".")[0] else False

    # Extract the parameters
    benchmark = BenchmarkRun(
        benchmark=benchmark_name,
        run_type=span_type,
        device=device,
        backend=backend,
        span_type=span_type,
        span=span,
        memory=memory,
        scale_factor=scale_factor,
        threads=threads,
        parallel=parallel,
        parallel_threads=parallel_threads,
        fdp=fdp
    )

    return benchmark


def parse_oocha_results(filepath: str) -> BenchmarkRun:
    """
    Parse the oocha results file to extract the benchmark name and parameters.
    """
    # Read the file
    oocha_groupings = {
        "l_returnflag-l_linestatus": 1, 
        "l_partkey": 2,
        "l_partkey-l_returnflag-l_linestatus": 3,
        "l_suppkey-l_partkey": 4,
        "l_orderkey": 5,
        "l_orderkey-l_returnflag-l_linestatus": 6,
        "l_suppkey-l_partkey-l_returnflag-l_linestatus": 7,
        "l_suppkey-l_partkey-l_shipinstruct": 8,
        "l_suppkey-l_partkey-l_shipmode": 9,
        "l_suppkey-l_partkey-l_shipinstruct-l_shipmode": 10,
        "l_orderkey-l_partkey": 11,
        "l_orderkey-l_suppkey": 12,
        "l_suppkey-l_partkey-l_orderkey": 13
    }

    benchmark = parse_filename(filepath)

    grouped_results = defaultdict(lambda: list())
    with open(filepath, newline='\n') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')

        for group, wide, elapsed_ms in reader:
            if group not in oocha_groupings:
                # Skip uknown groupings. I was stupid and generated to many grouping queries
                continue

            is_wide = True if wide == "True" else False

            grouped_results[(oocha_groupings[group], is_wide)].append(float(elapsed_ms))

    benchmark.results = grouped_results
    return benchmark