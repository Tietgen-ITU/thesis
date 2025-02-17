# NVMe Memory Layout

As our project communicates directly with the device, the "old" file abstractions is not really useable. DuckDB structures different categories of data in files, and have used the operating systems file abstraction layer. By using files they can still manage how the data is structured in the files, but still abstract the lower level details of communicating with the device. 

NvmeFs uses xNVMe to communicate with the device. By bypassing the file abstraction layer, the management of where the data is placed on the device(i.e. the NVMe SSD) is up to the user(i.e. the application). Since we want to integrate NvmeFs into the existing interface of DuckDB, we need to create a translation layer of reading and writing of files to actual LBAs inside the device.

#### Goal 

The goal of this document is to highlight the places in DuckDB where it interacts with the `FileSystem` and show different ideas to how we are going to structure the management of the data that is being persistently stored in the NVMe device. Additionally, we will provide a mapping mechanism going from the existing file abstractions to LBAs that is required by the device in order to write data to it.

## DuckDB

As mentioned DuckDB uses files to abstract how to manage their data. In each of their files they handle the management of data. DuckDB do not manage a lot of different files. We have managed to find three categories of files that DuckDB create and manage:

**Database Catalog** contains all the data of a database. That is the schemas, tables, indexes, data in tables, etc. The database catalog is one single file and is managed in collaboration between the [`DatabaseStorageManager`](https://github.com/duckdb/duckdb/blob/19864453f7d0ed095256d848b46e7b8630989bac/src/include/duckdb/storage/storage_manager.hpp) and [`SingleFileBlockManager`](https://github.com/duckdb/duckdb/blob/19864453f7d0ed095256d848b46e7b8630989bac/src/include/duckdb/storage/single_file_block_manager.hpp)

**Write-Ahead-Log (WAL)** is responsible to log the actions taken such that if a crash failure happens, then it can recover the steps it took to get the database to a particular state. The path of the write-ahead-log is the same as the path of the database, except that it will append `.wal` at the end. The write ahead log managed by the code in `write_ahead_log.cpp`.

**Temporary files** is used when a query has intermediary data that is larger-than-memory. All temporary files are managed by the `TemporaryFileManager` and the location of the temporary files is from the `DBConfig.options.temporary_directory`. 
