# Benchmark Runners

This directory contains the interfaces and implementations required by `../benchmark.py` to execute benchmarks for DuckDB. It provides a factory to create the appropriate benchmark setup functions and runners, ensuring a modular and extensible design for benchmarking.

## Purpose

The benchmark runners in this directory are responsible for:
- Setting up the environment for each benchmark.
- Executing the benchmarks with the specified configurations.
- Collecting and reporting results in a standardized format(csv).

These runners are designed to integrate seamlessly with the `../benchmark.py` script, which orchestrates the overall benchmarking process.

## Implemented Benchmarks

The following benchmarks are implemented in this directory:
- **TPCH Benchmark**: Executes the TPC-H queries to evaluate performance on analytical workloads.

Each benchmark is implemented with a corresponding runner and setup function, ensuring flexibility and reusability.
