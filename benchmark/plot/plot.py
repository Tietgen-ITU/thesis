from matplotlib import pyplot as plt
from pathlib import Path
from collections import defaultdict
import re
from datetime import datetime
import sys
import numpy as np
from matplotlib.ticker import MultipleLocator

def get_single_result(measurement):
    time, waf, host, media = measurement.split(",")
    return (float(waf), int(host), int(media))

def bytes_to_gb(value):
    return value / 1000000000

def get_results(result_path_str):
    res = defaultdict(tuple)

    bench_files_pattern = r"""^(?!.*result).*txt"""
    matched_files = []
    
    for path in Path(result_path_str).iterdir():
        if re.match(bench_files_pattern, str(path)):
            matched_files.append(path)
        
    for matched in matched_files:
        name = matched.stem
        with open(matched, "r") as file:
            measurements = file.readlines()

            wafs = []
            hosts = []
            medias = []

            last = get_single_result(measurements[0]) 
            
            for point in measurements[1:]:
                next = get_single_result(point)
                
                diff_host = next[1] - last[1]
                diff_media = next[2] - last[2]

                wafs.append(next[0])
                hosts.append(diff_host)
                medias.append(diff_media)
                last = next
            
            res[name] = (wafs, hosts, medias)
    
    return res


def plot_waf(result_path_str):
    results = get_results(result_path_str)

    tests = [("no_xnvme", "no_fdp", "fdp"), ("xnvme", "xnvme_no_fdp", "xnvme_fdp")]

    for test in tests:
        no_fdp_y = results[test[1]][0]
        fdp_y = results[test[2]][0]
        x_ticks = [x * 10 for x in range(0, len(no_fdp_y))]

        fig, ax = plt.subplots()
        ax.plot(x_ticks, no_fdp_y, label=test[1])
        ax.plot(x_ticks, fdp_y, label=test[2])

        ax.set_ylim(bottom=1)
        ax.set_xlabel("Minutes")
        ax.set_ylabel("Write Amplification Factor (WAF)")
        ax.xaxis.set_major_locator(MultipleLocator(60))
        ax.yaxis.set_major_locator(MultipleLocator(0.1))
        ax.legend(loc='upper left', ncols=1)

        plt.savefig(f"{result_path_str}/{test[0]}.pdf", format="pdf", bbox_inches="tight")

def plot_write(result_path_str):
    results = get_results(result_path_str)

    tests = [("no_xnvme", "no_fdp", "fdp"), ("xnvme", "xnvme_no_fdp", "xnvme_fdp")]

    for test in tests:
        no_fdp_host_y = list(map(bytes_to_gb, results[test[1]][1]))
        fdp_host_y = list(map(bytes_to_gb, results[test[2]][1]))
        no_fdp_media_y = list(map(bytes_to_gb, results[test[1]][2]))
        fdp_media_y = list(map(bytes_to_gb, results[test[2]][2]))
        x_ticks = [x * 10 for x in range(0, len(no_fdp_host_y))]

        fig, ax = plt.subplots()
        ax.plot(x_ticks, no_fdp_host_y, label=f"{test[1]}_host", color="r")
        ax.plot(x_ticks, fdp_host_y, label=f"{test[2]}_host", color="b")
        ax.plot(x_ticks, no_fdp_media_y, label=f"{test[1]}_media", linestyle="--", color="r")
        ax.plot(x_ticks, fdp_media_y, label=f"{test[2]}_media", linestyle="--", color="b")

        ax.set_xlabel("Minutes")
        ax.set_ylabel("GBs written last 10 min")
        ax.xaxis.set_major_locator(MultipleLocator(60))
        ax.yaxis.set_major_locator(MultipleLocator(0.05))
        ax.legend(loc='upper left', ncols=1)

        plt.savefig(f"{result_path_str}/{test[0]}_write.pdf", format="pdf", bbox_inches="tight")



if __name__ == "__main__":
    result_path = sys.argv[1]
    plot_waf(result_path)
    plot_write(result_path)