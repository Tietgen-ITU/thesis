#!/bin/bash
DURATION=10
READ_DURATION=30
REPETITIONS=10
DEVICE="/dev/nvme1"
INPUT_DIR="/mnt/duckdb"
MOUNT="/mnt/itu/duckdb"

#Max device blocks 91814953

M_SIZE_PRECONDITION=826334568 # ~3,38TB, 90% of device
L_SIZE_PRECONDITION=762064106 # ~3,12TB, 83% of device

precondition_device_fdp() {
    DEVICE_PATH=$1
    SIZE=$2

    nvme set-feature $DEVICE_PATH -f 0x1D -c 1 -s

    sudo nvme create-ns /dev/nvme1 -b 4096 --nsze=$SIZE --ncap=$SIZE --nphndls=1 --phndls=7
    sudo nvme attach-ns /dev/nvme1 --namespace-id=1 --controllers=0x7

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

###################################
# Run out-of-core benchmarks with focus on WAF numbers
###################################
# precondition_device_fdp $DEVICE $M_SIZE_PRECONDITION
# python3 benchmark.py -d $DURATION --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 3500 --sf 128 -t 16 --fdp oocha-spill
# remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

# precondition_device $DEVICE $M_SIZE_PRECONDITION
# python3 benchmark.py -d $DURATION --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 3500 --sf 128 -t 16 oocha-spill
# remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

precondition_device_fdp $DEVICE $M_SIZE_PRECONDITION
python3 benchmark.py -d $DURATION --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 14000 --sf 128 -t 64 -par 4 --fdp oocha-spill
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

precondition_device $DEVICE $M_SIZE_PRECONDITION
python3 benchmark.py -d $DURATION --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 14000 --sf 128 -t 64 -par 4 oocha-spill
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

# Base line for the out-of-core benchmark
# precondition_device $DEVICE $M_SIZE_PRECONDITION
# python3 benchmark.py -d $DURATION --mount_path $MOUNT --device_path $DEVICE --input_directory $INPUT_DIR -m 3500 --sf 128 -t 16 oocha-spill
# remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

precondition_device $DEVICE $M_SIZE_PRECONDITION
python3 benchmark.py -d $DURATION --mount_path $MOUNT --device_path $DEVICE --input_directory $INPUT_DIR -m 14000 --sf 128 -t 64 -par 4 oocha-spill
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

###################################
# Run all out-of-core benchmarks with focus on the individual elasped times
###################################
precondition_device_fdp $DEVICE $M_SIZE_PRECONDITION
python3 benchmark.py -r $REPETITIONS --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 3500 --sf 2 -t 16 --fdp oocha
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

precondition_device_fdp $DEVICE $M_SIZE_PRECONDITION
python3 benchmark.py -r $REPETITIONS --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 3500 --sf 8 -t 16 --fdp oocha
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

precondition_device_fdp $DEVICE $M_SIZE_PRECONDITION
python3 benchmark.py -r $REPETITIONS --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 3500 --sf 32 -t 16 --fdp oocha
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

precondition_device_fdp $DEVICE $M_SIZE_PRECONDITION
python3 benchmark.py -r $REPETITIONS --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 3500 --sf 128 -t 16 --fdp oocha
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

precondition_device $DEVICE $M_SIZE_PRECONDITION
python3 benchmark.py -r $REPETITIONS --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 3500 --sf 2 -t 16 oocha
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

precondition_device $DEVICE $M_SIZE_PRECONDITION
python3 benchmark.py -r $REPETITIONS --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 3500 --sf 8 -t 16 oocha
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

precondition_device $DEVICE $M_SIZE_PRECONDITION
python3 benchmark.py -r $REPETITIONS --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 3500 --sf 32 -t 16 oocha
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

precondition_device $DEVICE $M_SIZE_PRECONDITION
python3 benchmark.py -r $REPETITIONS --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 3500 --sf 128 -t 16 oocha
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

# # Base line for the out-of-core elapsed benchmark
precondition_device $DEVICE $M_SIZE_PRECONDITION
python3 benchmark.py -r $REPETITIONS --mount_path $MOUNT --device_path $DEVICE --input_directory $INPUT_DIR -m 3500 --sf 2 -t 16 oocha-spill
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

precondition_device $DEVICE $M_SIZE_PRECONDITION
python3 benchmark.py -r $REPETITIONS --mount_path $MOUNT --device_path $DEVICE --input_directory $INPUT_DIR -m 3500 --sf 8 -t 16 oocha-spill
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

precondition_device $DEVICE $M_SIZE_PRECONDITION
python3 benchmark.py -r $REPETITIONS --mount_path $MOUNT --device_path $DEVICE --input_directory $INPUT_DIR -m 3500 --sf 32 -t 16 oocha-spill
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

precondition_device $DEVICE $M_SIZE_PRECONDITION
python3 benchmark.py -r $REPETITIONS --mount_path $MOUNT --device_path $DEVICE --input_directory $INPUT_DIR -m 3500 --sf 128 -t 16 oocha-spill
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION
