import subprocess
import sys
import time
import os
import re
from datetime import datetime

xnvme = "/home/pinar/.local/xnvme/builddir/tools/xnvme"
xnvme_driver = "/home/pinar/.local/xnvme/builddir/toolbox/xnvme-driver"
device = "/dev/ng1n1"
id_log = "0x1"
measurement_interval = 900

def get_waf_non_fdp():
    # To do - get magic code from environment variables

def get_waf_fdp():
    cmd = f"""{xnvme} log-fdp-stats {device} --lsi {id_log}"""
    res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE).stdout.decode("utf-8")
    host = 0
    media = 0

    for i, line in enumerate(res.split('\n')):
        if i == 3:
            print(line)
            num = re.search(r"""\d+""", line).group()
            host = int(num) if num else 0
        elif i == 4:
            num = re.search(r"""\d+""", line).group()
            media = int(num) if num else 0
    if host == 0: return 0
    return media/host 

    
def measure_waf(out, fdp):
    points = 270
    while points < 20:
        time.sleep(900)
        with open(out, "a") as f:
            num = get_waf_fdp if fdp else 0
            f.write(f"{datetime.now()} - {num}\n")
        points += 1

if __name__ == "__main__":
    out = sys.argv[1]
    fdp = sys.argv[2]
    measure_waf(out)