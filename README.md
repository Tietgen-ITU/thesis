# Thesis 🏆 

This project is the Master's thesis of Emil (@emiloh) and Andreas (@arnenator) at the IT University of Copenhagen. The objective of this research is to evaluate the impact of an NVMe SSD with Flexible Data Placement when implemented in a Database System. Specifically, the focus is on analyzing Write Amplification (WA).

## Acknowledgements

This project is accomplished with collaboration from Samsung Memory Research Center and supervised by Pinar Tözün, Marcel Weisgut, and Vivek Shah.

## Building nvmefs 🛠️

To build nvmefs, it is necessary to install the required tools beforehand. Alternatively, you can use the development container, which comes with all prerequisites pre-installed.

After prerequisties are installed type in:

```bash
cd nvmefs/
GEN=ninja make release
```

The build binaries are stored in `nvmefs/build/release` and the extension that can be loaded into client programs is stored in `nvmefs/build/release/extension/nvmefs/nvmefs.duckdb_extension`