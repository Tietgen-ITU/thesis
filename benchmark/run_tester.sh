#!/bin/bash

# Run the tester workload query waf every minute in 15 min
sh bench.sh -w test -i 60  -d 900
