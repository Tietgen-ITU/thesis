
import os
import pathlib
import subprocess
from pathlib import Path

class NvmeDevice:
    """
    Represents an NVMe device. This class is used to interact with the administrative interface of the NVMe device using the nvme client.
    """
    def __init__(self, device_path: str):
        self.device_path = device_path
        self.block_size = 4096
        self.device_id = int(device_path[-1])

        # TODO: Document environment variables in readme
        self.log_id = os.getenv("LOGIDWAF")
        self.sent_offset = os.getenv("SENT_OFFSET")
        self.written_offset = os.getenv("WRITTEN_OFFSET")

        self.number_of_blocks = self.__get_device_info(device_path)
    
    def __get_device_info(self, device_path: str):
        command = f"nvme id-ctrl {device_path} | grep 'tnvmcap' | sed 's/,//g' | awk -v BS={self.block_size} '{{print $3/BS}}'"
        block_output = subprocess.check_output(command, shell=True)
        number_of_blocks = int(block_output)

        return number_of_blocks

    def deallocate(self, namespace_id: int):
        """
        Deallocates all blocks on the device
        """

        os.system(f"nvme dsm {self.device_path} --namespace-id={namespace_id} --ad -s 0 -b {self.number_of_blocks}")


    def enable_fdp(self):
        """
        Enables flexible data placement(FDP) on the device
        """
        os.system(f"nvme set-feature {self.device_path} -f 0x1D -c 1 -s")

    def disable_fdp(self):
        """
        Disables flexible data placement(FDP) on the device
        """
        os.system(f"nvme set-feature {self.device_path} -f 0x1D -c 0 -s")

    def delete_namespace(self, namespace_id: int):
        """
        Deletes a namespace on the device
        """
        os.system(f"nvme delete-ns {self.device_path} --namespace-id={namespace_id}")

    def create_namespace(self, device_path: str, namespace_id: int, enable_fdp: bool = False):
        """
        Creates a namespace on the device and attaches it
        """

        # Create a namespace on the device
        result = 1
        if enable_fdp:
            result = os.system(f"nvme create-ns {device_path} -b {self.block_size} --nsze={self.number_of_blocks} --ncap={self.number_of_blocks} --nphndls=7 --phndls=0,1,2,3,4,5,6")
        else: 
            result = os.system(f"nvme create-ns {device_path} -b {self.block_size} --nsze={self.number_of_blocks} --ncap={self.number_of_blocks}", device_path, self.block_size, self.number_of_blocks, self.number_of_blocks)

        if result != 0:
            raise Exception("Failed to create namespace")

        # Attach the namespace to the device
        result = os.system(f"nvme attach-ns {device_path} --namespace-id={namespace_id} --controllers=0x7")

        if result != 0:
            raise Exception("Failed to attach namespace")
        
        return self.device_path + namespace_id, f"/dev/ng{self.device_id}n{namespace_id}"

    def get_written_bytes(self):
        cmd = f"""nvme get-log {self.device_path} --log-id={self.id_log} --log-len=512 -b"""
        res = subprocess.check_output(cmd, shell=True)
        host_written = int.from_bytes(res[self.sent_offset[0]:self.sent_offset[1]+1], byteorder="little") 
        media_written = int.from_bytes(res[self.written_offset[0]:self.written_offset[1]+1], byteorder="little") 

        if host_written == 0: return (0,0)

        return (host_written, media_written)


def calculate_waf(host_written_bytes, media_written_bytes):
    """
    Calculates the Write Amplification Factor (WAF) based on host and media written bytes
    """
    if host_written_bytes == 0:
        return 0

    return media_written_bytes / host_written_bytes

def setup_device(device: NvmeDevice, namespace_id:int = 1, enable_fdp: bool = False):
    """
    Sets up the device by creating a namespace and enabling FDP if required
    """

    device_ns_path = pathlib.Path(f"/dev/nvme1n{namespace_id}")
    if device_ns_path.exists():
        device.deallocate(namespace_id)
        device.delete_namespace(namespace_id)
    
    # Ensure that FDP is enabled / disabled
    if enable_fdp:
        device.enable_fdp()
    else:
        device.disable_fdp()
    
    # Create new namespace with a new configuration
    return device.create_namespace(device.device_path, namespace_id, enable_fdp)