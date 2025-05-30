import sys
import os 
from runner.oocha.oocha import run_oocha_epoch_benchmark
from database.duckdb import Database, connect, ConnectionConfig

def run_bench_for_db(db: Database, iterations: int, scale_factor: int, output_file):
    for i in range(iterations):
        results = run_oocha_epoch_benchmark(db, scale_factor)
        file.write(results)

def setup():
    os.system("../../nvmefs/scripts/nvme/device_dealloc.sh")
    os.system("nvme delete-ns /dev/nvme1n1")
    os.system("../../nvmefs/scripts/nvme/create_fdp_device.sh")

if __name__ == "__main__":
    db_path = sys.argv[1]
    iterations = int(sys.argv[2])
    scale_factor = int(sys.argv[3])
    output_folder = sys.argv[4]
    os.makedirs(output_folder, exist_ok=True)



    ucmd_db = connect(db_path, 1, 2000, ConnectionConfig(device=db_path, backend="io_uring_cmd", use_fdp=True))
    spdk_db = connect(db_path, 1, 2000, ConnectionConfig(device=db_path, backend="spdk_sync", use_fdp=True))
    normal_cb = connect(db_path, 1, 2000)

    with open(f"{output_folder}/spdk_oocha.csv", mode="w", newline="\n") as file:
        setup()
        os.system("HUGHMEM=4096 xnvme-driver")
        run_bench_for_db(spdk_db, iterations, file)
        os.system("xnvme-driver reset")
    with open(f"{output_folder}/ucmd_oocha.csv", mode="w", newline="\n") as file:
        setup()
        run_bench_for_db(ucmd_db, iterations, file)
    with open(f"{output_folder}/normal_oocha.csv", mode="w", newline="\n") as file:
        setup()
        run_bench_for_db(normal_cb, iterations, file)