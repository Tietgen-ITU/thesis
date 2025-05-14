SELECT l_orderkey, l_suppkey FROM lineitem GROUP BY l_orderkey, l_suppkey OFFSET offset
