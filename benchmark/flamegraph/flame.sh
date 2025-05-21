#!/bin/bash

source /home/pinar/.bashrc
source ./init.sh

./run.sh
perf script | /home/pinar/.local/FlameGraph/stackcollapse-perf.pl > out.perf-folded 
/home/pinar/.local/FlameGraph/flamegraph.pl out.perf-folded > /home/pinar/ucmd.svg

