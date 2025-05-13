#!/bin/bash

DEVICE=$1
NS_ID=$2

echo "Unmounting ${DEVICE}n${NS_ID}"
umount -l "${DEVICE}n${NS_ID}"

nvme dsm $DEVICE --namespace-id=$NS_ID --ad -s 0 -b 500170752
nvme delete-ns $DEVICE --namespace-id=$NS_ID