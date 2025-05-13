#!/bin/bash

current_dir=$(pwd)

cd ../..
source ./init.sh
cd $current_dir

echo "Generate queries"
python3 querygen.py

echo "Generate data"
python3 querygen.py /mnt/duckdb