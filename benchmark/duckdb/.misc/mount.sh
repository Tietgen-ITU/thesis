#!/bin/bash

# TODO: Create namespaces with 50 % of the size of the device

# TODO: Format the namespace to ext4 and mount the second namespace to /mnt/benchmark

# Unmount the device aftwards
umount /dev/nvme1n1

# Then clean the device