from dataclasses import dataclass
from collections import defaultdict
import argparse
import os
from typing import Tuple, List

files = [("no_fdp.fio", False), ("fdp.fio", True), ("xnvme_no_fdp.fio", False), ("xnvme_fdp.fio", True)]

@dataclass 
class Arguments:
    workload: str = ""
    device: str = ""
    backend: str = ""
    out_dir: str = ""
    iodepth: int = 0
    block_size: str = ""
    threads: int = 0
    use_threads: bool = False
    timebased: bool = True
    duration: int = 0
    percent_temp_size: int = 0
    fill_times: int = 0
    nsid: int = 0


    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "-w",
            "--workload",
            type=str,
            help="The workload that should be generated",
            required=True
        )

        parser.add_argument(
            "--device",
            type=str,
            help="The device that will be used",
            required=True
        )

        parser.add_argument(
            "-be",
            "--backend",
            type=str,
            help="The IO backend that will be used",
            required=True
        )

        parser.add_argument(
            "-o",
            "--out_dir",
            type=str,
            help="Path to folder where the generated files should be placed",
            default="."
        )

        parser.add_argument(
            "-iod",
            "--iodepth",
            type=int,
            help="IO depth to be used",
            default=32
        )

        parser.add_argument(
            "-t",
            "--threads",
            type=int,
            help="Number of threads that will be used",
            default=1
        )

        parser.add_argument(
            "-bs",
            "--block_size",
            type=str,
            help="read/write granularity"
        )
        
        parser.add_argument(
            "--use_threads",
            type=bool,
            help="Use of threads instead of processes (necessary for spdk)",
            default=False
        )

        parser.add_argument(
            "--timebased",
            help="Be a time based experiment",
            action="store_true",
            default=False
        )

        parser.add_argument(
            "-d",
            "--duration",
            type=int,
            help="Duration of the experiment measured in seconds"
        )

        parser.add_argument(
            "-pcts",
            "--percent_temp_size",
            type=int,
            help="Size of temporary storage, specified in percentage of disk",
        )

        parser.add_argument(
            "-ft",
            "--fill_times",
            type=int,
            help="The amount of times the device should be filled in a duration",
            default=1
        )

        parser.add_argument(
            "--nsid",
            type=int,
            default=1
        )

        args = parser.parse_args()
        
        if args.workload == "database":
            error = False
            if args.block_size == "":
                error = True
                print("Error: block_size not specified it. Provide it with -bs")
            if args.timebased and args.duration == 0:
                error = True
                print("Error: time based experiment, duration not specified it. Provide it with -d")
            if args.percent_temp_size == 0:
                error = True
                print("Error: temporary storage size not specified it. Provide it with -pcts")
            if error:
                return
        
        arguments: Arguments = Arguments(
            workload=args.workload,
            device=args.device,
            iodepth=args.iodepth,
            backend=args.backend,
            out_dir=args.out_dir,
            block_size=args.block_size,
            threads=args.threads,
            use_threads=args.use_threads,
            timebased=args.timebased,
            duration=args.duration,
            percent_temp_size=args.percent_temp_size,
            fill_times=args.fill_times,
            nsid=args.nsid
        )

        return arguments

class Database:
    def _gen_global(args: Arguments, fdp: bool, filename: str) -> str:
        sec_global = f"""[global]
filename={args.device}
iodepth={args.iodepth}
bs={args.block_size}
numjobs={args.threads}
group_reporting
norandommap=1
"""         
        if "xnvme" in filename:
            sec_global += "thread=1\n"
            sec_global += "ioengine=xnvme\n"
            if args.backend == "spdk":
                sec_global += f"xnvme_be={args.backend}\n"
                sec_global += f"xnvme_dev_nsid={args.nsid}\n"
            else:
                sec_global += f"xnvme_async={args.backend}\n"
        else:
            sec_global += f"ioengine={args.backend}\n"
        
        if fdp:
            sec_global += "fdp=1\n"

        if args.timebased:
            sec_global += "time_based=1\n"
            sec_global += f"runtime={args.duration}\n"
        
        return sec_global
    
    def _gen_jobs(args: Arguments, fdp: bool, jobs: List[str]):
        cap_in_mib = 3_585_815

        # Rate to fill full device X the amount of fill times
        rate_full_device = (cap_in_mib / args.duration) * args.fill_times
        
        info = defaultdict(lambda: defaultdict(int))
        info["temporary"]["size"] = args.percent_temp_size;
        info["temporary"]["offset"] = 100 - info["temporary"]["size"]
        info["temporary"]["rate"] = int(rate_full_device * (info["temporary"]["size"] / 100))
        info["temporary"]["method"] = "randrw"

        info["wal"]["size"] = 1
        info["wal"]["offset"] = info["temporary"]["offset"] - 1
        info["wal"]["rate"] = int(rate_full_device * (info["wal"]["size"] / 100))
        info["wal"]["method"] = "write"

        info["database"]["size"] = 100 - info["temporary"]["size"] - info["wal"]["size"]
        info["database"]["offset"] = 0
        info["database"]["rate"] = int(rate_full_device * (info["database"]["size"]/100))
        info["database"]["method"] = "randrw"  

        total = []

        for job in jobs:
            sec_job = f"""\n[{job}]
rw={info[job]['method']}
offset={info[job]['offset']}%
size={info[job]['size']}%
rate={info[job]['rate']}mi,{info[job]['rate']}mi\n"""
            if job == "database":
                sec_job += "rwmixwrite=10%\n"
            if fdp:
                if job == "database":
                    sec_job += "fdp_pli=0,1,2,3,4\n"
                elif job == "wal":
                    sec_job += "fdp_pli=5\n"
                elif job == "temporary":
                    sec_job += "fdp_pli=6\n"
            sec_job += "new_group"
            total.append(sec_job)
        
        return '\n'.join(total)
        
    @staticmethod
    def gen_database_workload(args: Arguments):
        jobs = ["database", "temporary", "wal"]
        os.makedirs(args.out_dir, exist_ok=True)
        for (file, fdp) in files:
            with open(f"{args.out_dir}/{file}", mode="w+") as fd:
                fd.write(Database._gen_global(args, fdp, file))
                fd.write(Database._gen_jobs(args, fdp, jobs))

if __name__ == "__main__":
    args: Arguments = Arguments.parse_args()

    if args.workload == "database":
        Database.gen_database_workload(args)