#!/bin/bash

./run.sh
perf script | /home/pinar/.local/FlameGraph/stackcollapse-perf.pl > out.perf-folded 
/home/pinar/.local/FlameGraph/flamegraph.pl out.perf-folded > /home/pinar/ucmd.svg

