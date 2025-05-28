import os
import sys 
import parse
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np

def calculate_oocha_elapsed_aggregates(benchmark_runs: list[parse.BenchmarkRun]):
    results = []

    for grouping in range(1):
        agg_result = [0] * 3

        for run in benchmark_runs:
            index = 0

            if run.device == "nvme":
                index = 1 if not run.fdp else 2

            count = len(run.results[1])
            average = sum(run.results[1]) / len(run.results[1])
            std_deviation = np.std(run.results[1])
            percentile_ninenine = np.percentile(run.results[1], 99)
            percentile_ninefive = np.percentile(run.results[1], 95)
            agg_result[index] = (count, average, std_deviation, percentile_ninenine, percentile_ninefive)

        results = agg_result
    
    return results

def plot_oocha_spill_results(results: dict, x_names: list, title: str, output_dir: str, file_name: str):

    fig, ax = plt.subplots(layout='constrained')
    linestyles = ['-', '--', ':']  # solid, dashed, dotted

    y_display = [n*10 for n in range(0, len(results[0]))]
    width = 0.25  # the width of the bars
    multiplier = 0
    for idx, name in enumerate(x_names):

        data = results[idx]
        ax.plot(y_display, data, linestyle=linestyles[idx], label=name)

    ax.set_ylim(0, 3)
    ax.set_ylabel('Write Amplification Factor')
    ax.set_xlabel('Duration (minutes)')
    ax.set_title(title)
    ax.legend()

    format = "pdf"
    out_path = os.path.join(output_dir, file_name)
    plt.savefig(out_path,
        format=format, bbox_inches="tight")

def plot_oocha_spill_bytes_results(results: dict, x_names: list, title: str, y_label:str, output_dir: str, file_name: str):

    fig, ax = plt.subplots(layout='constrained')

    y_display = [n*10 for n in range(0, len(results[0][0]))]
    width = 0.25  # the width of the bars
    multiplier = 0
    for idx, name in enumerate(x_names):

        host_data, media_data = results[idx]
        ax.plot(y_display, host_data, label=f"{name} (Host Written)")
        ax.plot(y_display, media_data, linestyle='--', label=f"{name} (Media Written)")

    ax.set_ylabel(y_label)
    ax.set_xlabel('Duration (minutes)')
    ax.set_title(title)
    ax.legend()

    format = "pdf"
    out_path = os.path.join(output_dir, file_name)
    plt.savefig(out_path,
        format=format, bbox_inches="tight")

def create_stats_table(results: list, x_names: list):

    lines = []
    header = f"{'Configuration':<25} {'Count':<8} {'Average':<10} {'Standard Deviation':<20} {'P95':<10} {'P99':<10}"
    lines.append(header)
    lines.append('-' * len(header))

    # Rows
    for idx, name in enumerate(x_names):
        if name == "normal": # TODO: we should not skip this when the results are present
            continue

        count, avg, std_dev, p99, p95 = results[idx]
        lines.append(f"{name:<25} {count:<8} {avg:<10.2f} {std_dev:<20} {p95:<10.2f} {p99:<10.2f}")
    
    return "\n".join(lines)


def main(results_dir: str, output_dir:str):

    benchmark_runs = []
    benchmark_waf_runs = []


    legend = ["normal", "io_uring_cmd", "io_uring_cmd with fdp"]
    
    for file_name in os.listdir(results_dir):
        if file_name.startswith("oocha-spill") and file_name.endswith("fdp.csv"):
            parsed_elapsed: parse.BenchmarkRun = parse.parse_oocha_spill_elapsed_results(os.path.join(results_dir, file_name))
            benchmark_runs.append(parsed_elapsed)
        
        if file_name.startswith("oocha-spill") and file_name.endswith("fdp-device.csv"):
            parsed_waf: parse.BenchmarkRun = parse.parse_oocha_spill_waf_results(os.path.join(results_dir, file_name))
            benchmark_waf_runs.append(parsed_waf)

    memory = benchmark_runs[0].memory / 1000
    threads = benchmark_runs[0].threads

    elapsed_results = calculate_oocha_elapsed_aggregates(benchmark_runs)
    stats_table = create_stats_table(elapsed_results, legend)

    with open(os.path.join(output_dir, "oocha_spill_stats.txt"), "w") as f:
        f.write(stats_table)

    
    waf_results = []
    bytes_written_results = []
    bytes_written_results_raw = []
    mb = 1024 * 1024
    gb = mb * 1024
    for run in benchmark_waf_runs:
        results = [run.results[minute*10][0][2] for minute in range(0, len(run.results))]
        waf_results.append(results)

        host_written = [(run.results[minute*10][0][0] * 512)/gb for minute in range(0, len(run.results))]
        media_written = [(run.results[minute*10][0][1] * 512)/gb for minute in range(0, len(run.results))]

        host_written_original = [run.results[minute*10][0][0]/mb for minute in range(0, len(run.results))]
        media_written_original = [run.results[minute*10][0][1]/mb for minute in range(0, len(run.results))]

        bytes_written_results.append((host_written, media_written))
        bytes_written_results_raw.append((host_written_original, media_written_original))
    
    plot_prefix_name = f"OOCHA-Spill - Write Amplification"
    plot_bytes_written_prefix_name = f"OOCHA-Spill - Bytes Written"
    plot_oocha_spill_results(waf_results[1:], legend[1:], f"{plot_prefix_name}", output_dir, f"oocha_spill_waf.pdf")
    plot_oocha_spill_bytes_results(bytes_written_results[1:], legend[1:], f"{plot_bytes_written_prefix_name}", "Data Written to the Device (GB)", output_dir, f"oocha_spill_bytes.pdf")
    plot_oocha_spill_bytes_results(bytes_written_results_raw[1:], legend[1:], f"{plot_bytes_written_prefix_name}", "Data Written to the Device (MB)", output_dir, f"oocha_spill_bytes_raw.pdf")


if __name__ == '__main__':

    if len(sys.argv) != 3:
        print("Usage: python3 plot_oocha-spill.py <oocha_data_dir> <output_dir>")
        sys.exit(1)

    oocha_data_dir = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    main(oocha_data_dir, output_dir)