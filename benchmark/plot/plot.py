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
def bytes_to_gib(value):
    return value / 1073741824

def to_coords(seq):
    return map(lambda x: ((x[0]+1)*10, x[1]), enumerate(seq))

def get_results(result_path_str):
    res = defaultdict(tuple)
    counter_upscale = 512

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
            hosts_gib = []
            media_gib = []

            last = get_single_result(measurements[0]) 
            
            for point in measurements[1:]:
                next = get_single_result(point)
                
                diff_host = (next[1] - last[1]) * counter_upscale
                diff_media = (next[2] - last[2]) * counter_upscale

                wafs.append(next[0])
                hosts.append(diff_host)
                medias.append(diff_media)
                hosts_gib.append(bytes_to_gib(diff_host))
                media_gib.append(bytes_to_gib(diff_media))
                last = next

            with open(f"{result_path}/{name}_results.csv", mode="w+") as f:
                f.write(" ".join(map(str, to_coords(wafs))))
                f.write("\n")
                f.write(" ".join(map(str, to_coords(hosts_gib))))
                f.write("\n")
                f.write(" ".join(map(str, to_coords(media_gib))))
                f.write("\n")
            
            res[name] = (wafs, hosts, medias)
    
    pairs = [("no_fdp", "fdp"), ("xnvme_no_fdp", "xnvme_fdp")]

    for (nofdp, fdp) in pairs:
        if len(res[nofdp][0]) < len(res[fdp][0]):
            length = len(res[nofdp][0])
            new_waf = res[fdp][0][:length]
            new_host = res[fdp][1][:length]
            new_media = res[fdp][2][:length]
            res[fdp] = (new_waf, new_host, new_media)
        elif len(res[nofdp][0]) > len(res[fdp][0]):
            length = len(res[fdp][0])
            new_waf = res[nofdp][0][:length]
            new_host = res[nofdp][1][:length]
            new_media = res[nofdp][2][:length]
            res[nofdp] = (new_waf, new_host, new_media)

    return res


def plot_waf(result_path_str):
    results = get_results(result_path_str)

    tests = [("no_xnvme", "no_fdp", "fdp"), ("xnvme", "xnvme_no_fdp", "xnvme_fdp")]

    for test in tests:
        no_fdp_y = results[test[1]][0]
        fdp_y = results[test[2]][0]
        x_ticks = [x * 10 for x in range(1, len(no_fdp_y)+1)]

        fig, ax = plt.subplots()
        ax.plot(x_ticks, no_fdp_y, label=test[1], color="r")
        ax.plot(x_ticks, fdp_y, label=test[2], color="b")

        ax.set_ylim(bottom=1)
        ax.set_xlabel("Minutes")
        ax.set_ylabel("Write Amplification Factor (WAF)")
        ax.xaxis.set_major_locator(MultipleLocator(60))
        ax.yaxis.set_major_locator(MultipleLocator(0.2))
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
        x_ticks = [x * 10 for x in range(1, len(no_fdp_host_y)+1)]

        fig, ax = plt.subplots()
        ax.plot(x_ticks, no_fdp_host_y, label=f"{test[1]}_host", linestyle="dotted", color="r")
        ax.plot(x_ticks, fdp_host_y, label=f"{test[2]}_host", linestyle="dotted", color="b")
        ax.plot(x_ticks, no_fdp_media_y, label=f"{test[1]}_media", linestyle="dashed", color="r")
        ax.plot(x_ticks, fdp_media_y, label=f"{test[2]}_media", linestyle="dashed", color="b")

        ax.set_xlabel("Minutes")
        ax.set_ylabel("GBs written last 10 min")
        ax.xaxis.set_major_locator(MultipleLocator(30))
        ax.yaxis.set_major_locator(MultipleLocator(200))
        ax.legend(loc='upper left', ncols=1)

        plt.savefig(f"{result_path_str}/{test[0]}_write.pdf", format="pdf", bbox_inches="tight")



if __name__ == "__main__":
    result_path = sys.argv[1]
    plot_waf(result_path)
    plot_write(result_path)