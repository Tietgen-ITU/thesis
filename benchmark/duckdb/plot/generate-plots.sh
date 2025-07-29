#!/bin/bash

python3 plot_oocha.py ../results/output/oocha ./plots/oocha
python3 plot_oocha_single.py ../results/output/oocha-single ./plots/oocha/single_thread
python3 plot_tpch.py ../results/output/tpch ./plots/tpch
python3 plot_oocha-spill.py ../results/output/oocha-spill ./plots/oocha/spill