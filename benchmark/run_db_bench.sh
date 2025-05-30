#!/bin/bash

# Run the database workload for 3 hours, query waf every 10 min for each temporary size, so (3 * 4 * 4) hours
sh bench.sh -w database -i 600  -d 10800 -v generic -b io_uring_cmd -t 5 -t 10 -t 25 -t 50
