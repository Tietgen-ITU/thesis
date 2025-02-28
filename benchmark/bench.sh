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
BENCHMARK_OUT_DIR=/home/pinar/thesis/benchmark

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
    # TODO : fill device with random garbage using fio
    $FIO --filename=$DEVICE_NG --size="$UTIL%" --name fillDevice --rw=write --numjobs=1 --ioengine=io_uring_cmd --iodepth=64 --bs=128K
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
        $(fill_device $PRECON_UTIL)
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
        $(fill_device $PRECON_UTIL)
    fi
    echo "___________________________"
}

# IO_URING_CMD
setup_device_fdp_disabled 80
python3 waf.py "no_fdp.txt" false & IODEPTH=4 BS=4k THREADS=2 DEVICE=$DEVICE_NG OUTPUT="./no_fdp_results.txt" $FIO ./no_fdp.fio
setup_device_fdp_enabled 80
python3 waf.py "fdp.txt" true & IODEPTH=4 BS=4k THREADS=2 DEVICE=$DEVICE_NG OUTPUT="./fdp_results.txt" $FIO ./fdp.fio

# xNVMe IO_URING_CMD
setup_device_fdp_disabled 80
python3 waf.py "no_fdp.txt" false & IODEPTH=4 BS=4k THREADS=2 DEVICE=$DEVICE_NG OUTPUT="./xnvme_no_fdp_results.txt" $FIO ./xnvme_no_fdp.fio
setup_device_fdp_enabled 80
python3 waf.py "fdp.txt" true & IODEPTH=4 BS=4k THREADS=2 DEVICE=$DEVICE_NG OUTPUT="./xnvme_fdp_results.txt" $FIO ./xnvme_fdp.fio