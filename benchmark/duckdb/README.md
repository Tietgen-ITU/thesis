# DuckDB Benchmarks

This directory contains files to run benchmarks for the duckdb instance referenced by the nvmefs git submodule. The goal of this benchmark is measure the Write Amplification Factor(WAF) of an NVMe device when using an analytical database system such as DuckDB. In particular we want to see if Flexible Data Placement has a positive effect on WAF. 

## How to run the benchmark

> [!IMPORTANT]
> Before trying to run the benchmark it is important that the `nvmefs` extension has been built. Take a look at the [project readme](../../README.md) of this repo on how to build the extension.

In order to run the benchmark, you first need to setup up the python environment:

```sh
chmod +x ./init.sh
source ./init.sh
```

However, if you are using fish then you would have to source the environment after running the above commands:

```sh
sh ./init.sh
source .venv/bin/activate.fish
```
