#!/bin/bash
ITERATIONS=3
DEVICE="/dev/nvme1"

# Run the benchmark with the generic device, io_uring_cmd, and fdp
python3 benchmark.py -i $ITERATIONS -d $DEVICE --generic_device -b "io_uring_cmd" --fdp tpch

# Run the benchmark with the generic device, io_uring_cmd, but without fdp
python3 benchmark.py -i $ITERATIONS -d $DEVICE --generic_device -b "io_uring_cmd" tpch

# Run the benchmark with the nvme block device(e.g. /dev/nvme1n1) using io_uring
python3 benchmark.py -i $ITERATIONS -d $DEVICE -b "io_uring" tpch

# Run regular benchmark with default file system(could be a base line)
python3 benchmark.py -i $ITERATIONS tpch