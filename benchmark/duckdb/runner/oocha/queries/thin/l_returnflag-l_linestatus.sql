SELECT l_returnflag, l_linestatus FROM lineitem GROUP BY l_returnflag, l_linestatus OFFSET offset
