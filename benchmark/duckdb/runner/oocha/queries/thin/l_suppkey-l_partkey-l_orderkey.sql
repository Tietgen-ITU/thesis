SELECT l_suppkey, l_partkey, l_orderkey FROM lineitem GROUP BY l_suppkey, l_partkey, l_orderkey OFFSET offset
