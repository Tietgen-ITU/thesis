SELECT l_suppkey, l_partkey, l_shipinstruct, l_shipmode FROM lineitem GROUP BY l_suppkey, l_partkey, l_shipinstruct, l_shipmode OFFSET offset
