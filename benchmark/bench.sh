#!/bin/bash

# Device information
DEVICE=/dev/nvme1
DEVICE_NS=/dev/nvme1n1
DEVICE_NG=/dev/ng1n1
DEVICE_URI="0000\:ec\:00"
CONTROLLER=0x7
BLOCK_SIZE=4096

# Path
COMMANDS_DIR=/home/pinar/.local
BENCHMARK_DIR=/home/pinar/thesis/benchmark
DB_WORKLOAD_DIR=/home/pinar/thesis/benchmark/fio/db_workload

# Commands
NVME=$COMMANDS_DIR/nvme-cli/.build/nvme
XNVME=$COMMANDS_DIR/xnvme/builddir/tools/xnvme
XNVME_DRIVER=$COMMANDS_DIR/xnvme/builddir/toolbox/xnvme-driver
FIO=$COMMANDS_DIR/fio/fio

# FDP information
NAMESPACE=1
FDP=0x1D

# Exports
export LD_LIBRARY_PATH=/usr/local/lib64
source /home/pinar/.bashrc

# Return the total number of blocks on the device
blocks_on_device(){
    $NVME id-ctrl $DEVICE | grep 'tnvmcap' | sed 's/,//g' | awk -v BS=$BLOCK_SIZE '{print $3/BS}'
}

# Remove the namespace on the device
remove_namespace (){
    $NVME delete-ns $DEVICE -n $NAMESPACE
}

# Erase all blocks on the device
deallocate_device(){
    local var NUM_BLOCKS=$(blocks_on_device)
    $NVME dsm $DEVICE --namespace-id=$NAMESPACE --ad -s 0 -b $NUM_BLOCKS
}

disable_fdp(){
    $NVME set-feature $DEVICE -f $FDP -c 0 -s
    $NVME get-feature $DEVICE -f $FDP -H
}

enable_fdp(){
    $NVME set-feature $DEVICE -f $FDP -c 1 -s
    $NVME get-feature $DEVICE -f $FDP -H
}

reset_device() {
    echo "Deallocating all blocks..."
    deallocate_device
    echo "Removing previous namespace"
    remove_namespace
}

fill_device() {
    local var UTIL=$1
    echo "filling device to $UTIL%"
    $FIO --filename=$DEVICE_NG --size="$UTIL%" --name fillDevice --rw=write --numjobs=1 --ioengine=io_uring_cmd --iodepth=64 --bs=128K
    echo "done filling device to $UTIL%"
}

setup_device_fdp_disabled() {
    echo "______ SETUP NON-FDP ______"
    echo "Resetting the device: $DEVICE"
    reset_device
    echo "Disabling fdp on the device"
    disable_fdp
    
    local var PRECON_UTIL=${1:-0}
    local var DEVICE_CAP=$(blocks_on_device)
    
    echo "Creating namepace with size: $DEVICE_CAP, and block size: $BLOCK_SIZE"
    $NVME create-ns $DEVICE -b $BLOCK_SIZE --nsze=$DEVICE_CAP --ncap=$DEVICE_CAP
    
    echo "Attaching the namespace to the device: $DEVICE"
    $NVME attach-ns $DEVICE --namespace-id=$NAMESPACE --controllers=$CONTROLLER

    if [[ $PRECON_UTIL -gt 0 ]]; then
        fill_device $PRECON_UTIL
    fi
    echo "___________________________"
}

setup_device_fdp_enabled() {
    echo "________ SETUP FDP ________"
    echo "Resetting the device: $DEVICE"
    reset_device
    echo "enabling fdp on the device"
    enable_fdp

    local var PRECON_UTIL=${1:-0}
    local var DEVICE_CAP=$(blocks_on_device)
   
    # For some reason it is not possible to allocate all 8 reclaim unit handles. The error code can be found in the base specification by searching "2Ah"
    echo "Creating namepace with size: $DEVICE_CAP, and block size: $BLOCK_SIZE. Using placement handlers: 0,1,2,3,4,5,6" 
    $NVME create-ns $DEVICE -b $BLOCK_SIZE --nsze=$DEVICE_CAP --ncap=$DEVICE_CAP --nphndls=7 --phndls=0,1,2,3,4,5,6
    
    echo "Attaching the namespace to the device: $DEVICE."
    $NVME attach-ns $DEVICE --namespace-id=$NAMESPACE --controllers=$CONTROLLER
  
    if [[ $PRECON_UTIL -gt 0 ]]; then
        fill_device $PRECON_UTIL
    fi
    echo "___________________________"
}

# Takes 5 arguments: 
# - 1. name - name fio file without extension
# - 2. workload - string that specifies workload
# - 3. temp size - int that specifies the percentage size of temporary storage 
# - 4. duration - duration of experiment in seconds (default 1 hour)
# - 5. interval - the interval in which measurements should be taken (default 10 min)
run_workload() {
    local var IODEPTH=32
    local var THREADS=1
    local var L_DEVICE=$DEVICE_NG

    local var DATE=$(date +"%d_%m_%y")
    local var OUTDIR=""
    
    if [[ "$2" == "database" ]]; then
        OUTDIR="$DB_WORKLOAD_DIR/$DATE/TEMP_$3"
        python3 "$BENCHMARK_DIR/waf.py" "$OUTDIR/$1.txt" $5 $(($4 / $5 )) & IODEPTH=$IODEPTH THREADS=$THREADS TEMP_SIZE=$3 DEVICE=$L_DEVICE DURATION=$4 $FIO "$DB_WORKLOAD_DIR/$1.fio" --output="$OUTDIR/$1_result.txt" --output-format="json"
    fi
}

WORKLOAD="database"
TEMP_SIZES=()
INTERVAL=0
DURATION=0
while getopts ":w:i:d:t" opt
    do 
        case $opt in
            w) echo $OPTARG; WORKLOAD=$OPTARG;;
            t) echo $OPTARG; TEMP_SIZES+=$OPTARG;;
            i) echo $OPTARG; INTERVAL=$OPTARG;;
            d) echo $OPTARG; DURATION=$OPTARG;;
        esac
done

for tsize in "${TEMP_SIZES[@]}"
do
    setup_device_fdp_disabled
    run_workload "no_fdp" $WORKLOAD $tsize $DURATION $INTERVAL
    setup_device_fdp_enabled
    run_workload "fdp" $WORKLOAD $tsize $DURATION $INTERVAL

    setup_device_fdp_disabled
    run_workload "xnvme_no_fdp" $WORKLOAD $tsize $DURATION $INTERVAL
    setup_device_fdp_enabled
    run_workload "xnvme_fdp" $WORKLOAD $tsize $DURATION $INTERVAL
    
done
