import subprocess
import sys
import time
import os
import re
from datetime import datetime

nvme = "/home/pinar/.local/nvme-cli/.build/nvme"
xnvme = "/home/pinar/.local/xnvme/builddir/tools/xnvme"
xnvme_driver = "/home/pinar/.local/xnvme/builddir/toolbox/xnvme-driver"
device = "/dev/ng1n1"
id_log = os.getenv("LOGIDWAF")
id_log_xnvme = "0x1"
sent_offset = list(map(int, os.getenv("SENT_OFFSET").split("-")))
written_offset = list(map(int, os.getenv("WRITTEN_OFFSET").split("-")))
measurement_interval = 900
measurement_duration = 24 # every 15 min for 6 hours

def get_waf_non_fdp(last_host, last_media):
    cmd = f"""{nvme} get-log {device} --log-id={id_log} --log-len=512 -b"""
    res = subprocess.check_output(cmd, shell=True)
    host = int.from_bytes(res[sent_offset[0]:sent_offset[1]+1], byteorder="little") 
    media = int.from_bytes(res[written_offset[0]:written_offset[1]+1], byteorder="little") 
    
    diff_host = host - last_host
    diff_media = media - last_media

    return (diff_media/diff_host, host, media)

def get_waf_fdp(last_host, last_media):
    cmd = f"""{xnvme} log-fdp-stats {device} --lsi {id_log_xnvme}"""
    res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE).stdout.decode("utf-8")
    host = 0
    media = 0

    for i, line in enumerate(res.split('\n')):
        if i == 3:
            num = re.search(r"""\d+""", line).group()
            host = int(num) if num else 0
        elif i == 4:
            num = re.search(r"""\d+""", line).group()
            media = int(num) if num else 0
    if host == 0: return 0
    
    diff_host = host - last_host
    diff_media = media - last_media

    return (diff_media/diff_host, host, media)

def measure_waf(out, fdp):
    initial_stats = get_waf_non_fdp()
    current_host = initial_stats[1]
    current_media = initial_stats[2]

    points = 0
    max_points = measurement_duration
    waf_file = open(out, "w+")
    while points < max_points:
        time.sleep(measurement_interval)
        waf_stats = get_waf_fdp(current_host, current_media) if fdp else get_waf_non_fdp(current_host, current_media)
        current_host = waf_stats[1]
        current_media = waf_stats[2]
        waf_file.write(f"{datetime.now()} - {waf_stats}\n")
        points += 1
    waf_file.flush()
    os.fsync(waf_file.fileno())
    waf_file.close()

if __name__ == "__main__":
    out = sys.argv[1]
    fdp = False
    if sys.argv[2] == "true":
        fdp = True
    measure_waf(out, fdp)