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
FIO_BENCH_DIR=/home/pinar/thesis/benchmark/fio

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

# Takes 6 arguments: 
# - 1. workload - string that specifies workload
# - 2. temp size - int that specifies the percentage size of temporary storage 
# - 3. duration - duration of experiment in seconds (default 1 hour)
# - 4. interval - the interval in which measurements should be taken (default 10 min)
# - 5. device type - the type of device going to be used
# - 6. backend - io backend to be used
run_workload() {
    local var DATE=$(date +"%d_%m_%y")
    local var OUTDIR=""
    local L_DEVICE=$DEVICE_NS
    
    if [[ "$1" == "database" ]]; then
        OUTDIR="$DB_WORKLOAD_DIR/$DATE/$6_TEMP_$2"

        if [[ $5 == "generic" ]]; then
            L_DEVICE=$DEVICE_NG
        elif [[ $5 == "pci" ]]; then
            L_DEVICE=$DEVICE_URI
        fi

        python3 "$FIO_BENCH_DIR/gen_fio.py" --workload database --device $L_DEVICE -be $6 --out_dir $OUTDIR -bs 256ki --timebased -d 10800 -pcts $2 -ft 3       
        
        setup_device_fdp_disabled
        python3 "$BENCHMARK_DIR/waf.py" "$OUTDIR/no_fdp.txt" $4 $(( $3 / $4 )) & $FIO "$OUTDIR/no_fdp.fio" --output="$OUTDIR/no_fdp_result.txt" --output-format="json"
        setup_device_fdp_enabled
        python3 "$BENCHMARK_DIR/waf.py" "$OUTDIR/fdp.txt" $4 $(( $3 / $4 )) & $FIO "$OUTDIR/fdp.fio" --output="$OUTDIR/fdp_result.txt" --output-format="json"
        setup_device_fdp_disabled
        python3 "$BENCHMARK_DIR/waf.py" "$OUTDIR/xnvme_no_fdp.txt" $4 $(( $3 / $4 )) & $FIO "$OUTDIR/xnvme_no_fdp.fio" --output="$OUTDIR/xnvme_no_fdp_result.txt" --output-format="json"
        setup_device_fdp_enabled
        python3 "$BENCHMARK_DIR/waf.py" "$OUTDIR/xnvme_fdp.txt" $4 $(( $3 / $4 )) & $FIO "$OUTDIR/xnvme_fdp.fio" --output="$OUTDIR/xnvme_fdp_result.txt" --output-format="json"
    fi
}

# Takes two arguments
# 1 - duration
# 2 - interval
run_showcase_fdp() {
    local var OUTDIR="./fio/cachelib_workload" 

    setup_device_fdp_enabled
    python3 "$BENCHMARK_DIR/waf.py" "$OUTDIR/2_ruh_vary_write_rate/no_fdp.txt" $2 $(( $1 / $2 )) & $FIO "$OUTDIR/2_ruh_vary_write_rate/non_fdp.fio" --output="$OUTDIR/2_ruh_vary_write_rate/no_fdp_result.txt" --output-format="json"
    setup_device_fdp_enabled
    python3 "$BENCHMARK_DIR/waf.py" "$OUTDIR/2_ruh_vary_write_rate/fdp.txt" $2 $(( $1 / $2 )) & $FIO "$OUTDIR/2_ruh_vary_write_rate/fdp.fio" --output="$OUTDIR/2_ruh_vary_write_rate/fdp_result.txt" --output-format="json"
    setup_device_fdp_enabled
    python3 "$BENCHMARK_DIR/waf.py" "$OUTDIR/4_ruh_seq_and_rand/no_fdp.txt" $2 $(( $1 / $2 )) & $FIO "$OUTDIR/4_ruh_seq_and_rand/non_fdp.fio" --output="$OUTDIR/4_ruh_seq_and_rand/no_fdp_result.txt" --output-format="json"
    setup_device_fdp_enabled
    python3 "$BENCHMARK_DIR/waf.py" "$OUTDIR/4_ruh_seq_and_rand/fdp.txt" $2 $(( $1 / $2 )) & $FIO "$OUTDIR/4_ruh_seq_and_rand/fdp.fio" --output="$OUTDIR/4_ruh_seq_and_rand/fdp_result.txt" --output-format="json"

}

run_tester() {
    local var OUTDIR="./fio/test_runs/tester" 
    setup_device_fdp_enabled
    python3 "$BENCHMARK_DIR/waf.py" "$OUTDIR/tester.txt" $2 $(( $1 / $2 )) & $FIO "$OUTDIR/tester.fio" --output="$OUTDIR/tester_result.txt" --output-format="json"
}

WORKLOAD="database"
TEMP_SIZES=()
INTERVAL=0
DURATION=0
DEV_TYPE=""
BACKEND=""
while getopts ":w:i:d:v:b:t:" opt
    do 
        case $opt in
            w) echo $OPTARG; WORKLOAD=$OPTARG;;
            t) echo $OPTARG; TEMP_SIZES+=("$OPTARG");;
            i) echo $OPTARG; INTERVAL=$OPTARG;;
            d) echo $OPTARG; DURATION=$OPTARG;;
            v) echo $OPTARG; DEV_TYPE=$OPTARG;;
            b) echo $OPTARG; BACKEND=$OPTARG;;
        esac
done


if [[ $WORKLOAD == "database" ]]; then

    for tsize in "${TEMP_SIZES[@]}"
    do
      run_workload $WORKLOAD $tsize $DURATION $INTERVAL $DEV_TYPE $BACKEND
    done
elif [[ $WORKLOAD == "showcase" ]]; then
    run_showcase_fdp $DURATION $INTERVAL
elif [[ $WORKLOAD == "test" ]]; then
    run_showcase_fdp $DURATION $INTERVAL
fi
