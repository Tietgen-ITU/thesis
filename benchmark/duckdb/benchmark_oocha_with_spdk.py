import sys
import os 
from runner.oocha.oocha import run_oocha_epoch_benchmark, setup_oocha_benchmark
from database.duckdb import Database, connect, ConnectionConfig

def run_bench_for_db(db: Database, iterations: int, scale_factor: int, output_file):
    for i in range(iterations):
        print(f"iteration {i}")
        results = run_oocha_epoch_benchmark(db, scale_factor)
        file.write(results)

def setup():
    os.system("sh ../../nvmefs/scripts/nvme/device_dealloc.sh")
    os.system("nvme delete-ns /dev/nvme1 -n 1")
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
        ucmd_db = connect(db_path, 1, 2000, ConnectionConfig(device="/dev/ng1n1", backend="io_uring_cmd", use_fdp=True))
        with open(f"{output_folder}/ucmd_oocha.csv", mode="w", newline="\n") as file:
            setup_oocha_benchmark(ucmd_db, "/mnt/duckdb", scale_factor)
            run_bench_for_db(ucmd_db, iterations, scale_factor, file)
    elif db_path.startswith("nvmefs://") and user_space:
        setup()
        os.system("HUGHMEM=4096 xnvme-driver")
        spdk_db = connect(db_path, 1, 2000, ConnectionConfig(device="0000:ec:00.0", backend="spdk_sync", use_fdp=True))
        os.system("xnvme-driver reset")
        with open(f"{output_folder}/spdk_oocha.csv", mode="w", newline="\n") as file:
            os.system("HUGHMEM=4096 xnvme-driver")
            setup_oocha_benchmark(spdk_db, "/mnt/duckdb", scale_factor)
            run_bench_for_db(spdk_db, iterations, scale_factor, file)
            os.system("xnvme-driver reset")
    else:
        setup()
        normal_db = connect(db_path, 1, 2000)
        with open(f"{output_folder}/normal_oocha.csv", mode="w", newline="\n") as file:
            setup_oocha_benchmark(normal_db, "/mnt/duckdb", scale_factor)
            run_bench_for_db(normal_db, iterations, scale_factor, file)