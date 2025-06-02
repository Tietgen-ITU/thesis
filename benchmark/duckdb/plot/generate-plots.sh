#!/bin/bash

python3 plot_oocha.py ../results/shared_lock ./plots/oocha
python3 plot_oocha_single.py ../results/ocha_single_thread ./plots/oocha/single_thread
python3 plot_tpch.py ../results/May23 ./plots/tpch
python3 plot_oocha-spill.py ../results/May23 ./plots/oocha/spill