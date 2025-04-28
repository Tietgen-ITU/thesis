#!/bin/bash
DURATION=60
DEVICE="/dev/nvme1"
INPUT_DIR="/home/pinar"
MOUNT="/mnt/itu/duckdb"

source /home/pinar/.bashrc
source ./init.sh

# Run the benchmark with the generic device, io_uring_cmd, and fdp
python3 benchmark.py -d $DURATION --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 75 --fdp tpch

# Run the benchmark with the generic device, io_uring_cmd, but without fdp
# python3 benchmark.py -i $DURATION -d $DEVICE --generic_device -b "io_uring_cmd" tpch

# Run the benchmark with the nvme block device(e.g. /dev/nvme1n1) using io_uring
# python3 benchmark.py -i $DURATION -d $DEVICE -b "io_uring" tpch

# Run regular benchmark with default file system(could be a base line)
python3 benchmark.py -d $DURATION --mount_path $MOUNT --input_directory $INPUT_DIR tpch