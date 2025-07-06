#!/bin/bash
DURATION=240
REPETITIONS=6
DEVICE="/dev/nvme1"
INPUT_DIR="/mnt/duckdb"
MOUNT="/mnt/itu/duckdb"

#Max device blocks 91814953

M_SIZE_PRECONDITION=826334568 # ~3,38TB, 90% of device
L_SIZE_PRECONDITION=762064106 # ~3,12TB, 83% of device
XL_SIZE_PRECONDITION=524288000 # ~2,00TB, 55% of device

setup_precondition_ns_fdp() {

    DEVICE_PATH=$1
    SIZE=$2

    sudo nvme set-feature $DEVICE_PATH -f 0x1D -c 1 -s

    sudo nvme create-ns /dev/nvme1 -b 4096 --nsze=$SIZE --ncap=$SIZE --nphndls=1 --phndls=6
    sudo nvme attach-ns /dev/nvme1 --namespace-id=1 --controllers=0x7
}

precondition_device() {

    /home/pinar/.local/fio/fio --filename=/dev/ng1n1 --size="100%" --name fillDevice --rw=write --numjobs=1 --ioengine=io_uring_cmd --iodepth=64 --bs=256k
}

setup_precondition_ns() {
    DEVICE_PATH=$1
    SIZE=$2

    sudo nvme set-feature $DEVICE_PATH -f 0x1D -c 0 -s

    sudo nvme create-ns $DEVICE_PATH -b 4096 --nsze=$SIZE --ncap=$SIZE
    sudo nvme attach-ns $DEVICE_PATH --namespace-id=1 --controllers=0x7

}

remove_precondition_device() {
    DEVICE_PATH=$1
    SIZE=$2

    nvme dsm $DEVICE_PATH --namespace-id=1 --ad -s 0 -b $SIZE
    nvme delete-ns $DEVICE_PATH --namespace-id=1
}

source ./init.sh


###################################
# Run all out-of-core benchmarks with focus on the individual elasped times
###################################
TPCH_SIZES=(1 10 100 1000)

# nvme io_uring_cmd with fdp
for sf in "${TPCH_SIZES[@]}"
do
    setup_precondition_ns_fdp $DEVICE $XL_SIZE_PRECONDITION
    python3 benchmark.py -r $REPETITIONS --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 20000 --sf $sf -t 16 --fdp tpch
    remove_precondition_device $DEVICE $XL_SIZE_PRECONDITION
done

# nvme io_uring_cmd without fdp
for sf in "${TPCH_SIZES[@]}"
do
    setup_precondition_ns $DEVICE $XL_SIZE_PRECONDITION
    python3 benchmark.py -r $REPETITIONS --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 20000 --sf $sf -t 16 tpch
    remove_precondition_device $DEVICE $XL_SIZE_PRECONDITION
done

# Base line for the tpch elapsed benchmark
for sf in "${TPCH_SIZES[@]}"
do
    setup_precondition_ns $DEVICE $XL_SIZE_PRECONDITION
    python3 benchmark.py -r $REPETITIONS --mount_path $MOUNT --device_path $DEVICE --input_directory $INPUT_DIR -m 20000 --sf $sf -t 16 tpch
    remove_precondition_device $DEVICE $XL_SIZE_PRECONDITION
done

###################################
# Run all out-of-core benchmarks with focus on the individual elasped times
###################################

OOCHA_SIZES=(2 8 32 128)

for sf in "${OOCHA_SIZES[@]}"
do
    setup_precondition_ns_fdp $DEVICE $M_SIZE_PRECONDITION
    python3 benchmark.py -r $REPETITIONS --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 20000 --sf $sf -t 16 --fdp oocha
    remove_precondition_device $DEVICE $M_SIZE_PRECONDITION
done

for sf in "${OOCHA_SIZES[@]}"
do
    setup_precondition_ns $DEVICE $M_SIZE_PRECONDITION
    python3 benchmark.py -r $REPETITIONS --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 20000 --sf $sf -t 16 oocha
    remove_precondition_device $DEVICE $M_SIZE_PRECONDITION
done

# Base line for the out-of-core elapsed benchmark
for sf in "${OOCHA_SIZES[@]}"
do
    setup_precondition_ns $DEVICE $M_SIZE_PRECONDITION
    python3 benchmark.py -r $REPETITIONS --mount_path $MOUNT --device_path $DEVICE --input_directory $INPUT_DIR -m 20000 --sf $sf -t 16 oocha
    remove_precondition_device $DEVICE $M_SIZE_PRECONDITION
done

###################################
# Run all out-of-core benchmarks with focus on WAF
###################################

## normal
precondition_device $DEVICE $M_SIZE_PRECONDITION
precondition_device
python3 benchmark.py -d $DURATION --mount_path $MOUNT --device_path $DEVICE --input_directory $INPUT_DIR -m 20000 --sf 1000 -t 24 oocha-spill
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION


precondition_device $DEVICE $M_SIZE_PRECONDITION
precondition_device
python3 benchmark.py -d $DURATION --mount_path $MOUNT --device_path $DEVICE --input_directory $INPUT_DIR -m 40000 --sf 1000 -t 96 -par 4 oocha-spill
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

# nvme
setup_precondition_ns_fdp $DEVICE $M_SIZE_PRECONDITION
precondition_device
python3 benchmark.py -d $DURATION --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 20000 --sf 1000 -t 24 --fdp oocha-spill
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

setup_precondition_ns_fdp $DEVICE $M_SIZE_PRECONDITION
precondition_device
python3 benchmark.py -d $DURATION --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 14000 --sf 1000 -t 96 -par 4 --fdp oocha-spill
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

precondition_device $DEVICE $M_SIZE_PRECONDITION
precondition_device
python3 benchmark.py -d $DURATION --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 3500 --sf 1000 -t 24 oocha-spill
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION

setup_precondition_ns_fdp $DEVICE $M_SIZE_PRECONDITION
precondition_device
python3 benchmark.py -d $DURATION --input_directory $INPUT_DIR --device_path $DEVICE --generic_device -b "io_uring_cmd" -m 14000 --sf 1000 -t 96 -par 4 oocha-spill
remove_precondition_device $DEVICE $M_SIZE_PRECONDITION