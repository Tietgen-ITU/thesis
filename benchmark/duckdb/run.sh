#!/bin/bash
DURATION=240
READ_DURATION=30
DEVICE="/dev/nvme1"
INPUT_DIR="/home/pinar"
MOUNT="/mnt/itu/duckdb"

M_SIZE_DEVICE=91814953 # ~376GB, 10% of device
M_SIZE_PRECONDITION=826334573 # ~3,38TB, 90% of device
L_SIZE_DEVICE=156085420 # ~639GB, 17% of device
L_SIZE_PRECONDITION=762064106 # ~3,12TB, 83% of device

precondition_device_fdp() {
    DEVICE_PATH=$1
    SIZE=$2

    nvme set-feature $DEVICE_PATH -f 0x1D -c 1 -s

    nvme create-ns $DEVICE_PATH -b 4096 --nsze=$SIZE --ncap=$SIZE --nphndls=1 --phndls=6
    nvme attach-ns $DEVICE_PATH --namespace-id=1 --controllers=0x7

    #/home/pinar/.local/fio/fio --filename=/dev/ng1n1 --size="100%" --name fillDevice --rw=write --numjobs=1 --ioengine=io_uring_cmd --iodepth=64 --bs=256k
}

precondition_device() {
    DEVICE_PATH=$1
    SIZE=$2

    nvme set-feature $DEVICE_PATH -f 0x1D -c 0 -s

    nvme create-ns $DEVICE_PATH -b 4096 --nsze=$SIZE --ncap=$SIZE
    nvme attach-ns $DEVICE_PATH --namespace-id=1 --controllers=0x7

    #/home/pinar/.local/fio/fio --filename=/dev/ng1n1 --size="100%" --name fillDevice --rw=write --numjobs=1 --ioengine=io_uring_cmd --iodepth=64 --bs=256k
}

remove_precondition_device() {
    DEVICE_PATH=$1
    SIZE=$2

    nvme dsm $DEVICE_PATH --namespace-id=1 --ad -s 0 -b $SIZE
    nvme delete-ns $DEVICE_PATH --namespace-id=1
}

source /home/pinar/.bashrc
source ./init.sh

precondition_device_fdp $DEVICE $M_SIZE_PRECONDITION

python3 benchmark.py -d $DURATION --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 500 --sf 100 --fdp tpch

remove_precondition_device $DEVICE $M_SIZE_PRECONDITION
precondition_device $DEVICE $M_SIZE_PRECONDITION

python3 benchmark.py -d $DURATION --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 500 --sf 100 tpch

remove_precondition_device $DEVICE $M_SIZE_PRECONDITION


# Run benchmarks with enough main memory to not make it spill to disk
# python3 benchmark.py -d $READ_DURATION --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 50000 tpch
# python3 benchmark.py -d $READ_DURATION --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 50000 --fdp tpch
# python3 benchmark.py -d $READ_DURATION --mount_path $MOUNT --device_path $DEVICE --input_directory $INPUT_DIR -m 50000 tpch

# Run the benchmark with the generic device, io_uring_cmd, and fdp
# python3 benchmark.py -d $DURATION --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 75 tpch
# python3 benchmark.py -d $DURATION --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 75 --fdp tpch

# Run regular benchmark with default file system(could be a base line)
# python3 benchmark.py -d $DURATION --mount_path $MOUNT --device_path $DEVICE --input_directory $INPUT_DIR -m 75 tpch