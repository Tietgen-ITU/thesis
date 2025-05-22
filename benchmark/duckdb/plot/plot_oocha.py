import os
import sys 
import parse
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np

def calculate_oocha_aggregates(benchmark_runs: list[parse.BenchmarkRun]):
    grouping_thin_results = defaultdict(lambda: list())
    grouping_wide_results = defaultdict(lambda: list())

    for grouping in range(1, 14):
        agg_thin_result = [0] * 3
        agg_wide_result = [0] * 3

        for run in benchmark_runs:
            index = 0

            if run.device == "nvme":
                index = 1 if not run.fdp else 2

            agg_thin_result[index] = sum(run.results[(grouping, False)]) / len(run.results[(grouping, False)])
            agg_wide_result[index] = sum(run.results[(grouping, True)]) / len(run.results[(grouping, True)])

        grouping_thin_results[grouping] = agg_thin_result
        grouping_wide_results[grouping] = agg_wide_result
    
    return grouping_thin_results, grouping_wide_results

def plot_bar_oocha_results(results: dict, x_names: list, title: str, output_dir: str, file_name: str):

    groupings = [group for group in results.keys()] 
    groupings.sort()
    categories = groupings
    x = np.arange(len(categories))

    fig, ax = plt.subplots(layout='constrained')

    width = 0.25  # the width of the bars
    multiplier = 0
    for idx, name in enumerate(x_names):
        res = []
        for grouping in range(1, 14):
            res.append(results[grouping][idx])

        offset = width * multiplier
        print(res)
        rects = ax.bar(x + offset, res, width, label=name)
        multiplier += 1

    ax.set_ylabel('Elapsed Time (ms)')
    ax.set_title(title)
    ax.set_xticks(x + width, categories)
    ax.legend()

    format = "pdf"
    out_path = os.path.join(output_dir, file_name)
    plt.savefig(out_path,
        format=format, bbox_inches="tight")


def main(results_dir: str, output_dir:str):

    benchmark_runs = defaultdict(lambda: list())
    legend = ["normal", "io_uring_cmd", "io_uring_cmd with fdp"]
    
    for file_name in os.listdir(results_dir):
        if not (file_name.startswith("oocha-reps") and file_name.endswith("fdp.csv")):
            continue
        
        parsed: parse.BenchmarkRun = parse.parse_oocha_results(os.path.join(results_dir, file_name))

        benchmark_runs[parsed.scale_factor].append(parsed)

    memory = benchmark_runs[2][0].memory / 1000
    threads = benchmark_runs[2][0].threads
    plot_prefix_name = f"OOCHA Elapsed Time, {memory} GB, {threads} Threads"
    
    for scale_factor in benchmark_runs.keys():
        results_thin, results_wide = calculate_oocha_aggregates(benchmark_runs[scale_factor])
        plot_bar_oocha_results(results_wide, legend, f"{plot_prefix_name}, SF {scale_factor}, wide", output_dir, f"oocha_wide_{scale_factor}.pdf")
        plot_bar_oocha_results(results_thin, legend, f"{plot_prefix_name}, SF {scale_factor}, thin", output_dir, f"oocha_thin_{scale_factor}.pdf")



if __name__ == '__main__':

    if len(sys.argv) != 3:
        print("Usage: python prepcounts.py <oocha_data_dir>")
        sys.exit(1)

    oocha_data_dir = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    main(oocha_data_dir, output_dir)