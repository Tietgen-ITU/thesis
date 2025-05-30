#!/bin/bash

python3 plot_oocha.py ../results/shared_lock ./plots/oocha
python3 plot_tpch.py ../results/May23 ./plots/tpch
python3 plot_oocha-spill.py ../results/May23 ./plots/oocha/spill