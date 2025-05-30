SELECT l_partkey, l_returnflag, l_linestatus FROM lineitem GROUP BY l_partkey, l_returnflag, l_linestatus OFFSET offset
