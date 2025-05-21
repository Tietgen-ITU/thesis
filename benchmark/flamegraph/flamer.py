import duckdb
import sys
import os

def collect(ctl_fd, ctl_fd_ack):
    with os.fdopen(ctl_fd, mode="w") as write_fd:
        with os.fdopen(ctl_fd_ack, mode="r") as read_fd:
            with duckdb.connect("flamer.db", config={"allow_unsigned_extensions": "true"}) as con:
                con.install_extension("../../nvmefs/build/release/extension/nvmefs/nvmefs.duckdb_extension")
                con.load_extension("nvmefs")

                con.query(f"ATTACH DATABASE 'nvmefs://flamer.db' AS flamer (READ_WRITE);")
                con.query(f"use flamer;")
                con.query(f"set memory_limit='3500MB';")
                con.query(f"set threads to 4;")

                write_fd.write("enable\n")
                res = read_fd.read(5)
                if res != "ack\n":
                    raise Exception("no ack from fd")
                con.query(f"SELECT count(*) FROM (SELECT distinct(l_orderkey) FROM lineitem)")
                write_fd.write("disable\n")
                res = read_fd.read(5)
                if res != "ack\n":
                    raise Exception("no ack from fd")


if __name__ == "__main__":
    ctl_fd = sys.argv[1]
    ctl_fd_ack = sys.argv[2]

    collect(ctl_fd, ctl_fd_ack)