# Analyzing best option of disk spilling

I am running different queries with different configurations. I am measuring how much a query has spilled by utilizing the `duckdb_memory()` table function.
All queries are performed on the TPC-H generated table by the DuckDB team with a scaling factor of 1000.

```sql
select * from duckdb_memory();
```

## l_orderkey - 25%
```sql
SELECT l_orderkey FROM lineitem GROUP BY l_orderkey OFFSET 1499999999
```
| mem (MB) | threads | spilled GB | elapsed (seconds) |
| -------- | ------- | ---------- | ----------------- |
| 35000    | 96      | 29         | 11                |
| 25000    | 96      | 188        | 48                |
| 35000    | 24      | 21         | 18                |
| 25000    | 24      | 90         | 32                |
| 30000    | 24      | 63         | 26                |
| 20000    | 24      | 106        | 34                |

## l_suppkey, l_partkey, l_shipmode - 61%

```sql
SELECT l_suppkey, l_partkey, l_shipmode FROM lineitem GROUP BY l_suppkey, l_partkey, l_shipmode OFFSET 1603128962
```

| mem (MB) | threads | spilled GB | elapsed (seconds) |
| -------- | ------- | ---------- | ----------------- |
| 35000    | 96      | 175        | 73                |
| 25000    | 96      | NaN        | NaN               |
| 35000    | 24      | 171        | 70                |
| 25000    | 24      | 189        | 84                |
| 35000    | 32      | 169        | 69                |
| 25000    | 32      | 195        | 85                |

## l_orderkey, l_partkey - 99%

```sql
SELECT l_orderkey, l_partkey FROM lineitem GROUP BY l_orderkey, l_partkey OFFSET 5999989636;
```

| mem (MB) | threads | spilled GB | elapsed (seconds) |
| -------- | ------- | ---------- | ----------------- |
| 35000    | 96      | 131        | 59                |
| 25000    | 96      | 194        | 83                |
| 35000    | 24      | 123        | 59                |
| 25000    | 24      | 138        | 71                |
