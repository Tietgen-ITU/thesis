#!/bin/bash

current_dir=$(pwd)

cd ../..
source ./init.sh
cd $current_dir

echo "Generate data"
python3 datagen.py /mnt/duckdb

echo "Generate counts data"
python3 prepcounts.py /mnt/duckdb