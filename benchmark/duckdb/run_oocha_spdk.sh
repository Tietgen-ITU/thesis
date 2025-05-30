source "/home/pinar/.bashrc"
source "./init.sh"

cp -f "/home/pinar/copy_secrets/spdk_nvmefs.duckdb_secret" "~/.duckdb/stored_secrets/nvmefs.duckdb_secret"
python3 "benchmark_oocha_with_spdk.py" "0000:ec:00.0" 1 2000 "results/ocha_single_thread"

cp -f "/home/pinar/copy_secrets/ucmd_nvmefs.duckdb_secret" "~/.duckdb/stored_secrets/nvmefs.duckdb_secret"
python3 "benchmark_oocha_with_spdk.py" "/dev/ng1n1" 1 2000 "results/ocha_single_thread"

python3 "benchmark_oocha_with_spdk.py" "/dev/nvme1n1" 1 2000 "results/ocha_single_thread"