SELECT l_orderkey, l_returnflag, l_linestatus FROM lineitem GROUP BY l_orderkey, l_returnflag, l_linestatus OFFSET offset
