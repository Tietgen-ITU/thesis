SELECT l_suppkey, l_partkey, l_shipinstruct FROM lineitem GROUP BY l_suppkey, l_partkey, l_shipinstruct OFFSET offset
