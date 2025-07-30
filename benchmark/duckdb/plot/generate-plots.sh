#!/bin/bash

python3 plot_oocha.py ../results/oocha ./plots/oocha
python3 plot_oocha_single.py ../results/oocha-single ./plots/oocha/single_thread
python3 plot_tpch.py ../results/tpch ./plots/tpch
python3 plot_oocha-spill.py ../results/oocha-spill ./plots/oocha/spill