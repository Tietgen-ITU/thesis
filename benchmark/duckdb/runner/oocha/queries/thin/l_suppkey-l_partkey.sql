SELECT l_suppkey, l_partkey FROM lineitem GROUP BY l_suppkey, l_partkey OFFSET offset
