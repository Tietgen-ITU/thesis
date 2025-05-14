SELECT l_suppkey, l_returnflag, l_linestatus FROM lineitem GROUP BY l_suppkey, l_returnflag, l_linestatus OFFSET offset
