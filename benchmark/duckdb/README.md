# DuckDB Benchmarks

This directory contains files to run benchmarks for the duckdb instance referenced by the nvmefs git submodule. The goal of this benchmark is measure the Write Amplification Factor(WAF) of an NVMe device when using an analytical database system such as DuckDB. In particular we want to see if Flexible Data Placement have an impact on WAF. 

## Prerequisites

- **[nvme-cli](https://github.com/linux-nvme/nvme-cli)**
- **Python**: v3.13.2
- **nvmefs**: needs to be built from the git submodule

When running the benchmark, the script will create a python environment and install the necessary dependencies, including the DuckDB python client build from the contents of the Git submodule nvmefs.

## How to run the benchmark

> [!IMPORTANT]
> Before trying to run the benchmark it is important that the `nvmefs` extension has been built. Take a look at the [project readme](../../README.md) of this repo on how to build the extension.

In order to run the benchmark, you first need to setup up the python environment:

```sh
chmod +x ./init.sh
chmod +x ./run.sh
source ./init.sh
```

However, if you are using fish then you would have to source the environment after running the above commands:

```sh
chmod +x ./run.sh
sh ./init.sh
source .venv/bin/activate.fish
```

> [!NOTE]
> If you encounter an error indicating the device cannot be opened, try running the DuckDB executable with elevated privileges (e.g., using `sudo`).

Running the benchmarks is as simple as:
```sh
./run.sh
```
