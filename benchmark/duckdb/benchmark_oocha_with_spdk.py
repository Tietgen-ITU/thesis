import sys
import time
import csv
import os 
from runner.oocha.oocha import run_oocha_epoch_benchmark, setup_oocha_benchmark
from database.duckdb import Database, connect, ConnectionConfig
import duckdb

def run_bench_for_db(db: Database, iterations: int, scale_factor: int, output_file):
    for i in range(iterations):
        print(f"iteration {i}")
        results = run_oocha_epoch_benchmark(db, scale_factor)
        file.write(results)


def _getqueries(queries_dir: str):
    thin_queries_dir = os.path.join(queries_dir, "thin")
    wide_queries_dir = os.path.join(queries_dir, "wide")
    
    wides = [True]
    queries = []
    for wide in wides:
        source_dir = wide_queries_dir if wide else thin_queries_dir
        for file_name in os.listdir(source_dir):
            file_path = f'{source_dir}/{file_name}'
            with open(file_path, 'r') as f:
                queries.append((file_name.split('.')[0], wide, f.read()))

    return queries

def _getcounts(queries_dir: str, scale_factor: int):
    counts_filepath = f"{queries_dir}/counts-{scale_factor}.csv"
    query_counts = {}

    with open(counts_filepath, newline='\n') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        next(reader, None) # Skip the header

        for group, count in reader:
            query_counts[group] = int(count)

    return query_counts


def run_and_setup_bench_for_db(db_path:str, config: ConnectionConfig, iterations: int, scale_factor: int, output_file):
    con = duckdb.connect(config={"allow_unsigned_extensions": "true", "max_temp_directory_size": "150GB", "memory_limit": "2000MB", "threads": 1})
    if db_path.startswith("nvmefs"):
        con.install_extension("nvmefs")
        con.load_extension("nvmefs")
        con.execute(f"""CREATE OR REPLACE PERSISTENT SECRET nvmefs (
                        TYPE NVMEFS,
                        nvme_device_path '{config.device}',
                        fdp_plhdls       '{7}',
                        backend          '{config.backend}'
                    );""")
    
    con.close()

    con = duckdb.connect(config={"allow_unsigned_extensions": "true", "max_temp_directory_size": "150GB", "memory_limit": "2000MB", "threads": 1})    
    if db_path.startswith("nvmefs"):
        con.install_extension("nvmefs")
        con.load_extension("nvmefs")
    con.execute(f"ATTACH DATABASE '{db_path}' AS bench (READ_WRITE);")
    con.execute("USE bench;")
    con.execute(f"ATTACH DATABASE '/mnt/duckdb/oocha-32.db' AS oocha;")
    con.execute("COPY FROM DATABASE oocha TO bench;")
    con.execute("DETACH DATABASE oocha;")
    con.execute("PRAGMA disable_object_cache;")
     
    for i in range(iterations):
        print(f"iteration {i}")
        results = []
        queries_dir = "./runner/oocha/queries"
        queries = _getqueries(queries_dir)
        query_counts = _getcounts(queries_dir, scale_factor)

        # counts_con = duckdb.connect()
        for grouping, wide, query in queries:
            print(f"Running {grouping} {'wide' if wide else 'thin'} query")
            count = query_counts[grouping]
            prepared_query = query.replace('offset', f'{count - 1}')

            start = time.perf_counter()
            con.query(prepared_query).fetchall()
            end = time.perf_counter()

            # Get query elapsed time in milliseconds
            query_elapsed = (end - start) * 1000
            print(query_elapsed)
            results.append(f"{grouping};{wide};{query_elapsed}")
        file.write("\n".join(results))

def setup():
    os.system("xnvme-driver reset")
    os.system("sh ../../nvmefs/scripts/nvme/device_dealloc.sh")
    os.system("echo 1 | sudo tee /sys/class/nvme/nvme1/rescan_controller")
    os.system("nvme delete-ns /dev/nvme1 -n 1")
    os.system("echo 1 | sudo tee /sys/class/nvme/nvme1/rescan_controller")
    os.system("sh ../../nvmefs/scripts/nvme/create_fdp_device.sh")

if __name__ == "__main__":
    db_path = sys.argv[1]
    iterations = int(sys.argv[2])
    scale_factor = int(sys.argv[3])
    output_folder = sys.argv[4]
    user_space = True if int(sys.argv[5]) == 1 else 0
    os.makedirs(output_folder, exist_ok=True)


    if db_path.startswith("nvmefs://") and not user_space:
        setup()
        with open(f"{output_folder}/ucmd_oocha.csv", mode="w", newline="\n") as file:
            run_and_setup_bench_for_db(db_path, ConnectionConfig(device="/dev/ng1n1", backend="io_uring_cmd", use_fdp=True, memory=2000, threads=1), iterations, scale_factor, file)
    elif db_path.startswith("nvmefs://") and user_space:
        setup()
        with open(f"{output_folder}/spdk_oocha.csv", mode="w", newline="\n") as file:
            os.system("HUGHMEM=4096 xnvme-driver")
            run_and_setup_bench_for_db(db_path, ConnectionConfig(device="0000:ec:00.0", backend="spdk_async", use_fdp=True, memory=2000, threads=1), iterations, scale_factor, file)
            os.system("xnvme-driver reset")
    else:
        #setup()
        with open(f"{output_folder}/normal_oocha.csv", mode="w", newline="\n") as file:
            run_and_setup_bench_for_db(db_path, None, iterations, scale_factor, file)
