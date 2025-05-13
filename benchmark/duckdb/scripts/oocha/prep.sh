#!/bin/bash

echo "Generate queries"
python3 querygen.py

echo "Generate data"
python3 querygen.py /mnt/duckdb