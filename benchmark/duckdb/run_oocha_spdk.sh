source "/home/pinar/.bashrc"
source "./init.sh"

cp -f "/home/pinar/copy_secrets/spdk_nvmefs.duckdb_secret" "/root/.duckdb/stored_secrets/nvmefs.duckdb_secret"
python3 ./benchmark_oocha_with_spdk.py "nvmefs://bench.db" 1 2000 "results/ocha_single_thread" 1

cp -f "/home/pinar/copy_secrets/ucmd_nvmefs.duckdb_secret" "/root/.duckdb/stored_secrets/nvmefs.duckdb_secret"
python3 ./benchmark_oocha_with_spdk.py "nvmefs://bench.db" 1 2000 "results/ocha_single_thread" 0

python3 ./benchmark_oocha_with_spdk.py "bench.db" 1 2000 "results/ocha_single_thread" 0