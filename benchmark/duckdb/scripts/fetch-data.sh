#!/bin/bash

DEVICE=$1
NS_ID=$2

BLOCK_SIZE=512


# Creates a namespace with ~2TB of space
nvme create-ns $DEVICE -b 512 --nsze=1640766128 --ncap=1640766128
nvme attach-ns $DEVICE --namespace-id=$NS_ID --controllers=0

# Format the namespace with a filesystem
mkfs.ext4 -b 4096 "${DEVICE}n${NS_ID}"

if [ ! -d "/mnt/duckdb" ]; then
    mkdir -p /mnt/duckdb
else
    echo "Directory /mnt/duckdb already exists. Skipping creation."
fi

echo "Mounting ${DEVICE}n${NS_ID} to /mnt/duckdb"
mount "${DEVICE}n${NS_ID}" /mnt/duckdb

CURRENT_DIR=$(pwd)

cd /mnt/duckdb

echo "Fetching tpch data sf1"
wget https://blobs.duckdb.org/data/tpch-sf1.db

echo "Fetching tpch data sf3"
wget https://blobs.duckdb.org/data/tpch-sf3.db

echo "Fetching tpch data sf10"
wget https://blobs.duckdb.org/data/tpch-sf10.db

echo "Fetching tpch data sf100"
wget https://blobs.duckdb.org/data/tpch-sf100.db

echo "Fetching tpch data sf300"
wget https://blobs.duckdb.org/data/tpch-sf300.db

echo "Fetching tpch data sf1000"
wget https://blobs.duckdb.org/data/tpch-sf1000.db

# echo "Fetching tpch data sf3000"
# wget https://blobs.duckdb.org/data/tpch-sf3000.db

cd $CURRENT_DIR